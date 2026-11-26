"""Endpoint JSON per login/logout."""

from __future__ import annotations

from flask import jsonify, request

import global_values
import settings
from scripts.database_sql import sql_users
from utils import auth


def login():
    """Accetta un token firmato; consente il primo accesso agli utenti storici.

    Gli utenti creati prima dell'introduzione dei token non ne hanno ancora
    uno: possono reclamare il proprio profilo una sola volta, dopodiché serve
    il token emesso al momento della creazione.
    """

    data = request.get_json(silent=True) or {}
    token = data.get("auth_token")
    username = auth.verify_token(token)

    if settings.ALLOW_LEGACY_CLAIM and not username and not auth.current_username():
        requested = data.get("username")
        if isinstance(requested, str) and requested.strip():
            user = sql_users.get_user(global_values.get_connection(), requested)
            if user.get("exist") and not user.get("auth_token_hash"):
                token = auth.issue_token(requested)
                username = requested

    if not username:
        return jsonify({"success": False, "message": "Credenziali non valide"}), 401

    auth.login(username, token)
    return jsonify({"success": True, "username": username, "auth_token": token})


def logout():
    auth.logout()
    return jsonify({"success": True})
