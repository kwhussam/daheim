def test_health_mock_mode(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["ha_mode"] == "mock"
    assert data["database"] == "ok"
    assert data["home_assistant"]["reachable"] is True
    assert data["home_assistant"]["mode"] == "mock"
