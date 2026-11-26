"""Stato condiviso dell'applicazione.

La connessione al database viene creata una sola volta, scegliendo il backend
in base alla configurazione *prima* che vengano registrate le route.
"""

from __future__ import annotations

import settings
from scripts import image_handler
from scripts.database_sql import migrations, sql_init

RUN_LOCALLY: bool = settings.RUN_LOCALLY
INIT_DATABASE: bool = False
conn = None


def load_database(mode: str | None = None) -> None:
    """Inizializza database e storage immagini.

    Args:
        mode: ``"local"`` oppure ``"turso"``. Se omesso usa la configurazione.
    """

    global conn, RUN_LOCALLY

    RUN_LOCALLY = (mode == "local") if mode is not None else settings.RUN_LOCALLY

    if RUN_LOCALLY:
        conn = sql_init.init_local_database()
        image_handler.init_local_database()
    else:
        conn = sql_init.init_turso_database()
        image_handler.init_glob_database()

    migrations.run_migrations(conn)


def get_connection():
    """Restituisce la connessione, inizializzandola se necessario."""

    if conn is None:
        load_database()
    return conn
