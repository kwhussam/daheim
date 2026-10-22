def test_missing_token_rejected(client):
    resp = client.post("/api/v1/installations", json={"network_mode": "managed"})
    assert resp.status_code == 401


def test_invalid_token_rejected(client):
    resp = client.post(
        "/api/v1/installations",
        json={"network_mode": "managed"},
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert resp.status_code == 401


def test_valid_token_accepted(client, auth_headers):
    resp = client.post(
        "/api/v1/installations", json={"network_mode": "managed"}, headers=auth_headers
    )
    assert resp.status_code == 201


def test_health_requires_no_token(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
