"""Health-Endpoint -- kein Auth-Token erforderlich (Erreichbarkeits-Check für Supervisor/Monitoring)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text

from app.api.deps import get_ha_client
from app.config import Settings, get_settings
from app.db.base import get_sessionmaker
from app.schemas.manifest import HAHealth, HealthStatus

router = APIRouter()


@router.get("/health", response_model=HealthStatus)
async def health_check(
    settings: Settings = Depends(get_settings),
    ha_client=Depends(get_ha_client),
) -> HealthStatus:
    db_status = "ok"
    try:
        session = get_sessionmaker()()
        try:
            session.execute(text("SELECT 1"))
        finally:
            session.close()
    except Exception:  # noqa: BLE001 -- Health-Check darf nicht wegen DB-Fehler crashen
        db_status = "error"

    ha_result = await ha_client.check_health()
    return HealthStatus(
        status="ok",
        version=settings.app_version,
        ha_mode=settings.ha_mode.value,
        database=db_status,
        home_assistant=HAHealth(
            reachable=ha_result.reachable, mode=ha_result.mode, detail=ha_result.detail
        ),
    )
