def test_status_shape(client):
    tc, _, _ = client
    resp = tc.get("/api/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "ollama_ok" in data
    assert "model" in data
    assert "projects_count" in data
    assert "last_latency_ms" in data
