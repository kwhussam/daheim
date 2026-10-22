"""Zentrale Konfiguration des Daheim+ Agent.

Alle Werte kommen ausschließlich aus Umgebungsvariablen (Prefix DAHEIM_) oder einer lokalen,
nicht versionierten .env-Datei -- niemals hartcodiert. Siehe docs/TESTING.md für die Liste der
unterstützten Variablen.
"""
from __future__ import annotations

import enum
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class HAMode(str, enum.Enum):
    """Betriebsmodus des Home-Assistant-Clients -- siehe docs/ARCHITECTURE.md Abschnitt 4."""

    MOCK = "mock"
    LIVE = "live"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DAHEIM_", env_file=".env", extra="ignore")

    app_version: str = "0.2.0"
    api_token: str | None = None
    db_path: str = "./data/daheim.db"

    ha_mode: HAMode = HAMode.MOCK
    ha_url: str | None = None
    ha_token: str | None = None
    ha_enable_area_registry: bool = True

    # Bewusst noch nicht aktivierbar -- Remote-Zugriff erfordert gemäß Vorgabe eine
    # explizite, separate Freigabe (geplant für M7).
    remote_access_enabled: bool = False

    @property
    def sqlite_url(self) -> str:
        if self.db_path == ":memory:":
            return "sqlite:///:memory:"
        return f"sqlite:///{self.db_path}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
