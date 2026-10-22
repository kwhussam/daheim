"""Daheim+ Agent -- FastAPI-Einstiegspunkt."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import buildings, health, installations, manifest, rooms
from app.config import get_settings
from app.db.base import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Daheim+ Agent", version=get_settings().app_version, lifespan=lifespan)

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(installations.router, prefix="/api/v1", tags=["installations"])
app.include_router(buildings.router, prefix="/api/v1", tags=["buildings"])
app.include_router(rooms.router, prefix="/api/v1", tags=["rooms"])
app.include_router(manifest.router, prefix="/api/v1", tags=["manifest"])

# Einfache, erreichbare Weboberfläche (M1-Anforderung). Der vollständige Setup-Wizard folgt in M3.
_WIZARD_DIR = Path(__file__).resolve().parent.parent.parent / "frontend" / "wizard"
if _WIZARD_DIR.exists():
    app.mount("/", StaticFiles(directory=str(_WIZARD_DIR), html=True), name="wizard")
