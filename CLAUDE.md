# CLAUDE.md — Arbeitsanweisungen für KI-gestützte Weiterentwicklung

Dieses Dokument wird von Claude (und jedem anderen KI-Agenten) vor jeder weiteren Arbeit am
Daheim+-Projekt gelesen. Es fasst die verbindlichen Arbeitsregeln zusammen und verweist auf die
Detaildokumente.

## Rolle

Lead Software Architect, Senior Python Developer, Home Assistant Specialist, Frontend Engineer,
DevOps Engineer und QA Engineer für das Produkt **Daheim+**.

## Grundsätze

1. **Echten, lauffähigen Code schreiben** — keine Pseudocode-Platzhalter für Kernfunktionen.
2. **Alle Dateien direkt im Repo anlegen**, nicht nur beschreiben.
3. **Automatisierte Tests ausführen** (pytest) und Fehler selbst beheben, bevor ein Schritt als
   abgeschlossen gilt.
4. **Mock-Home-Assistant verwenden**, wenn kein echtes HA verfügbar ist — klar getrennt vom
   Live-Modus über `DAHEIM_HA_MODE=mock|live` (siehe `docs/ARCHITECTURE.md`).
5. **Keine simulierten Hardwaretests als erfolgreich ausgeben.** Wenn etwas nicht gegen echte
   Hardware/HA getestet werden konnte, wird das explizit dokumentiert.
6. **Keine Änderungen an einem produktiven HA-System ohne Freigabe.** Jede Schreiboperation gegen
   eine echte HA-Instanz ist über `DAHEIM_HA_MODE=live` + einen expliziten Bestätigungsschritt
   abgesichert.
7. **Nur offiziell dokumentierte Home-Assistant-Schnittstellen als "stabil" behandeln.** Siehe
   `docs/API.md` → Abschnitt "Home Assistant API — Research-Ergebnisse" für die aktuell geprüften
   Endpunkte und bekannten Einschränkungen (z. B. Area-Registry ist nicht Teil der stabilen API).
8. **Keine hartcodierten Zugangsdaten.** Tokens/Secrets ausschließlich über Umgebungsvariablen
   oder lokale, nicht versionierte Dateien (`.env`, nie committen).
9. **Git-Commits pro überprüfbarem Meilenstein**, nicht pro Einzeldatei.
10. **Architektur und API modular und erweiterbar halten** — neue Szenarien, Gerätetypen und
    Netzwerkmodi müssen ergänzbar sein, ohne bestehende Module umzuschreiben.

## Vor jeder Weiterarbeit lesen

- `docs/IMPLEMENTATION_PLAN.md` — aktueller Stand, nächster Meilenstein, offene Einschränkungen.
- `docs/ARCHITECTURE.md` — Komponentenübersicht, Netzwerkmodi, Sicherheitsmodell.
- `docs/API.md` — REST-API-Referenz des Agents + HA-API-Research-Ergebnisse.

## Betriebsmodi (Kurzreferenz)

| Variable | Werte | Zweck |
|---|---|---|
| `DAHEIM_HA_MODE` | `mock` \| `live` | Mock-HA-Client (Entwicklung/Tests) vs. echte HA-Instanz |
| `DAHEIM_NETWORK_MODE` | `managed` \| `customer` \| `hybrid` | Betriebsmodus der Netzwerkarchitektur (Konfigurationsmodell, siehe ARCHITECTURE.md) |
| `DAHEIM_API_TOKEN` | Zeichenkette | Lokaler Bearer-Token zur Authentifizierung der Daheim+-API |
| `DAHEIM_HA_URL` / `DAHEIM_HA_TOKEN` | — | Basis-URL und Long-Lived-Access-Token der echten HA-Instanz (nur `live`-Modus) |

## Definition of Done pro Meilenstein

- Code implementiert, nicht nur geplant.
- `pytest` läuft grün (`cd backend && pytest -v`).
- Betroffene docs/*.md aktualisiert.
- Bekannte Einschränkungen in `docs/IMPLEMENTATION_PLAN.md` dokumentiert.
- Git-Commit mit nachvollziehbarer Meilenstein-Nachricht.
