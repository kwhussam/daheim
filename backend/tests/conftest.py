"""Pytest-Fixtures: isolierte SQLite-Datei + Mock-HA-Client pro Test."""
from __future__ import annotations

import uuid

import pytest


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = tmp_path / f"{uuid.uuid4()}.db"
    monkeypatch.setenv("DAHEIM_DB_PATH", str(db_path))
    monkeypatch.setenv("DAHEIM_API_TOKEN", "test-token")
    monkeypatch.setenv("DAHEIM_HA_MODE", "mock")

    from app import config as config_module

    config_module.get_settings.cache_clear()

    from app.db import base as db_base

    db_base.reset_db_state()
    db_base.init_db()

    from app.api.deps import get_ha_client, reset_ha_client_singleton
    from app.ha_client.mock_client import MockHomeAssistantClient
    from app.main import app

    reset_ha_client_singleton()
    mock_ha = MockHomeAssistantClient()
    app.dependency_overrides[get_ha_client] = lambda: mock_ha

    from fastapi.testclient import TestClient

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    config_module.get_settings.cache_clear()
    db_base.reset_db_state()


@pytest.fixture()
def auth_headers():
    return {"Authorization": "Bearer test-token"}
