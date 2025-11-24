"""
FastAPI application exposing OmniDoc as a JSON-first API.

This module sets up the main FastAPI application with:
- CORS middleware for cross-origin requests
- Rate limiting using slowapi
- Request ID middleware for logging and tracing
- Router registration for API endpoints
- Lifespan management for shared services

The application follows a modular architecture with separate routers for:
- Projects: Project creation, status, and document management
- Documents: Document template catalog
- WebSocket: Real-time progress updates

Security Features:
- Rate limiting on all endpoints
- Request validation
- CORS configuration
- Input sanitization

Monitoring:
- Request/response logging with request IDs
- Error logging with stack traces
- Rate limit violation logging
"""
from __future__ import annotations

import os
import re
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.exceptions import HTTPException

from src.config.document_catalog import load_document_definitions
from src.coordination.coordinator import WorkflowCoordinator
from src.context.context_manager import ContextManager
from src.utils.logger import get_logger
from src.web.monitoring import increment_counter
from src.web.routers import documents, projects, websocket, metrics
from src.web import health
from src.web.routers.projects import set_context_manager, set_limiter as set_projects_limiter
from src.web.routers.documents import set_limiter as set_documents_limiter

logger = get_logger(__name__)

# Request ID middleware for logging and distributed tracing
REQUEST_ID_HEADER = "X-Request-ID"

def match_origin(origin: str, pattern: str) -> bool:
    """
    Check if an origin matches a pattern, supporting wildcards.
    
    Examples:
        match_origin("https://omni-doc.vercel.app", "https://*.vercel.app") -> True
        match_origin("https://omnidoc.info", "https://omnidoc.info") -> True
    """
    if origin == pattern:
        return True
    
    # Support wildcard patterns like https://*.vercel.app
    if "*" in pattern:
        # Replace * with regex pattern
        pattern_regex = pattern.replace(".", r"\.").replace("*", r".+")
        return bool(re.match(f"^{pattern_regex}$", origin))
    
    return False


def get_allowed_origins() -> list[str]:
    """
    Get allowed origins, expanding wildcard patterns.
    """
    origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
    origins = [origin.strip() for origin in origins_str.split(",") if origin.strip()]
    
    # Log allowed origins (mask sensitive parts)
    logger.info(f"CORS allowed origins: {[o[:30] + '...' if len(o) > 30 else o for o in origins]}")
    
    return origins


ALLOWED_ORIGINS = get_allowed_origins()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Global coordinator/context instances
coordinator: Optional[WorkflowCoordinator] = None
context_manager: Optional[ContextManager] = None


