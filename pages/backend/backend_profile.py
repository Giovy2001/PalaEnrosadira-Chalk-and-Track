"""Endpoint JSON per profilo, statistiche, esplorazione e bete."""

from __future__ import annotations

from flask import jsonify, request

import global_values
from route_constants import POINTS_PER_COMPLETED_ROUTE
from scripts.database_sql import sql_betas, sql_routes, sql_users
from utils import auth


def _json_body() -> dict:
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def _public_user(user: dict) -> dict:
    return {key: value for key, value in user.items() if key != "auth_token_hash"}


def _checked_username(data: dict) -> str | None:
    """Restituisce l'utente autenticato, rifiutandoUsername contraffatti."""

    username = auth.require_user()
    requested = data.get("username")
    if requested is not None and requested != username:
        from flask import abort

        abort(403)
    return username


def _completed_routes(user: dict) -> list[dict]:
    conn = global_values.get_connection()
    completed: list[dict] = []
    for route_id in user.get("serialized_completed_routes") or []:
        route = sql_routes.get_route(conn, route_id)
        if route is not None:
            completed.append(
                {
                    "route_id": route["route_id"],
                    "route_name": route["route_name"],
                    "route_grade": route["route_grade"],
                    "image_url": route["image_url"],
                    "creation_date": route["creation_date"],
                }
            )
    return completed


def update_color():
    data = _json_body()
    username = _checked_username(data)
    color_id = data.get("color_id")
    try:
        color = int(color_id)
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Colore non valido"}), 400
    if not 0 <= color <= 7:
        return jsonify({"success": False, "message": "Colore non valido"}), 400

    try:
        sql_users.edit_user(
            global_values.get_connection(), username, {"user_color": str(color)}
        )
    except Exception as exc:
        return jsonify({"success": False, "message": str(exc)}), 400
    return jsonify({"success": True, "color_id": color})


def get_profile():
    data = _json_body()
    username = _checked_username(data)
    conn = global_values.get_connection()
    user = sql_users.get_user(conn, username)
    if not user.get("exist"):
        return jsonify({"success": False, "message": "Utente non trovato"}), 404

    return jsonify(
        {
            "success": True,
            "user": _public_user(user),
            "routes": sql_routes.get_routes_from_author(conn, username),
            "completed": _completed_routes(user),
        }
    )


def get_completed():
    data = _json_body()
    username = _checked_username(data)
    user = sql_users.get_user(global_values.get_connection(), username)
    if not user.get("exist"):
        return jsonify({"success": False, "message": "Utente non trovato"}), 404
    return jsonify({"success": True, "completed": _completed_routes(user)})


def complete_route():
    data = _json_body()
    username = _checked_username(data)
    conn = global_values.get_connection()
    try:
        route_id = int(data.get("route_id"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Blocco non valido"}), 400

    route = sql_routes.get_route(conn, route_id)
    if route is None:
        return jsonify({"success": False, "message": "Blocco non trovato"}), 404

    user = sql_users.get_user(conn, username)
    completed = list(user.get("serialized_completed_routes") or [])
    if route_id not in completed:
        completed.append(route_id)
        sql_users.edit_completed_routes(conn, username, completed)
        sql_users.add_points(conn, username, POINTS_PER_COMPLETED_ROUTE)

    updated = sql_users.get_user(conn, username)
    return jsonify(
        {
            "success": True,
            "points": updated["points"],
            "completed": _completed_routes(updated),
        }
    )


def search_routes():
    data = _json_body()
    # Esplora e archivio sono pubblici in lettura: nessuna autorizzazione richiesta.
    conn = global_values.get_connection()
    excluded = data.get("excluded_ids") or []
    if not isinstance(excluded, list):
        excluded = []
    routes = sql_routes.search_routes(
        conn,
        author=data.get("author") or None,
        name=data.get("name") or None,
        grade=data.get("grade") or None,
        excluded_ids=[int(value) for value in excluded if str(value).isdigit()],
        limit=min(int(data.get("limit") or 50), 200),
    )
    return jsonify({"success": True, "routes": routes})


def add_beta():
    data = _json_body()
    username = _checked_username(data)
    conn = global_values.get_connection()
    try:
        route_id = int(data.get("route_id"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Blocco non valido"}), 400
    if sql_routes.get_route(conn, route_id) is None:
        return jsonify({"success": False, "message": "Blocco non trovato"}), 404
    try:
        sql_betas.add_beta(
            conn, route_id, {"title": data.get("title"), "body": data.get("body")}
        )
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400
    return jsonify({"success": True, "betas": sql_betas.get_betas(conn, route_id)})
