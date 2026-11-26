"""Creazione di una route in tre passaggi."""

from __future__ import annotations

import json

from flask import redirect, render_template, request, session, url_for

import global_values
from route_constants import GRADES
from scripts import image_handler
from scripts.database_sql import sql_holds, sql_routes
from utils import auth


def select_image():
    if request.method == "POST":
        username = auth.require_user()
        upload = request.files.get("image")
        if upload is None or not upload.filename:
            return render_template(
                "select_image.html", error="Seleziona un'immagine prima di continuare"
            ), 400
        try:
            image_url = image_handler.put(upload.filename, upload.read())
        except (ValueError, RuntimeError) as exc:
            return render_template("select_image.html", error=str(exc)), 400

        session["pending_image_url"] = image_url
        session.pop("pending_holds", None)
        return redirect(url_for("create_route"))

    return render_template("select_image.html")


def create_route():
    image_url = session.get("pending_image_url")
    if not image_url:
        return redirect(url_for("select_image"))

    if request.method == "POST":
        auth.require_user()
        raw_holds = request.form.get("jsonHolds")
        if not raw_holds:
            return render_template(
                "create_route.html",
                data={"image_url": image_url, "holds_array": []},
                error="Nessuna presa selezionata",
            ), 400
        try:
            holds = json.loads(raw_holds)
            if not isinstance(holds, list) or not holds:
                raise ValueError("Seleziona almeno una presa")
            validated = sql_holds.validate_holds(
                [hold.get("data", hold) if isinstance(hold, dict) else hold for hold in holds]
            )
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            return render_template(
                "create_route.html",
                data={"image_url": image_url, "holds_array": []},
                error=f"Prese non valide: {exc}",
            ), 400

        session["pending_holds"] = validated
        return redirect(url_for("save_route"))

    return render_template(
        "create_route.html", data={"image_url": image_url, "holds_array": []}
    )


def save_route():
    image_url = session.get("pending_image_url")
    holds = session.get("pending_holds")
    username = auth.current_username()

    if request.method == "POST":
        username = auth.require_user()
        route_name = (request.form.get("routeName") or "").strip()
        grade = request.form.get("routeGrade") or None
        description = request.form.get("routeDescription") or ""

        if not route_name:
            return render_template(
                "save_route.html",
                route_object=None,
                error="Il nome della via è obbligatorio",
                author=username,
                grades=GRADES,
            ), 400
        if grade and grade not in GRADES:
            return render_template(
                "save_route.html",
                route_object=None,
                error="Grado non valido",
                author=username,
                grades=GRADES,
            ), 400
        if not image_url or not isinstance(holds, list) or not holds:
            return redirect(url_for("select_image"))

        try:
            sql_routes.add_route(
                global_values.get_connection(),
                {
                    "route_name": route_name,
                    "author": username,  # l'autore viene dalla sessione, non dal form
                    "route_grade": grade,
                    "route_description": description,
                    "image_url": image_url,
                },
                holds,
            )
        except ValueError as exc:
            return render_template(
                "save_route.html",
                route_object=None,
                error=str(exc),
                author=username,
                grades=GRADES,
            ), 400

        session.pop("pending_image_url", None)
        session.pop("pending_holds", None)
        return redirect(url_for("render_home_archive"))

    return render_template(
        "save_route.html",
        route_object=None,
        author=username,
        grades=GRADES,
    )
