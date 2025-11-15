"""Project-related API endpoints"""
from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set

from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from slowapi import Limiter

from src.config.document_catalog import get_document_by_id
from src.context.context_manager import ContextManager
from src.utils.logger import get_logger
from src.tasks.generation_tasks import generate_documents_task
from src.tasks.celery_app import REDIS_AVAILABLE
from src.web.utils import parse_json_field

logger = get_logger(__name__)

router = APIRouter(prefix="/api/projects", tags=["projects"])

# Rate limiter (will be set by main app)
limiter: Optional[Limiter] = None

# Dependency injection for context manager (will be set by main app)
context_manager: Optional[ContextManager] = None


def set_context_manager(cm: ContextManager) -> None:
    """Set the context manager for this router"""
    global context_manager
    context_manager = cm


def set_limiter(lim: Limiter) -> None:
    """Set the rate limiter for this router"""
    global limiter
    limiter = lim


class ProjectCreateRequest(BaseModel):
    user_idea: str = Field(..., min_length=1, max_length=5000)
    selected_documents: List[str] = Field(default_factory=list)
    provider_name: Optional[str] = Field(default=None, max_length=100)
    codebase_path: Optional[str] = None


class ProjectCreateResponse(BaseModel):
    project_id: str
    status: str
    message: Optional[str] = None


class ProjectStatusResponse(BaseModel):
    project_id: str
    status: str
    selected_documents: List[str] = Field(default_factory=list)
    completed_documents: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    updated_at: Optional[str] = None


class GeneratedDocument(BaseModel):
    id: str
    name: str
    status: str
    file_path: Optional[str] = None
    content: Optional[str] = None


class ProjectDocumentsResponse(BaseModel):
    project_id: str
    documents: List[GeneratedDocument] = Field(default_factory=list)


@router.post("", response_model=ProjectCreateResponse, status_code=202)
async def create_project(request: Request, project_request: ProjectCreateRequest) -> ProjectCreateResponse:
    """Create a new documentation project"""
    # Validate input
    if not project_request.user_idea or not project_request.user_idea.strip():
        raise HTTPException(status_code=422, detail="Project idea cannot be empty.")
    
    if len(project_request.user_idea) > 5000:
        raise HTTPException(status_code=422, detail="Project idea exceeds maximum length of 5000 characters.")
    
    if not project_request.selected_documents:
        raise HTTPException(status_code=422, detail="Select at least one document to generate.")

    if context_manager is None:
        raise HTTPException(status_code=500, detail="Context manager not initialized.")

    # Sanitize user input (basic sanitization)
    user_idea = project_request.user_idea.strip()[:5000]
    
    project_id = f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    # Remove duplicates while preserving order
    selected_documents = list(dict.fromkeys(project_request.selected_documents))

    context_manager.create_project(project_id, user_idea)
    context_manager.update_project_status(
        project_id=project_id,
        status="in_progress",
        user_idea=user_idea,
        profile="config_driven",
        provider_name=project_request.provider_name or "default",
        completed_agents=[],
        results={},
        selected_documents=selected_documents,
    )

    # Check if Redis/Celery is available before submitting task
    if not REDIS_AVAILABLE:
        error_msg = (
            "Redis is not available. Please start Redis server to use background task processing.\n"
            "On macOS: brew services start redis\n"
            "On Linux: sudo systemctl start redis\n"
            "Or run: redis-server"
        )
        logger.error(f"Redis not available for project {project_id} [Request-ID: {getattr(request.state, 'request_id', 'N/A')}]")
        raise HTTPException(
            status_code=503,
            detail=error_msg
        )

    # Submit task to Celery queue
    try:
        task = generate_documents_task.delay(
            project_id=project_id,
            user_idea=user_idea,
            selected_documents=selected_documents,
            provider_name=project_request.provider_name,
            codebase_path=project_request.codebase_path,
        )
        
        logger.info(f"Submitted generation task {task.id} for project {project_id} [Request-ID: {getattr(request.state, 'request_id', 'N/A')}]")
    except Exception as exc:
        error_msg = f"Failed to submit task to Celery queue: {str(exc)}"
        logger.error(f"{error_msg} [Request-ID: {getattr(request.state, 'request_id', 'N/A')}]", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=(
                "Failed to submit task to background queue. "
                "Please ensure Redis is running and Celery worker is started.\n"
                f"Error: {str(exc)}"
            )
        )

    return ProjectCreateResponse(
        project_id=project_id,
        status="started",
        message="Project accepted. Generation has started.",
    )


