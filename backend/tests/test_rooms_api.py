def _setup_floor(client, auth_headers):
    inst = client.post(
        "/api/v1/installations", json={"network_mode": "managed"}, headers=auth_headers
    ).json()
    building = client.post(
        "/api/v1/buildings", json={"installation_id": inst["id"], "name": "Haus"}, headers=auth_headers
    ).json()
    floor = client.post(
        f"/api/v1/buildings/{building['id']}/floors",
        json={"name": "EG", "level": 0},
        headers=auth_headers,
    ).json()
    return inst["id"], building["id"], floor["id"]


def test_create_room_and_duplicate_rejected(client, auth_headers):
    _, _, floor_id = _setup_floor(client, auth_headers)
    payload = {"floor_id": floor_id, "name": "Wohnzimmer", "room_type": "living_room"}
    resp = client.post("/api/v1/rooms", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    room = resp.json()
    assert room["sync_status"] == "pending"
    assert room["ha_area_id"] is None

    dup = client.post("/api/v1/rooms", json=payload, headers=auth_headers)
    assert dup.status_code == 409


def test_room_sync_against_mock_ha(client, auth_headers):
    _, _, floor_id = _setup_floor(client, auth_headers)
    room = client.post(
        "/api/v1/rooms",
        json={"floor_id": floor_id, "name": "Küche", "room_type": "kitchen"},
        headers=auth_headers,
    ).json()

    resp = client.post(f"/api/v1/rooms/{room['id']}/sync", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["sync_status"] == "synced"
    assert data["ha_area_id"]

    resp2 = client.post(f"/api/v1/rooms/{room['id']}/sync", headers=auth_headers)
    assert resp2.json()["ha_area_id"] == data["ha_area_id"]


def test_room_update_and_delete(client, auth_headers):
    _, _, floor_id = _setup_floor(client, auth_headers)
    room = client.post(
        "/api/v1/rooms",
        json={"floor_id": floor_id, "name": "Büro", "room_type": "office"},
        headers=auth_headers,
    ).json()

    patched = client.patch(
        f"/api/v1/rooms/{room['id']}", json={"name": "Arbeitszimmer"}, headers=auth_headers
    )
    assert patched.status_code == 200
    assert patched.json()["name"] == "Arbeitszimmer"

    deleted = client.delete(f"/api/v1/rooms/{room['id']}", headers=auth_headers)
    assert deleted.status_code == 204


def test_manifest_export_contains_room(client, auth_headers):
    installation_id, building_id, floor_id = _setup_floor(client, auth_headers)
    client.post(
        "/api/v1/rooms",
        json={"floor_id": floor_id, "name": "Flur", "room_type": "hallway"},
        headers=auth_headers,
    )
    resp = client.get(f"/api/v1/manifest?installation_id={installation_id}", headers=auth_headers)
    assert resp.status_code == 200
    manifest_data = resp.json()
    assert manifest_data["installation"]["id"] == installation_id
    rooms = manifest_data["buildings"][0]["floors"][0]["rooms"]
    assert any(r["name"] == "Flur" for r in rooms)
