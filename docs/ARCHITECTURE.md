# Architektur — Daheim+ Agent

## 1. Überblick

Der **Daheim+ Agent** ist eine dauerhaft laufende Python/FastAPI-Anwendung, die als Home-Assistant-
Supervisor-Add-on neben Home Assistant Core auf dem Raspberry Pi läuft. Er verwaltet ein lokales
**Installation Manifest** (SQLite), spricht mit Home Assistant über dessen **dokumentierte**
REST- und WebSocket-API, und stellt eine Web-API für den Customer Setup Wizard bereit.

```
┌─────────────────────────────────────────────────────────────────┐
│ Raspberry Pi — Home Assistant OS                                 │
│                                                                   │
│  ┌───────────────────┐        ┌───────────────────────────────┐ │
│  │ Home Assistant Core│◄──────►│ Daheim+ Agent (dieses Repo)    │ │
│  │ (Supervisor-verw.) │  REST/ │                                 │ │
│  │                    │  WS    │ ┌─────────────┐ ┌─────────────┐ │ │
│  └───────────────────┘        │ │ FastAPI      │ │ SQLite       │ │ │
│                                 │ │ (Backend)    │ │ (Manifest)   │ │ │
│                                 │ └─────────────┘ └─────────────┘ │ │
│                                 │ ┌─────────────┐ ┌─────────────┐ │ │
│                                 │ │ HA-Client    │ │ Wizard-     │ │ │
│                                 │ │ (REST+WS)    │ │ Weboberfläche│ │ │
│                                 │ └─────────────┘ └─────────────┘ │ │
│                                 └───────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
          ▲
          │ HTTPS (lokal / optional Remote, siehe §6 Sicherheit)
          │
   Kunden-Browser (Setup Wizard, Dashboard)
```

## 2. Backend-Module (`backend/app`)

| Modul | Verantwortung | Milestone |
|---|---|---|
| `config.py` | Zentrale Settings via `pydantic-settings`, ausschließlich aus Umgebungsvariablen/`.env` | M1 |
| `db/` | SQLAlchemy Engine, Session-Verwaltung, ORM-Modelle (Installation, Building, Floor, Room, Resident) | M1/M2 |
| `schemas/` | Pydantic-Schemas für API-I/O und das Installation-Manifest-Aggregat | M1/M2 |
| `manifest/` | `ManifestService` — idempotente CRUD-Operationen, Versionierung, Soll-Ist-Abgleich (Rooms↔HA-Areas) | M2 |
| `ha_client/` | `HomeAssistantClient`-Protokoll mit REST-Implementierung, WS-Implementierung (inkl. Best-Effort-Area-Registry) und Mock-Implementierung | M1–M4 |
| `api/` | FastAPI-Router, lokale Token-Authentifizierung, Health-/Buildings-/Rooms-/Manifest-Endpunkte | M1/M2 |

Spätere Module (Device Discovery Manager, Shelly Adapter, Scenario Engine, Automation/Dashboard
Generator, Reconciliation Engine, Health Monitoring, Audit Logging) werden ab M3 ergänzt — siehe
`docs/IMPLEMENTATION_PLAN.md`.

## 3. Installation Manifest

Das Manifest ist die **Single Source of Truth** für eine Installation. Es wird in SQLite
gespeichert und über `ManifestService` versioniert (`Installation.manifest_version`, monoton
steigend bei jeder strukturellen Änderung).

Aktuell (M2) abgedeckte Entitäten:

- **Installation** — ID (UUID), Netzwerkmodus, Deployment-Status, Manifest-Version, Zeitstempel.
- **Building** — gehört zu genau einer Installation.
- **Floor** — gehört zu genau einem Building, optionale Ebenen-Nummer.
- **Room** — gehört zu genau einem Floor, Raumtyp, optionale `ha_area_id` + `sync_status` sobald
  ein Soll-Ist-Abgleich mit Home Assistant stattgefunden hat.

Für M3+ reservierte, in `docs/IMPLEMENTATION_PLAN.md` als offen dokumentierte Erweiterungen:
Bewohnerprofile (Resident), Sensoren/Geräte inkl. Capability Registry, Szenarien, Automations­
parameter. Diese Felder sind im Manifest-Schema als "reserved" markiert, aber noch nicht mit
Endpunkten versehen.

### Raumidentität

Ein Room wird intern über eine stabile UUID identifiziert, niemals über eine IP-Adresse oder reine
Namensgleichheit. Die optionale `ha_area_id` ist nur ein *Sync-Artefakt* — verliert der Agent die
Verbindung zu HA, bleibt das Manifest weiterhin die autoritative Quelle.

## 4. Home Assistant Integration — Research-Ergebnisse

Vor der Implementierung wurde die offizielle HA-Entwicklerdokumentation geprüft
(contributors.home-assistant.io, Stand Oktober 2026, Redirect von developers.home-assistant.io):

