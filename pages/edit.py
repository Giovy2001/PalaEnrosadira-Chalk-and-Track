"""Modifica delle prese e dei dettagli di una route."""

from __future__ import annotations

import json

from flask import abort, redirect, render_template, request, url_for

import global_values
from route_constants import GRADES
from scripts.database_sql import sql_holds, sql_routes
from utils import auth


def edit_holds(route_id: int):
    conn = global_values.get_connection()
    route, _ = auth.require_author(route_id)

    if request.method == "POST":
        raw_holds = request.form.get("jsonHolds")
        if not raw_holds:
            return render_template(
                "create_route.html",
                data={"image_url": route["image_url"], "holds_array": []},
                error="Nessuna presa selezionata",
            ), 400
        try:
            parsed = json.loads(raw_holds)
            holds = [
                hold.get("data", hold) if isinstance(hold, dict) else hold
                for hold in parsed
            ]
            sql_holds.edit_holds(conn, route_id, holds)
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            return render_template(
                "create_route.html",
                data={
                    "image_url": route["image_url"],
                    "holds_array": sql_holds.get_holds(conn, route_id),
                },
                error=f"Prese non valide: {exc}",
            ), 400
        return redirect(url_for("view_route", route_id=route_id))

    return render_template(
        "create_route.html",
        data={
            "image_url": route["image_url"],
            "holds_array": sql_holds.get_holds(conn, route_id),
        },
    )


def edit_name_description(route_id: int):
    conn = global_values.get_connection()
    route, _ = auth.require_author(route_id)

    if request.method == "POST":
        name = (request.form.get("routeName") or "").strip()
        grade = request.form.get("routeGrade") or None
        description = request.form.get("routeDescription") or ""
        if not name:
            return render_template(
                "save_route.html", route_object=route, error="Nome obbligatorio", grades=GRADES
            ), 400
        if grade and grade not in GRADES:
            return render_template(
                "save_route.html", route_object=route, error="Grado non valido", grades=GRADES
            ), 400
        sql_routes.edit_route(
            conn,
            route_id,
            {
                "route_name": name,
                "route_grade": grade,
                "route_description": description,
            },
        )
        return redirect(url_for("view_route", route_id=route_id))

    return render_template(
        "save_route.html", route_object=route, author=route["author"], grades=GRADES
    )
