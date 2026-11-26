"""Visualizzazione e azioni sulla singola route."""

from __future__ import annotations

import logging

from flask import abort, redirect, render_template, request, url_for

import global_values
from route_constants import GRADES, POINTS_PER_COMPLETED_ROUTE
from scripts import image_handler
from scripts.database_sql import sql_betas, sql_holds, sql_routes, sql_users
from utils import auth

logger = logging.getLogger(__name__)


def _load_route(route_id: int) -> dict:
    route = sql_routes.get_route(global_values.get_connection(), route_id)
    if route is None:
        abort(404)
    return route


def view_route(route_id: int):
    conn = global_values.get_connection()
    route = _load_route(route_id)
    username = auth.current_username()

    if request.method == "POST":
        if "completeRoute" in request.form:
            user = auth.require_user()
            user_data = sql_users.get_user(conn, user)
            completed = list(user_data.get("serialized_completed_routes") or [])
            if route_id not in completed:
                completed.append(route_id)
                sql_users.edit_completed_routes(conn, user, completed)
                sql_users.add_points(conn, user, POINTS_PER_COMPLETED_ROUTE)
            return redirect(url_for("view_route", route_id=route_id))

        route, username = auth.require_author(route_id)

        if "authorName" in request.form:
            return redirect(url_for("edit_name_description", route_id=route_id))
        if "authorHolds" in request.form:
            return redirect(url_for("edit_holds", route_id=route_id))
        if "authorDelete" in request.form:
            image_url = route["image_url"]
            sql_routes.del_route(conn, route_id)  # transazione DB prima
            try:
                image_handler.delete(image_url)
            except Exception:
                logger.exception("Impossibile eliminare l'immagine %s", image_url)
            return redirect(url_for("render_home_archive"))
        abort(400)

    return render_template(
        "view.html",
        route=route,
        holds=sql_holds.get_holds(conn, route_id),
        betas=sql_betas.get_betas(conn, route_id),
        is_author=bool(username and username == route["author"]),
        current_user=username,
        grades=GRADES,
    )
