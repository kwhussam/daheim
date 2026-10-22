def _create_installation(client, auth_headers):
    resp = client.post(
        "/api/v1/installations", json={"network_mode": "managed"}, headers=auth_headers
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def test_create_and_list_building(client, auth_headers):
    installation_id = _create_installation(client, auth_headers)
    resp = client.post(
        "/api/v1/buildings",
        json={"installation_id": installation_id, "name": "Hauptgebäude"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "Hauptgebäude"

    resp = client.get(f"/api/v1/buildings?installation_id={installation_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_duplicate_building_name_rejected(client, auth_headers):
    installation_id = _create_installation(client, auth_headers)
    payload = {"installation_id": installation_id, "name": "Hauptgebäude"}
    first = client.post("/api/v1/buildings", json=payload, headers=auth_headers)
    assert first.status_code == 201
    second = client.post("/api/v1/buildings", json=payload, headers=auth_headers)
    assert second.status_code == 409


def test_building_for_unknown_installation_returns_404(client, auth_headers):
    resp = client.post(
        "/api/v1/buildings",
        json={"installation_id": "does-not-exist", "name": "X"},
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_manifest_version_increments_on_building_create(client, auth_headers):
    installation_id = _create_installation(client, auth_headers)
    before = client.get(f"/api/v1/installations/{installation_id}", headers=auth_headers).json()
    client.post(
        "/api/v1/buildings",
        json={"installation_id": installation_id, "name": "Gebäude A"},
        headers=auth_headers,
    )
    after = client.get(f"/api/v1/installations/{installation_id}", headers=auth_headers).json()
    assert after["manifest_version"] > before["manifest_version"]


def test_update_and_delete_building(client, auth_headers):
    installation_id = _create_installation(client, auth_headers)
    building = client.post(
        "/api/v1/buildings",
        json={"installation_id": installation_id, "name": "Altname"},
        headers=auth_headers,
    ).json()

    patched = client.patch(
        f"/api/v1/buildings/{building['id']}", json={"name": "Neuname"}, headers=auth_headers
    )
    assert patched.status_code == 200
    assert patched.json()["name"] == "Neuname"

    deleted = client.delete(f"/api/v1/buildings/{building['id']}", headers=auth_headers)
    assert deleted.status_code == 204

    listing = client.get(
        f"/api/v1/buildings?installation_id={installation_id}", headers=auth_headers
    ).json()
    assert listing == []
