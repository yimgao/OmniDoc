"""
Notification throttling and batching to reduce Redis connection pressure.

This module implements throttling and batching for WebSocket notifications
to prevent overwhelming Redis with too many individual publish operations.
"""
from __future__ import annotations

import os
import time
import threading
from typing import Dict, Any, Optional, Callable
from collections import deque
from dataclasses import dataclass, field

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class NotificationBatch:
    """Batch of notifications for a project"""
    project_id: str
    messages: deque = field(default_factory=deque)
    last_flush: float = field(default_factory=time.time)
    lock: threading.Lock = field(default_factory=threading.Lock)


class NotificationThrottler:
    """
    Throttles and batches WebSocket notifications to reduce Redis connection pressure.
    
    Features:
    - Batches notifications within a time window (default 0.5s)
    - Limits notification rate per project (default 10/sec)
    - Automatically flushes batches after timeout
    - Thread-safe
    """
    
    def __init__(
        self,
        batch_window: float = 0.5,  # Batch notifications within 0.5 seconds
        max_rate_per_project: float = 10.0,  # Max 10 notifications per second per project
        max_batch_size: int = 5,  # Max notifications per batch
    ):
        self.batch_window = batch_window
        self.max_rate_per_project = max_rate_per_project
        self.max_batch_size = max_batch_size
        
        self.batches: Dict[str, NotificationBatch] = {}
        self._lock = threading.Lock()
        self._publish_func: Optional[Callable[[str, str], bool]] = None
    
    def set_publish_function(self, publish_func: Callable[[str, str], bool]):
        """Set the function to use for publishing notifications"""
        self._publish_func = publish_func
    
    def should_throttle(self, project_id: str) -> bool:
        """
        Check if notification should be throttled for this project.
        
        Returns True if notification should be throttled/dropped.
        """
        with self._lock:
            if project_id not in self.batches:
                return False
            
            batch = self.batches[project_id]
            with batch.lock:
                time_since_last = time.time() - batch.last_flush
                notifications_in_window = len(batch.messages)
                
                # If we have too many notifications in the current window, throttle
                if notifications_in_window > 0 and time_since_last < (1.0 / self.max_rate_per_project):
                    return True
                
                return False
    
    def add_notification(self, project_id: str, message: Dict[str, Any]) -> bool:
        """
        Add a notification to the batch queue.
        
        Returns True if notification was added, False if throttled.
        """
        # Check if we should throttle this notification
        if self.should_throttle(project_id):
            logger.debug(
                f"Throttling notification for project {project_id} "
                f"(rate limit: {self.max_rate_per_project}/sec)"
            )
            return False
        
        with self._lock:
            if project_id not in self.batches:
                self.batches[project_id] = NotificationBatch(project_id=project_id)
            
            batch = self.batches[project_id]
        
        with batch.lock:
            # Add message to batch
            batch.messages.append((time.time(), message))
            
            # Check if batch should be flushed
            time_since_last = time.time() - batch.last_flush
            should_flush = (
                len(batch.messages) >= self.max_batch_size or
                time_since_last >= self.batch_window
            )
            
            if should_flush:
                self._flush_batch(project_id, batch)
                batch.last_flush = time.time()
        
        return True
    
    def _flush_batch(self, project_id: str, batch: NotificationBatch):
        """Flush a batch of notifications"""
        if not batch.messages or not self._publish_func:
            return
        
        # Get the most recent notification in the batch (or merge if needed)
        # For simplicity, we'll send the latest notification as it contains the most up-to-date state
        if batch.messages:
            _, latest_message = batch.messages[-1]
            
            try:
                import json
                channel = f"projects:{project_id}:events"
                payload = json.dumps(latest_message)
                
                success = self._publish_func(channel, payload)
                if success:
                    logger.debug(
                        f"✅ Flushed notification batch for project {project_id} "
                        f"({len(batch.messages)} messages batched)"
                    )
                batch.messages.clear()
            except Exception as e:
                logger.error(f"Error flushing notification batch for {project_id}: {e}")
    
    def flush_all(self):
        """Flush all pending batches"""
        with self._lock:
            project_ids = list(self.batches.keys())
        
        for project_id in project_ids:
            with self._lock:
                batch = self.batches.get(project_id)
                if not batch:
                    continue
            
            with batch.lock:
                self._flush_batch(project_id, batch)
    
    def cleanup_old_batches(self, max_age: float = 300.0):
        """Clean up batches that haven't been used in a while"""
        current_time = time.time()
        with self._lock:
            to_remove = []
            for project_id, batch in self.batches.items():
                with batch.lock:
                    if current_time - batch.last_flush > max_age:
                        # Flush before removing
                        if batch.messages:
                            self._flush_batch(project_id, batch)
                        to_remove.append(project_id)
            
            for project_id in to_remove:
                del self.batches[project_id]


# Global throttler instance
_notification_throttler: Optional[NotificationThrottler] = None


def get_notification_throttler() -> NotificationThrottler:
    """Get or create global notification throttler"""
    global _notification_throttler
    
    if _notification_throttler is None:
        _notification_throttler = NotificationThrottler(
            batch_window=float(os.getenv("NOTIFICATION_BATCH_WINDOW", "0.5")),
            max_rate_per_project=float(os.getenv("NOTIFICATION_MAX_RATE", "10.0")),
            max_batch_size=int(os.getenv("NOTIFICATION_MAX_BATCH_SIZE", "5")),
        )
    
    return _notification_throttler

