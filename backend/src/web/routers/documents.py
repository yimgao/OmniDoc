"""Document template-related API endpoints"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from slowapi import Limiter

from src.config.document_catalog import load_document_definitions, get_all_dependencies
from src.utils.cache import cache_document_templates

router = APIRouter(prefix="/api/document-templates", tags=["documents"])

# Rate limiter (will be set by main app)
limiter: Optional[Limiter] = None


def set_limiter(lim: Limiter) -> None:
    """Set the rate limiter for this router"""
    global limiter
    limiter = lim


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


@router.get("", response_model=DocumentCatalogResponse)
async def get_document_templates(request: Request) -> DocumentCatalogResponse:
    """
    Get all available document templates.
    
    Returns the complete catalog of document types that can be generated,
    including metadata such as dependencies, priority, and descriptions.
    Uses cached definitions from app.state (loaded at startup).
    
    Returns:
        DocumentCatalogResponse with list of document templates
    
    Note:
        This endpoint is rate-limited to 100 requests per minute per IP.
        Document definitions are cached in app.state after startup.
    """
    # Use cached definitions from app.state if available
    definitions = getattr(request.app.state, "document_definitions", None)
    if definitions is None:
        # Fallback to loading (shouldn't happen after startup)
        definitions = load_document_definitions()
    generated_at: Optional[str] = None
    source: Optional[str] = None

    # Get document config path, with smart fallback for new backend/ structure
    env_path = os.getenv("DOCUMENT_CONFIG_PATH")
    if env_path:
        catalog_file = Path(env_path)
        # If relative, try to resolve from project root
        if not catalog_file.is_absolute():
            # Try to find project root (go up from backend/src/web/routers/)
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent.parent  # backend/src/web/routers -> project root
            catalog_file = project_root / catalog_file
    else:
        # Default: try backend/config/document_definitions.json
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent.parent
        catalog_file = project_root / "backend" / "config" / "document_definitions.json"
        # Fallback to old location
        if not catalog_file.exists():
            catalog_file = project_root / "config" / "document_definitions.json"
    if catalog_file.exists():
        try:
            payload = json.loads(catalog_file.read_text(encoding="utf-8"))
            generated_at = payload.get("generated_at")
            source = payload.get("source")
        except json.JSONDecodeError:
            from src.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.warning("Unable to parse catalog metadata from %s", catalog_file)

    documents = [
        DocumentTemplate(
            id=definition.id,
            name=definition.name,
            category=definition.category,
            description=definition.description,
            prompt_key=definition.prompt_key,
            agent_class=definition.agent_class,
            dependencies=get_all_dependencies(definition.id),  # Use merged dependencies from both sources
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

