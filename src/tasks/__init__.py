"""Background tasks for OmniDoc using Celery"""
import os
import sys
from src.tasks.celery_app import celery_app, REDIS_AVAILABLE, check_redis_available

# Check Redis availability and handle limit errors gracefully
if not REDIS_AVAILABLE:
    # Re-check to get the specific error message
    try:
        check_redis_available()
    except Exception as e:
        error_str = str(e).lower()
        if "max requests limit exceeded" in error_str:
            print(
                "[CELERY WORKER] Redis request limit exceeded. "
                "Worker cannot start. Main application will continue without background tasks.",
                file=sys.stderr,
                flush=True
            )
            # Exit gracefully instead of crashing
            sys.exit(0)

__all__ = ["celery_app"]
