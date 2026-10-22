# Daheim+

Daheim+ ist ein Smart-Home-Produkt auf Basis von **Raspberry Pi** und **Home Assistant OS**.
Kunden erhalten einen vorkonfigurierten Raspberry Pi (optional mit vorbereiteten Shelly-Sensoren),
scannen einen QR-Code und richten ihr Zuhause über einen webbasierten Setup-Wizard ein. Danach läuft
ein konfiguriertes Home Assistant mit Räumen, Entitäten, Automationen und einem generierten Dashboard.

Diese Repository enthält den **Daheim+ Agent** — eine dauerhaft laufende Komponente, die als
Home-Assistant-Add-on installiert wird, ein lokales Installation Manifest pflegt und Home Assistant
über dokumentierte Schnittstellen konfiguriert.

> **Status:** M1 (installierbarer Agent, FastAPI-Backend, HA-Client, einfache Weboberfläche) und
> M2 (SQLite, Installation Manifest, Gebäude- & Raumverwaltung) sind implementiert und getestet.
> Siehe [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md) für den vollständigen Fahrplan
> und offene Einschränkungen.

## Projektstruktur

```
Daheim/
├── backend/            # FastAPI-Backend ("Daheim+ Agent"), SQLite, HA-Client, Tests
│   ├── app/
│   │   ├── api/        # FastAPI-Routen + Auth
│   │   ├── db/         # SQLAlchemy Engine, Session, ORM-Modelle
│   │   ├── schemas/    # Pydantic-Schemas (API + Manifest)
│   │   ├── manifest/   # Installation-Manifest-Service (Business-Logik)
│   │   └── ha_client/  # Home Assistant REST/WebSocket-Client + Mock
│   └── tests/          # pytest-Suite
├── frontend/wizard/    # Minimale, erreichbare Weboberfläche (volle React-UI folgt in M3)
├── ha_addon/           # Home Assistant Supervisor Add-on Packaging
├── docs/               # Architektur, Implementierungsplan, API- und Testdokumentation
└── scripts/            # Entwicklungs-Helferskripte
```

## Schnellstart (Entwicklung, ohne echtes Home Assistant)

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Agent im Mock-HA-Modus starten (kein echtes Home Assistant nötig)
export DAHEIM_HA_MODE=mock
export DAHEIM_API_TOKEN=dev-local-token   # lokaler API-Token, NICHT committen
uvicorn app.main:app --reload --port 8099
```

Danach erreichbar:

- Health-Check: `GET http://localhost:8099/api/v1/health`
- Einfache Weboberfläche: `http://localhost:8099/`
- API-Dokumentation (OpenAPI/Swagger): `http://localhost:8099/docs`

Details zu Konfiguration, Betriebsmodi und Tests: [`docs/TESTING.md`](docs/TESTING.md).

## Tests ausführen

```bash
cd backend
pytest -v
```

## Wichtige Dokumente

| Dokument | Inhalt |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | Arbeitsregeln und Kontext für KI-gestützte Weiterentwicklung |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Architektur, Komponenten, Netzwerkmodi, Sicherheitsmodell |
| [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md) | Meilensteine M1–M7, Status, bekannte Einschränkungen |
| [`docs/API.md`](docs/API.md) | REST-API-Referenz des Daheim+ Agent |
| [`docs/TESTING.md`](docs/TESTING.md) | Installations-, Test- und Entwicklungsanleitung |

## Lizenz / Status

Internes Entwicklungsprojekt. Noch nicht für den Produktivbetrieb mit echten Kundendaten freigegeben.
