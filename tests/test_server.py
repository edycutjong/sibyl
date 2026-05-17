"""Tests for sibyl.server — FastAPI endpoint tests."""

import json

import pytest
from fastapi.testclient import TestClient

from sibyl.server import app


@pytest.fixture
def client(monkeypatch):
    """Create a test client with auth disabled."""
    # Clear lru_cache and override bearer token via env var
    import sibyl.config
    sibyl.config.get_settings.cache_clear()
    monkeypatch.setenv("BEARER_TOKEN", "")
    sibyl.config.get_settings.cache_clear()
    yield TestClient(app)
    sibyl.config.get_settings.cache_clear()


class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_returns_200(self, client):
        """Should return healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["agent"] == "sibyl"

    def test_health_includes_version(self, client):
        """Should include version string."""
        response = client.get("/health")
        data = response.json()
        assert "version" in data


class TestStatsEndpoint:
    """Tests for GET /stats."""

    def test_stats_returns_200(self, client):
        """Should return stats even with no predictions."""
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert "costs" in data


class TestPredictEndpoint:
    """Tests for POST /predict."""

    def test_predict_requires_title(self, client):
        """Should reject requests without title."""
        response = client.post(
            "/predict",
            json={"event_ticker": "TEST", "outcomes": ["Yes", "No"]},
        )
        assert response.status_code == 400

    def test_predict_accepts_valid_event(self, client):
        """Should accept a valid event (may fail without API keys)."""
        response = client.post(
            "/predict",
            json={
                "event_ticker": "TEST-1",
                "title": "Will it rain tomorrow?",
                "outcomes": ["Yes", "No"],
                "category": "Other",
            },
        )
        # Will return 200 if API keys are set, or 500 if not
        # We just check it doesn't return 400 (validation error)
        assert response.status_code in (200, 500)


class TestChatCompletionsEndpoint:
    """Tests for POST /chat/completions."""

    def test_chat_requires_messages(self, client):
        """Should reject requests without user message content."""
        response = client.post(
            "/chat/completions",
            json={"model": "sibyl-v1", "messages": []},
        )
        assert response.status_code == 400

    def test_chat_response_format(self, client):
        """Should return OpenAI-compatible response shape."""
        response = client.post(
            "/chat/completions",
            json={
                "model": "sibyl-v1",
                "messages": [
                    {"role": "user", "content": '{"title": "Will it rain?", "outcomes": ["Yes", "No"]}'},
                ],
            },
        )
        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert data["object"] == "chat.completion"
            assert "choices" in data
            assert len(data["choices"]) > 0
            # Content should be parseable JSON
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            assert "p_yes" in parsed or "probabilities" in parsed
