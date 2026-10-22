# Installations- und Testanleitung — Daheim+ Agent

## Voraussetzungen

- Python 3.12 (oder neuer)
- Kein echtes Home Assistant notwendig für Entwicklung/Tests (Mock-Modus)

## Installation (Entwicklung)

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Konfiguration

Kopiere `.env.example` nach `.env` und passe Werte an (niemals `.env` committen):

```bash
cp .env.example .env
```

Wichtige Variablen (siehe `app/config.py`):

| Variable | Default | Beschreibung |
|---|---|---|
| `DAHEIM_HA_MODE` | `mock` | `mock` (kein echtes HA nötig) oder `live` |
| `DAHEIM_API_TOKEN` | — (Pflicht) | Bearer-Token für die Daheim+-Web-API |
| `DAHEIM_DB_PATH` | `./data/daheim.db` | Pfad zur SQLite-Datei |
| `DAHEIM_HA_URL` | — | Nur bei `live`: Basis-URL der Home-Assistant-Instanz, z. B. `http://homeassistant.local:8123` |
| `DAHEIM_HA_TOKEN` | — | Nur bei `live`: Long-Lived Access Token der HA-Instanz |
| `DAHEIM_HA_ENABLE_AREA_REGISTRY` | `true` | Best-Effort-Area-Sync aktivieren/deaktivieren |

## Backend starten

```bash
cd backend
export $(grep -v '^#' .env | xargs)   # oder: set -a; source .env; set +a
uvicorn app.main:app --reload --port 8099
```

Erreichbar:
- `GET http://localhost:8099/api/v1/health`
- `http://localhost:8099/` (einfache Weboberfläche)
- `http://localhost:8099/docs` (Swagger UI)

## Automatisierte Tests ausführen

```bash
cd backend
pytest -v
```

Erwartete Abdeckung (M1/M2):

| Testdatei | Prüft |
|---|---|
| `test_health.py` | Health-Endpoint, Mock-Modus-Kennzeichnung |
| `test_security.py` | Fehlender/ungültiger Token → 401, gültiger Token → 200 |
| `test_installations_api.py` | Installation anlegen/abrufen, Versionierung |
| `test_buildings_api.py` | Building-CRUD, Duplikatserkennung |
| `test_rooms_api.py` | Floor/Room-CRUD, Duplikatserkennung, Manifest-Versionssprung |
| `test_ha_client_mock.py` | Mock-HA-Client: Area anlegen/auflisten/aktualisieren |
| `test_room_sync.py` | `/rooms/{id}/sync` gegen Mock-HA (Erfolgsfall) und simulierter Fehlerfall |
| `test_manifest_export.py` | `/manifest`-Export-Struktur und -Version |

Mit Coverage-Report:

```bash
pytest --cov=app --cov-report=term-missing
```

## Manueller End-to-End-Test (ohne echtes HA)

1. Backend im Mock-Modus starten (siehe oben).
2. `POST /api/v1/installations` → `installation_id` notieren.
3. `POST /api/v1/buildings` mit dieser `installation_id`.
4. `POST /api/v1/buildings/{id}/floors`.
5. `POST /api/v1/rooms` mit der `floor_id`.
6. `POST /api/v1/rooms/{id}/sync` → `sync_status` sollte `synced` werden (Mock-Area wurde angelegt).
7. `GET /api/v1/manifest?installation_id=...` → vollständiger Baum inkl. synchronisiertem Raum.
8. `http://localhost:8099/` öffnen → Gebäude/Räume werden angezeigt.

## Test gegen eine echte Home-Assistant-Instanz (optional, nicht automatisiert)

**Nur mit ausdrücklicher Freigabe und auf einer Test-/Nicht-Produktivinstanz:**

1. `DAHEIM_HA_MODE=live`, `DAHEIM_HA_URL` und `DAHEIM_HA_TOKEN` (Long-Lived Access Token, erstellt
   im HA-Profil) setzen.
2. `GET /api/v1/health` → `home_assistant.reachable` sollte `true` sein (REST-API-Check).
3. `POST /api/v1/rooms/{id}/sync` → prüft Area-Anlage über die Best-Effort-WebSocket-Integration.
   **Wichtig:** Da dies nicht-offizielle WS-Befehle nutzt, kann dieser Schritt je nach HA-
   Core-Version fehlschlagen (`sync_status = "failed"`) — das ist erwartetes, dokumentiertes
   Verhalten, kein Bug.

Dieser Schritt wurde in der aktuellen Entwicklungsumgebung **nicht** durchgeführt, da kein echtes
Home Assistant verfügbar war (siehe `docs/IMPLEMENTATION_PLAN.md` → Bekannte Einschränkungen).

## Home-Assistant-Add-on lokal bauen (optional)

```bash
cd ha_addon/daheim_plus_agent
docker build -t daheim-plus-agent:dev .
```

Ein echter Supervisor-Installationstest (Add-on-Store, lokales Repository) wurde in dieser Umgebung
nicht durchgeführt — siehe Einschränkungen in `docs/IMPLEMENTATION_PLAN.md`.