def validate_environment() -> None:
    """
    Validate required environment variables before startup.
    
    Raises:
        ValueError: If required environment variables are missing
    """
    required_vars = {
        "DATABASE_URL": "Database connection string (e.g., postgresql://...)",
        "REDIS_URL": "Redis connection string (e.g., redis://...)",
    }
    
    # Debug: Log all environment variables (mask sensitive values)
    all_env_vars = {k: v[:20] + "..." if len(v) > 20 else v for k, v in os.environ.items() if "KEY" in k or "URL" in k or "TOKEN" in k}
    logger.info(f"Environment variables found: {list(all_env_vars.keys())}")
    
    missing = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        # Check for both None and empty string
        if not value or value.strip() == "":
            # Check if variable exists but is empty
            raw_value = os.environ.get(var)
            if raw_value is not None:
                missing.append(f"{var} ({description}) - VARIABLE EXISTS BUT IS EMPTY! Please set a value in Railway Variables.")
            else:
                missing.append(f"{var} ({description})")
        else:
            # Log that variable exists (but not the full value for security)
            logger.info(f"✓ {var} is set (length: {len(value)})")
    
    if missing:
        from src.config.settings import get_settings
        settings = get_settings()
        is_prod = settings.environment.value == "prod"
        
        if is_prod:
            # Production (Railway) troubleshooting
            troubleshooting = (
                "TROUBLESHOOTING (Production/Railway):\n"
                + "1. Go to Railway → Your Service → Variables tab\n"
                + "2. Make sure variables are set at SERVICE level (not just project level)\n"
                + "3. Check that variable VALUES are not empty\n"
                + "4. Remove any quotes around values (Railway may add them automatically)\n"
                + "5. Click 'Update Variables' button to save\n"
                + "6. Wait for service to redeploy\n"
            )
        else:
            # Local development troubleshooting
            troubleshooting = (
                "TROUBLESHOOTING (Local Development):\n"
                + "1. Check your .env file in the project root\n"
                + "2. Add the missing variables:\n"
                + "   DATABASE_URL=postgresql://localhost/omnidoc\n"
                + "   REDIS_URL=redis://localhost:6379/0\n"
                + "3. For cloud services (recommended):\n"
                + "   - Database: Use Neon (https://neon.tech) - free managed PostgreSQL\n"
                + "   - Redis: Use Upstash (https://upstash.com) - free managed Redis\n"
                + "4. Run: ./backend/scripts/setup.sh (creates .env with defaults)\n"
                + "5. Or manually create .env file with your connection strings\n"
            )
        
        error_msg = (
            "Missing required environment variables:\n"
            + "\n".join(f"  - {var}" for var in missing)
            + "\n\n"
            + troubleshooting
        )
        logger.error(error_msg)
        raise ValueError(error_msg)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Initializes shared services on startup and cleans up on shutdown.
    This ensures proper resource management and dependency injection.
    
    Startup:
    - Validates required environment variables
    - Creates database connection manager
    - Initializes workflow coordinator
    - Loads document definitions
    - Configures routers with dependencies
    
    Shutdown:
    - Closes database connections
    - Cleans up resources
    
    Note:
        This function is called automatically by FastAPI on application
        startup and shutdown. Changes here affect all requests.
    """
    global coordinator, context_manager
    
    # Validate environment variables first
    try:
        validate_environment()
    except ValueError as e:
        logger.error(f"Environment validation failed: {e}")
        raise
    
    context_manager = ContextManager()
    coordinator = WorkflowCoordinator(context_manager=context_manager)
    
    # Store in app state for dependency injection
    app.state.context_manager = context_manager
    app.state.limiter = limiter
    
    # Set context manager and limiter for routers (backward compatibility)
    set_context_manager(context_manager)
    set_projects_limiter(limiter)
    set_documents_limiter(limiter)
    
    # Load and cache document catalog on startup
    # This is already cached with @lru_cache, but we trigger load now
    definitions = load_document_definitions()
    app.state.document_definitions = definitions
    logger.info(f"Loaded {len(definitions)} document definitions at startup")
    
    # Initialize WebSocket Redis connection with fallback
    from src.web.websocket_manager import websocket_manager
    await websocket_manager.connect_redis()
    
    logger.info("OmniDoc API initialized successfully")
    yield
    
    # Cleanup on shutdown
    await websocket_manager.shutdown()
    logger.info("OmniDoc API shutting down")


app = FastAPI(
    title="OmniDoc API",
    version="2.0.0",
    description="AI-powered documentation generation API",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Global exception handler to add CORS headers to error responses
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    origin = request.headers.get("origin")
    allowed = False
    if origin:
        for pattern in ALLOWED_ORIGINS:
            if match_origin(origin, pattern):
                allowed = True
                break
    
    response = JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
    
    if allowed and origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Request-ID"
    
    return response

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    origin = request.headers.get("origin")
    allowed = False
    if origin:
        for pattern in ALLOWED_ORIGINS:
            if match_origin(origin, pattern):
                allowed = True
                break
    
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    response = JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
    
    if allowed and origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Request-ID"
    
    return response

# Custom CORS middleware to support wildcard patterns
class WildcardCORSMiddleware(BaseHTTPMiddleware):
    """CORS middleware that supports wildcard patterns in allowed origins."""
    
    async def dispatch(self, request, call_next):
        origin = request.headers.get("origin")
        
        # Check if origin is allowed
        allowed = False
        if origin:
            for pattern in ALLOWED_ORIGINS:
                if match_origin(origin, pattern):
                    allowed = True
                    break
        
        # Handle preflight OPTIONS request first
        if request.method == "OPTIONS":
            response = Response(status_code=200)
            if allowed and origin:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
                response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Request-ID"
            response.headers["Access-Control-Max-Age"] = "3600"
            return response
        
        # Process actual request
        response = await call_next(request)
        
        # Add CORS headers if origin is allowed (for all responses including errors)
        if allowed and origin:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Request-ID"
        
        return response

app.add_middleware(WildcardCORSMiddleware)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """
    Add request ID to all requests for logging and distributed tracing.
    
    This middleware:
    - Generates or extracts request ID from headers
    - Adds request ID to request state for use in handlers
    - Includes request ID in response headers
    - Logs request/response with request ID for correlation
    - Tracks metrics for monitoring
    
    The request ID allows tracing a request across:
    - API endpoints
    - Celery tasks
    - Database operations
    - External service calls
    
    Args:
        request: Incoming HTTP request
        call_next: Next middleware/handler in chain
    
    Returns:
        HTTP response with X-Request-ID header
    
    Note:
        Request ID format: UUID v4
        Clients can provide their own request ID via X-Request-ID header
    """
    import time
    
    request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Track request metrics
    increment_counter("api.requests.total")
    increment_counter(f"api.requests.{request.method}")
    
    # Log request with request ID for correlation
    logger.info(
        "Request started: %s %s [Request-ID: %s]",
        request.method,
        request.url.path,
        request_id
    )
    
    # Time the request
    start_time = time.time()
    try:
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        
        # Track response metrics
        duration = time.time() - start_time
        from src.web.monitoring import record_timing
        record_timing("api.response_time", duration)
        
        # Track status code metrics
        increment_counter(f"api.responses.{response.status_code}")
        
        # Log response with status code for monitoring
        logger.info(
            "Request completed: %s %s [Request-ID: %s] [Status: %d] [Duration: %.3fs]",
            request.method,
            request.url.path,
            request_id,
            response.status_code,
            duration
        )
        
        return response
    except Exception as exc:
        # Track error metrics
        increment_counter("api.errors.total")
        increment_counter(f"api.errors.{type(exc).__name__}")
        logger.error(
            "Request failed: %s %s [Request-ID: %s] [Error: %s]",
            request.method,
            request.url.path,
            request_id,
            str(exc),
            exc_info=True
        )
        raise


# Include routers
app.include_router(health.router)  # Health checks (no prefix for /health, /ready)
app.include_router(documents.router)
app.include_router(projects.router)
app.include_router(websocket.router)
app.include_router(metrics.router)  # Metrics and observability endpoints
