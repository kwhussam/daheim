# Daheim+ Agent -- Home Assistant Add-on

Dieses Verzeichnis folgt dem offiziellen Home-Assistant-Add-on-Schema
(`config.yaml`, `Dockerfile`, `run.sh` mit `bashio`).

**Lokal bauen (ungetestet gegen echten Supervisor, siehe docs/IMPLEMENTATION_PLAN.md):**

```bash
docker build -t daheim-plus-agent:dev --build-arg BUILD_FROM=ghcr.io/home-assistant/amd64-base:3.19 .
```

**Als lokales Add-on-Repository einbinden:** dieses Repository (bzw. einen Ordner, der
`ha_addon/daheim_plus_agent/` enthält) im Home-Assistant-Supervisor unter
*Einstellungen -> Add-ons -> Add-on-Store -> Repositories* hinzufügen.
