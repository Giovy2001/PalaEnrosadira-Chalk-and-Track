"""Fixture condivise: database temporaneo isolato, mai quello dell'utente."""

from __future__ import annotations

import os
import shutil
import tempfile

import pytest

_TMP_DIR = tempfile.mkdtemp(prefix="chalk-and-track-tests-")

# Queste variabili DEVONO essere impostate prima di importare settings/global_values.
os.environ["APP_ENV"] = "local"
os.environ["SECRET_KEY"] = "test-secret-key-only"
os.environ["LOCAL_DB_PATH"] = os.path.join(_TMP_DIR, "test.db")
os.environ["LOCAL_IMAGES_DIR"] = os.path.join(_TMP_DIR, "Images")

import global_values  # noqa: E402
from app import create_app  # noqa: E402
from scripts.database_sql import sql_betas, sql_holds, sql_routes, sql_users  # noqa: E402

_TABLES = ("betas", "holds", "routes", "users", "schema_migrations")


def _wipe(conn) -> None:
    cursor = conn.cursor()
    for table in _TABLES:
        try:
            cursor.execute(f"DELETE FROM {table}")
        except Exception:
            pass
    try:
        cursor.execute("DELETE FROM sqlite_sequence")
    except Exception:
        pass
    conn.commit()


@pytest.fixture()
def conn():
    connection = global_values.get_connection()
    _wipe(connection)
    return connection


@pytest.fixture()
def app(conn):
    application = create_app()
    application.config["TESTING"] = True
    return application


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def sample_user(conn):
    sql_users.add_user(conn, {"user_name": "Tester", "user_color": 0})
    return "Tester"


@pytest.fixture()
def sample_route(conn, sample_user):
    route_id = sql_routes.add_route(
        conn,
        {
            "route_name": "Via di prova",
            "author": sample_user,
            "route_grade": "6A",
            "route_description": "Descrizione",
            "image_url": "/static/test.jpg",
        },
        [
            {
                "x": 0.5,
                "y": 0.5,
                "size": 2,
                "progression_id": "start",
                "constraint_id": "normal",
            }
        ],
    )
    return route_id


@pytest.fixture(scope="session", autouse=True)
def _cleanup_tmp_dir():
    yield
    shutil.rmtree(_TMP_DIR, ignore_errors=True)
