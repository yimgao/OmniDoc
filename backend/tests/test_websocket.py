"""
Tests for WebSocket functionality
"""
import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket

from src.web.app import app

client = TestClient(app)


@pytest.mark.asyncio
async def test_websocket_connection_invalid_project_id():
    """Test WebSocket connection with invalid project ID format"""
    with client.websocket_connect("/ws/invalid_id") as websocket:
        # Should close immediately with error code 1008
        with pytest.raises(Exception):
            websocket.receive_json()


@pytest.mark.skip(reason="Requires running server and valid project")
async def test_websocket_connection_valid():
    """Test WebSocket connection with valid project ID"""
    # This test requires a valid project_id
    project_id = "project_20240101_120000_abc123"
    with client.websocket_connect(f"/ws/{project_id}") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "connected"
        assert data["project_id"] == project_id

