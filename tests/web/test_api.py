def test_status_shape(client):
    tc, _, _ = client
    resp = tc.get("/api/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "ollama_ok" in data
    assert "model" in data
    assert "projects_count" in data
    assert "last_latency_ms" in data


def test_list_projects_empty(client):
    tc, mock_store, _ = client
    mock_store.list_all.return_value = []
    resp = tc.get("/api/projects")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_project(client):
    tc, mock_store, _ = client
    from jarvis.memory.store import Project
    created = Project(name="TestProj", goal="Test goal", status="idea")
    mock_store.create.return_value = created
    resp = tc.post("/api/projects", json={"name": "TestProj", "goal": "Test goal"})
    assert resp.status_code == 201
    assert resp.json()["name"] == "TestProj"


def test_create_project_duplicate(client):
    tc, mock_store, _ = client
    import sqlite3
    mock_store.create.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed")
    resp = tc.post("/api/projects", json={"name": "Dup"})
    assert resp.status_code == 409


def test_update_project(client):
    tc, mock_store, _ = client
    from jarvis.memory.store import Project
    updated = Project(name="X", goal="new goal")
    mock_store.update.return_value = updated
    resp = tc.patch("/api/projects/X", json={"goal": "new goal"})
    assert resp.status_code == 200
    assert resp.json()["goal"] == "new goal"


def test_update_project_not_found(client):
    tc, mock_store, _ = client
    mock_store.update.return_value = None
    resp = tc.patch("/api/projects/Missing", json={"goal": "x"})
    assert resp.status_code == 404


def test_delete_project(client):
    tc, mock_store, _ = client
    mock_store.delete.return_value = True
    resp = tc.delete("/api/projects/X")
    assert resp.status_code == 204


def test_delete_project_not_found(client):
    tc, mock_store, _ = client
    mock_store.delete.return_value = False
    resp = tc.delete("/api/projects/Missing")
    assert resp.status_code == 404


def test_chat_streams_tokens(client):
    tc, _, mock_brain = client
    mock_brain.chat.return_value = iter(["Olá", " mundo", "!"])
    resp = tc.post("/api/chat", json={"message": "oi"})
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]


def test_reset_history(client):
    tc, _, mock_brain = client
    resp = tc.delete("/api/chat/history")
    assert resp.status_code == 204
    mock_brain.reset.assert_called_once()
