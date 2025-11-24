"""
Tests for health check endpoints
"""
import pytest
from fastapi.testclient import TestClient

from src.web.app import app

client = TestClient(app)


def test_health_endpoint():
    """Test basic health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "2.0.0"
    assert data["service"] == "omnidoc-api"


@pytest.mark.skip(reason="Requires database connection")
def test_readiness_endpoint():
    """Test readiness check endpoint"""
    response = client.get("/ready")
    # Should return 200 if ready, 503 if not ready
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "redis" in data

