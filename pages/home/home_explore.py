"""Feed Esplora: blocchi recenti, escludendo quelli già completati."""

from __future__ import annotations

import random

from flask import render_template

import global_values
from scripts.database_sql import sql_routes, sql_users
from utils import auth


def render_home_explore():
    conn = global_values.get_connection()
    username = auth.current_username()

    completed_ids: list[int] = []
    if username:
        user = sql_users.get_user(conn, username)
        if user.get("exist"):
            completed_ids = [
                int(route_id)
                for route_id in user.get("serialized_completed_routes") or []
                if str(route_id).isdigit()
            ]

    routes = sql_routes.search_routes(conn, excluded_ids=completed_ids, limit=50)
    # Un po' di casualità mantenendo i più recenti in testa alla prima schermata.
    if len(routes) > 6:
        head, tail = routes[:6], routes[6:]
        random.shuffle(tail)
        routes = head + tail

    return render_template("home/explore.html", routes=routes, empty=not routes)
