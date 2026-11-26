"""Test del profilo reale: statistiche, gradi, punti e asset PWA."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

import global_values
from route_constants import POINTS_PER_COMPLETED_ROUTE
from scripts.database_sql import sql_routes, sql_users
from utils import auth


def test_pwa_assets_and_palette_available(client):
    css = client.get("/static/css/palette.css").get_data(as_text=True)
    for index in range(1, 9):
        assert f"--user-color-{index}:" in css

    manifest = client.get("/static/icons/site.webmanifest").get_json()
    assert manifest["name"]
    assert manifest["start_url"] == "/"
    assert manifest["scope"] == "/"
    assert manifest["display"] == "standalone"

    for icon_id in range(8):
        assert client.get(f"/static/icons/profile/Icon_{icon_id}.png").status_code == 200
        color_manifest = client.get(
            f"/static/icons/site-color-{icon_id}.webmanifest"
        ).get_json()
        assert color_manifest["theme_color"].startswith("#")


def test_completing_route_awards_points_once(client, sample_user, sample_route):
    token = auth.issue_token(sample_user)
    headers = {"X-Auth-Token": token}
    today = datetime.now(timezone.utc).date().isoformat()

    first = client.post(
        "/backend_complete_route", json={"route_id": sample_route}, headers=headers
    )
    assert first.status_code == 200
    assert first.get_json()["points"] == POINTS_PER_COMPLETED_ROUTE

    second = client.post(
        "/backend_complete_route", json={"route_id": sample_route}, headers=headers
    )
    assert second.get_json()["points"] == POINTS_PER_COMPLETED_ROUTE

    completed = client.post(
        "/backend_get_completed", json={}, headers=headers
    ).get_json()["completed"]
    assert [route["route_id"] for route in completed] == [sample_route]
    assert completed[0]["route_grade"] == "6A"

    user = sql_users.get_user(global_values.get_connection(), sample_user)
    assert user["points"] == POINTS_PER_COMPLETED_ROUTE
    assert user["last_seen_date"] == today


@pytest.mark.parametrize("color_id", [0, 7])
def test_color_boundaries_are_persisted(client, sample_user, color_id):
    token = auth.issue_token(sample_user)
    response = client.post(
        "/backend_update_color",
        json={"color_id": color_id},
        headers={"X-Auth-Token": token},
    )
    assert response.status_code == 200
    assert response.get_json()["color_id"] == color_id
    user = sql_users.get_user(global_values.get_connection(), sample_user)
    assert user["user_color"] == str(color_id)


def test_profile_page_uses_server_data(client, sample_user, sample_route):
    token = auth.issue_token(sample_user)
    assert client.post("/backend_login", json={"auth_token": token}).status_code == 200

    html = client.get("/profile").get_data(as_text=True)
    assert "8C+" in html
    assert 'id="myRoutesList"' in html
    assert 'id="completedList"' in html
    assert "googleusercontent" not in html

    route = sql_routes.get_route(global_values.get_connection(), sample_route)
    assert route["route_grade"] == "6A"
