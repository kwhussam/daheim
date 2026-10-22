"""Lokale Bearer-Token-Authentifizierung der Daheim+-Web-API.

Kein Default-Token im Code. Fehlt DAHEIM_API_TOKEN, antwortet jeder geschützte Endpunkt mit
503 statt mit einem unsicheren Default -- siehe docs/ARCHITECTURE.md Abschnitt 6.
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings, get_settings

_bearer_scheme = HTTPBearer(auto_error=False)


def require_api_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> None:
    if not settings.api_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Server is missing DAHEIM_API_TOKEN configuration.",
        )
    if credentials is None or credentials.credentials != settings.api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API token."
        )
