"""Fehlerklassen der Home-Assistant-Integration."""
from __future__ import annotations


class HomeAssistantError(Exception):
    """Basisklasse für alle Home-Assistant-Integrationsfehler."""


class HomeAssistantUnavailableError(HomeAssistantError):
    """Die konfigurierte Home-Assistant-Instanz ist nicht erreichbar oder die
    Authentifizierung ist fehlgeschlagen."""


class AreaRegistryUnsupportedError(HomeAssistantError):
    """Die Best-Effort-Area-Registry-WebSocket-Befehle sind fehlgeschlagen oder nicht
    verfügbar.

    Diese Befehle (`config/area_registry/*`) sind NICHT Teil der offiziell dokumentierten,
    stabilen Home-Assistant-API (siehe docs/ARCHITECTURE.md Abschnitt 4). Diese Exception
    signalisiert einen kontrollierten, erwarteten Fehlerfall -- Aufrufer müssen sie abfangen
    und kontrolliert degradieren (Room.sync_status = failed), niemals abstürzen.
    """
