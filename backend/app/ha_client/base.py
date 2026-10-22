"""Gemeinsame Typen/Protokoll für Home-Assistant-Clients (Mock und Live)."""
from __future__ import annotations

from typing import Protocol, TypedDict


class AreaDict(TypedDict):
    area_id: str
    name: str


class HAHealthResult:
    def __init__(self, reachable: bool, mode: str, detail: str | None = None) -> None:
        self.reachable = reachable
        self.mode = mode
        self.detail = detail


class HomeAssistantClient(Protocol):
    """Schnittstelle, die sowohl MockHomeAssistantClient als auch LiveHomeAssistantClient
    erfüllen. Business-Logik (ManifestService) programmiert ausschließlich gegen dieses
    Protokoll, nie gegen eine konkrete Implementierung."""

    mode: str

    async def check_health(self) -> HAHealthResult: ...

    async def get_or_create_area(self, name: str) -> AreaDict: ...

    async def close(self) -> None: ...
