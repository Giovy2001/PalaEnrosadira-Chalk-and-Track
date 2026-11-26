"""Test end-to-end dell'app Flask: pagine pubbliche e autorizzazione."""

from __future__ import annotations

import json
import re
from io import BytesIO

from PIL import Image

import global_values
from scripts.database_sql import sql_routes, sql_users
from utils import auth


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_public_pages(client):
    for path in ("/", "/archive", "/use_condition", "/create_user"):
        assert client.get(path).status_code == 200, path


def test_linked_css_files_are_served(client):
    hrefs = set()
    for path in ("/", "/archive", "/use_condition", "/create_user"):
        html = client.get(path).get_data(as_text=True)
        hrefs.update(re.findall(r'href="(/static/css/[^"]+)"', html))

    assert "/static/css/bottom-nav.css" in hrefs
    for href in hrefs:
        assert client.get(href).status_code == 200, href

    css = client.get("/static/css/bottom-nav.css").get_data(as_text=True)
    assert ".bottom-nav" in css
    assert "position: fixed" in css
    assert "#create-button-hidden" in css


def test_unknown_route_returns_404(client):
    assert client.get("/route_999").status_code == 404


def test_authorization_on_edit(client, sample_user, sample_route):
    # Senza token: 401.
    response = client.post(
        f"/edit_route_{sample_route}", data={"routeName": "hack"}
    )
    assert response.status_code == 401

    # Token valido ma utente diverso: 403.
    sql_users.add_user(global_values.get_connection(), {"user_name": "Other"})
    other_token = auth.issue_token("Other")
    response = client.post(
        f"/edit_route_{sample_route}",
        data={"routeName": "hack", "auth_token": other_token},
    )
    assert response.status_code == 403

    # Autore: modifica consentita.
    own_token = auth.issue_token(sample_user)
    response = client.post(
        f"/edit_route_{sample_route}",
        data={"routeName": "Nuovo nome", "auth_token": own_token},
    )
    assert response.status_code == 302


def test_color_whitelist(client, sample_user):
    token = auth.issue_token(sample_user)
    headers = {"X-Auth-Token": token}

    valid = client.post(
        "/backend_update_color",
        json={"username": sample_user, "color_id": 3},
        headers=headers,
    )
    assert valid.status_code == 200
    assert valid.get_json()["success"] is True

    invalid = client.post(
        "/backend_update_color",
        json={"username": sample_user, "color_id": 99},
        headers=headers,
    )
    assert invalid.status_code == 400
    assert invalid.get_json()["success"] is False


def test_get_profile_requires_auth(client, sample_user):
    response = client.post("/backend_get_profile", json={"username": sample_user})
    assert response.status_code == 401


def test_get_profile_with_token(client, sample_user):
    token = auth.issue_token(sample_user)
    response = client.post(
        "/backend_get_profile",
        json={"username": sample_user},
        headers={"X-Auth-Token": token},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["user"]["user_name"] == sample_user
    assert "auth_token_hash" not in data["user"]


def test_duplicate_username_rejected(client, sample_user):
    response = client.post("/create_user", data={"username-input": sample_user})
    assert response.status_code == 400
    assert "gi" in response.get_data(as_text=True).lower()


def test_token_in_query_string_is_ignored(client, sample_user, sample_route):
    token = auth.issue_token(sample_user)
    response = client.post(
        f"/edit_route_{sample_route}?auth_token={token}",
        data={"routeName": "hack"},
    )
    assert response.status_code == 401


def test_session_allows_edit_without_explicit_token(client, sample_user, sample_route):
    token = auth.issue_token(sample_user)
    assert client.post("/backend_login", json={"auth_token": token}).status_code == 200

    response = client.post(
        f"/edit_route_{sample_route}", data={"routeName": "Via sessione"}
    )
    assert response.status_code == 302


def test_edit_holds_requires_author(client, sample_user, sample_route):
    sql_users.add_user(global_values.get_connection(), {"user_name": "Other"})
    other_token = auth.issue_token("Other")
    holds = json.dumps(
        [
            {
                "x": 0.5,
                "y": 0.5,
                "size": 2,
                "progression_id": "top",
                "constraint_id": "normal",
            }
        ]
    )

    forbidden = client.post(
        f"/edit_holds_{sample_route}",
        data={"jsonHolds": holds, "auth_token": other_token},
    )
    assert forbidden.status_code == 403

    own_token = auth.issue_token(sample_user)
    allowed = client.post(
        f"/edit_holds_{sample_route}",
        data={"jsonHolds": holds, "auth_token": own_token},
    )
    assert allowed.status_code == 302


def test_cannot_update_color_of_other_user(client, sample_user):
    conn = global_values.get_connection()
    sql_users.add_user(conn, {"user_name": "Other", "user_color": 0})
    token = auth.issue_token(sample_user)

    response = client.post(
        "/backend_update_color",
        json={"username": "Other", "color_id": 5},
        headers={"X-Auth-Token": token},
    )
    assert response.status_code == 403
    assert sql_users.get_user(conn, "Other")["user_color"] == "0"


def test_get_profile_rejects_foreign_username(client, sample_user):
    token = auth.issue_token(sample_user)
    response = client.post(
        "/backend_get_profile",
        json={"username": "NonEsiste"},
        headers={"X-Auth-Token": token},
    )
    assert response.status_code == 403
    assert response.get_json()["success"] is False


def test_long_username_rejected_with_visible_error(client):
    response = client.post("/create_user", data={"username-input": "A" * 41})
    assert response.status_code == 400
    assert "40 caratteri" in response.get_data(as_text=True)


def test_create_flow_keeps_pending_data_with_form_token(client, sample_user):
    token = auth.issue_token(sample_user)
    assert client.post("/backend_login", json={"auth_token": token}).status_code == 200

    image = BytesIO()
    Image.new("RGB", (70, 100), "white").save(image, format="JPEG")
    image.seek(0)
    upload = client.post(
        "/select_image",
        data={"image": (image, "wall.jpg"), "auth_token": token},
        content_type="multipart/form-data",
    )
    assert upload.status_code == 302
    assert upload.headers["Location"].endswith("/create_route")
    assert client.get("/create_route").status_code == 200

    holds = json.dumps(
        [
            {
                "x": 0.5,
                "y": 0.5,
                "size": 2,
                "progression_id": "start",
                "constraint_id": "normal",
            }
        ]
    )
    finalize = client.post(
        "/create_route",
        data={"jsonHolds": holds, "auth_token": token},
    )
    assert finalize.status_code == 302
    assert finalize.headers["Location"].endswith("/save_route")
    assert client.get("/save_route").status_code == 200

    saved = client.post(
        "/save_route",
        data={
            "routeName": "Via di regressione",
            "routeGrade": "6A",
            "routeDescription": "Flusso completo",
            "auth_token": token,
        },
    )
    assert saved.status_code == 302
    assert saved.headers["Location"].endswith("/archive")
    names = [
        route["route_name"]
        for route in sql_routes.get_all_routes(global_values.get_connection())
    ]
    assert "Via di regressione" in names
