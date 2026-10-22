# Implementierungsplan — Daheim+

## Meilenstein-Übersicht

| Meilenstein | Inhalt | Status |
|---|---|---|
| **M1** | Installierbarer Agent (HA-Add-on-Grundgerüst), FastAPI, HA-API-Client, Health-Endpoint, einfache Weboberfläche | ✅ Implementiert & getestet |
| **M2** | SQLite, Installation Manifest, Gebäude- & Raumverwaltung (inkl. Best-Effort-HA-Area-Sync) | ✅ Implementiert & getestet |
| **M3** | Wizard für Gebäude, Räume, Bewohnerprofile, Szenarioauswahl (React/TS, Fortschritts-Persistenz) | ⏳ Offen |
| **M4** | Shelly-Discovery, Geräteidentifikation, Raumzuordnung, Device Capability Registry | ⏳ Offen |
| **M5** | Automation Generator, Dashboard Generator, Validierung, Backups vor kritischen Änderungen | ⏳ Offen |
| **M6** | Funktionstests, QR-Onboarding, Hybridnetzwerk-Prüfungen, geführte Matter-Integration | ⏳ Offen |
| **M7** | Remote Management, Monitoring, kontrolliertes Recovery | ⏳ Offen |

Dieses Dokument wird nach jedem Meilenstein aktualisiert.

---

## M1 — Was tatsächlich implementiert und getestet wurde

- **FastAPI-Backend** (`backend/app/main.py`) mit modularer Router-Struktur.
- **Health-Endpoint** `GET /api/v1/health`: prüft App-Status, DB-Erreichbarkeit und (falls
  `DAHEIM_HA_MODE=live`) HA-Erreichbarkeit über die dokumentierte REST-API (`GET /api/`).
  Im Mock-Modus liefert er einen klar als `"ha_mode": "mock"` gekennzeichneten Status.
- **Home Assistant REST-Client** (`ha_client/rest_client.py`): nutzt ausschließlich dokumentierte,
  stabile Endpunkte (`/api/`, `/api/config`) mit Bearer-Token-Auth (`httpx`).
- **Home Assistant WebSocket-Client** (`ha_client/ws_client.py`): implementiert den dokumentierten
  Auth-Handshake und generische Befehlsversendung; die Area-Registry-Methoden sind separat als
  Best-Effort markiert (siehe `docs/ARCHITECTURE.md` §4).
- **Mock-HA-Client** (`ha_client/mock_client.py`): vollständige In-Memory-Implementierung für
  Entwicklung/Tests ohne echtes Home Assistant. Default in Entwicklung.
- **Einfache, erreichbare Weboberfläche** (`frontend/wizard/index.html`): statische Seite, die
  Health-Status sowie (ab M2) Gebäude/Räume über die API abruft und anzeigt. Dies **ist nicht**
  der vollständige Setup-Wizard (folgt in M3), sondern erfüllt die M1-Anforderung "einfache
  erreichbare Wizard-Weboberfläche".
- **Home-Assistant-Add-on-Grundgerüst** (`ha_addon/daheim_plus_agent/`): `config.yaml`, `Dockerfile`,
  `run.sh` nach dem offiziellen HA-Add-on-Schema (Supervisor-Add-on-Format), sodass der Agent als
  lokales Add-on gebaut/installiert werden kann. **Nicht getestet** gegen eine echte Supervisor-
  Installation (kein Hardware/HA-OS in dieser Entwicklungsumgebung verfügbar) — siehe
  "Bekannte Einschränkungen" unten.
- **Automatisierte Tests** (`backend/tests/`): pytest-Suite, u. a. Health-Endpoint, Mock-HA-Client.

## M2 — Was tatsächlich implementiert und getestet wurde

- **SQLite-Datenbank** über SQLAlchemy 2.0 (`db/base.py`, `db/models.py`), idempotente
  Tabellenerstellung beim Start.
- **Installation-Manifest-Modell**: `Installation` (ID, Netzwerkmodus, Deployment-Status,
  Manifest-Version) als Wurzel, mit `Building` → `Floor` → `Room`.
