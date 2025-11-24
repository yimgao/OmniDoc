"""Background tasks for OmniDoc using Celery"""
import os
import sys

# Check if we're being imported by Celery worker (not main app)
# This check happens BEFORE importing celery_app to prevent connection attempts
is_celery_worker = 'celery' in sys.argv[0] or any('celery' in arg for arg in sys.argv)

if is_celery_worker:
    # We're in a Celery worker process - check Redis BEFORE importing celery_app
    # Import only what we need to check Redis, not the full celery_app
    import redis
    import ssl
    from urllib.parse import urlparse
    
    # Get Redis URL from environment (same as celery_app.py does)
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Check Redis availability
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
        if "max requests limit exceeded" in error_str or "limit exceeded" in error_str:
            print(
                "[CELERY WORKER] ⚠️  Redis monthly limit exceeded.\n"
                f"[CELERY WORKER] Error: {str(e)}\n"
                "[CELERY WORKER] Worker cannot start until limit resets.\n"
                "[CELERY WORKER] Main application will continue to work without background tasks.\n"
                "[CELERY WORKER] To fix: Upgrade Upstash plan or wait for monthly limit reset.",
                file=sys.stderr,
                flush=True
            )
            # Exit gracefully with code 0 (not an error, just unavailable)
            # Use os._exit to bypass cleanup that might try Redis again
            import os
            os._exit(0)
    except Exception as e:
        # Check for limit errors in exception string representation
        error_str = str(e).lower()
        if "max requests limit exceeded" in error_str or "limit exceeded" in error_str:
            print(
                f"[CELERY WORKER] ⚠️  Redis limit exceeded (in exception): {str(e)}\n"
                "[CELERY WORKER] Worker cannot start. Main application will continue.",
                file=sys.stderr,
                flush=True
            )
            import os
            os._exit(0)
        # Other Redis errors - let Celery handle them
        pass

# Import celery_app (only if we didn't exit above)
from src.tasks.celery_app import celery_app

__all__ = ["celery_app"]
