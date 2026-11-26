"""Migrazioni dello schema versionate e idempotenti.

Le vecchie tabelle vengono mantenute: gli ALTER sono incrementali e non
cancellano i dati. Le migrazioni vengono eseguite all'avvio dell'app.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

import libsql

from scripts.database_sql import (
    sql_betas,
    sql_holds,
    sql_routes,
    sql_users,
)
from scripts.database_sql.transaction import atomic

SCHEMA_VERSION = 4


def _columns(conn: libsql.Connection, table: str) -> set[str]:
    cursor = conn.cursor()
    try:
        rows = cursor.execute(f"PRAGMA table_info({table})").fetchall()
    except Exception:
        return set()
    return {row[1] for row in rows}


def _table_exists(conn: libsql.Connection, table: str) -> bool:
    cursor = conn.cursor()
    row = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row is not None


def _table_sql(conn: libsql.Connection, table: str) -> str:
    row = conn.cursor().execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return str(row[0]) if row and row[0] is not None else ""


def _has_on_delete_cascade(conn: libsql.Connection, table: str) -> bool:
    return "ON DELETE CASCADE" in _table_sql(conn, table).upper()


def _applied_versions(conn: libsql.Connection) -> set[int]:
    if not _table_exists(conn, "schema_migrations"):
        return set()
    cursor = conn.cursor()
    rows = cursor.execute("SELECT version FROM schema_migrations").fetchall()
    return {int(row[0]) for row in rows}


def _enable_foreign_keys(conn: libsql.Connection) -> None:
    # Su Turso alcune PRAGMA possono essere rifiutate: non è fatale, le
    # cancellazioni vengono gestite esplicitamente nel codice.
    try:
        conn.cursor().execute("PRAGMA foreign_keys=ON")
    except Exception:
        pass


def _migration_1(conn: libsql.Connection) -> None:
    """Aggiunge l'hash del token di login alla tabella utenti."""
    columns = _columns(conn, "users")
    if "auth_token_hash" not in columns:
        conn.cursor().execute("ALTER TABLE users ADD COLUMN auth_token_hash TEXT")


def _migration_2(conn: libsql.Connection) -> None:
    """Aggiunge indici per le interrogazioni più frequenti."""
    statements: Iterable[str] = (
        "CREATE INDEX IF NOT EXISTS idx_routes_author ON routes(author)",
        "CREATE INDEX IF NOT EXISTS idx_routes_created ON routes(creation_date)",
        "CREATE INDEX IF NOT EXISTS idx_holds_route ON holds(route_id)",
        "CREATE INDEX IF NOT EXISTS idx_betas_route ON betas(route_id)",
    )
    for statement in statements:
        conn.cursor().execute(statement)


def _migration_3(conn: libsql.Connection) -> None:
    """Rende user_name UNIQUE: la FK di routes.author la richiede.

    Senza un indice UNIQUE, SQLite segnala ``foreign key mismatch`` quando si
    inserisce una route con ``PRAGMA foreign_keys=ON``.
    """

    duplicates = conn.cursor().execute(
        "SELECT user_name FROM users GROUP BY user_name HAVING COUNT(*) > 1"
    ).fetchall()
    if duplicates:
        # Non cancellare dati dell'utente: segnala e lascia lo schema invariato.
        raise RuntimeError(
            "Impossibile creare l'indice UNIQUE su users.user_name: "
            f"trovati {len(duplicates)} username duplicati"
        )
    conn.cursor().execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_name ON users(user_name)"
    )


def _migration_4(conn: libsql.Connection) -> None:
    """Aggiunge ON DELETE CASCADE alle tabelle figlie.

    SQLite non permette di modificare una FK con ALTER TABLE: le tabelle
    vengono ricreate mantenendo dati, ID e indici.
    """

    if not _has_on_delete_cascade(conn, "holds"):
        with atomic(conn) as cursor:
            cursor.execute("DROP TABLE IF EXISTS holds_cascade")
            cursor.execute(sql_holds.create_table_sql("holds_cascade"))
            cursor.execute(
                "INSERT INTO holds_cascade "
                "(hold_id, route_id, x, y, size, progression_id, constraint_id) "
                "SELECT hold_id, route_id, x, y, size, progression_id, constraint_id "
                "FROM holds"
            )
            cursor.execute("DROP TABLE holds")
            cursor.execute("ALTER TABLE holds_cascade RENAME TO holds")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_holds_route ON holds(route_id)")

    if not _has_on_delete_cascade(conn, "betas"):
        with atomic(conn) as cursor:
            cursor.execute("DROP TABLE IF EXISTS betas_cascade")
            cursor.execute(sql_betas.create_table_sql("betas_cascade"))
            cursor.execute(
                "INSERT INTO betas_cascade (beta_id, route_id, title, body) "
                "SELECT beta_id, route_id, title, body FROM betas"
            )
            cursor.execute("DROP TABLE betas")
            cursor.execute("ALTER TABLE betas_cascade RENAME TO betas")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_betas_route ON betas(route_id)")


MIGRATIONS = {
    1: _migration_1,
    2: _migration_2,
    3: _migration_3,
    4: _migration_4,
}


def run_migrations(conn: libsql.Connection) -> None:
    """Porta il database allo schema corrente, in modo idempotente."""
    _enable_foreign_keys(conn)

    sql_routes.init_routes_table(conn)
    sql_holds.init_holds_table(conn)
    sql_users.init_users_table(conn)
    sql_betas.init_betas_table(conn)

    conn.cursor().execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations("
        "version INTEGER PRIMARY KEY, applied_at TEXT)"
    )
    applied = _applied_versions(conn)

    for version in sorted(MIGRATIONS):
        if version in applied:
            continue
        MIGRATIONS[version](conn)
        conn.cursor().execute(
            "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
            (version, datetime.now(timezone.utc).isoformat()),
        )

    conn.commit()
