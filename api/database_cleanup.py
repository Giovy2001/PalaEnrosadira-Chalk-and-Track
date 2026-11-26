"""Serverless cron: rimuove route orfane e immagini non referenziate."""

from __future__ import annotations

import hmac
import logging

import global_values
import settings
from flask import Flask, abort, jsonify, request
from scripts import image_handler
from scripts.database_sql import sql_routes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _normalize(url: str) -> str:
    return str(url).replace("\\", "/").lower()


def database_cleanup() -> int:
    conn = global_values.get_connection()
    images_urls = image_handler.list()
    database_entries = sql_routes.get_all_routes(conn)
    # Se l'elenco immagini è vuoto per un errore temporaneo del backend, non
    # cancellare tutte le route: è più sicuro non fare nulla e riprovare.
    if database_entries and not images_urls:
        logger.warning("Nessuna immagine trovata: pulizia annullata")
        return 0
    database_urls = {
        _normalize(entry["image_url"])
        for entry in database_entries
        if entry.get("image_url")
    }

    cleanup_actions = 0
    for entry in database_entries:
        image_url = entry.get("image_url")
        if not image_url:
            continue
        if _normalize(image_url) not in {_normalize(url) for url in images_urls}:
            logger.info("Cancello route orfana %s", entry["route_id"])
            sql_routes.del_route(conn, entry["route_id"])
            cleanup_actions += 1

    for url in images_urls:
        if _normalize(url) not in database_urls:
            logger.info("Cancello immagine orfana %s", url)
            image_handler.delete(url)
            cleanup_actions += 1

    return cleanup_actions


app = Flask(__name__)


@app.get("/api/database_cleanup")
def init_cron():
    authorization = request.headers.get("Authorization", "")
    provided_secret = (
        authorization.removeprefix("Bearer ")
        or request.headers.get("x-vercel-cron-secret")
        or request.headers.get("x-cron-secret")
    )
    if not settings.CRON_SECRET:
        logger.error("CRON_SECRET non configurato: pulizia disabilitata")
        abort(401)
    if not hmac.compare_digest(str(provided_secret), str(settings.CRON_SECRET)):
        abort(401)

    logger.info("Received cleanup request at /api/database_cleanup")
    # La modalità remota viene forzata: il filesystem di Vercel è read-only.
    global_values.load_database("turso")
    cleanup_actions = database_cleanup()
    logger.info("Database cleanup completed with %d actions", cleanup_actions)
    return jsonify({"status": "ok", "cleanup_actions": cleanup_actions})
