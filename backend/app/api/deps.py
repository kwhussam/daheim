"""FastAPI-Dependencies: DB-Session pro Request, HA-Client als Prozess-Singleton.

Der HA-Client wird bewusst als Singleton gehalten, damit der MockHomeAssistantClient seinen
In-Memory-Zustand (angelegte Areas) über mehrere Requests hinweg behält -- genau wie ein echter
Home-Assistant-Prozess seinen Zustand über Requests hinweg behält.
"""
from __future__ import annotations

from typing import Generator

from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.base import get_sessionmaker
from app.ha_client.factory import build_ha_client

_ha_client_singleton = None


def get_db() -> Generator[Session, None, None]:
    SessionLocal = get_sessionmaker()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_ha_client():
    global _ha_client_singleton
    if _ha_client_singleton is None:
        _ha_client_singleton = build_ha_client(get_settings())
    return _ha_client_singleton


def reset_ha_client_singleton() -> None:
    """Nur für Tests: verwirft den Singleton, damit eine neue Konfiguration wirksam wird."""
    global _ha_client_singleton
    _ha_client_singleton = None
