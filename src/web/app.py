"""FastAPI application exposing OmniDoc as a JSON-first API."""
from __future__ import annotations

import asyncio
import json
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator

from src.config.document_catalog import (
    DocumentDefinition,
    get_document_by_id,
    load_document_definitions,
)
from src.coordination.coordinator import WorkflowCoordinator
from src.context.context_manager import ContextManager
from src.utils.logger import get_logger

logger = get_logger(__name__)

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

# In-memory selection tracker until DB persistence fully migrated
PROJECT_SELECTIONS: Dict[str, List[str]] = {}

# Global coordinator/context instances
coordinator: Optional[WorkflowCoordinator] = None
context_manager: Optional[ContextManager] = None


class DocumentStage(BaseModel):
    label: Optional[str] = None
    notes: Optional[str] = None


class DocumentTemplate(BaseModel):
    id: str
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    prompt_key: Optional[str] = None
    agent_class: Optional[str] = "generic"
    dependencies: List[str] = Field(default_factory=list)
    priority: Optional[str] = None
    owner: Optional[str] = None
    status: Optional[str] = None
    audience: Optional[str] = None
    stage: Optional[DocumentStage] = None
    must_have: Optional[str] = None
    usage_frequency: Optional[str] = None
    notes: Optional[str] = None


class DocumentCatalogResponse(BaseModel):
    generated_at: Optional[str] = None
    source: Optional[str] = None
    documents: List[DocumentTemplate] = Field(default_factory=list)


class ProjectCreateRequest(BaseModel):
    user_idea: str = Field(..., min_length=1, max_length=5000)
    selected_documents: List[str] = Field(default_factory=list)
    provider_name: Optional[str] = Field(default=None, max_length=100)
    codebase_path: Optional[str] = None

    @field_validator("selected_documents")
    @classmethod
    def ensure_known_documents(cls, v: List[str]) -> List[str]:
        """Validate that all selected document IDs exist in the catalog."""
        for document_id in v:
            metadata = get_document_by_id(document_id)
            if metadata is None:
                raise ValueError(f"Unknown document id '{document_id}'")
        return v


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


class WebSocketManager:
    """Manage WebSocket connections per project."""
    
    def __init__(self) -> None:
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, project_id: str) -> None:
        await websocket.accept()
        self.active_connections.setdefault(project_id, set()).add(websocket)

    def disconnect(self, websocket: WebSocket, project_id: str) -> None:
        connections = self.active_connections.get(project_id)
        if not connections:
            return
        connections.discard(websocket)
        if not connections:
            self.active_connections.pop(project_id, None)

    async def send_progress(self, project_id: str, message: Dict[str, Any]) -> None:
        connections = self.active_connections.get(project_id)
        if not connections:
            return
        
        payload = {**message, "timestamp": datetime.now().isoformat()}
        disconnected: Set[WebSocket] = set()

        for connection in connections:
            try:
                await connection.send_json(payload)
            except Exception as exc:
                logger.warning("Failed to send WebSocket message: %s", exc)
                disconnected.add(connection)
        
        for connection in disconnected:
            self.disconnect(connection, project_id)


