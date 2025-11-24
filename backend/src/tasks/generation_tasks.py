"""
Celery tasks for document generation
"""
import asyncio
import logging
import sys
import time
from typing import Any, Dict, List, Optional

from celery import Task

from src.coordination.coordinator import WorkflowCoordinator
from src.context.context_manager import ContextManager
try:
    from src.tasks.celery_app import celery_app
    CELERY_AVAILABLE = celery_app is not None
except (ImportError, AttributeError):
    celery_app = None
    CELERY_AVAILABLE = False
from src.utils.logger import get_logger

logger = get_logger(__name__)

# In Celery worker, ensure all handlers work correctly
# Replace RotatingFileHandler with FileHandler if needed (to avoid seek errors)
for handler in list(logger.handlers):
    # Replace RotatingFileHandler with FileHandler in Celery worker (avoids seek errors)
    if hasattr(handler, 'baseFilename') and hasattr(handler, 'shouldRollover'):
        # Get the log file path
        log_file = handler.baseFilename
        logger.removeHandler(handler)
        # Replace with regular FileHandler
        file_handler = logging.FileHandler(log_file, encoding='utf-8', mode='a')
        file_handler.setLevel(logging.DEBUG)
        # Copy formatter from old handler
        if handler.formatter:
            file_handler.setFormatter(handler.formatter)
        logger.addHandler(file_handler)
        logger.debug(f"Replaced RotatingFileHandler with FileHandler in Celery worker: {log_file}")
    
    # Ensure console handlers use stdout/stderr
    if hasattr(handler, 'stream') and handler.stream in (sys.stdout, sys.stderr):
        # Already using stdout/stderr - good
        pass


def run_document_generation_sync(
    project_id: str,
    user_idea: str,
    selected_documents: List[str],
    provider_name: Optional[str] = None,
    codebase_path: Optional[str] = None,
) -> Dict:
    """
    Synchronous helper function to generate documents.
    Can be called directly (FastAPI BackgroundTasks) or from Celery task.
    
    Args:
        project_id: Project identifier
        user_idea: User's project idea
        selected_documents: List of document IDs to generate
        provider_name: Optional LLM provider name
        codebase_path: Optional codebase path
        
    Returns:
        Dictionary with generation results
    """
    context_manager = ContextManager()
    generation_start_time = time.time()
    
    try:
        import sys
        logger.info(
            "🚀 Starting document generation [Project: %s] [Documents: %d] [Provider: %s]",
            project_id,
            len(selected_documents),
            provider_name or "default"
        )
        print(f"[DOCUMENT GENERATION] Starting for project {project_id}", file=sys.stderr, flush=True)
        
        # Send WebSocket notification
        send_websocket_notification(project_id, {
            "type": "status",
            "status": "started",
            "message": "Document generation started",
            "project_id": project_id,
        })
        
        # Create initial project status
        context_manager.update_project_status(
            project_id=project_id,
            status="in_progress",
            user_idea=user_idea,
            provider_name=provider_name,
            selected_documents=selected_documents,
        )
        
        # Create coordinator
        if provider_name:
            coordinator = WorkflowCoordinator(
                context_manager=context_manager,
                provider_name=provider_name
            )
        else:
            coordinator = WorkflowCoordinator(context_manager=context_manager)
        
        # Create progress callback
        async def progress_callback(message: Dict[str, Any]) -> None:
            send_websocket_notification(project_id, message)
        
        # Run generation
        results = asyncio.run(
            coordinator.async_generate_all_docs(
                user_idea=user_idea,
                project_id=project_id,
                selected_documents=selected_documents,
                codebase_path=codebase_path,
                progress_callback=progress_callback,
            )
        )
        
        generation_duration = time.time() - generation_start_time
        
        # Update project status
        context_manager.update_project_status(
            project_id=project_id,
            status="complete",
            user_idea=user_idea,
            completed_agents=list(results.get("files", {}).keys()),
            results=results,
            selected_documents=selected_documents,
        )
        
        # Send success notification
        send_websocket_notification(project_id, {
            "type": "status",
            "status": "complete",
            "message": f"Successfully generated {len(results.get('files', {}))} documents",
            "project_id": project_id,
            "files_count": len(results.get("files", {})),
        })
        
        logger.info(
            "✅ Document generation completed [Project: %s] [Duration: %.2fs] [Documents: %d]",
            project_id,
            generation_duration,
            len(results.get("files", {}))
        )
        
        return {
            "status": "complete",
            "project_id": project_id,
            "files_count": len(results.get("files", {})),
        }
        
    except Exception as exc:
        error_message = str(exc)
        generation_duration = time.time() - generation_start_time
        
        logger.error(
            "❌ Document generation failed [Project: %s] [Duration: %.2fs] [Error: %s]",
            project_id,
            generation_duration,
            error_message,
            exc_info=True
        )
        
        # Update project status with error
        context_manager.update_project_status(
            project_id=project_id,
            status="failed",
            user_idea=user_idea,
            error=error_message,
            selected_documents=selected_documents,
        )
        
        # Send failure notification
        send_websocket_notification(project_id, {
            "type": "status",
            "status": "failed",
            "message": "Document generation failed",
            "project_id": project_id,
            "error": error_message,
        })
        
        raise


