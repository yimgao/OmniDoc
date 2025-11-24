"""
Integration tests for API endpoints
"""
import pytest
from fastapi.testclient import TestClient

from src.web.app import app

client = TestClient(app)


def test_health_check():
    """Test that the API is accessible"""
    # This is a basic test - in a real scenario, you'd add a /health endpoint
    response = client.get("/docs")
    assert response.status_code in [200, 404]  # Docs endpoint may or may not exist


def test_get_document_templates():
    """Test fetching document templates"""
    response = client.get("/api/document-templates")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert isinstance(data["documents"], list)


def test_create_project_validation():
    """Test project creation with invalid input"""
    # Test empty user_idea
    response = client.post("/api/projects", json={
        "user_idea": "",
        "selected_documents": ["readme"]
    })
    assert response.status_code == 422
    
    # Test missing selected_documents
    response = client.post("/api/projects", json={
        "user_idea": "Test project",
        "selected_documents": []
    })
    assert response.status_code == 422


def test_create_project_success():
    """Test successful project creation"""
    response = client.post("/api/projects", json={
        "user_idea": "A test project for API testing",
        "selected_documents": ["readme"]
    })
    # Should return 202 Accepted
    assert response.status_code == 202
    data = response.json()
    assert "project_id" in data
    assert "status" in data
    assert data["status"] == "started"


def test_get_project_status_not_found():
    """Test getting status for non-existent project"""
    response = client.get("/api/projects/project_nonexistent_12345/status")
    assert response.status_code == 404


def test_get_project_status_invalid_format():
    """Test getting status with invalid project ID format"""
    response = client.get("/api/projects/invalid_id/status")
    assert response.status_code == 400


@pytest.mark.skip(reason="Requires running Celery worker and database")
def test_project_lifecycle():
    """Test complete project lifecycle (requires running services)"""
    # Create project
    create_response = client.post("/api/projects", json={
        "user_idea": "A comprehensive test project",
        "selected_documents": ["readme", "api_documentation"]
    })
    assert create_response.status_code == 202
    project_id = create_response.json()["project_id"]
    
    # Get status
    status_response = client.get(f"/api/projects/{project_id}/status")
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["project_id"] == project_id
    
    # Get documents (may be empty if generation not complete)
    docs_response = client.get(f"/api/projects/{project_id}/documents")
    assert docs_response.status_code == 200
    docs_data = docs_response.json()
    assert docs_data["project_id"] == project_id
    assert isinstance(docs_data["documents"], list)

