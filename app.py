"""Application factory di Chalk & Track."""

from __future__ import annotations

import settings
from flask import Flask, jsonify, request, session

import global_values
from utils import auth


def _error_response(status: int, message: str):
    if request.path.startswith("/backend_") or request.path.startswith("/api/"):
        return jsonify({"success": False, "message": message}), status
    return (
        f"<!doctype html><title>Errore {status}</title>"
        f"<h1>{status}</h1><p>{message}</p>"
        f'<a href="/archive">Torna all\'archivio</a>',
        status,
    )


def create_app() -> Flask:
    global_values.load_database()

    app = Flask(__name__, static_folder="static", static_url_path="/static")
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["DEBUG"] = settings.DEBUG
    app.config["MAX_CONTENT_LENGTH"] = settings.MAX_CONTENT_LENGTH
    app.config["RUN_LOCALLY"] = global_values.RUN_LOCALLY

    from pages import create, edit, index, use_condition, view
    from pages.backend import backend_auth, backend_profile
    from pages.home import home_explore, home_profile

    @app.before_request
    def restore_session_from_token():
        auth.restore_from_request()

    @app.context_processor
    def inject_auth_context():
        return {
            "current_user": auth.current_username(),
            "auth_token": session.get("auth_token"),
        }

    for status, message in (
        (400, "Richiesta non valida"),
        (401, "Accedi per continuare"),
        (403, "Non hai il permesso di eseguire questa operazione"),
        (404, "Pagina o blocco non trovato"),
        (405, "Metodo non consentito"),
        (413, "File troppo grande"),
        (500, "Errore interno del server"),
    ):
        app.register_error_handler(
            status, lambda error, code=status, text=message: _error_response(code, text)
        )

    # Pagine
    app.add_url_rule("/", view_func=home_explore.render_home_explore)
    app.add_url_rule(
        "/profile",
        view_func=home_profile.render_home_profile,
        methods=["GET", "POST"],
    )
    app.add_url_rule(
        "/create_user",
        view_func=home_profile.render_create_user,
        methods=["GET", "POST"],
    )
    app.add_url_rule("/archive", view_func=index.render_home_archive)
    app.add_url_rule("/use_condition", view_func=use_condition.render_use_condition)

    app.add_url_rule(
        "/route_<int:route_id>", view_func=view.view_route, methods=["GET", "POST"]
    )
    app.add_url_rule(
        "/edit_route_<int:route_id>",
        view_func=edit.edit_name_description,
        methods=["GET", "POST"],
    )
    app.add_url_rule(
        "/edit_holds_<int:route_id>",
        view_func=edit.edit_holds,
        methods=["GET", "POST"],
    )

    app.add_url_rule(
        "/select_image", view_func=create.select_image, methods=["GET", "POST"]
    )
    app.add_url_rule(
        "/create_route", view_func=create.create_route, methods=["GET", "POST"]
    )
    app.add_url_rule(
        "/save_route", view_func=create.save_route, methods=["GET", "POST"]
    )

    # API JSON
    app.add_url_rule(
        "/backend_login", view_func=backend_auth.login, methods=["POST"]
    )
    app.add_url_rule(
        "/backend_logout", view_func=backend_auth.logout, methods=["POST"]
    )
    app.add_url_rule(
        "/backend_update_color",
        view_func=backend_profile.update_color,
        methods=["POST"],
    )
    app.add_url_rule(
        "/backend_get_profile",
        view_func=backend_profile.get_profile,
        methods=["POST"],
    )
    app.add_url_rule(
        "/backend_get_completed",
        view_func=backend_profile.get_completed,
        methods=["POST"],
    )
    app.add_url_rule(
        "/backend_complete_route",
        view_func=backend_profile.complete_route,
        methods=["POST"],
    )
    app.add_url_rule(
        "/backend_search_routes",
        view_func=backend_profile.search_routes,
        methods=["POST"],
    )
    app.add_url_rule(
        "/backend_add_beta",
        view_func=backend_profile.add_beta,
        methods=["POST"],
    )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
