"""In-Memory-Ersatz für Home Assistant -- für Entwicklung und Tests ohne echte Hardware/HA.

WICHTIG: Dieser Client ist bewusst NICHT mit einem echten Home-Assistant-System verbunden.
Jede Aussage über Erfolg ("synced") bezieht sich ausschließlich auf den In-Memory-Zustand
dieses Mocks, nicht auf eine tatsächlich getestete Hardware-/HA-Integration.
"""
from __future__ import annotations

import re

from app.ha_client.base import AreaDict, HAHealthResult


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")
    return slug or "area"


class MockHomeAssistantClient:
    mode = "mock"

    def __init__(self) -> None:
        self._areas: dict[str, AreaDict] = {}

    async def check_health(self) -> HAHealthResult:
        return HAHealthResult(reachable=True, mode=self.mode, detail="mock client always reachable")

    async def list_areas(self) -> list[AreaDict]:
        return list(self._areas.values())

    async def get_or_create_area(self, name: str) -> AreaDict:
        for area in self._areas.values():
            if area["name"] == name:
                return area
        area_id = _slugify(name)
        area: AreaDict = {"area_id": area_id, "name": name}
        self._areas[area_id] = area
        return area

    async def close(self) -> None:
        return None
