"""Factory: liefert je nach Konfiguration den Mock- oder den Live-HA-Client.

Trennt Mock-Betrieb eindeutig vom Produktivbetrieb (Vorgabe Abschnitt 11, Punkt 6):
nur DAHEIM_HA_MODE=live spricht jemals mit einer echten Home-Assistant-Instanz.
"""
from __future__ import annotations

from app.config import HAMode, Settings
from app.ha_client.live_client import LiveHomeAssistantClient
from app.ha_client.mock_client import MockHomeAssistantClient


def build_ha_client(settings: Settings):
    if settings.ha_mode == HAMode.LIVE:
        if not settings.ha_url or not settings.ha_token:
            raise RuntimeError(
                "DAHEIM_HA_MODE=live erfordert DAHEIM_HA_URL und DAHEIM_HA_TOKEN."
            )
        return LiveHomeAssistantClient(settings.ha_url, settings.ha_token)
    return MockHomeAssistantClient()
