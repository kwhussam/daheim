#!/usr/bin/with-contenv bashio
# Startet den Daheim+ Agent innerhalb des Home-Assistant-Supervisor-Add-on-Containers.
# HINWEIS: Dieses Skript wurde NICHT gegen eine echte Supervisor-Umgebung getestet
# (siehe docs/IMPLEMENTATION_PLAN.md, Bekannte Einschraenkungen). Es folgt dem offiziellen
# Add-on-Schema (bashio::config liest die in config.yaml definierten `options`).
set -e

export DAHEIM_HA_MODE="$(bashio::config 'ha_mode')"
export DAHEIM_API_TOKEN="$(bashio::config 'api_token')"
export DAHEIM_HA_ENABLE_AREA_REGISTRY="$(bashio::config 'ha_enable_area_registry')"
export DAHEIM_DB_PATH="/data/daheim.db"

if [ -z "${DAHEIM_API_TOKEN}" ]; then
  bashio::log.warning "Kein api_token in den Add-on-Optionen gesetzt -- die Daheim+-API bleibt bis zur Konfiguration gesperrt (503)."
fi

cd /app
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8099