@router.get("/{project_id}/status", response_model=ProjectStatusResponse)
async def get_project_status(request: Request, project_id: str) -> ProjectStatusResponse:
    """
    Get the current status of a project.
    
    Returns the project status including:
    - Current generation status (pending, in_progress, complete, failed)
    - List of selected documents
    - List of completed documents
    - Error message (if failed)
    - Last update timestamp
    
    Args:
        request: FastAPI request object
        project_id: Project identifier (format: project_YYYYMMDD_HHMMSS_hex)
    
    Returns:
        ProjectStatusResponse with project status information
    
    Raises:
        HTTPException: 400 if project_id format invalid, 404 if project not found
    """
    # Validate project_id format
    if not project_id or not project_id.startswith("project_") or len(project_id) > 255:
        raise HTTPException(status_code=400, detail="Invalid project ID format.")
    
    if context_manager is None:
        raise HTTPException(status_code=500, detail="Context manager not initialized.")

    status_row = context_manager.get_project_status(project_id)
    if not status_row:
        raise HTTPException(status_code=404, detail="Project not found.")

    completed_agents = parse_json_field(status_row.get("completed_agents"), default=[])
    selected_documents = parse_json_field(status_row.get("selected_documents"), default=[])
    
    # Ensure both are lists
    if not isinstance(completed_agents, list):
        completed_agents = []
    if not isinstance(selected_documents, list):
        selected_documents = []

    return ProjectStatusResponse(
        project_id=project_id,
        status=status_row["status"],
        selected_documents=selected_documents,
        completed_documents=completed_agents,
        error=status_row.get("error"),
        updated_at=status_row.get("updated_at"),
    )


@router.get("/{project_id}/documents", response_model=ProjectDocumentsResponse)
async def get_project_documents(
    request: Request,
    project_id: str,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=100, description="Number of documents per page"),
) -> ProjectDocumentsResponse:
    """
    Get all documents for a project with pagination support.
    
    Args:
        project_id: Project identifier
        page: Page number (1-indexed, default: 1)
        page_size: Number of documents per page (default: 50, max: 100)
    """
    # Validate project_id format
    if not project_id or not project_id.startswith("project_") or len(project_id) > 255:
        raise HTTPException(status_code=400, detail="Invalid project ID format.")
    
    # Validate pagination parameters
    if page < 1:
        raise HTTPException(status_code=400, detail="Page number must be >= 1")
    if page_size < 1 or page_size > 100:
        raise HTTPException(status_code=400, detail="Page size must be between 1 and 100")
    
    if context_manager is None:
        raise HTTPException(status_code=500, detail="Context manager not initialized.")

    status_row = context_manager.get_project_status(project_id)
    if not status_row:
        raise HTTPException(status_code=404, detail="Project not found.")

    results_raw = parse_json_field(status_row.get("results"), default={})
    if not isinstance(results_raw, dict):
        results_raw = {}

    files = results_raw.get("files", {})
    all_documents: List[GeneratedDocument] = []
    
    # Parse completed_agents to check document status
    completed_agents = parse_json_field(status_row.get("completed_agents"), default=[])
    completed_agents_set: Set[str] = set(completed_agents) if isinstance(completed_agents, list) else set()

    # Get content from database instead of files
    context_manager = request.app.state.context_manager
    
    for doc_id, file_path in files.items():
        definition = get_document_by_id(doc_id)
        doc_name = definition.name if definition else doc_id.replace("_", " ").title()
        path_value = file_path.get("path") if isinstance(file_path, dict) else file_path
        content: Optional[str] = None

        # Get content from database (agent_outputs table)
        try:
            # Try to get from agent_outputs by document_type
            from src.context.shared_context import AgentType
            # Map document_id to agent_type if possible
            agent_type = None
            try:
                agent_type = AgentType(doc_id)
            except ValueError:
                # Not a standard AgentType, try to find by document_type
                pass
            
            if agent_type:
                agent_output = context_manager.get_agent_output(project_id, agent_type)
                if agent_output:
                    content = agent_output.content
            else:
                # Try to find by document_type directly
                conn = context_manager._get_connection()
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute("""
                    SELECT content FROM agent_outputs 
                    WHERE project_id = %s AND document_type = %s
                    ORDER BY version DESC LIMIT 1
                """, (project_id, doc_id))
                row = cursor.fetchone()
                cursor.close()
                if row:
                    content = row["content"]
        except Exception as exc:
            logger.warning("Failed to read document %s from database: %s", doc_id, exc)

        all_documents.append(
            GeneratedDocument(
                id=doc_id,
                name=doc_name,
                status="complete" if doc_id in completed_agents_set else "pending",
                file_path=path_value if isinstance(path_value, str) else None,  # Virtual path for reference
                content=content,  # Content from database
            )
        )

    # Apply pagination
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    documents = all_documents[start_idx:end_idx]

    return ProjectDocumentsResponse(project_id=project_id, documents=documents)


