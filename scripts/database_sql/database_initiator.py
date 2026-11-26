"""Inizializzazione manuale del database (usa le migrazioni versionate)."""

from __future__ import annotations

import global_values
from scripts.database_sql import migrations, sql_init


def init_database(mode: str) -> None:
    """Crea/aggiorna lo schema per la modalità indicata.

    Args:
        mode: ``"local"`` oppure ``"turso"``.
    """

    if mode == "turso":
        conn = sql_init.init_turso_database()
    elif mode == "local":
        conn = sql_init.init_local_database()
    else:
        raise ValueError(f"Modalità sconosciuta: {mode}")

    migrations.run_migrations(conn)
    global_values.conn = conn
