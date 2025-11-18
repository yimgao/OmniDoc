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
from src.tasks.celery_app import celery_app
from src.utils.logger import get_logger
from src.web.websocket_manager import websocket_manager

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


def send_websocket_notification(project_id: str, message: Dict[str, Any]) -> None:
    """
    Send WebSocket notification to connected clients.
    
    Note: In Celery worker, we can't create a new event loop because
    asyncio.run() is already running. We'll use a thread-safe approach
    or skip WebSocket notifications in worker (they're not critical).
    """
    try:
        # Check if we're in an async context (Celery worker with asyncio.run)
        try:
            loop = asyncio.get_running_loop()
            # If we're here, we're in an async context - can't create new loop
            # Use a thread to send the notification
            import threading
            def send_in_thread():
                try:
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    new_loop.run_until_complete(websocket_manager.send_progress(project_id, message))
                    new_loop.close()
                except Exception as e:
                    logger.debug(f"WebSocket notification failed in thread: {e}")
            
            thread = threading.Thread(target=send_in_thread, daemon=True)
            thread.start()
        except RuntimeError:
            # No running event loop - safe to create new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(websocket_manager.send_progress(project_id, message))
            loop.close()
    except Exception as exc:
        # WebSocket notifications are not critical - log as debug to reduce noise
        logger.debug(f"WebSocket notification skipped for project {project_id}: {exc}")


@celery_app.task(
    bind=True,
    name="omnidoc.generate_documents",
    max_retries=3,
    default_retry_delay=60,  # Retry after 60 seconds
    soft_time_limit=3600,  # 1 hour soft timeout
    time_limit=3700,  # 1 hour 10 seconds hard timeout
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
    Celery task to generate documents for a project
    
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
    
    task_start_time = time.time()
    try:
        # IMPORTANT: Force log to stdout/stderr (Railway captures stdout)
        import sys
        logger.info(
            "🚀 Starting document generation task [Project: %s] [Documents: %d] [Attempt: %d/%d] [Provider: %s] [Task ID: %s]",
            project_id,
            len(selected_documents),
            self.request.retries + 1,
            self.max_retries + 1,
            provider_name or "default",
            self.request.id
        )
        # Also print to stderr for Railway logs
        print(f"[CELERY TASK] Starting document generation for project {project_id}", file=sys.stderr, flush=True)
        print(f"[CELERY TASK] Selected documents: {selected_documents}", file=sys.stderr, flush=True)
        
        # Send WebSocket notification
        send_websocket_notification(project_id, {
            "type": "status",
            "status": "started",
            "message": "Document generation started",
            "project_id": project_id,
        })
        
        # Update task state
        self.update_state(state="PROGRESS", meta={"status": "initializing", "project_id": project_id})
        
        # Create initial project status (required before coordinator starts)
        context_manager.update_project_status(
            project_id=project_id,
            status="in_progress",
            user_idea=user_idea,
            provider_name=provider_name,
            selected_documents=selected_documents,
        )
        
        # Create coordinator
        if provider_name:
            logger.debug("Creating WorkflowCoordinator with provider: %s [Project: %s]", provider_name, project_id)
            coordinator = WorkflowCoordinator(
                context_manager=context_manager,
                provider_name=provider_name
            )
        else:
            logger.debug("Creating WorkflowCoordinator with default provider [Project: %s]", project_id)
            coordinator = WorkflowCoordinator(context_manager=context_manager)
        
        # Create progress callback to send WebSocket updates
        async def progress_callback(message: Dict[str, Any]) -> None:
            """Send progress updates via WebSocket"""
            logger.debug(
                "Progress update [Project: %s] [Type: %s] [Document: %s]",
                project_id,
                message.get("type"),
                message.get("document_id", "N/A")
            )
            send_websocket_notification(project_id, message)
        
        # Run generation asynchronously with progress callback
        logger.info("📋 Starting document generation workflow [Project: %s] [Documents: %s]", project_id, selected_documents)
        print(f"[CELERY TASK] Starting workflow for project {project_id}", file=sys.stderr, flush=True)
        generation_start_time = time.time()
        results = asyncio.run(
            coordinator.async_generate_all_docs(
                user_idea=user_idea,
                project_id=project_id,
                selected_documents=selected_documents,
                codebase_path=codebase_path,
                progress_callback=progress_callback,
            )
        )
        print(f"[CELERY TASK] Workflow completed for project {project_id}", file=sys.stderr, flush=True)
        generation_duration = time.time() - generation_start_time
        
        # Calculate detailed statistics
        files = results.get("files", {})
        total_docs = len(files)
        total_size = sum(len(str(doc.get("content", ""))) for doc in files.values())
        
        logger.info(
            "📊 Document generation workflow completed [Project: %s] [Duration: %.2fs] [Documents: %d] [Total size: %d chars]",
            project_id,
            generation_duration,
            total_docs,
            total_size
        )
        
        # Log each generated document
        logger.info(
            "📄 Generated documents for project %s:",
            project_id
        )
        for doc_id, doc_info in files.items():
            content_size = len(str(doc_info.get("content", "")))
            file_path = doc_info.get("path", "N/A")
            logger.info(
                "  - %s: %d chars [Path: %s]",
                doc_id,
                content_size,
                file_path
            )
        
        # Update project status
        context_manager.update_project_status(
            project_id=project_id,
            status="complete",
            user_idea=user_idea,  # Include user_idea for consistency
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
        
        total_duration = time.time() - task_start_time
        logger.info(
            "✅ Document generation task completed [Project: %s] [Total duration: %.2fs] [Generation: %.2fs] [Documents: %d]",
            project_id,
            total_duration,
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
        total_duration = time.time() - task_start_time
        error_type = type(exc).__name__
        
        logger.error(
            "❌ Document generation failed [Project: %s] [Duration: %.2fs] [Error: %s] [Type: %s]",
            project_id,
            total_duration,
            error_message,
            error_type,
            exc_info=True
        )
        
        # Check if this is a retryable error
        is_retryable = isinstance(exc, (ConnectionError, TimeoutError, OSError))
        retries_left = self.max_retries - self.request.retries
        
        if is_retryable and retries_left > 0:
            # Retry with exponential backoff
            retry_delay = 60 * (2 ** self.request.retries)  # Exponential backoff: 60s, 120s, 240s
            logger.warning(
                "Retrying task [Project: %s] [Attempt: %d/%d] [Delay: %ds] [Error: %s]",
                project_id,
                self.request.retries + 1,
                self.max_retries,
                retry_delay,
                error_type
            )
            
            # Send retry notification
            send_websocket_notification(project_id, {
                "type": "status",
                "status": "retrying",
                "message": f"Generation failed, retrying in {retry_delay} seconds...",
                "project_id": project_id,
                "error": error_message,
                "retry_attempt": self.request.retries + 1,
                "max_retries": self.max_retries,
            })
            
            # Schedule retry
            raise self.retry(exc=exc, countdown=retry_delay)
        else:
            # Final failure - no more retries
            logger.error(
                "Task failed permanently [Project: %s] [Total duration: %.2fs] [Retries exhausted: %d/%d] [Error: %s]",
                project_id,
                total_duration,
                self.request.retries,
                self.max_retries,
                error_type
            )
            
            # Update project status with error
            context_manager.update_project_status(
                project_id=project_id,
                status="failed",
                user_idea=user_idea,  # Include user_idea for consistency
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
            
            # Re-raise to mark task as failed
            raise

