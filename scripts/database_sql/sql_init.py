"""Inizializzazione delle connessioni al database."""

from __future__ import annotations

import os

import libsql

import settings


def init_turso_database() -> libsql.Connection:
    """Connette al database Turso remoto usando le variabili d'ambiente."""

    url = os.getenv("TURSO_DATABASE_URL")
    token = os.getenv("TURSO_AUTH_TOKEN", "")
    if not url:
        raise RuntimeError("TURSO_DATABASE_URL deve essere impostata in produzione")

    # libsql accetta solo stringhe: se il token manca passiamo una stringa vuota.
    return libsql.connect(database=url, auth_token=token)


def init_local_database() -> libsql.Connection:
    """Connette al database SQLite locale."""

    return libsql.connect(settings.LOCAL_DB_PATH)
