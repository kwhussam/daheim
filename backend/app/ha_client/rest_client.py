"""Client für die offiziell dokumentierte Home-Assistant-REST-API.

Nutzt ausschließlich Endpunkte, die unter
contributors.home-assistant.io/core/internals/rest-api/ dokumentiert sind
(GET /api/ als Erreichbarkeits-Check; Bearer-Token-Authentifizierung). Siehe
docs/ARCHITECTURE.md Abschnitt 4 für die Research-Grundlage dieser Entscheidung.
"""
from __future__ import annotations

import httpx

from app.ha_client.base import HAHealthResult


class HomeAssistantRestClient:
    def __init__(self, base_url: str, token: str, timeout: float = 5.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {token}"}
        self._timeout = timeout

    async def check_health(self) -> HAHealthResult:
        url = f"{self._base_url}/api/"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url, headers=self._headers)
        except httpx.HTTPError as exc:
            return HAHealthResult(reachable=False, mode="live", detail=f"request failed: {exc}")

        if response.status_code == 200:
            return HAHealthResult(reachable=True, mode="live", detail="REST API reachable")
        return HAHealthResult(
            reachable=False, mode="live", detail=f"unexpected status code {response.status_code}"
        )
