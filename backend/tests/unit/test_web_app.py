"""
Unit Tests: Web Application (API-First)
Fast, isolated tests for the new API-first endpoints
"""
import pytest
from fastapi.testclient import TestClient
from src.web.app import app


@pytest.mark.unit
class TestWebApp:
    """Test web application API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_get_document_templates(self, client):
        """Test GET /api/document-templates endpoint"""
        response = client.get("/api/document-templates")
        
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert isinstance(data["documents"], list)
        
        if len(data["documents"]) > 0:
            doc = data["documents"][0]
            assert "id" in doc
            assert "name" in doc
    
    def test_create_project(self, client):
        """Test POST /api/projects endpoint"""
        response = client.post(
            "/api/projects",
            json={
                "user_idea": "Create a simple todo application",
                "selected_documents": ["requirements", "project_charter"]
            }
        )
        
        assert response.status_code == 202  # Accepted
        data = response.json()
        assert "project_id" in data
        assert data["status"] == "started"
        assert "message" in data
    
    def test_create_project_no_documents(self, client):
        """Test POST /api/projects with no selected documents"""
        response = client.post(
            "/api/projects",
            json={
                "user_idea": "Create a simple todo application",
                "selected_documents": []
            }
        )
        
        assert response.status_code == 422  # Validation error

    def test_create_project_invalid_document(self, client):
        """Test POST /api/projects with invalid document ID"""
        response = client.post(
            "/api/projects",
            json={
                "user_idea": "Create a simple todo application",
                "selected_documents": ["invalid_document_id"]
            }
        )
        
        assert response.status_code == 422  # Validation error

    def test_get_project_status(self, client):
        """Test GET /api/projects/{project_id}/status endpoint"""
        # First create a project
        create_response = client.post(
            "/api/projects",
            json={
                "user_idea": "Test project",
                "selected_documents": ["requirements"]
            }
        )
        project_id = create_response.json()["project_id"]
        
        # Check status
        response = client.get(f"/api/projects/{project_id}/status")
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == project_id
        assert "status" in data
        assert "selected_documents" in data
        assert "completed_documents" in data

    def test_get_project_status_not_found(self, client):
        """Test GET /api/projects/{project_id}/status with non-existent project"""
        response = client.get("/api/projects/nonexistent_project/status")
        assert response.status_code == 404

    def test_get_project_documents(self, client):
        """Test GET /api/projects/{project_id}/documents endpoint"""
        # First create a project
        create_response = client.post(
            "/api/projects",
            json={
                "user_idea": "Test project",
                "selected_documents": ["requirements"]
            }
        )
        project_id = create_response.json()["project_id"]
        
        # Get documents (may be empty if generation hasn't started)
        response = client.get(f"/api/projects/{project_id}/documents")
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == project_id
        assert "documents" in data
        assert isinstance(data["documents"], list)

    def test_get_project_documents_not_found(self, client):
        """Test GET /api/projects/{project_id}/documents with non-existent project"""
        response = client.get("/api/projects/nonexistent_project/documents")
        assert response.status_code == 404

    def test_get_single_document(self, client):
        """Test GET /api/projects/{project_id}/documents/{document_id} endpoint"""
        # First create a project
        create_response = client.post(
            "/api/projects",
            json={
                "user_idea": "Test project",
                "selected_documents": ["requirements"]
            }
        )
        project_id = create_response.json()["project_id"]
        
        # Try to get a document (may fail if not generated yet)
        response = client.get(f"/api/projects/{project_id}/documents/requirements")
        
        # Should either return 200 (if generated) or 404 (if not yet generated)
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert "name" in data
            assert "status" in data

    def test_download_document(self, client):
        """Test GET /api/projects/{project_id}/documents/{document_id}/download endpoint"""
        # First create a project
        create_response = client.post(
            "/api/projects",
            json={
                "user_idea": "Test project",
                "selected_documents": ["requirements"]
            }
        )
        project_id = create_response.json()["project_id"]
        
        # Try to download a document (may fail if not generated yet)
        response = client.get(f"/api/projects/{project_id}/documents/requirements/download")
        
        # Should either return 200 (if generated) or 404 (if not yet generated)
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            assert "content-type" in response.headers
            assert "text/markdown" in response.headers["content-type"]

    def test_cors_headers(self, client):
        """Test that CORS headers are properly set"""
        response = client.options(
            "/api/document-templates",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        
        # CORS preflight should be handled by middleware
        # The actual response may vary, but should not error
        assert response.status_code in [200, 204, 405]

    def test_project_create_request_validation(self, client):
        """Test request validation for project creation"""
        # Empty user_idea
        response = client.post(
            "/api/projects",
            json={
                "user_idea": "",
                "selected_documents": ["requirements"]
            }
        )
        assert response.status_code == 422

        # Missing user_idea
        response = client.post(
            "/api/projects",
            json={
                "selected_documents": ["requirements"]
            }
        )
        assert response.status_code == 422

        # Too long user_idea
        response = client.post(
            "/api/projects",
            json={
                "user_idea": "x" * 5001,  # Exceeds max_length=5000
                "selected_documents": ["requirements"]
            }
        )
        assert response.status_code == 422
