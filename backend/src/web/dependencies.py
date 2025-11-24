"""
FastAPI dependency injection helpers.

Replaces global variables and setter functions with proper dependency injection.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from slowapi import Limiter

from src.context.context_manager import ContextManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


def get_context_manager(request: Request) -> ContextManager:
    """
    Get ContextManager from app state.
    
    Dependency for FastAPI routes that need database access.
    
    Usage:
        @router.get("/projects/{project_id}")
        async def get_project(
            project_id: str,
            cm: ContextManager = Depends(get_context_manager)
        ):
            return cm.get_project_status(project_id)
    """
    cm = getattr(request.app.state, "context_manager", None)
    if cm is None:
        # Fallback to global if not in app state (backward compatibility)
        from src.web.routers.projects import context_manager as global_cm
        if global_cm is None:
            raise RuntimeError("ContextManager not initialized. Check app startup.")
        return global_cm
    return cm


def get_limiter(request: Request) -> Limiter:
    """
    Get rate limiter from app state.
    
    Dependency for FastAPI routes that need rate limiting.
    
    Usage:
        @router.post("/projects")
        @limiter.limit("10/minute")
        async def create_project(
            request: Request,
            limiter: Limiter = Depends(get_limiter)
        ):
            ...
    """
    limiter = getattr(request.app.state, "limiter", None)
    if limiter is None:
        from src.web.app import limiter as global_limiter
        return global_limiter
    return limiter


# Type aliases for cleaner function signatures
ContextManagerDep = Annotated[ContextManager, Depends(get_context_manager)]
LimiterDep = Annotated[Limiter, Depends(get_limiter)]

