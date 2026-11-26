"""Accesso alla tabella holds."""

from __future__ import annotations

import libsql

from scripts.database_sql.transaction import atomic

PROGRESSION_IDS = {"start", "middle", "zone", "top"}
CONSTRAINT_IDS = {
    "normal",
    "foot",
    "only_hand",
    "only_foot",
    "only_volume",
    "no_volume",
}
TABLE_STRUCTURE = (
    "hold_id",
    "route_id",
    "x",
    "y",
    "size",
    "progression_id",
    "constraint_id",
)


def format_table(hold_object: tuple) -> dict:
    return {
        column: hold_object[index]
        for index, column in enumerate(TABLE_STRUCTURE)
        if index < len(hold_object)
    }


def validate_holds(holds_data: list) -> list[dict]:
    """Normalizza e valida le prese ricevute dal client."""

    if not isinstance(holds_data, list):
        raise ValueError("Le prese devono essere una lista")
    validated: list[dict] = []
    for hold in holds_data:
        try:
            x = float(hold["x"])
            y = float(hold["y"])
            size = float(hold["size"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Coordinate o dimensione della presa non valide") from exc
        if not (-0.01 <= x <= 1.01) or not (-0.01 <= y <= 1.01):
            raise ValueError("Coordinate della presa fuori intervallo")
        if not 0.1 <= size <= 12:
            raise ValueError("Dimensione della presa non valida")
        progression = hold.get("progression_id", "middle")
        constraint = hold.get("constraint_id", "normal")
        if progression not in PROGRESSION_IDS:
            raise ValueError("Tipo di presa non valido")
        if constraint not in CONSTRAINT_IDS:
            raise ValueError("Utilizzo della presa non valido")
        validated.append(
            {
                "x": x,
                "y": y,
                "size": size,
                "progression_id": progression,
                "constraint_id": constraint,
            }
        )
    return validated


### GETS


def get_holds(conn: libsql.Connection, route_id: int) -> list[dict]:
    holds = conn.cursor().execute(
        "SELECT * FROM holds WHERE route_id = ? ORDER BY hold_id", (route_id,)
    ).fetchall()
    return [format_table(hold) for hold in holds]


### SETS


def insert_holds(cursor, route_id: int, holds_data: list) -> None:
    """Inserisce le prese utilizzando il cursor di una transazione in corso."""

    for hold in validate_holds(holds_data):
        cursor.execute(
            "INSERT INTO holds (route_id, x, y, size, progression_id, constraint_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                route_id,
                hold["x"],
                hold["y"],
                hold["size"],
                hold["progression_id"],
                hold["constraint_id"],
            ),
        )


def add_holds(conn: libsql.Connection, route_id: int, holds_data: list) -> None:
    with atomic(conn) as cursor:
        insert_holds(cursor, route_id, holds_data)


def edit_holds(conn: libsql.Connection, route_id: int, holds_data: list) -> None:
    """Sostituisce le prese in modo atomico: non resta mai una route vuota."""

    validated = validate_holds(holds_data)
    with atomic(conn) as cursor:
        cursor.execute("DELETE FROM holds WHERE route_id = ?", (route_id,))
        insert_holds(cursor, route_id, validated)


### DELETES


def del_holds(conn: libsql.Connection, route_id: int) -> None:
    with atomic(conn) as cursor:
        cursor.execute("DELETE FROM holds WHERE route_id = ?", (route_id,))


### INIT


def init_holds_table(conn: libsql.Connection) -> None:
    conn.cursor().execute(
        """CREATE TABLE IF NOT EXISTS holds(
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
    conn.commit()
