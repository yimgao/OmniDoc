#!/usr/bin/env python3
"""Test all API endpoints to verify they work correctly."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
import websockets
from websockets.client import WebSocketClientProtocol


BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_result(success: bool, message: str, details: Optional[str] = None) -> None:
    """Print a test result."""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {message}")
    if details:
        print(f"      {details}")


async def test_document_templates(client: httpx.AsyncClient) -> bool:
    """Test GET /api/document-templates"""
    print_section("1. GET /api/document-templates")
    try:
        response = await client.get(f"{BASE_URL}/api/document-templates")
        if response.status_code == 200:
            data = response.json()
            doc_count = len(data.get("documents", []))
            print_result(True, f"Retrieved {doc_count} document templates")
            print(f"      Generated at: {data.get('generated_at', 'N/A')}")
            print(f"      Source: {data.get('source', 'N/A')}")
            
            # Check a few document properties
            if doc_count > 0:
                first_doc = data["documents"][0]
                print(f"      Sample document: {first_doc.get('id')} - {first_doc.get('name')}")
            return True
        else:
            print_result(False, f"Unexpected status code: {response.status_code}")
            print(f"      Response: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Request failed: {e}")
        return False


async def test_create_project(client: httpx.AsyncClient) -> Optional[str]:
    """Test POST /api/projects"""
    print_section("2. POST /api/projects")
    try:
        # First, get available documents
        templates_response = await client.get(f"{BASE_URL}/api/document-templates")
        if templates_response.status_code != 200:
            print_result(False, "Could not fetch templates to select documents")
            return None
        
        templates = templates_response.json().get("documents", [])
        if not templates:
            print_result(False, "No templates available to select")
            return None
        
        # Select first 3 documents (or fewer if not available)
        selected_docs = [doc["id"] for doc in templates[:3]]
        
        payload = {
            "user_idea": "Create a task management application with user authentication, project boards, and real-time collaboration features.",
            "selected_documents": selected_docs,
            "provider_name": "gemini"
        }
        
        response = await client.post(
            f"{BASE_URL}/api/projects",
            json=payload,
            timeout=30.0
        )
        
        if response.status_code == 202:
            data = response.json()
            project_id = data.get("project_id")
            print_result(True, f"Project created: {project_id}")
            print(f"      Status: {data.get('status')}")
            print(f"      Message: {data.get('message')}")
            print(f"      Selected documents: {', '.join(selected_docs)}")
            return project_id
        else:
            print_result(False, f"Unexpected status code: {response.status_code}")
            print(f"      Response: {response.text}")
            return None
    except Exception as e:
        print_result(False, f"Request failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_project_status(client: httpx.AsyncClient, project_id: str) -> bool:
    """Test GET /api/projects/{project_id}/status"""
    print_section("3. GET /api/projects/{project_id}/status")
    try:
        response = await client.get(f"{BASE_URL}/api/projects/{project_id}/status")
        if response.status_code == 200:
            data = response.json()
            print_result(True, f"Retrieved status for project: {project_id}")
            print(f"      Status: {data.get('status')}")
            print(f"      Selected documents: {len(data.get('selected_documents', []))}")
            print(f"      Completed documents: {len(data.get('completed_documents', []))}")
            if data.get('error'):
                print(f"      Error: {data.get('error')}")
            return True
        elif response.status_code == 404:
            print_result(False, f"Project not found: {project_id}")
            return False
        else:
            print_result(False, f"Unexpected status code: {response.status_code}")
            print(f"      Response: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Request failed: {e}")
        return False


async def test_project_documents(client: httpx.AsyncClient, project_id: str) -> bool:
    """Test GET /api/projects/{project_id}/documents"""
    print_section("4. GET /api/projects/{project_id}/documents")
    try:
        response = await client.get(f"{BASE_URL}/api/projects/{project_id}/documents")
        if response.status_code == 200:
            data = response.json()
            documents = data.get("documents", [])
            print_result(True, f"Retrieved {len(documents)} documents")
            for doc in documents[:3]:  # Show first 3
                print(f"      - {doc.get('id')}: {doc.get('name')} ({doc.get('status')})")
            if len(documents) > 3:
                print(f"      ... and {len(documents) - 3} more")
            return True
        elif response.status_code == 404:
            print_result(False, f"Project not found: {project_id}")
            return False
        else:
            print_result(False, f"Unexpected status code: {response.status_code}")
            print(f"      Response: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Request failed: {e}")
        return False


async def test_single_document(client: httpx.AsyncClient, project_id: str) -> Optional[str]:
    """Test GET /api/projects/{project_id}/documents/{document_id}"""
    print_section("5. GET /api/projects/{project_id}/documents/{document_id}")
    try:
        # First get the list of documents
        docs_response = await client.get(f"{BASE_URL}/api/projects/{project_id}/documents")
        if docs_response.status_code != 200:
            print_result(False, "Could not fetch documents list")
            return None
        
        documents = docs_response.json().get("documents", [])
        if not documents:
            print_result(False, "No documents available to test")
            return None
        
        document_id = documents[0].get("id")
        response = await client.get(
            f"{BASE_URL}/api/projects/{project_id}/documents/{document_id}"
        )
        
        if response.status_code == 200:
            data = response.json()
            content_length = len(data.get("content", ""))
            print_result(True, f"Retrieved document: {document_id}")
            print(f"      Name: {data.get('name')}")
            print(f"      Status: {data.get('status')}")
            print(f"      Content length: {content_length} characters")
            if data.get("file_path"):
                print(f"      File path: {data.get('file_path')}")
            return document_id
        elif response.status_code == 404:
            print_result(False, f"Document not found: {document_id}")
            return None
        else:
            print_result(False, f"Unexpected status code: {response.status_code}")
            print(f"      Response: {response.text}")
            return None
    except Exception as e:
        print_result(False, f"Request failed: {e}")
        return None


async def test_download_document(client: httpx.AsyncClient, project_id: str, document_id: str) -> bool:
    """Test GET /api/projects/{project_id}/documents/{document_id}/download"""
    print_section("6. GET /api/projects/{project_id}/documents/{document_id}/download")
    try:
        response = await client.get(
            f"{BASE_URL}/api/projects/{project_id}/documents/{document_id}/download",
            follow_redirects=True
        )
        
        if response.status_code == 200:
            content_length = len(response.content)
            content_type = response.headers.get("content-type", "unknown")
            print_result(True, f"Downloaded document: {document_id}")
            print(f"      Content type: {content_type}")
            print(f"      Content length: {content_length} bytes")
            return True
        elif response.status_code == 404:
            print_result(False, f"Document not found or not generated yet: {document_id}")
            print("      (This is normal if generation is still in progress)")
            return False
        else:
            print_result(False, f"Unexpected status code: {response.status_code}")
            print(f"      Response: {response.text[:200]}")
            return False
    except Exception as e:
        print_result(False, f"Request failed: {e}")
        return False


async def test_websocket(project_id: str) -> bool:
    """Test WebSocket /ws/{project_id}"""
    print_section("7. WebSocket /ws/{project_id}")
    try:
        uri = f"{WS_URL}/ws/{project_id}"
        async with websockets.connect(uri) as websocket:
            # Wait for connection message
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                if data.get("type") == "connected":
                    print_result(True, f"WebSocket connected to project: {project_id}")
                    print(f"      Message: {data.get('message')}")
                    
                    # Wait a bit for any progress updates
                    try:
                        progress = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        progress_data = json.loads(progress)
                        print(f"      Progress update: {progress_data.get('type')}")
                    except asyncio.TimeoutError:
                        print("      (No progress updates received within 2 seconds)")
                    
                    return True
                else:
                    print_result(False, f"Unexpected message type: {data.get('type')}")
                    return False
            except asyncio.TimeoutError:
                print_result(False, "No connection message received")
                return False
    except Exception as e:
        print_result(False, f"WebSocket connection failed: {e}")
        return False


async def main() -> None:
    """Run all endpoint tests."""
    print("\n" + "="*60)
    print("  OmniDoc API Endpoint Tests")
    print("="*60)
    print(f"\nTesting API at: {BASE_URL}")
    print("Make sure the backend is running before starting tests!")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    try:
        input()
    except KeyboardInterrupt:
        print("\n❌ Tests cancelled")
        sys.exit(1)
    
    results: Dict[str, bool] = {}
    project_id: Optional[str] = None
    document_id: Optional[str] = None
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test 1: Document templates
        results["templates"] = await test_document_templates(client)
        
        # Test 2: Create project
        project_id = await test_create_project(client)
        results["create_project"] = project_id is not None
        
        if not project_id:
            print("\n⚠️  Cannot continue tests without a project_id")
            print_summary(results)
            sys.exit(1)
        
        # Wait a moment for project to be created
        await asyncio.sleep(1)
        
        # Test 3: Project status
        results["status"] = await test_project_status(client, project_id)
        
        # Test 4: Project documents
        results["documents"] = await test_project_documents(client, project_id)
        
        # Test 5: Single document
        document_id = await test_single_document(client, project_id)
        results["single_document"] = document_id is not None
        
        # Test 6: Download document
        if document_id:
            results["download"] = await test_download_document(client, project_id, document_id)
        else:
            print_section("6. GET /api/projects/{project_id}/documents/{document_id}/download")
            print_result(False, "Skipped - no document available")
            results["download"] = False
        
        # Test 7: WebSocket
        results["websocket"] = await test_websocket(project_id)
    
    # Print summary
    print_summary(results)


def print_summary(results: Dict[str, bool]) -> None:
    """Print test summary."""
    print_section("Test Summary")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"  {status} {test_name.replace('_', ' ').title()}")
    
    print(f"\nTotal: {total} | Passed: {passed} | Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Check the output above for details.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

