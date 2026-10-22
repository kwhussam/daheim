"""SQLAlchemy Engine/Session-Verwaltung.

Engine und Sessionmaker werden lazy aufgebaut (nicht beim Modul-Import), damit Tests über
Umgebungsvariablen + reset_db_state() eine eigene, isolierte SQLite-Datei je Testlauf verwenden
können, ohne das Modul neu importieren zu müssen.
"""
from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def _build_engine() -> Engine:
    settings = get_settings()
    db_path = settings.db_path
    if db_path != ":memory:":
        directory = os.path.dirname(db_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
    return create_engine(settings.sqlite_url, connect_args={"check_same_thread": False})


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = _build_engine()
    return _engine


def get_sessionmaker() -> sessionmaker[Session]:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)
    return _SessionLocal


def init_db() -> None:
    """Erzeugt fehlende Tabellen idempotent. Sicher bei jedem Start erneut aufzurufen."""
    from app.db import models  # noqa: F401 -- registriert ORM-Modelle an Base.metadata

    Base.metadata.create_all(bind=get_engine())


def reset_db_state() -> None:
    """Nur für Tests: verwirft Engine/Sessionmaker, damit eine neue DAHEIM_DB_PATH wirksam wird."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
