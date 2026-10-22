# API-Referenz — Daheim+ Agent (Stand: M1/M2)

Basis-URL (Entwicklung): `http://localhost:8099`
Alle Endpunkte (außer `/api/v1/health`) erfordern einen Bearer-Token:

```
Authorization: Bearer <DAHEIM_API_TOKEN>
```

Fehlt oder ist der Token ungültig → `401 Unauthorized`.

Interaktive OpenAPI-Dokumentation: `GET /docs` (Swagger UI), `GET /openapi.json`.

## Home Assistant API — Research-Ergebnisse (Grundlage dieser Implementierung)

Geprüft am 22.10.2026 gegen die offizielle HA-Entwicklerdokumentation
(`contributors.home-assistant.io`, Redirect-Ziel von `developers.home-assistant.io/docs/api/*`):

| Mechanismus | Status | Verwendung in Daheim+ |
|---|---|---|
| REST `GET /api/`, `/api/config`, `/api/states`, `/api/services`, `/api/template` | **Offiziell dokumentiert, stabil**, Bearer-Token-Auth | Health-Check, zukünftige State-Abfragen |
| WebSocket Auth-Handshake, `call_service`, `get_states`, `subscribe_events` | **Offiziell dokumentiert, stabil** | Grundlage des WS-Clients |
| WebSocket `config/area_registry/list\|create\|update\|delete` | **Nicht in der offiziellen API-Doku beschrieben** — intern vom HA-Frontend genutzt, keine Backward-Compat-Garantie | Best-Effort-Raum-Sync (`POST /rooms/{id}/sync`), mit Fehlerbehandlung statt Absturz |
| REST-Endpunkt für Area-Verwaltung | **Existiert nicht** | — |

Konsequenz: Jeder Endpunkt dieser API, der HA-Areas erzeugt, ist explizit als "Best-Effort"
gekennzeichnet (Response-Feld `sync_status`), niemals als garantiert.

---

## `GET /api/v1/health`

Kein Auth-Token erforderlich (Erreichbarkeits-Check für Monitoring/Supervisor).

**Response `200 OK`:**
```json
{
  "status": "ok",
  "version": "0.2.0",
  "ha_mode": "mock",
  "database": "ok",
  "home_assistant": {
    "reachable": true,
    "mode": "mock",
    "detail": "mock client always reachable"
  }
}
```

Im `live`-Modus wird `home_assistant.reachable` über einen echten `GET /api/`-Aufruf an die
konfigurierte HA-Instanz ermittelt (dokumentierte REST-API, 5s Timeout, Fehler werden nicht nach
außen geworfen, sondern als `reachable: false` + `detail` gemeldet).

---

## `POST /api/v1/installations`

Legt eine neue Installation an (idempotent über optional übergebene `installation_id`).

**Request:**
```json
{ "network_mode": "managed" }
```
`network_mode` ∈ `managed | customer | hybrid` (Default: `managed`).

**Response `201 Created`:**
```json
{
  "id": "6a9f6e2e-6c3b-4b7a-9a3b-1f9e8d2c4a10",
  "network_mode": "managed",
  "deployment_status": "draft",
  "manifest_version": 1,
  "created_at": "2026-10-22T10:00:00Z",
  "updated_at": "2026-10-22T10:00:00Z"
}
```

## `GET /api/v1/installations/{installation_id}`

Gibt die Installation ohne verschachtelte Buildings zurück (siehe `/manifest` für den vollen Baum).

---

## `POST /api/v1/buildings`

**Request:**
```json
{ "installation_id": "6a9f6e2e-...", "name": "Hauptgebäude", "address": "Musterstraße 1" }
```

**Response `201 Created`:** Building-Objekt mit `id`. Doppelter `name` innerhalb derselben
Installation → `409 Conflict`.

## `GET /api/v1/buildings?installation_id=...`

Liste aller Buildings einer Installation.

## `PATCH /api/v1/buildings/{building_id}`

Teilupdate (`name`, `address`). Erhöht `manifest_version` der zugehörigen Installation.

## `DELETE /api/v1/buildings/{building_id}`

Löscht Building inkl. Floors/Rooms (Cascade). `404` falls nicht vorhanden.

---

## `POST /api/v1/buildings/{building_id}/floors`

**Request:** `{ "name": "Erdgeschoss", "level": 0 }`

**Response `201 Created`:** Floor-Objekt. Doppelter `name` auf demselben Building → `409`.

## `GET /api/v1/buildings/{building_id}/floors`

Liste der Floors eines Buildings.

---

## `POST /api/v1/rooms`

**Request:**
```json
{
  "floor_id": "f1b2...",
  "name": "Wohnzimmer",
  "room_type": "living_room"
}
```
`room_type` ∈ `living_room | bedroom | kitchen | bathroom | hallway | office | other`.

**Response `201 Created`:**
```json
{
  "id": "r001...",
  "floor_id": "f1b2...",
  "name": "Wohnzimmer",
  "room_type": "living_room",
  "ha_area_id": null,
  "sync_status": "pending",
  "created_at": "2026-10-22T10:05:00Z"
}
```

Doppelter `name` auf demselben Floor → `409 Conflict` ("keine doppelten Räume").

## `GET /api/v1/rooms?floor_id=...`

Liste der Räume eines Floors.

## `PATCH /api/v1/rooms/{room_id}` / `DELETE /api/v1/rooms/{room_id}`

Teilupdate bzw. Löschen. Erhöhen/ändern `manifest_version`.

## `POST /api/v1/rooms/{room_id}/sync`

Löst den **Best-Effort**-Abgleich mit Home Assistant aus: legt (im `live`-Modus) eine HA-Area über
die nicht-offizielle WebSocket-Area-Registry an bzw. verknüpft eine vorhandene Area, oder bedient im
`mock`-Modus den `MockHomeAssistantClient`.

**Response `200 OK` (Erfolg):**
```json
{ "id": "r001...", "ha_area_id": "wohnzimmer", "sync_status": "synced" }
```

**Response `200 OK` (Fehlschlag, kontrolliert):**
```json
{ "id": "r001...", "ha_area_id": null, "sync_status": "failed", "sync_error": "home assistant unreachable" }
```

Dieser Endpunkt wirft **nie** eine 5xx-Exception wegen eines HA-Fehlers — ein nicht erreichbares
oder inkompatibles HA-System führt zu einem dokumentierten `failed`-Zustand, nicht zu einem Absturz.

---

## `GET /api/v1/manifest?installation_id=...`

Gibt den vollständigen aktuellen Manifest-Baum zurück (Installation → Buildings → Floors → Rooms)
inklusive `manifest_version`. Dient dem Wizard/Dashboard als Single-Source-of-Truth-Export.

```json
{
  "installation": { "id": "...", "network_mode": "managed", "deployment_status": "draft", "manifest_version": 4 },
  "buildings": [
    {
      "id": "...", "name": "Hauptgebäude",
      "floors": [
        {
          "id": "...", "name": "Erdgeschoss",
          "rooms": [
            { "id": "...", "name": "Wohnzimmer", "room_type": "living_room", "sync_status": "pending" }
          ]
        }
      ]
    }
  ]
}
```

---

## Fehlerformat

Alle Fehler folgen dem FastAPI-Standard:
```json
{ "detail": "Building with this name already exists for this installation." }
```

## Geplante Endpunkte (M3+, noch nicht implementiert)

- `POST /api/v1/residents`, Szenario-Auswahl, Automationsparameter (M3)
- `POST /api/v1/devices/discover`, Shelly-Zuordnung (M4)
- `POST /api/v1/automations/generate`, `POST /api/v1/dashboard/generate` (M5)