websocket_manager = WebSocketManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize shared services."""
    global coordinator, context_manager
    context_manager = ContextManager()
    coordinator = WorkflowCoordinator(context_manager=context_manager)
    
    load_document_definitions()
    yield
    

app = FastAPI(title="OmniDoc API", version="2.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/document-templates", response_model=DocumentCatalogResponse)
async def get_document_templates() -> DocumentCatalogResponse:
    definitions = load_document_definitions()
    generated_at: Optional[str] = None
    source: Optional[str] = None

    catalog_file = Path(os.getenv("DOCUMENT_CONFIG_PATH", "config/document_definitions.json"))
    if catalog_file.exists():
        try:
            payload = json.loads(catalog_file.read_text(encoding="utf-8"))
            generated_at = payload.get("generated_at")
            source = payload.get("source")
        except json.JSONDecodeError:
            logger.warning("Unable to parse catalog metadata from %s", catalog_file)

    documents = [
        DocumentTemplate(
            id=definition.id,
            name=definition.name,
            category=definition.category,
            description=definition.description,
            prompt_key=definition.prompt_key,
            agent_class=definition.agent_class,
            dependencies=definition.dependencies,
            priority=definition.priority,
            owner=definition.owner,
            status=definition.status,
            audience=definition.audience,
            stage=DocumentStage(label=definition.stage_label, notes=definition.stage_notes),
            must_have=definition.must_have,
            usage_frequency=definition.usage_frequency,
            notes=definition.notes,
        )
        for definition in definitions.values()
    ]

    return DocumentCatalogResponse(generated_at=generated_at, source=source, documents=documents)


@app.post("/api/projects", response_model=ProjectCreateResponse, status_code=202)
async def create_project(request: ProjectCreateRequest) -> ProjectCreateResponse:
    if not request.selected_documents:
        raise HTTPException(status_code=422, detail="Select at least one document to generate.")

    if context_manager is None:
        raise HTTPException(status_code=500, detail="Context manager not initialized.")

    project_id = f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    PROJECT_SELECTIONS[project_id] = list(dict.fromkeys(request.selected_documents))

    context_manager.create_project(project_id, request.user_idea)
    context_manager.update_project_status(
        project_id=project_id,
        status="in_progress",
        user_idea=request.user_idea,
        profile="config_driven",
        provider_name=request.provider_name or "default",
        completed_agents=[],
        results={},
        selected_documents=request.selected_documents,
    )

    asyncio.create_task(
        run_generation_async(
            user_idea=request.user_idea,
            project_id=project_id,
            selected_documents=PROJECT_SELECTIONS[project_id],
            provider_name=request.provider_name,
            codebase_path=request.codebase_path,
        )
    )

    return ProjectCreateResponse(
        project_id=project_id,
        status="started",
        message="Project accepted. Generation has started.",
    )


@app.get("/api/projects/{project_id}/status", response_model=ProjectStatusResponse)
async def get_project_status(project_id: str) -> ProjectStatusResponse:
    if context_manager is None:
        raise HTTPException(status_code=500, detail="Context manager not initialized.")

    status_row = context_manager.get_project_status(project_id)
    if not status_row:
        raise HTTPException(status_code=404, detail="Project not found.")

    completed_agents_raw = status_row.get("completed_agents") or []
    completed_agents: List[str] = []
    if isinstance(completed_agents_raw, str):
        try:
            completed_agents = json.loads(completed_agents_raw)
        except json.JSONDecodeError:
            completed_agents = []
    elif isinstance(completed_agents_raw, list):
        completed_agents = completed_agents_raw

    selected_documents_raw = status_row.get("selected_documents") or PROJECT_SELECTIONS.get(project_id, [])
    selected_documents: List[str] = []
    if isinstance(selected_documents_raw, str):
        try:
            selected_documents = json.loads(selected_documents_raw)
        except json.JSONDecodeError:
            selected_documents = []
    elif isinstance(selected_documents_raw, list):
        selected_documents = selected_documents_raw

    return ProjectStatusResponse(
                project_id=project_id,
        status=status_row["status"],
        selected_documents=selected_documents,
        completed_documents=completed_agents,
        error=status_row.get("error"),
        updated_at=status_row.get("updated_at"),
    )


@app.get("/api/projects/{project_id}/documents", response_model=ProjectDocumentsResponse)
async def get_project_documents(project_id: str) -> ProjectDocumentsResponse:
    if context_manager is None:
        raise HTTPException(status_code=500, detail="Context manager not initialized.")

    status_row = context_manager.get_project_status(project_id)
    if not status_row:
        raise HTTPException(status_code=404, detail="Project not found.")

    results_raw = status_row.get("results") or {}
    if isinstance(results_raw, str):
        try:
            results_raw = json.loads(results_raw)
        except json.JSONDecodeError:
            results_raw = {}

    files = results_raw.get("files", {})
    documents: List[GeneratedDocument] = []
    
    # Parse completed_agents to check document status
    completed_agents_raw = status_row.get("completed_agents") or []
    completed_agents_set: Set[str] = set()
    if isinstance(completed_agents_raw, str):
        try:
            completed_agents_set = set(json.loads(completed_agents_raw))
        except json.JSONDecodeError:
            completed_agents_set = set()
    elif isinstance(completed_agents_raw, list):
        completed_agents_set = set(completed_agents_raw)

    for doc_id, file_path in files.items():
        definition = get_document_by_id(doc_id)
        doc_name = definition.name if definition else doc_id.replace("_", " ").title()
        path_value = file_path.get("path") if isinstance(file_path, dict) else file_path
        content: Optional[str] = None

        if isinstance(path_value, str) and Path(path_value).exists():
            try:
                content = Path(path_value).read_text(encoding="utf-8")
            except OSError as exc:
                logger.warning("Failed to read document %s at %s: %s", doc_id, path_value, exc)

        documents.append(
            GeneratedDocument(
                id=doc_id,
                name=doc_name,
                status="complete" if doc_id in completed_agents_set else "pending",
                file_path=path_value if isinstance(path_value, str) else None,
                content=content,
            )
        )

    return ProjectDocumentsResponse(project_id=project_id, documents=documents)


@app.get("/api/projects/{project_id}/documents/{document_id}", response_model=GeneratedDocument)
async def get_single_document(project_id: str, document_id: str) -> GeneratedDocument:
    if context_manager is None:
        raise HTTPException(status_code=500, detail="Context manager not initialized.")

    catalog_doc = get_document_by_id(document_id)
    status_row = context_manager.get_project_status(project_id)
    if not status_row:
        raise HTTPException(status_code=404, detail="Project not found.")

    results_raw = status_row.get("results") or {}
    if isinstance(results_raw, str):
        try:
            results_raw = json.loads(results_raw)
        except json.JSONDecodeError:
            results_raw = {}

    files = results_raw.get("files", {})
    if document_id not in files:
        raise HTTPException(status_code=404, detail="Document not generated.")

    # Parse completed_agents to check document status
    completed_agents_raw = status_row.get("completed_agents") or []
    completed_agents_set: Set[str] = set()
    if isinstance(completed_agents_raw, str):
        try:
            completed_agents_set = set(json.loads(completed_agents_raw))
        except json.JSONDecodeError:
            completed_agents_set = set()
    elif isinstance(completed_agents_raw, list):
        completed_agents_set = set(completed_agents_raw)

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


@app.get("/api/projects/{project_id}/documents/{document_id}/download")
async def download_document(project_id: str, document_id: str) -> FileResponse:
    document = await get_single_document(project_id, document_id)
    if not document.file_path:
        raise HTTPException(status_code=404, detail="Document file not found on disk.")

    file_path = Path(document.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document file not found on disk.")

    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{file_path.name}"'},
    )


@app.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str) -> None:
    await websocket_manager.connect(websocket, project_id)
    try:
        await websocket.send_json(
            {
            "type": "connected",
            "message": "WebSocket connected",
            "project_id": project_id,
                "timestamp": datetime.now().isoformat(),
            }
        )
        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                await websocket.send_json(
                    {"type": "heartbeat", "timestamp": datetime.now().isoformat()}
                )
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, project_id)
    except Exception as exc:
        logger.error("WebSocket error for %s: %s", project_id, exc, exc_info=True)
        websocket_manager.disconnect(websocket, project_id)


async def run_generation_async(
    user_idea: str,
    project_id: str,
    selected_documents: List[str],
    provider_name: Optional[str] = None,
    codebase_path: Optional[str] = None,
) -> None:
    local_context = context_manager or ContextManager()

    try:
        logger.info("Starting generation for %s", project_id)
        await websocket_manager.send_progress(
            project_id,
            {"type": "start", "project_id": project_id, "selected_documents": selected_documents},
        )

        if provider_name:
            local_coordinator = WorkflowCoordinator(context_manager=local_context, provider_name=provider_name)
        else:
            local_coordinator = coordinator or WorkflowCoordinator(context_manager=local_context)

        async def progress_callback(event: Dict[str, Any]) -> None:
            await websocket_manager.send_progress(project_id, event)

        results = await local_coordinator.async_generate_all_docs(
            user_idea=user_idea,
            project_id=project_id,
            selected_documents=selected_documents,
            codebase_path=codebase_path,
            progress_callback=progress_callback,
        )

        await websocket_manager.send_progress(
            project_id,
            {"type": "complete", "project_id": project_id, "files_count": len(results.get("files", {}))},
        )

        local_context.update_project_status(
            project_id=project_id,
            status="complete",
            completed_agents=list(results.get("files", {}).keys()),
            results=results,
            selected_documents=selected_documents,
        )
    except Exception as exc:
        logger.error("Generation failed for %s: %s", project_id, exc, exc_info=True)
        await websocket_manager.send_progress(
            project_id,
            {"type": "error", "project_id": project_id, "message": str(exc)},
        )
        local_context.update_project_status(
            project_id=project_id,
            status="failed",
            error=str(exc),
            selected_documents=selected_documents,
    )

