"""Test end-to-end dell'app Flask: pagine pubbliche e autorizzazione."""

from __future__ import annotations

import global_values
from scripts.database_sql import sql_users
from utils import auth


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_public_pages(client):
    for path in ("/", "/archive", "/use_condition", "/create_user"):
        assert client.get(path).status_code == 200, path


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
