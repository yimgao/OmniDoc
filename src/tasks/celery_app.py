"""
Celery application configuration for background task processing.

This module configures the Celery distributed task queue for handling
long-running document generation tasks asynchronously.

Configuration:
- Broker: Redis (primary) or PostgreSQL database (fallback when Redis unavailable)
- Backend: Redis (primary) or PostgreSQL database (fallback when Redis unavailable)
- Serialization: JSON (for compatibility)
- Timezone: UTC
- Fallback: Automatically uses database broker/backend if Redis is unavailable (requires SQLAlchemy)

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
from celery.signals import worker_process_init
import redis
import ssl  # 导入 ssl 模块
from urllib.parse import urlparse  # 导入 urlparse

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
        is_ssl = False

        if "upstash.io" in REDIS_URL or REDIS_URL.startswith("rediss://"):
            is_ssl = True
            # Upstash requires SSL, convert redis:// to rediss://
            if not test_url.startswith("rediss://"):
                test_url = test_url.replace("redis://", "rediss://", 1)
        
        # *** 修复 ***
        # 不再使用 redis.from_url() 来避免 URL 字符串解析问题。
        # 我们手动解析 URL 并直接实例化 redis.Redis 客户端，
        # 这样就可以正确传递 Python ssl 常量。
        
        parsed_url = urlparse(test_url)
        
        if is_ssl:
            r = redis.Redis(
                host=parsed_url.hostname,
                port=parsed_url.port or 6379, # 提供默认端口
                password=parsed_url.password,
                ssl=True,
                ssl_cert_reqs=ssl.CERT_NONE, # 直接使用 ssl 常量
                socket_connect_timeout=5,
                socket_timeout=5,
                decode_responses=False  # Celery needs bytes
            )
        else:
            r = redis.Redis(
                host=parsed_url.hostname,
                port=parsed_url.port or 6379, # 提供默认端口
                password=parsed_url.password,
                socket_connect_timeout=5,
                socket_timeout=5,
                decode_responses=False  # Celery needs bytes
            )
        
        r.ping()
        return True
    except redis.exceptions.ResponseError as e:
        # Check for specific Redis limit errors
        error_str = str(e).lower()
        if "max requests limit exceeded" in error_str:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(
                "Redis request limit exceeded. Celery worker cannot start. "
                "Please upgrade your Upstash plan or wait for the limit to reset. "
                "The main application will continue to work without background tasks."
            )
            # Return False so worker can handle gracefully
            return False
        else:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Redis connection failed: {type(e).__name__}: {str(e)}")
            return False
    except Exception as e:
        # Log the error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Redis connection failed: {type(e).__name__}: {str(e)}")
        return False


# Check Redis availability at module load time
REDIS_AVAILABLE = check_redis_available()

# Determine broker and backend URLs
# Fallback to database if Redis is unavailable
DATABASE_URL = os.getenv("DATABASE_URL")
USE_DATABASE_FALLBACK = not REDIS_AVAILABLE and DATABASE_URL

if USE_DATABASE_FALLBACK:
    # Use PostgreSQL database as broker and backend
    import logging
    logger = logging.getLogger(__name__)
    
    # Check if SQLAlchemy is available (required for database broker)
    try:
        import sqlalchemy
        SQLALCHEMY_AVAILABLE = True
    except ImportError:
        SQLALCHEMY_AVAILABLE = False
        logger.warning(
            "SQLAlchemy not available. Cannot use database fallback for Celery. "
            "Install with: pip install sqlalchemy. "
            "Worker will exit gracefully."
        )
    
    if SQLALCHEMY_AVAILABLE:
        logger.info(
            "Redis unavailable, falling back to PostgreSQL database for Celery broker/backend. "
            "Note: Database broker is slower than Redis but ensures background tasks continue to work."
        )
        
        # Convert PostgreSQL URL format for Celery
        # Celery database broker uses: db+postgresql://user:pass@host/db
        if DATABASE_URL.startswith("postgresql://"):
            db_conn_part = DATABASE_URL.replace("postgresql://", "", 1)
            celery_broker_url = f"db+postgresql://{db_conn_part}"
            celery_backend_url = f"db+postgresql://{db_conn_part}"
        elif DATABASE_URL.startswith("postgres://"):
            db_conn_part = DATABASE_URL.replace("postgres://", "", 1)
            celery_broker_url = f"db+postgresql://{db_conn_part}"
            celery_backend_url = f"db+postgresql://{db_conn_part}"
        else:
            # Assume it's already in the right format or try to use as-is
            celery_broker_url = f"db+{DATABASE_URL}" if not DATABASE_URL.startswith("db+") else DATABASE_URL
            celery_backend_url = celery_broker_url
    else:
        # SQLAlchemy not available, cannot use database fallback
        celery_broker_url = None
        celery_backend_url = None
else:
    # Use Redis as normal
    celery_redis_url = REDIS_URL
    is_ssl_celery = False

    if "upstash.io" in REDIS_URL or REDIS_URL.startswith("rediss://"):
        is_ssl_celery = True
        if not celery_redis_url.startswith("rediss://"):
            # Upstash requires SSL, convert redis:// to rediss://
            celery_redis_url = celery_redis_url.replace("redis://", "rediss://", 1)

    # *** 修复 ***
    # 如果使用 SSL (rediss://)，Celery 后端会引发 ValueError，除非
    # 提供了 ssl_cert_reqs。我们将其添加到 URL 查询字符串中。
    # redis-py URL 解析器需要字符串 'none'，而不是 'CERT_NONE'。
    if is_ssl_celery and "ssl_cert_reqs" not in celery_redis_url:
        separator = "?" if "?" not in celery_redis_url else "&"
        celery_redis_url += f"{separator}ssl_cert_reqs=none"
    
    celery_broker_url = celery_redis_url
    celery_backend_url = celery_redis_url

# Create Celery app with application name
# Use a custom connection pool that handles limit errors gracefully
try:
    if celery_broker_url is None:
        # Cannot create Celery app - no broker available
        import logging
        import sys
        logger = logging.getLogger(__name__)
        logger.error(
            "Cannot create Celery app: Redis unavailable and database fallback not possible. "
            "Worker will exit gracefully. Main application will continue without background tasks."
        )
        sys.exit(0)
    
    celery_app = Celery(
        "omnidoc",
        broker=celery_broker_url,  # Message broker (Redis or Database)
        backend=celery_backend_url,  # Result backend (Redis or Database)
        include=["src.tasks.generation_tasks"],  # Task modules to include
    )
except Exception as e:
    # If Celery app creation fails due to Redis issues, log and re-raise
    import logging
    logger = logging.getLogger(__name__)
    error_str = str(e).lower()
    if "max requests limit exceeded" in error_str:
        logger.error(
            "Cannot create Celery app: Redis request limit exceeded. "
            "Worker will exit gracefully. Main application will continue without background tasks."
        )
    raise

# Celery configuration for production use
# SSL configuration for Upstash Redis (required for rediss://)
# Note: Database broker doesn't need SSL transport options
broker_transport_options = {}
# Only apply SSL options if using Redis (not database fallback)
# Check if broker URL starts with db+ (database) - if so, skip SSL options
if celery_broker_url and not celery_broker_url.startswith("db+") and ("upstash.io" in REDIS_URL or REDIS_URL.startswith("rediss://")):
    # *** 修复 ***
    # 使用 CERT_NONE 来匹配 URL 参数。
    broker_transport_options = {
        "ssl_cert_reqs": ssl.CERT_NONE,
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
    
    # Broker connection retry settings (handle Redis limit errors gracefully)
    broker_connection_retry_on_startup=True,  # Retry connection on startup
    broker_connection_retry=True,  # Enable connection retries
    broker_connection_max_retries=3,  # Reduced retries to fail faster when limit exceeded
    broker_connection_retry_delay=10.0,  # Longer delay between retries (10 seconds)
    
    # SSL configuration for Redis broker (Upstash requires SSL)
    broker_transport_options=broker_transport_options,
    result_backend_transport_options=broker_transport_options,
)

# Add signal handler to catch Redis limit errors and exit gracefully
# This only runs in Celery worker processes, not in the main app
@worker_process_init.connect
def check_redis_on_worker_start(sender=None, **kwargs):
    """Check Redis availability when worker starts (only in worker processes)"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        if not check_redis_available():
            # Try to get specific error
            try:
                test_url = REDIS_URL
                is_ssl = False
                if "upstash.io" in REDIS_URL or REDIS_URL.startswith("rediss://"):
                    is_ssl = True
                    if not test_url.startswith("rediss://"):
                        test_url = test_url.replace("redis://", "rediss://", 1)
                
                parsed_url = urlparse(test_url)
                if is_ssl:
                    r = redis.Redis(
                        host=parsed_url.hostname,
                        port=parsed_url.port or 6379,
                        password=parsed_url.password,
                        ssl=True,
                        ssl_cert_reqs=ssl.CERT_NONE,
                        socket_connect_timeout=5,
                        socket_timeout=5,
                        decode_responses=False
                    )
                else:
                    r = redis.Redis(
                        host=parsed_url.hostname,
                        port=parsed_url.port or 6379,
                        password=parsed_url.password,
                        socket_connect_timeout=5,
                        socket_timeout=5,
                        decode_responses=False
                    )
                r.ping()
            except redis.exceptions.ResponseError as e:
                error_str = str(e).lower()
                if "max requests limit exceeded" in error_str:
                    logger.error(
                        "Redis request limit exceeded. Worker cannot start. "
                        "Main application will continue without background tasks. "
                        "To fix: Upgrade Upstash plan or wait for monthly limit reset."
                    )
                    # Exit gracefully (only in worker process)
                    import sys
                    sys.exit(0)
    except Exception as e:
        logger.warning(f"Error checking Redis on worker start: {e}")
        # Don't exit - let Celery handle it