// Einfache, erreichbare Weboberfläche für M1/M2 (kein React-Wizard -- siehe docs/IMPLEMENTATION_PLAN.md M3).
// Verwendet ausschließlich die dokumentierten Daheim+-API-Endpunkte aus docs/API.md.

const API_BASE = "/api/v1";

function getToken() {
  return sessionStorage.getItem("daheim_api_token") || "";
}

function authHeaders() {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function loadHealth() {
  const el = document.getElementById("health-status");
  try {
    const resp = await fetch(`${API_BASE}/health`);
    const data = await resp.json();
    const badgeClass = data.home_assistant.reachable ? "ok" : "warn";
    el.innerHTML = `
      <span class="badge ${badgeClass}">HA: ${data.home_assistant.mode} - ${
      data.home_assistant.reachable ? "erreichbar" : "nicht erreichbar"
    }</span>
      <span class="badge ok">DB: ${data.database}</span>
      <span class="muted">Agent-Version ${data.version}</span>
    `;
  } catch (err) {
    el.innerHTML = `<span class="badge err">Backend nicht erreichbar</span>`;
  }
}

function initTokenControls() {
  const input = document.getElementById("token-input");
  const state = document.getElementById("token-state");
  input.value = getToken();
  state.textContent = getToken() ? "Token gesetzt" : "kein Token gesetzt";

  document.getElementById("token-save").addEventListener("click", () => {
    sessionStorage.setItem("daheim_api_token", input.value.trim());
    state.textContent = input.value.trim() ? "Token gesetzt" : "kein Token gesetzt";
  });
}

function renderManifest(manifest) {
  const container = document.getElementById("manifest-result");
  if (!manifest) {
    container.innerHTML = "";
    return;
  }
  const inst = manifest.installation;
  let html = `<p class="muted">Installation ${inst.id} - Version ${inst.manifest_version} - Modus ${inst.network_mode}</p>`;
  html += '<ul class="tree">';
  for (const building of manifest.buildings) {
    html += `<li class="building">${building.name}</li>`;
    for (const floor of building.floors) {
      html += `<li class="floor">${floor.name}</li>`;
      for (const room of floor.rooms) {
        html += `<li class="room">${room.name} (${room.room_type}, sync: ${room.sync_status})</li>`;
      }
    }
  }
  html += "</ul>";
  container.innerHTML = html;
}

async function loadManifest() {
  const installationId = document.getElementById("installation-id-input").value.trim();
  const container = document.getElementById("manifest-result");
  if (!installationId) {
    container.innerHTML = '<span class="badge warn">Bitte Installation-ID eingeben</span>';
    return;
  }
  try {
    const resp = await fetch(`${API_BASE}/manifest?installation_id=${encodeURIComponent(installationId)}`, {
      headers: authHeaders(),
    });
    if (!resp.ok) {
      const body = await resp.json().catch(() => ({}));
      container.innerHTML = `<span class="badge err">Fehler ${resp.status}: ${body.detail || resp.statusText}</span>`;
      return;
    }
    renderManifest(await resp.json());
  } catch (err) {
    container.innerHTML = `<span class="badge err">Anfrage fehlgeschlagen: ${err}</span>`;
  }
}

async function createInstallation() {
  const container = document.getElementById("manifest-result");
  try {
    const resp = await fetch(`${API_BASE}/installations`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ network_mode: "managed" }),
    });
    if (!resp.ok) {
      const body = await resp.json().catch(() => ({}));
      container.innerHTML = `<span class="badge err">Fehler ${resp.status}: ${body.detail || resp.statusText}</span>`;
      return;
    }
    const installation = await resp.json();
    document.getElementById("installation-id-input").value = installation.id;
    container.innerHTML = `<span class="badge ok">Installation angelegt: ${installation.id}</span>`;
  } catch (err) {
    container.innerHTML = `<span class="badge err">Anfrage fehlgeschlagen: ${err}</span>`;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  loadHealth();
  initTokenControls();
  document.getElementById("load-manifest").addEventListener("click", loadManifest);
  document.getElementById("create-installation").addEventListener("click", createInstallation);
});