@router.get("/{project_id}/documents/{document_id}", response_model=GeneratedDocument)
async def get_single_document(request: Request, project_id: str, document_id: str) -> GeneratedDocument:
    """
    Get a specific generated document by its ID.
    
    Returns the document content, metadata, and file path.
    The document content is read from disk if the file exists.
    
    Args:
        request: FastAPI request object
        project_id: Project identifier
        document_id: Document identifier (e.g., "readme", "api_documentation")
    
    Returns:
        GeneratedDocument with content, status, and file path
    
    Raises:
        HTTPException: 400 if IDs invalid, 404 if project or document not found
    """
    # Validate IDs
    if not project_id or not project_id.startswith("project_") or len(project_id) > 255:
        raise HTTPException(status_code=400, detail="Invalid project ID format.")
    if not document_id or len(document_id) > 255:
        raise HTTPException(status_code=400, detail="Invalid document ID format.")
    
    if context_manager is None:
        raise HTTPException(status_code=500, detail="Context manager not initialized.")

    catalog_doc = get_document_by_id(document_id)
    status_row = context_manager.get_project_status(project_id)
    if not status_row:
        raise HTTPException(status_code=404, detail="Project not found.")

    results_raw = parse_json_field(status_row.get("results"), default={})
    if not isinstance(results_raw, dict):
        results_raw = {}

    files = results_raw.get("files", {})
    if document_id not in files:
        raise HTTPException(status_code=404, detail="Document not generated.")

    # Parse completed_agents to check document status
    completed_agents = parse_json_field(status_row.get("completed_agents"), default=[])
    completed_agents_set: Set[str] = set(completed_agents) if isinstance(completed_agents, list) else set()

    path_value = files[document_id].get("path") if isinstance(files[document_id], dict) else files[document_id]
    content: Optional[str] = None
    if isinstance(path_value, str) and Path(path_value).exists():
        try:
            content = Path(path_value).read_text(encoding="utf-8")
        except OSError as exc:
            logger.warning("Failed to read document %s at %s: %s", document_id, path_value, exc)

    return GeneratedDocument(
        id=document_id,
        name=catalog_doc.name if catalog_doc else document_id,
        status="complete" if document_id in completed_agents_set else "pending",
        file_path=path_value if isinstance(path_value, str) else None,
        content=content,
    )


@router.get("/{project_id}/documents/{document_id}/download")
async def download_document(request: Request, project_id: str, document_id: str) -> FileResponse:
    """
    Download a generated document as a file.
    
    Returns the document file with appropriate headers for download.
    The file is served as text/markdown with Content-Disposition header.
    
    Args:
        request: FastAPI request object
        project_id: Project identifier
        document_id: Document identifier
    
    Returns:
        FileResponse with the document file
    
    Raises:
        HTTPException: 400 if IDs invalid, 404 if file not found on disk
    """
    # Validate IDs
    if not project_id or not project_id.startswith("project_") or len(project_id) > 255:
        raise HTTPException(status_code=400, detail="Invalid project ID format.")
    if not document_id or len(document_id) > 255:
        raise HTTPException(status_code=400, detail="Invalid document ID format.")
    
    document = await get_single_document(request, project_id, document_id)
    
    # Content is stored in database, not in files
    if not document.content:
        raise HTTPException(status_code=404, detail="Document content not found.")
    
    # Generate filename from document type
    filename = f"{document.name or document_id}.md"
    
    # Return content as file download (from database)
    from fastapi.responses import Response
    return Response(
        content=document.content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": "text/markdown; charset=utf-8"
        }
    )

