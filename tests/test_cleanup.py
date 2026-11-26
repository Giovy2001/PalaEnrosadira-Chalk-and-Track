"""Test della protezione del cron di pulizia."""

from __future__ import annotations

import importlib

import settings


def test_cron_requires_secret_when_unconfigured(monkeypatch):
    monkeypatch.delenv("CRON_SECRET", raising=False)
    monkeypatch.setattr(settings, "CRON_SECRET", "")
    import api.database_cleanup as cleanup

    importlib.reload(cleanup)
    assert cleanup.app.test_client().get("/api/database_cleanup").status_code == 401


def test_cron_rejects_wrong_secret(monkeypatch):
    monkeypatch.setattr(settings, "CRON_SECRET", "secret-corretto")
    import api.database_cleanup as cleanup

    importlib.reload(cleanup)
    client = cleanup.app.test_client()
    assert (
        client.get(
            "/api/database_cleanup", headers={"Authorization": "Bearer sbagliato"}
        ).status_code
        == 401
    )
