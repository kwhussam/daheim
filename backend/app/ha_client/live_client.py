"""Komponiert REST- (Health) und WebSocket-Client (Best-Effort-Areas) zu einem einzigen
HomeAssistantClient-kompatiblen Objekt für echte Home-Assistant-Instanzen."""
from __future__ import annotations

from app.ha_client.base import AreaDict, HAHealthResult
from app.ha_client.rest_client import HomeAssistantRestClient
from app.ha_client.ws_client import HomeAssistantWebSocketClient


def _ws_url_from_base(base_url: str) -> str:
    url = base_url.rstrip("/")
    if url.startswith("https://"):
        return "wss://" + url[len("https://") :] + "/api/websocket"
    if url.startswith("http://"):
        return "ws://" + url[len("http://") :] + "/api/websocket"
    return url + "/api/websocket"


class LiveHomeAssistantClient:
    mode = "live"

    def __init__(self, base_url: str, token: str) -> None:
        self._rest = HomeAssistantRestClient(base_url, token)
        self._ws = HomeAssistantWebSocketClient(_ws_url_from_base(base_url), token)

    async def check_health(self) -> HAHealthResult:
        return await self._rest.check_health()

    async def get_or_create_area(self, name: str) -> AreaDict:
        return await self._ws.get_or_create_area(name)

    async def close(self) -> None:
        return None
