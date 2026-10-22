"""WebSocket-Client für Home Assistant.

Der Verbindungsaufbau (auth_required -> auth -> auth_ok) und die generische Befehlshülle
(aufsteigende `id`, `type`) folgen der offiziell dokumentierten WebSocket-API.

Die Area-Registry-Hilfsmethode `get_or_create_area` nutzt dagegen die `config/area_registry/*`-
Befehle, die NICHT Teil der offiziell dokumentierten, stabilen API sind (siehe
docs/ARCHITECTURE.md Abschnitt 4). Sie werden vom offiziellen HA-Frontend verwendet, können sich
aber zwischen HA-Core-Versionen ohne Vorankündigung ändern. Jeder Fehlschlag wird daher als
`AreaRegistryUnsupportedError` signalisiert -- niemals als harter Absturz.
"""
from __future__ import annotations

import itertools
import json

import websockets

from app.ha_client.base import AreaDict
from app.ha_client.exceptions import AreaRegistryUnsupportedError, HomeAssistantUnavailableError


class HomeAssistantWebSocketClient:
    def __init__(self, ws_url: str, token: str, timeout: float = 10.0) -> None:
        self._ws_url = ws_url
        self._token = token
        self._timeout = timeout
        self._id_counter = itertools.count(1)

    async def _authenticated_connection(self):
        ws = await websockets.connect(self._ws_url, open_timeout=self._timeout)
        try:
            hello = json.loads(await ws.recv())
            if hello.get("type") != "auth_required":
                raise HomeAssistantUnavailableError(f"unexpected handshake message: {hello}")
            await ws.send(json.dumps({"type": "auth", "access_token": self._token}))
            auth_result = json.loads(await ws.recv())
            if auth_result.get("type") != "auth_ok":
                raise HomeAssistantUnavailableError(f"authentication failed: {auth_result}")
            return ws
        except Exception:
            await ws.close()
            raise

    async def _send_command(self, ws, payload: dict) -> dict:
        command_id = next(self._id_counter)
        await ws.send(json.dumps({**payload, "id": command_id}))
        response = json.loads(await ws.recv())
        if response.get("id") != command_id:
            raise HomeAssistantUnavailableError(f"out-of-order WebSocket response: {response}")
        return response

    async def get_or_create_area(self, name: str) -> AreaDict:
        """Best-Effort: listet vorhandene Areas, legt bei Bedarf eine neue an.

        Nutzt die internen Befehle `config/area_registry/list` und
        `config/area_registry/create`. Nicht über HA-Core-Versionen hinweg stabil garantiert.
        """
        try:
            ws = await self._authenticated_connection()
        except HomeAssistantUnavailableError:
            raise
        except Exception as exc:
            raise HomeAssistantUnavailableError(str(exc)) from exc

        try:
            list_resp = await self._send_command(ws, {"type": "config/area_registry/list"})
            if not list_resp.get("success"):
                raise AreaRegistryUnsupportedError(f"area_registry/list failed: {list_resp}")
            for area in list_resp.get("result", []):
                if area.get("name") == name:
                    return {"area_id": area["area_id"], "name": area["name"]}

            create_resp = await self._send_command(
                ws, {"type": "config/area_registry/create", "name": name}
            )
            if not create_resp.get("success"):
                raise AreaRegistryUnsupportedError(f"area_registry/create failed: {create_resp}")
            result = create_resp["result"]
            return {"area_id": result["area_id"], "name": result["name"]}
        except AreaRegistryUnsupportedError:
            raise
        except Exception as exc:
            raise AreaRegistryUnsupportedError(str(exc)) from exc
        finally:
            await ws.close()
