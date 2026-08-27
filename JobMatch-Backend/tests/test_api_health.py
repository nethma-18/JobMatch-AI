def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "running"
    assert "JobMatch" in json_data["app"]

def test_health_endpoints(client):
    # Test /health
    res1 = client.get("/health")
    assert res1.status_code == 200
    assert res1.json()["status"] == "ok"
    assert res1.json()["database"] == "connected"

    # Test /health/database
    res2 = client.get("/health/database")
    assert res2.status_code == 200
    assert res2.json()["status"] == "ok"
    assert res2.json()["database"] == "connected"
