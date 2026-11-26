"""Helper per eseguire più istruzioni in modo atomico."""

from __future__ import annotations

from contextlib import contextmanager

import libsql


@contextmanager
def atomic(conn: libsql.Connection):
    """Esegue le istruzioni in un blocco, con commit o rollback."""

    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
