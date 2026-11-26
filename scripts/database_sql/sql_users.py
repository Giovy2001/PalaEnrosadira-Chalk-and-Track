"""Accesso alla tabella users."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import libsql

EDITABLE_FIELDS = {
    "user_color",
    "points",
    "last_seen_date",
    "serialized_completed_routes",
    "auth_token_hash",
}

TABLE_STRUCTURE = (
    "user_id",
    "user_name",
    "user_color",
    "creation_date",
    "last_seen_date",
    "points",
    "serialized_completed_routes",
    "auth_token_hash",
)
# SELECT esplicito: i database creati prima della rimozione di `user_icon`
# hanno un numero di colonne diverso, quindi `SELECT *` sfaserebbe i campi.
SELECT_COLUMNS = ", ".join(TABLE_STRUCTURE)


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _validate_username(user_name: str) -> str:
    if not isinstance(user_name, str) or not user_name.strip():
        raise ValueError("Nome utente non valido")
    return user_name.strip()


def format_table(user_object: tuple) -> dict:
    """Converte una riga users in dizionario, deserializzando i completamenti."""

    user_dict = {
        column: user_object[index]
        for index, column in enumerate(TABLE_STRUCTURE)
        if index < len(user_object)
    }
    raw_completed = user_dict.get("serialized_completed_routes") or "[]"
    try:
        user_dict["serialized_completed_routes"] = json.loads(raw_completed)
    except (TypeError, ValueError):
        user_dict["serialized_completed_routes"] = []
    return user_dict


### GETS


def get_all_users(conn: libsql.Connection) -> list[dict]:
    cursor = conn.cursor()
    users = cursor.execute(f"SELECT {SELECT_COLUMNS} FROM users").fetchall()
    return [format_table(user) for user in users]


def get_user(conn: libsql.Connection, user_name: str) -> dict:
    """Restituisce l'utente oppure ``{"exist": False}``."""

    if not isinstance(user_name, str) or not user_name.strip():
        return {"exist": False}
    cursor = conn.cursor()
    user = cursor.execute(
        f"SELECT {SELECT_COLUMNS} FROM users WHERE user_name = ?",
        (user_name.strip(),),
    ).fetchone()
    if not user:
        return {"exist": False}
    user_dict = format_table(user)
    user_dict["exist"] = True
    return user_dict


### SETS


def edit_user(conn: libsql.Connection, user_name: str, data_to_override: dict) -> None:
    """Aggiorna solo colonne ammesse della tabella users."""

    if not data_to_override:
        raise ValueError("Nessun dato da aggiornare")
    invalid = set(data_to_override) - EDITABLE_FIELDS
    if invalid:
        raise ValueError(f"Campi non aggiornabili: {', '.join(sorted(invalid))}")

    user_name = _validate_username(user_name)
    instruction = ", ".join(f"{key} = ?" for key in data_to_override)
    values = [*data_to_override.values(), user_name]
    conn.cursor().execute(
        f"UPDATE users SET {instruction} WHERE user_name = ?", values
    )
    conn.commit()


def edit_completed_routes(
    conn: libsql.Connection, user_name: str, completed_routes: list
) -> None:
    if not isinstance(completed_routes, list):
        raise ValueError("I blocchi completati devono essere una lista")
    edit_user(
        conn,
        user_name,
        {
            "serialized_completed_routes": json.dumps(completed_routes),
            "last_seen_date": _today(),
        },
    )


def add_points(conn: libsql.Connection, user_name: str, points: int) -> None:
    """Aggiunge punti all'utente, aggiornando last_seen_date."""

    if not isinstance(points, int):
        raise ValueError("I punti devono essere un intero")
    user = get_user(conn, user_name)
    if not user.get("exist"):
        raise ValueError("Utente inesistente")
    edit_user(
        conn,
        user_name,
        {
            "points": int(user["points"] or 0) + points,
            "last_seen_date": _today(),
        },
    )


def add_user(conn: libsql.Connection, user_data: dict) -> None:
    """Crea un nuovo utente. Solleva ValueError se i dati non sono validi."""

    user_name = _validate_username(user_data.get("user_name"))
    color = user_data.get("user_color", 0)
    try:
        color = int(color)
    except (TypeError, ValueError) as exc:
        raise ValueError("Colore non valido") from exc
    if not 0 <= color <= 7:
        raise ValueError("Colore non valido")

    if get_user(conn, user_name).get("exist"):
        raise ValueError("Utente già esistente")

    today = _today()
    conn.cursor().execute(
        "INSERT INTO users(user_name, user_color, creation_date, last_seen_date, "
        "points, serialized_completed_routes, auth_token_hash) VALUES (?,?,?,?,?,?,?)",
        (user_name, str(color), today, today, 0, json.dumps([]), None),
    )
    conn.commit()


### DELETES


def del_user(conn: libsql.Connection, user_name: str) -> None:
    conn.cursor().execute(
        "DELETE FROM users WHERE user_name = ?", (_validate_username(user_name),)
    )
    conn.commit()


### INIT


def init_users_table(conn: libsql.Connection) -> None:
    conn.cursor().execute(
        """CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT UNIQUE,
        user_color TEXT,
        creation_date TEXT,
        last_seen_date TEXT,
        points INTEGER,
        serialized_completed_routes TEXT,
        auth_token_hash TEXT
    )"""
    )
    conn.commit()
