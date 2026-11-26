"""Accesso alla tabella routes."""

from __future__ import annotations

from datetime import datetime, timezone

import libsql

from scripts.database_sql import sql_betas, sql_holds
from scripts.database_sql.transaction import atomic

EDITABLE_FIELDS = {
    "route_name",
    "route_grade",
    "route_description",
    "image_url",
    "author",
}
TABLE_STRUCTURE = (
    "route_id",
    "route_name",
    "author",
    "creation_date",
    "route_grade",
    "route_description",
    "image_url",
)


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def format_table(route_object: tuple) -> dict:
    return {
        column: route_object[index]
        for index, column in enumerate(TABLE_STRUCTURE)
        if index < len(route_object)
    }


### GETS


def get_all_routes(conn: libsql.Connection) -> list[dict]:
    cursor = conn.cursor()
    routes = cursor.execute(
        "SELECT * FROM routes ORDER BY creation_date DESC, route_id DESC"
    ).fetchall()
    return [format_table(route) for route in routes]


def search_routes(
    conn: libsql.Connection,
    *,
    author: str | None = None,
    name: str | None = None,
    grade: str | None = None,
    excluded_ids: list[int] | None = None,
    limit: int | None = None,
) -> list[dict]:
    """Filtra le route con parametri legati, evitando SQL costruito a mano."""

    conditions: list[str] = []
    values: list = []

    if author:
        conditions.append("author = ?")
        values.append(author)
    if name:
        conditions.append("route_name LIKE ?")
        values.append(f"%{name}%")
    if grade:
        conditions.append("route_grade = ?")
        values.append(grade)
    if excluded_ids:
        placeholders = ", ".join("?" for _ in excluded_ids)
        conditions.append(f"route_id NOT IN ({placeholders})")
        values.extend(excluded_ids)

    query = "SELECT * FROM routes"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY creation_date DESC, route_id DESC"
    if limit is not None:
        query += " LIMIT ?"
        values.append(int(limit))

    cursor = conn.cursor()
    routes = cursor.execute(query, values).fetchall()
    return [format_table(route) for route in routes]


def get_route(conn: libsql.Connection, route_id: int) -> dict | None:
    cursor = conn.cursor()
    route = cursor.execute(
        "SELECT * FROM routes WHERE route_id = ?", (route_id,)
    ).fetchone()
    return format_table(route) if route else None


def get_routes_from_author(conn: libsql.Connection, author: str) -> list[dict]:
    if not author:
        return []
    return search_routes(conn, author=author)


### SETS


def edit_route(
    conn: libsql.Connection, route_id: int, data_to_override: dict
) -> None:
    if not data_to_override:
        raise ValueError("Nessun dato da aggiornare")
    invalid = set(data_to_override) - EDITABLE_FIELDS
    if invalid:
        raise ValueError(f"Campi non aggiornabili: {', '.join(sorted(invalid))}")
    instruction = ", ".join(f"{key} = ?" for key in data_to_override)
    values = [*data_to_override.values(), route_id]
    with atomic(conn) as cursor:
        cursor.execute(f"UPDATE routes SET {instruction} WHERE route_id = ?", values)


def add_route(conn: libsql.Connection, route_data: dict, holds_data: list) -> int:
    """Inserisce una route e le sue prese in un'unica transazione."""

    name = route_data.get("route_name")
    author = route_data.get("author")
    image_url = route_data.get("image_url")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Nome della via obbligatorio")
    if not isinstance(author, str) or not author.strip():
        raise ValueError("Autore obbligatorio")
    if not isinstance(image_url, str) or not image_url:
        raise ValueError("Immagine della via obbligatoria")
    if not isinstance(holds_data, list):
        raise ValueError("Prese non valide")

    with atomic(conn) as cursor:
        cursor.execute(
            "INSERT INTO routes(route_name, author, creation_date, route_grade, "
            "route_description, image_url) VALUES (?,?,?,?,?,?)",
            (
                name.strip(),
                author.strip(),
                _today(),
                route_data.get("route_grade") or None,
                route_data.get("route_description") or "",
                image_url,
            ),
        )
        route_id = cursor.lastrowid
        sql_holds.insert_holds(cursor, route_id, holds_data)
    return route_id


### DELETES


def del_route(conn: libsql.Connection, route_id: int) -> None:
    """Cancella route, prese e bete in un'unica transazione.

    La rimozione dell'immagine è responsabilità del chiamante e va fatta solo
    dopo il successo di questa funzione.
    """

    with atomic(conn) as cursor:
        cursor.execute("DELETE FROM betas WHERE route_id = ?", (route_id,))
        cursor.execute("DELETE FROM holds WHERE route_id = ?", (route_id,))
        cursor.execute("DELETE FROM routes WHERE route_id = ?", (route_id,))


### INIT


def init_routes_table(conn: libsql.Connection) -> None:
    conn.cursor().execute(
        """CREATE TABLE IF NOT EXISTS routes(
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
    conn.commit()
