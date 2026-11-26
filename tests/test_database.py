"""Test del livello dati: atomicita', date ISO, cascade e validazione."""

from __future__ import annotations

import re

import pytest

from scripts.database_sql import sql_betas, sql_holds, sql_routes, sql_users


ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def test_dates_are_iso(conn, sample_user, sample_route):
    user = sql_users.get_user(conn, sample_user)
    route = sql_routes.get_route(conn, sample_route)
    assert ISO_DATE.match(user["creation_date"])
    assert ISO_DATE.match(user["last_seen_date"])
    assert ISO_DATE.match(route["creation_date"])


def test_add_route_with_invalid_holds_is_atomic(conn, sample_user):
    before = len(sql_routes.get_all_routes(conn))
    with pytest.raises(ValueError):
        sql_routes.add_route(
            conn,
            {
                "route_name": "Via invalida",
                "author": sample_user,
                "image_url": "/static/test.jpg",
            },
            [{"x": 2, "y": 0.5, "size": 2}],  # coordinata fuori intervallo
        )
    assert len(sql_routes.get_all_routes(conn)) == before


def test_edit_holds_replaces_atomically(conn, sample_route):
    sql_holds.edit_holds(conn, sample_route, [])
    assert sql_holds.get_holds(conn, sample_route) == []

    new_holds = [
        {
            "x": 0.1,
            "y": 0.2,
            "size": 1,
            "progression_id": "top",
            "constraint_id": "foot",
        }
    ]
    sql_holds.edit_holds(conn, sample_route, new_holds)
    holds = sql_holds.get_holds(conn, sample_route)
    assert len(holds) == 1
    assert holds[0]["progression_id"] == "top"
    assert holds[0]["constraint_id"] == "foot"


def test_edit_holds_invalid_keeps_previous(conn, sample_route):
    original = sql_holds.get_holds(conn, sample_route)
    with pytest.raises(ValueError):
        sql_holds.edit_holds(conn, sample_route, [{"x": "bad"}])
    assert sql_holds.get_holds(conn, sample_route) == original


def test_del_route_removes_holds_and_betas(conn, sample_route):
    sql_betas.add_beta(conn, sample_route, {"title": "Beta", "body": "Prova"})
    assert len(sql_holds.get_holds(conn, sample_route)) > 0
    assert len(sql_betas.get_betas(conn, sample_route)) == 1

    sql_routes.del_route(conn, sample_route)

    assert sql_routes.get_route(conn, sample_route) is None
    assert sql_holds.get_holds(conn, sample_route) == []
    assert sql_betas.get_betas(conn, sample_route) == []


def test_edit_beta_updates_correct_table(conn, sample_route):
    beta_id = sql_betas.add_beta(
        conn, sample_route, {"title": "Titolo", "body": "Testo"}
    )
    sql_betas.edit_beta(conn, beta_id, {"title": "Nuovo titolo"})
    beta = sql_betas.get_beta(conn, beta_id)
    assert beta["title"] == "Nuovo titolo"
    assert beta["body"] == "Testo"


def test_search_routes_filters(conn, sample_user):
    sql_routes.add_route(
        conn,
        {
            "route_name": "Prima",
            "author": sample_user,
            "route_grade": "5A",
            "image_url": "/static/a.jpg",
        },
        [],
    )
    sql_routes.add_route(
        conn,
        {
            "route_name": "Seconda",
            "author": sample_user,
            "route_grade": "8A",
            "image_url": "/static/b.jpg",
        },
        [],
    )

    assert len(sql_routes.search_routes(conn, name="Prima")) == 1
    assert len(sql_routes.search_routes(conn, grade="8A")) == 1
    assert len(sql_routes.search_routes(conn, author="Nessuno")) == 0


def test_get_user_missing_returns_exist_false(conn):
    user = sql_users.get_user(conn, "NonEsiste")
    assert user["exist"] is False