### REST-API (offiziell, stabil)

Dokumentierte Endpunkte u. a.: `GET /api/`, `GET /api/config`, `GET /api/states`,
`GET/POST /api/states/<entity_id>`, `GET /api/services`, `POST /api/services/<domain>/<service>`,
`POST /api/template`, `GET /api/events`. Authentifizierung ausschließlich über **Long-Lived Access
Tokens** als `Authorization: Bearer <token>`-Header.

→ **Es existiert kein dokumentierter REST-Endpunkt zur Verwaltung von Areas (Räumen).**

### WebSocket-API (offiziell dokumentierte Teile)

Auth-Handshake (`auth` → `auth_ok`), generische Befehlshülle (`id`, `type`, …),
`call_service`, `get_states`, `subscribe_events` etc. sind dokumentiert und stabil.

→ **Area-Registry-Befehle (`config/area_registry/list|create|update|delete`) sind NICHT in der
offiziellen WebSocket-API-Dokumentation beschrieben.** Sie existieren im HA-Core-Quellcode und
werden vom offiziellen Frontend verwendet, unterliegen aber nicht der versionierten
Backward-Compatibility-Garantie der dokumentierten API.

### Architekturentscheidung

1. Alle **lesenden** Health-/Status-Operationen laufen ausschließlich über die dokumentierte
   REST-API.
2. Die **Area-Erstellung** (`POST /manifest/rooms/{id}/sync`) nutzt die WS-Area-Registry-Befehle,
   ist aber explizit als **Best-Effort / nicht-stabile Integration** gekennzeichnet:
   - Feature-Flag `settings.ha_enable_area_registry` (Default: `true`, abschaltbar).
   - Jeder Fehler (z. B. unbekannter Befehl in künftigen HA-Versionen) führt zu einem klar
     protokollierten, nicht-fatalen `sync_status = "failed"` am Room — das Manifest bleibt
     konsistent, kein Absturz.
   - Diese Einschränkung ist in `docs/IMPLEMENTATION_PLAN.md` unter "Bekannte Einschränkungen"
     dokumentiert und wird dem Nutzer im Wizard als "Räume wurden im Manifest angelegt; HA-Sync:
     bestmöglich, nicht garantiert" kommuniziert.
3. Für Tests und lokale Entwicklung ohne echtes Home Assistant existiert ein
   `MockHomeAssistantClient`, der dieselbe Schnittstelle (`HomeAssistantClient`-Protokoll)
   implementiert. Umschaltung über `DAHEIM_HA_MODE=mock|live`.

## 5. Netzwerkarchitektur (Konfigurationsmodell)

`NetworkMode` (Enum: `MANAGED`, `CUSTOMER`, `HYBRID`) wird pro Installation im Manifest gespeichert.
Für M1/M2 ist dies ein reines **Konfigurationsmodell ohne automatische Netzwerk-Änderungen** — der
Agent liest/schreibt keine Netzwerk-Konfiguration des Raspberry Pi oder Routers. Erkennungs- und
Prüflogik (z. B. "ist ein eigener AP aktiv?", IPv6/mDNS-Voraussetzungen für Matter) folgt in M4/M6
und wird in `docs/IMPLEMENTATION_PLAN.md` als offen geführt.

## 6. Sicherheitsmodell

- **Authentifizierung der Daheim+-Web-API:** lokaler Bearer-Token (`DAHEIM_API_TOKEN`), geprüft via
  FastAPI-Dependency (`api/security.py`). Kein Default-Token im Code — fehlt die Variable, startet
  der Agent nicht im `live`-Modus.
- **Keine Secrets im Code oder in Git.** `.env` ist in `.gitignore`; `.env.example` dokumentiert
  benötigte Variablen ohne Werte.
- **Trennung lokal/remote:** Remote-Zugriff ist in M1/M2 nicht implementiert (Platzhalter in
  `config.py`, Default `disabled`) — wird gemäß Vorgabe erst nach expliziter Freigabe in M7 aktiv.
- **Audit-Grundlage:** Jede schreibende Manifest-Operation wird mit Zeitstempel, Benutzeraktion und
  Ergebnis geloggt (strukturierte Logs; dediziertes Audit-Log-Modul folgt in M4+).

## 7. Datenhaltung

SQLite-Datei unter `DAHEIM_DB_PATH` (Default: `./data/daheim.db`, in `.gitignore`). Tabellen werden
beim Start idempotent erzeugt (`Base.metadata.create_all`). Für M1/M2 wird bewusst auf ein externes
Migrationswerkzeug (Alembic) verzichtet, da das Schema additiv und einfach ist; sobald
Breaking-Changes an produktiven Manifesten nötig werden, wird Alembic nachgerüstet (siehe
Implementation Plan, M5/M6).
