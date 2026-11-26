"""Archivio dei blocchi, con filtri opzionali."""

from __future__ import annotations

from flask import render_template, request

import global_values
from route_constants import GRADES
from scripts.database_sql import sql_routes


def render_home_archive():
    filters = {
        "author": (request.args.get("author") or "").strip(),
        "name": (request.args.get("name") or "").strip(),
        "grade": (request.args.get("grade") or "").strip(),
    }
    routes = sql_routes.search_routes(
        global_values.get_connection(),
        author=filters["author"] or None,
        name=filters["name"] or None,
        grade=filters["grade"] or None,
    )
    return render_template(
        "home/archive.html", routes=routes, filters=filters, grades=GRADES
    )
