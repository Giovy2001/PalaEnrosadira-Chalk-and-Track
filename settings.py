"""Configurazione centralizzata dell'applicazione.

Tutte le decisioni dipendenti dall'ambiente vengono prese qui, prima
dell'inizializzazione del database. In questo modo il deploy serverless non
può aprire inavvertitamente il database locale.
"""

from __future__ import annotations

import os
from pathlib import Path

# Vercel imposta sempre VERCEL o VERCEL_ENV. Se siamo serverless la modalità
# predefinita è produzione, indipendentemente da APP_ENV.
IS_VERCEL: bool = bool(os.getenv("VERCEL") or os.getenv("VERCEL_ENV"))
APP_ENV: str = os.getenv("APP_ENV", "production" if IS_VERCEL else "local").lower()
RUN_LOCALLY: bool = APP_ENV == "local"
DEBUG: bool = bool(os.getenv("FLASK_DEBUG", "0") == "1" and RUN_LOCALLY)

# Il segreto serve sia per le sessioni Flask sia per firmare i token di login.
# In produzione deve essere configurato esplicitamente.
SECRET_KEY: str = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    if not RUN_LOCALLY:
        raise RuntimeError("SECRET_KEY deve essere impostata in produzione")
    SECRET_KEY = "chalk-and-track-development-secret"

# Per il cron di pulizia: se non impostato, l'endpoint è disabilitato.
CRON_SECRET: str = os.getenv("CRON_SECRET", "")

# Migrazione una tantum: consente a un profilo storico senza token di reclamare
# il proprio username. Di default attivo solo in locale: in produzione va
# abilitato temporaneamente con ALLOW_LEGACY_CLAIM=1 e poi disattivato.
ALLOW_LEGACY_CLAIM: bool = (
    os.getenv("ALLOW_LEGACY_CLAIM", "1" if RUN_LOCALLY else "0") == "1"
)

# Database locale (override utile per i test).
BASE_DIR = Path(__file__).resolve().parent
LOCAL_DB_PATH: str = os.getenv("LOCAL_DB_PATH", str(BASE_DIR / "static" / "local_database" / "sql_database.db"))
LOCAL_IMAGES_DIR: str = os.getenv(
    "LOCAL_IMAGES_DIR", str(BASE_DIR / "static" / "local_database" / "Images")
)

# Limite upload: 12 MB.
MAX_CONTENT_LENGTH: int = 12 * 1024 * 1024

# Durata validità token di login (30 giorni).
TOKEN_MAX_AGE: int = 60 * 60 * 24 * 30
