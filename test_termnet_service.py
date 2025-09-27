#!/usr/bin/env python3
"""Minimal tests for TermNet FastAPI service."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock, patch
import json

# Mock dependencies before import
with patch("redis.asyncio.from_url") as mock_redis, \
     patch("sqlalchemy.create_engine") as mock_engine, \
     patch("faiss.IndexFlatL2") as mock_faiss:

    mock_redis.return_value = AsyncMock()
    mock_engine.return_value = MagicMock()
    mock_faiss.return_value = MagicMock()

    from termnet_service import app

@pytest.fixture
def client():
    """Test client fixture."""
    with TestClient(app) as test_client:
        # Mock app state
        app.state.redis = AsyncMock()
        app.state.retrieval = MagicMock()
        app.state.dispatcher = MagicMock()
        app.state.agent = AsyncMock()

        # Configure mocks
        app.state.redis.get.return_value = None
        app.state.dispatcher.validate_tool_call.return_value = True
        app.state.agent.run.return_value = {
            "reasoning": {"task": "test", "plan": "Execute test"},
            "actions": {"actions": ["test_action"], "status": "completed"},
            "observations": {"observations": "Executed 1 actions", "success": True},
            "grounding": {"grounded": True, "score": 0.95}
        }

        yield test_client

def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/agent.json")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "TermNet"
    assert data["version"] == "1.0.0"
    assert "capabilities" in data
    assert "endpoints" in data

def test_run_endpoint(client):
    """Test /run endpoint."""
    request_data = {
        "task": "test task",
        "context": {"key": "value"},
        "tools": ["tool1"]
    }

    with patch("termnet_service.SessionLocal") as mock_session:
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        response = client.post("/run", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "trace_id" in data
        assert "result" in data
        assert "duration" in data
        assert data["grounding_score"] == 0.95

def test_trace_endpoint(client):
    """Test /trace/{id} endpoint."""
    trace_id = "test-trace-123"

    with patch("termnet_service.SessionLocal") as mock_session:
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock trace query
        mock_trace = MagicMock()
        mock_trace.id = trace_id
        mock_trace.task = "test task"
        mock_trace.started_at.isoformat.return_value = "2024-01-01T00:00:00"
        mock_trace.duration = 1.23
        mock_trace.result = {"test": "result"}
        mock_trace.spans = {"reason": True, "act": True, "observe": True}
        mock_trace.grounding_score = 0.95

        mock_db.query.return_value.filter.return_value.first.return_value = mock_trace

        response = client.get(f"/trace/{trace_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == trace_id
        assert data["task"] == "test task"
        assert data["grounding_score"] == 0.95

def test_trace_not_found(client):
    """Test /trace/{id} with non-existent trace."""
    with patch("termnet_service.SessionLocal") as mock_session:
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = client.get("/trace/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

def test_metrics_endpoint(client):
    """Test /metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    # Metrics should return Prometheus format text
    assert response.headers["content-type"] == "text/plain; charset=utf-8"

def test_run_with_cache_hit(client):
    """Test /run with cached result."""
    cached_result = {
        "reasoning": {"cached": True},
        "actions": {"cached": True},
        "observations": {"cached": True},
        "grounding": {"grounded": True, "score": 0.88}
    }

    # Mock agent run to return cached result
    app.state.agent.run.return_value = cached_result
    app.state.redis.get.return_value = json.dumps(cached_result)

    request_data = {
        "task": "cached task",
        "context": {},
        "tools": []
    }

    with patch("termnet_service.SessionLocal") as mock_session:
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        response = client.post("/run", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["grounding_score"] == 0.88

def test_run_error_handling(client):
    """Test /run error handling."""
    app.state.agent.run.side_effect = Exception("Test error")

    request_data = {
        "task": "error task",
        "context": {},
        "tools": []
    }

    with patch("termnet_service.SessionLocal") as mock_session:
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        response = client.post("/run", json=request_data)

        assert response.status_code == 500
        assert "Test error" in response.json()["detail"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])