def send_websocket_notification(project_id: str, message: Dict[str, Any]) -> None:
    """
    Send WebSocket notification via Redis Pub/Sub with throttling, rate limiting and fallback.
    
    This works even from Celery workers because it bypasses the in-memory
    WebSocket manager of the worker process and talks directly to Redis,
    which the main API server is listening to.
    
    Features:
    - Throttling/batching to reduce Redis connection pressure
    - Connection pooling for efficiency
    - Rate limiting to respect monthly Redis limits
    - Automatic fallback when Redis is unavailable or rate-limited
    """
    try:
        from src.utils.redis_client import get_redis_pool
        from src.utils.notification_throttle import get_notification_throttler
        from datetime import datetime
        import json
        
        redis_pool = get_redis_pool()
        
        if redis_pool:
            # Use throttler to batch notifications and reduce connection pressure
            throttler = get_notification_throttler()
            
            # Set publish function if not already set
            if throttler._publish_func is None:
                def publish_func(channel: str, payload: str) -> bool:
                    def fallback_notify():
                        logger.warning(
                            f"Redis unavailable/rate-limited for WebSocket notification. "
                            f"Message queued in database for project {project_id}. "
                            f"Frontend will receive via polling."
                        )
                    return redis_pool.safe_publish(channel, payload, fallback_func=fallback_notify)
                
                throttler.set_publish_function(publish_func)
            
            # Add timestamp to message
            payload = {**message, "timestamp": datetime.now().isoformat()}
            
            # Add to throttler (will batch and publish automatically)
            added = throttler.add_notification(project_id, payload)
            
            if added:
                logger.debug(f"✅ WebSocket notification queued for project {project_id} (will be batched)")
            else:
                logger.debug(f"⚠️ WebSocket notification throttled for project {project_id} (rate limit)")
        else:
            # No Redis available - fallback to logging
            logger.debug(
                f"Redis not available for WebSocket notification. "
                f"Frontend will receive updates via polling for project {project_id}."
            )
            
    except Exception as exc:
        logger.debug(f"WebSocket notification failed: {exc}. Frontend will use polling fallback.", exc_info=True)


# Register Celery task only if Celery is available
generate_documents_task = None
if CELERY_AVAILABLE and celery_app:
    @celery_app.task(
        bind=True,
        name="omnidoc.generate_documents",
        max_retries=3,
        default_retry_delay=60,
        soft_time_limit=3600,
        time_limit=3700,
    )
    def generate_documents_task(
        self: Task,
        project_id: str,
        user_idea: str,
        selected_documents: List[str],
        provider_name: Optional[str] = None,
        codebase_path: Optional[str] = None,
    ) -> Dict:
        """
        Celery task wrapper that calls the synchronous helper function.
        Includes retry logic and task state tracking.
        """
        task_start_time = time.time()
        try:
            import sys
            logger.info(
                "🚀 Starting Celery task [Project: %s] [Attempt: %d/%d] [Task ID: %s]",
                project_id,
                self.request.retries + 1,
                self.max_retries + 1,
                self.request.id
            )
            print(f"[CELERY TASK] Starting for project {project_id}", file=sys.stderr, flush=True)
            
            # Update task state
            self.update_state(state="PROGRESS", meta={"status": "initializing", "project_id": project_id})
            
            # Call the synchronous helper function
            result = run_document_generation_sync(
                project_id=project_id,
                user_idea=user_idea,
                selected_documents=selected_documents,
                provider_name=provider_name,
                codebase_path=codebase_path,
            )
            
            total_duration = time.time() - task_start_time
            logger.info(
                "✅ Celery task completed [Project: %s] [Duration: %.2fs]",
                project_id,
                total_duration
            )
            return result
            
        except Exception as exc:
            error_message = str(exc)
            total_duration = time.time() - task_start_time
            error_type = type(exc).__name__
            
            # Check if retryable
            is_retryable = isinstance(exc, (ConnectionError, TimeoutError, OSError))
            retries_left = self.max_retries - self.request.retries
            
            if is_retryable and retries_left > 0:
                retry_delay = 60 * (2 ** self.request.retries)
                logger.warning(
                    "Retrying Celery task [Project: %s] [Attempt: %d/%d] [Delay: %ds]",
                    project_id,
                    self.request.retries + 1,
                    self.max_retries,
                    retry_delay
                )
                
                send_websocket_notification(project_id, {
                    "type": "status",
                    "status": "retrying",
                    "message": f"Generation failed, retrying in {retry_delay} seconds...",
                    "project_id": project_id,
                    "error": error_message,
                })
                
                raise self.retry(exc=exc, countdown=retry_delay)
            else:
                logger.error(
                    "Celery task failed permanently [Project: %s] [Duration: %.2fs] [Error: %s]",
                    project_id,
                    total_duration,
                    error_type,
                    exc_info=True
                )
                raise
