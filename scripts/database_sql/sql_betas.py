"""Accesso alla tabella betas."""

from __future__ import annotations

import libsql

from scripts.database_sql.transaction import atomic

EDITABLE_FIELDS = {"title", "body"}
TABLE_STRUCTURE = ("beta_id", "route_id", "title", "body")


def format_table(beta_object: tuple) -> dict:
    return {
        column: beta_object[index]
        for index, column in enumerate(TABLE_STRUCTURE)
        if index < len(beta_object)
    }


### GETS


def get_betas(conn: libsql.Connection, route_id: int) -> list[dict]:
    betas = conn.cursor().execute(
        "SELECT * FROM betas WHERE route_id = ? ORDER BY beta_id", (route_id,)
    ).fetchall()
    return [format_table(beta) for beta in betas]


def get_beta(conn: libsql.Connection, beta_id: int) -> dict | None:
    beta = conn.cursor().execute(
        "SELECT * FROM betas WHERE beta_id = ?", (beta_id,)
    ).fetchone()
    return format_table(beta) if beta else None


### SETS


def add_beta(conn: libsql.Connection, route_id: int, beta_data: dict) -> int:
    title = beta_data.get("title")
    body = beta_data.get("body")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("Titolo beta obbligatorio")
    if not isinstance(body, str):
        raise ValueError("Testo beta non valido")
    with atomic(conn) as cursor:
        cursor.execute(
            "INSERT INTO betas (route_id, title, body) VALUES (?, ?, ?)",
            (route_id, title.strip(), body),
        )
        return cursor.lastrowid


def edit_beta(
    conn: libsql.Connection, beta_id: int, data_to_override: dict
) -> None:
    if not data_to_override:
        raise ValueError("Nessun dato da aggiornare")
    invalid = set(data_to_override) - EDITABLE_FIELDS
    if invalid:
        raise ValueError(f"Campi non aggiornabili: {', '.join(sorted(invalid))}")
    instruction = ", ".join(f"{key} = ?" for key in data_to_override)
    values = [*data_to_override.values(), beta_id]
    with atomic(conn) as cursor:
        cursor.execute(f"UPDATE betas SET {instruction} WHERE beta_id = ?", values)


### DELETES


def del_beta(conn: libsql.Connection, beta_id: int) -> None:
    with atomic(conn) as cursor:
        cursor.execute("DELETE FROM betas WHERE beta_id = ?", (beta_id,))


def del_betas(conn: libsql.Connection, route_id: int) -> None:
    with atomic(conn) as cursor:
        cursor.execute("DELETE FROM betas WHERE route_id = ?", (route_id,))


### INIT


def create_table_sql(table_name: str = "betas") -> str:
    """DDL della tabella bete, usata anche dalla migrazione delle FK."""

    return f"""CREATE TABLE IF NOT EXISTS {table_name}(
        beta_id INTEGER PRIMARY KEY AUTOINCREMENT,
        route_id INTEGER,
        title TEXT,
        body TEXT,
        FOREIGN KEY (route_id) REFERENCES routes(route_id) ON DELETE CASCADE
    )"""


def init_betas_table(conn: libsql.Connection) -> None:
    conn.cursor().execute(create_table_sql())
    conn.commit()
