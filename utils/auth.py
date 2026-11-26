"""Identità e autorizzazione lato server.

Il nome utente nel localStorage non è una credenziale: viene usato solo come
preferenza di interfaccia. Le operazioni di scrittura richiedono una sessione
Flask oppure un token firmato inviato tramite header o campo nascosto.
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Any

import global_values
import settings
from flask import abort, request, session
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from scripts.database_sql import sql_routes, sql_users

_serializer = URLSafeTimedSerializer(settings.SECRET_KEY, salt="chalk-and-track-login")


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def make_token(username: str) -> str:
    """Crea un token firmato per l'utente indicato."""

    return _serializer.dumps({"u": username})


def verify_token(token: str | None) -> str | None:
    """Verifica un token e restituisce l'utente associato, se valido."""

    if not token:
        return None
    try:
        payload: Any = _serializer.loads(token, max_age=settings.TOKEN_MAX_AGE)
    except (BadSignature, SignatureExpired, ValueError, TypeError):
        return None

    username = payload.get("u") if isinstance(payload, dict) else None
    if not isinstance(username, str) or not username:
        return None

    user = sql_users.get_user(global_values.get_connection(), username)
    if not user.get("exist"):
        return None

    expected_hash = user.get("auth_token_hash")
    if expected_hash and not hmac.compare_digest(str(expected_hash), _hash(token)):
        return None
    return username


def issue_token(username: str) -> str:
    """Genera un token e lo collega all'utente nel database."""

    token = make_token(username)
    sql_users.edit_user(
        global_values.get_connection(), username, {"auth_token_hash": _hash(token)}
    )
    return token


def login(username: str, token: str | None = None) -> None:
    """Imposta l'identità senza perdere lo stato temporaneo della creazione.

    I form includono il token firmato per sopravvivere a un cold start: se
    l'identità è già la stessa, riscrivere la sessione cancellerebbe
    ``pending_image_url`` e ``pending_holds`` a metà del flusso.
    """

    previous = current_username()
    if previous and previous != username:
        for key in ("pending_image_url", "pending_holds"):
            session.pop(key, None)

    session["username"] = username
    if token:
        session["auth_token"] = token
    else:
        session.pop("auth_token", None)
    session.permanent = True


def logout() -> None:
    session.clear()


def current_username() -> str | None:
    username = session.get("username")
    return username if isinstance(username, str) and username else None


def restore_from_request() -> str | None:
    """Ripristina l'identita' da un token esplicito o dalla sessione.

    Un token firmato inviato nella richiesta ha la priorita' sulla sessione:
    cio' permette di passare da un profilo all'altro anche se il cookie e'
    ancora valido per il profilo precedente. Un token non valido non cancella
    una sessione gia' autenticata.
    """

    # Il token non viene accettato nella query string: finirebbe nei log e
    # nella cronologia del browser. Solo header, body form o sessione.
    token = (
        request.headers.get("X-Auth-Token")
        or request.form.get("auth_token")
    )
    if token:
        username = verify_token(token)
        if username:
            # Non riscrivere la sessione quando è già autenticata con lo stesso
            # token: i form inviano il token a ogni step della creazione.
            if session.get("username") != username or session.get("auth_token") != token:
                login(username, token)
            return username

    return current_username()


def require_user() -> str:
    """Restituisce l'utente corrente oppure risponde 401."""

    username = restore_from_request()
    if not username:
        abort(401)
    return username


def require_author(route_id: int) -> tuple[dict, str]:
    """Verifica che l'utente corrente sia l'autore della route.

    Raises:
        401: se non è presente un'identità valida.
        404: se la route non esiste.
        403: se l'utente non è l'autore.
    """

    username = require_user()
    route = sql_routes.get_route(global_values.get_connection(), route_id)
    if route is None:
        abort(404)
    if route["author"] != username:
        abort(403)
    return route, username
