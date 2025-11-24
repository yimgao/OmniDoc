"""
Health check endpoints for monitoring and load balancers.

This module provides endpoints for checking application health,
readiness, and liveness. These are essential for:
- Kubernetes liveness/readiness probes
- Load balancer health checks
- Monitoring systems
- Deployment verification
"""
from __future__ import annotations

import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.context.context_manager import ContextManager
from src.tasks.celery_app import REDIS_AVAILABLE, check_redis_available
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    version: str
    service: str


class ReadinessResponse(BaseModel):
    """Readiness check response model"""
    status: str
    database: str
    redis: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Basic health check endpoint.
    
    Returns 200 if the application is running.
    Used by load balancers and monitoring systems.
    
    Returns:
        HealthResponse with status, version, and service name
    
    Note:
        This endpoint does not check dependencies (use /ready for that)
    """
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        service="omnidoc-api"
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check() -> ReadinessResponse:
    """
    Readiness check endpoint.
    
    Checks if the application is ready to serve traffic by verifying:
    - Database connectivity
    - Redis connectivity (if configured)
    
    Returns 200 if ready, 503 if not ready.
    Used by Kubernetes readiness probes.
    
    Returns:
        ReadinessResponse with status of each dependency
    
    Raises:
        HTTPException: 503 if any dependency is unavailable
    """
    database_status = "unknown"
    redis_status = "unknown"
    
    # Check database
    try:
        context_manager = ContextManager()
        # Try a simple query
        context_manager._get_cursor()
        database_status = "connected"
    except Exception as exc:
        logger.warning(f"Database health check failed: {exc}")
        database_status = "disconnected"
    
    # Check Redis (optional - only if configured)
    # Use the same check as Celery to ensure consistency
    if check_redis_available():
        redis_status = "connected"
    else:
        redis_status = "disconnected"
        logger.warning("Redis health check failed: Redis is not available")
    
    # If critical dependencies are down, return 503
    if database_status == "disconnected":
        raise HTTPException(
            status_code=503,
            detail="Service not ready: database unavailable"
        )
    
    return ReadinessResponse(
        status="ready" if database_status == "connected" else "not_ready",
        database=database_status,
        redis=redis_status
    )