- **ManifestService** (`manifest/service.py`): idempotente CRUD-Operationen für Buildings/Floors/
  Rooms, automatische Versionierung des Manifests bei jeder strukturellen Änderung, Soll-Ist-
  Vergleich (`reconcile_rooms`) zwischen Manifest-Räumen und (im Live-Modus) tatsächlichen
  HA-Areas.
- **API-Endpunkte**:
  - `POST/GET /api/v1/installations`
  - `POST/GET/PATCH/DELETE /api/v1/buildings`
  - `POST/GET/PATCH/DELETE /api/v1/buildings/{id}/floors`
  - `POST/GET/PATCH/DELETE /api/v1/rooms`
  - `GET /api/v1/manifest` (vollständiger aktueller Manifest-Export inkl. Version)
  - `POST /api/v1/rooms/{id}/sync` (Best-Effort HA-Area-Erstellung/-Abgleich)
- **Tatsächliche HA-Raum-Erstellung**: implementiert über die (nicht offiziell stabile)
  WebSocket-Area-Registry-Befehle, **nur im `live`-Modus** und nur nach explizitem Aufruf des
  Sync-Endpunkts (keine automatischen, ungefragten Änderungen an einer echten HA-Instanz).
  Im Mock-Modus wird dieselbe Logik gegen den `MockHomeAssistantClient` **funktional getestet**
  (Area wird im Mock-Zustand angelegt, `sync_status` wechselt zu `synced`).
  **Gegen eine echte Home-Assistant-Instanz wurde dies in dieser Umgebung nicht getestet** —
  siehe Einschränkungen.
- **Validierung**: keine doppelten Räume pro Floor (eindeutiger Name+Floor-Constraint), keine
  doppelten Buildings pro Installation.
- **Tests**: Building-CRUD, Room-CRUD, Manifest-Versionierung, Reconciliation gegen Mock-HA,
  Auth (fehlender/ungültiger Token → 401).

## Bekannte Einschränkungen (ehrlich dokumentiert)

1. **Keine echte Home-Assistant-Instanz verfügbar.** Alle HA-Interaktionen wurden gegen den
   `MockHomeAssistantClient` getestet, nicht gegen eine echte HA-OS-Installation auf einem
   Raspberry Pi. Die REST/WS-Client-Implementierung folgt exakt der offiziellen Doku, ist aber
   nicht gegen reale Versions-Eigenheiten verifiziert.
2. **Area-Registry-Sync ist Best-Effort, nicht garantiert stabil.** Die verwendeten
   `config/area_registry/*`-WebSocket-Befehle sind nicht Teil der offiziell versionierten API.
   Bricht ein zukünftiges HA-Core-Update diese Befehle, bleibt das Manifest konsistent, aber der
   Sync schlägt kontrolliert fehl (`sync_status = "failed"`, keine Exception nach außen).
3. **Home-Assistant-Add-on wurde nicht in einer echten Supervisor-Umgebung installiert/getestet.**
   Struktur und Konfiguration folgen dem offiziellen Add-on-Schema, aber ein realer
   Installationstest auf HA OS steht aus.
4. **Residents, Sensoren, Szenarien, Automationsparameter** sind im Manifest-Schema als
   "reserved"/zukünftig markiert, aber in M1/M2 bewusst **nicht** implementiert — das ist exakt der
   in der Vorgabe definierte Scope von M3/M4/M5.
5. **Netzwerkmodus (Managed/Customer/Hybrid)** existiert nur als Konfigurations-Enum im Manifest.
   Erkennungs-/Prüflogik (AP-Erkennung, IPv6/mDNS/Matter-Routing-Anforderungen) ist nicht
   implementiert — geplant für M4/M6.
6. **Kein Remote-Zugriff implementiert.** Bewusst nicht vor M7 und expliziter Freigabe.
7. **Kein Alembic/Migrationswerkzeug.** Für das aktuelle additive Schema ausreichend; wird vor
   produktionskritischen Schemaänderungen nachgerüstet.

## Nächste Schritte (M3)

- React/TypeScript-Wizard mit den 10 in der Vorgabe definierten Schritten.
- Persistenz des Wizard-Fortschritts (serverseitig, an die Installation gebunden, überlebt
  Browser-Neustart).
- Resident-Schema (ohne unnötige PII) + Szenario-Auswahl-Endpunkte.
