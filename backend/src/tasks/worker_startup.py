"""
Custom Celery worker startup script that handles Redis limit errors gracefully.
This prevents the worker from crashing when Redis request limit is exceeded.
"""
import os
import sys
import redis
import ssl
from urllib.parse import urlparse
from src.tasks.celery_app import REDIS_URL, check_redis_available


def check_redis_before_start():
    """
    Check Redis availability before starting Celery worker.
    Exits gracefully if Redis limit is exceeded.
    """
    try:
        # Check if Redis is available
        if not check_redis_available():
            # Try to get more specific error information
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
                    print(
                        "[CELERY WORKER] ⚠️  Redis request limit exceeded (500,000 requests).\n"
                        "[CELERY WORKER] Worker cannot start until limit resets.\n"
                        "[CELERY WORKER] Main application will continue to work without background tasks.\n"
                        "[CELERY WORKER] To fix: Upgrade Upstash plan or wait for monthly limit reset.",
                        file=sys.stderr,
                        flush=True
                    )
                    # Exit gracefully with code 0 (not an error, just unavailable)
                    sys.exit(0)
            except Exception as e:
                # Other Redis errors - log and exit
                print(
                    f"[CELERY WORKER] ⚠️  Redis connection error: {e}\n"
                    f"[CELERY WORKER] Worker cannot start. Main application will continue.",
                    file=sys.stderr,
                    flush=True
                )
                sys.exit(0)
        
        # Redis is available, continue normally
        return True
    except Exception as e:
        print(
            f"[CELERY WORKER] ⚠️  Error checking Redis: {e}\n"
            f"[CELERY WORKER] Worker will attempt to start anyway.",
            file=sys.stderr,
            flush=True
        )
        # Don't exit - let Celery handle the connection
        return True


if __name__ == "__main__":
    # This can be called before starting Celery worker
    check_redis_before_start()

