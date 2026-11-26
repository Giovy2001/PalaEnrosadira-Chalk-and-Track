"""Test del livello dati: atomicita', date ISO, cascade e validazione."""

from __future__ import annotations

import re

import libsql
import pytest

from scripts.database_sql import migrations, sql_betas, sql_holds, sql_routes, sql_users


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


def test_routes_are_ordered_by_creation_date(conn, sample_user):
    older = sql_routes.add_route(
        conn,
        {
            "route_name": "Vecchia",
            "author": sample_user,
            "image_url": "/static/old.jpg",
        },
        [],
    )
    newer = sql_routes.add_route(
        conn,
        {
            "route_name": "Nuova",
            "author": sample_user,
            "image_url": "/static/new.jpg",
        },
        [],
    )
    # ID crescenti ma date invertite: l'ordine deve seguire la data ISO.
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE routes SET creation_date = ? WHERE route_id = ?", ("2026-01-01", older)
    )
    cursor.execute(
        "UPDATE routes SET creation_date = ? WHERE route_id = ?", ("2026-02-01", newer)
    )
    conn.commit()

    names = [route["route_name"] for route in sql_routes.get_all_routes(conn)]
    assert names == ["Nuova", "Vecchia"]


def test_foreign_keys_cascade_from_route(conn, sample_route):
    sql_betas.add_beta(conn, sample_route, {"title": "Beta", "body": "Prova"})
    assert sql_holds.get_holds(conn, sample_route)
    assert sql_betas.get_betas(conn, sample_route)

    conn.cursor().execute("DELETE FROM routes WHERE route_id = ?", (sample_route,))
    conn.commit()

    assert sql_holds.get_holds(conn, sample_route) == []
    assert sql_betas.get_betas(conn, sample_route) == []


def test_migrations_are_idempotent(conn, sample_route):
    holds_before = sql_holds.get_holds(conn, sample_route)
    migrations.run_migrations(conn)
    migrations.run_migrations(conn)

    versions = {
        int(row[0])
        for row in conn.cursor()
        .execute("SELECT version FROM schema_migrations")
        .fetchall()
    }
    assert versions == set(migrations.MIGRATIONS)
    assert sql_holds.get_holds(conn, sample_route) == holds_before
    assert sql_routes.get_route(conn, sample_route) is not None


def test_migration_upgrades_legacy_schema_without_data_loss(tmp_path):
    legacy = libsql.connect(str(tmp_path / "legacy.db"))
    cursor = legacy.cursor()
    cursor.execute(
        """CREATE TABLE users(
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT,
        user_color TEXT,
        creation_date TEXT,
        last_seen_date TEXT,
        points INTEGER,
        serialized_completed_routes TEXT
    )"""
    )
    cursor.execute("CREATE UNIQUE INDEX idx_users_name ON users(user_name)")
    cursor.execute(
        """CREATE TABLE routes(
        route_id INTEGER PRIMARY KEY AUTOINCREMENT,
        route_name TEXT,
        author TEXT,
        creation_date TEXT,
        route_grade TEXT,
        route_description TEXT,
        image_url TEXT,
        FOREIGN KEY (author) REFERENCES users(user_name)
    )"""
    )
    cursor.execute(
        """CREATE TABLE holds(
        hold_id INTEGER PRIMARY KEY AUTOINCREMENT,
        route_id INTEGER,
        x REAL,
        y REAL,
        size REAL,
        progression_id TEXT,
        constraint_id TEXT,
        FOREIGN KEY (route_id) REFERENCES routes(route_id)
    )"""
    )
    cursor.execute(
        """CREATE TABLE betas(
        beta_id INTEGER PRIMARY KEY AUTOINCREMENT,
        route_id INTEGER,
        title TEXT,
        body TEXT,
        FOREIGN KEY (route_id) REFERENCES routes(route_id)
    )"""
    )
    cursor.execute(
        "INSERT INTO users(user_name, creation_date, last_seen_date, points, "
        "serialized_completed_routes) VALUES (?, ?, ?, ?, ?)",
        ("Storico", "2026-01-01", "2026-01-01", 0, "[]"),
    )
    cursor.execute(
        "INSERT INTO routes(route_name, author, creation_date, image_url) "
        "VALUES (?, ?, ?, ?)",
        ("Via storica", "Storico", "2026-01-01", "/static/legacy.jpg"),
    )
    cursor.execute(
        "INSERT INTO holds(route_id, x, y, size, progression_id, constraint_id) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (1, 0.5, 0.5, 2, "start", "normal"),
    )
    cursor.execute(
        "INSERT INTO betas(route_id, title, body) VALUES (?, ?, ?)",
        (1, "Beta storica", "Testo"),
    )
    legacy.commit()

    migrations.run_migrations(legacy)

    assert migrations._has_on_delete_cascade(legacy, "holds")
    assert migrations._has_on_delete_cascade(legacy, "betas")
    assert sql_routes.get_route(legacy, 1)["route_name"] == "Via storica"
    assert len(sql_holds.get_holds(legacy, 1)) == 1
    assert sql_betas.get_betas(legacy, 1)[0]["title"] == "Beta storica"

    legacy.cursor().execute("DELETE FROM routes WHERE route_id = ?", (1,))
    legacy.commit()
    assert sql_holds.get_holds(legacy, 1) == []
    assert sql_betas.get_betas(legacy, 1) == []
    legacy.close()
