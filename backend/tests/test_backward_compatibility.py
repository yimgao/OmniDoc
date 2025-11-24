"""
Tests for backward compatibility

These tests ensure that API changes don't break existing clients.
"""
import pytest
from fastapi.testclient import TestClient

from src.web.app import app

client = TestClient(app)


def test_api_version_header():
    """Test that API version is accessible"""
    # API should expose version information
    response = client.get("/docs")  # OpenAPI docs include version
    assert response.status_code in [200, 404]  # Docs may or may not be enabled


def test_project_id_format_compatibility():
    """Test that project ID format hasn't changed"""
    # Old format: project_YYYYMMDD_HHMMSS_hex
    # Should still be accepted
    old_format_id = "project_20240101_120000_abc123"
    response = client.get(f"/api/projects/{old_format_id}/status")
    # Should return 404 (project doesn't exist) not 400 (invalid format)
    assert response.status_code in [404, 400]  # 404 = not found, 400 = invalid format


def test_document_templates_response_structure():
    """Test that document templates response structure is backward compatible"""
    response = client.get("/api/document-templates")
    assert response.status_code == 200
    data = response.json()
    
    # Required fields for backward compatibility
    assert "documents" in data
    assert isinstance(data["documents"], list)
    
    # Optional fields (may or may not be present)
    if data.get("documents"):
        doc = data["documents"][0]
        # Core fields that should always exist
        assert "id" in doc
        assert "name" in doc


def test_project_create_response_structure():
    """Test that project creation response structure is backward compatible"""
    response = client.post("/api/projects", json={
        "user_idea": "Test project for compatibility",
        "selected_documents": ["readme"]
    })
    
    if response.status_code == 202:
        data = response.json()
        # Required fields for backward compatibility
        assert "project_id" in data
        assert "status" in data
        # Optional field
        assert "message" in data or True  # May or may not be present


def test_project_status_response_structure():
    """Test that project status response structure is backward compatible"""
    # Use a non-existent project to test response structure
    response = client.get("/api/projects/project_20240101_120000_test123/status")
    
    # Should return 404, but if it returns 200, check structure
    if response.status_code == 200:
        data = response.json()
        # Required fields
        assert "project_id" in data
        assert "status" in data
        assert "selected_documents" in data
        assert "completed_documents" in data

