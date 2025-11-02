"""
Unit Tests: Web Application
Fast, isolated tests for web interface
"""
import pytest
from fastapi.testclient import TestClient
from src.web.app import app


@pytest.mark.unit
class TestWebApp:
    """Test web application"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns HTML"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "DOCU-GEN" in response.text
    
    def test_generate_endpoint(self, client):
        """Test generation endpoint"""
        response = client.post(
            "/api/generate",
            json={"user_idea": "Test project"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "project_id" in data
        assert data["status"] == "started"
    
    def test_status_endpoint(self, client):
        """Test status endpoint"""
        # First create a project
        generate_response = client.post(
            "/api/generate",
            json={"user_idea": "Test project"}
        )
        project_id = generate_response.json()["project_id"]
        
        # Check status
        response = client.get(f"/api/status/{project_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == project_id
        assert "status" in data

