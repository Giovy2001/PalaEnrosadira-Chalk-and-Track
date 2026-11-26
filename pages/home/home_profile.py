"""Home: profilo utente e creazione profilo."""

from __future__ import annotations

from flask import make_response, redirect, render_template, request, url_for

import global_values
from route_constants import GRADES
from scripts.database_sql import sql_users
from utils import auth


def render_home_profile():
    if request.method == "POST":
        current = auth.require_user()
        try:
            new_username = sql_users.validate_new_username(
                request.form.get("username-input")
            )
        except ValueError as exc:
            return render_template(
                "home/profile.html", error=str(exc), grades=GRADES
            ), 400

        user_data = sql_users.get_user(global_values.get_connection(), new_username)
        if not user_data["exist"]:
            return redirect(url_for("render_create_user", username=new_username))

        # Cambio profilo consentito solo per il profilo corrente o per profili
        # storici non ancora associati a un token.
        if new_username != current and user_data.get("auth_token_hash"):
            return render_template(
                "home/profile.html",
                error="Questo profilo è associato a un altro dispositivo",
                grades=GRADES,
            ), 403

        token = auth.issue_token(new_username)
        auth.login(new_username, token)
        return redirect(url_for("render_home_profile", username_changed=new_username))

    return render_template(
        "home/profile.html",
        username_created=request.args.get("username_created"),
        username_changed=request.args.get("username_changed"),
        error=request.args.get("error"),
        grades=GRADES,
    )


def render_create_user():
    if request.method == "POST":
        try:
            username = sql_users.validate_new_username(
                request.form.get("username-input")
            )
        except ValueError as exc:
            return render_template(
                "create_user.html", username="", error=str(exc)
            ), 400

        try:
            sql_users.add_user(
                global_values.get_connection(),
                {"user_name": username, "user_color": 0},
            )
        except ValueError as exc:
            return render_template(
                "create_user.html", username=username, error=str(exc)
            ), 400

        token = auth.issue_token(username)
        auth.login(username, token)

        response = make_response(
            redirect(url_for("render_home_profile", username_created=username))
        )
        # Il token viene salvato anche lato client per ripristinare la sessione
        # dopo un cold start serverless o la scadenza del cookie.
        response.set_cookie(
            "chalk_and_track_token", token, samesite="Lax", max_age=60 * 60 * 24 * 30
        )
        return response

    return render_template(
        "create_user.html",
        username=request.args.get("username") or "",
        error=request.args.get("error"),
    )
