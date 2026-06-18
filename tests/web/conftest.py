import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

_FAKE_CFG = {
    "brain": {"laptop_ip": "127.0.0.1", "ollama_port": 11434, "model": "qwen3:4b"},
    "web": {"port": 7777},
}


@pytest.fixture
def client():
    mock_store = MagicMock()
    mock_store.list_all.return_value = []
    mock_store.get_by_name.return_value = None

    mock_brain = MagicMock()
    mock_brain.last_latency_ms = 0
    mock_brain.reset = MagicMock()

    from jarvis.web.api import app, get_store, get_brain

    app.dependency_overrides[get_store] = lambda: mock_store
    app.dependency_overrides[get_brain] = lambda: mock_brain

    with patch("jarvis.web.api._load_config", return_value=_FAKE_CFG):
        yield TestClient(app), mock_store, mock_brain

    app.dependency_overrides.clear()
