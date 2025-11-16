"""
Celery application configuration for background task processing.

This module configures the Celery distributed task queue for handling
long-running document generation tasks asynchronously.

Configuration:
- Broker: Redis (for task queue)
- Backend: Redis (for task results)
- Serialization: JSON (for compatibility)
- Timezone: UTC

Task Limits:
- Maximum task duration: 1 hour (hard limit)
- Soft timeout: 55 minutes (allows graceful shutdown)
- Worker restart: After 10 tasks (prevents memory leaks)

Security:
- Tasks run in isolated worker processes
- No direct database access from web server
- Task results stored in Redis (can be configured for persistence)

Monitoring:
- Task state tracking enabled
- Task start/end times logged
- Failed tasks logged with full stack traces

Backward Compatibility:
- JSON serialization ensures compatibility across Python versions
- Task names are versioned in task definitions
"""
import os
from celery import Celery
import redis

# Get Redis URL from environment or use default
# Environment variable allows configuration without code changes
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


def check_redis_available() -> bool:
    """
    Check if Redis is available for Celery broker/backend.
    
    Returns:
        True if Redis is available, False otherwise
    """
    try:
        # For Upstash Redis, we need SSL support
        # Check if URL contains upstash.io (requires SSL)
        test_url = REDIS_URL
        
        if "upstash.io" in REDIS_URL:
            # Upstash requires SSL, convert redis:// to rediss://
            if not REDIS_URL.startswith("rediss://"):
                test_url = REDIS_URL.replace("redis://", "rediss://", 1)
        
        # Try to connect to Redis with longer timeout for cloud services
        # rediss:// automatically enables SSL, no need to pass ssl parameter
        r = redis.from_url(
            test_url,
            socket_connect_timeout=5,
            socket_timeout=5,
            decode_responses=False  # Celery needs bytes
        )
        r.ping()
        return True
    except Exception as e:
        # Log the error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Redis connection failed: {type(e).__name__}: {str(e)}")
        return False


# Check Redis availability at module load time
REDIS_AVAILABLE = check_redis_available()

# Prepare Redis URL for Celery (may need SSL for Upstash)
celery_redis_url = REDIS_URL
if "upstash.io" in REDIS_URL and not REDIS_URL.startswith("rediss://"):
    # Upstash requires SSL, convert redis:// to rediss://
    celery_redis_url = REDIS_URL.replace("redis://", "rediss://", 1)

# Create Celery app with application name
celery_app = Celery(
    "omnidoc",
    broker=celery_redis_url,  # Message broker for task queue
    backend=celery_redis_url,  # Result backend for task results
    include=["src.tasks.generation_tasks"],  # Task modules to include
)

# Celery configuration for production use
# SSL configuration for Upstash Redis (required for rediss://)
broker_transport_options = {}
if "upstash.io" in REDIS_URL or celery_redis_url.startswith("rediss://"):
    # For Upstash or any SSL Redis, configure SSL parameters
    import ssl
    broker_transport_options = {
        "ssl_cert_reqs": ssl.CERT_REQUIRED,
        "ssl_ca_certs": None,  # Use system CA certificates
    }

celery_app.conf.update(
    # Serialization settings (JSON for compatibility)
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Timezone settings
    timezone="UTC",
    enable_utc=True,
    
    # Task tracking for monitoring
    task_track_started=True,
    
    # Time limits (prevent runaway tasks)
    task_time_limit=3600,  # 1 hour max per task (hard limit)
    task_soft_time_limit=3300,  # 55 minutes soft limit (allows cleanup)
    
    # Worker settings (prevent memory leaks)
    worker_prefetch_multiplier=1,  # Process one task at a time (better for long tasks)
    worker_max_tasks_per_child=10,  # Restart worker after 10 tasks to prevent memory leaks
    
    # SSL configuration for Redis broker (Upstash requires SSL)
    broker_transport_options=broker_transport_options,
    result_backend_transport_options=broker_transport_options,
)

