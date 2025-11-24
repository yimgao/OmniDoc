"""WebSocket connection manager with Redis Pub/Sub support"""
from __future__ import annotations

import asyncio
import json
import os
import ssl
from datetime import datetime
from typing import Any, Dict, List, Set, Optional
from urllib.parse import urlparse

from fastapi import WebSocket
import redis.asyncio as redis

from src.utils.logger import get_logger

logger = get_logger(__name__)


class WebSocketManager:
    """
    Manage WebSocket connections per project with Redis Pub/Sub support.
    
    This class maintains a registry of active WebSocket connections grouped
    by project ID, allowing broadcast of progress updates to all connected
    clients for a specific project across multiple server instances.
    
    Features:
    - Redis Pub/Sub for cross-process messaging
    - Per-project connection tracking
    - Automatic cleanup of disconnected clients
    - Message queue for disconnected clients
    """
    
    def __init__(self, max_connections_per_project: int = 5, max_queue_size: int = 100, 
                 heartbeat_interval: int = 30, heartbeat_timeout: int = 60) -> None:
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.message_queue: Dict[str, List[Dict[str, Any]]] = {}
        self.connection_last_pong: Dict[WebSocket, float] = {}
        self.max_connections_per_project = max_connections_per_project
        self.max_queue_size = max_queue_size
        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_timeout = heartbeat_timeout
        
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub = None
        self.redis_task = None

    async def connect_redis(self) -> None:
        """Initialize Redis connection and start listener with fallback"""
        from src.utils.redis_client import get_redis_pool
        
        redis_pool = get_redis_pool()
        
        if not redis_pool:
            logger.warning("⚠️ Redis not configured. WebSocket Manager will use local-only mode.")
            self.redis_client = None
            return
        
        try:
            # Use async client from pool
            self.redis_client = await redis_pool.get_async_client()
            
            # Test connection
            await self.redis_client.ping()
            logger.info("✅ WebSocket Manager connected to Redis")
            
            # Start listener
            self.pubsub = self.redis_client.pubsub()
            await self.pubsub.psubscribe("projects:*:events")
            self.redis_task = asyncio.create_task(self._redis_listener())
            
        except Exception as e:
            logger.warning(f"⚠️ WebSocket Manager failed to connect to Redis: {e}. Falling back to local-only mode.")
            logger.warning("Frontend will receive updates via polling fallback.")
            self.redis_client = None

    async def _redis_listener(self):
        """Listen for messages from Redis and broadcast locally"""
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "pmessage":
                    try:
                        channel = message["channel"]
                        # Channel format: projects:{project_id}:events
                        project_id = channel.split(":")[1]
                        payload = json.loads(message["data"])
                        
                        # Broadcast to local connections for this project
                        await self._broadcast_local(project_id, payload)
                    except Exception as e:
                        logger.error(f"Error processing Redis message: {e}")
        except Exception as e:
            logger.error(f"Redis listener error: {e}")

    async def shutdown(self):
        """Cleanup resources"""
        if self.pubsub:
            await self.pubsub.unsubscribe()
        if self.redis_task:
            self.redis_task.cancel()
        if self.redis_client:
            await self.redis_client.close()

    async def connect(self, websocket: WebSocket, project_id: str) -> None:
        """Connect a WebSocket to a project."""
        connections = self.active_connections.get(project_id, set())
        if len(connections) >= self.max_connections_per_project:
            await websocket.close(code=1008, reason="Too many connections")
            return
        
        await websocket.accept()
        self.active_connections.setdefault(project_id, set()).add(websocket)
        
        import time
        self.connection_last_pong[websocket] = time.time()
        
        # Send queued messages
        if project_id in self.message_queue and self.message_queue[project_id]:
            queued = self.message_queue[project_id]
            for msg in queued:
                await websocket.send_json(msg)
            del self.message_queue[project_id]

    def disconnect(self, websocket: WebSocket, project_id: str) -> None:
        """Disconnect a WebSocket."""
        connections = self.active_connections.get(project_id)
        if connections:
            connections.discard(websocket)
            if not connections:
                self.active_connections.pop(project_id, None)
        self.connection_last_pong.pop(websocket, None)

    async def send_progress(self, project_id: str, message: Dict[str, Any]) -> None:
        """
        Send progress update with rate limiting and fallback.
        
        If Redis is available and within rate limits, publish to Redis.
        If Redis is rate-limited or unavailable, broadcast locally directly.
        """
        from src.utils.redis_client import get_redis_pool
        
        payload = {**message, "timestamp": datetime.now().isoformat()}
        
        redis_pool = get_redis_pool()
        
        if redis_pool and self.redis_client:
            try:
                # Check rate limit before publishing
                can_make, error_msg = redis_pool.check_rate_limit()
                
                if can_make:
                    await self.redis_client.publish(
                        f"projects:{project_id}:events",
                        json.dumps(payload)
                    )
                    redis_pool.record_request()
                    return
                else:
                    logger.debug(f"Redis rate limit reached for WebSocket: {error_msg}. Using local broadcast.")
                    # Fall through to local broadcast
            except Exception as e:
                logger.debug(f"Failed to publish to Redis: {e}. Using local broadcast.")
        
        # Fallback to local broadcast if Redis failed, not configured, or rate-limited
        await self._broadcast_local(project_id, payload)

    async def _broadcast_local(self, project_id: str, payload: Dict[str, Any]) -> None:
        """Send to locally connected clients"""
        connections = self.active_connections.get(project_id)
        
        if not connections:
            # Queue message if no active connections (local only)
            # Note: With Redis, we might rely on persistence there, but for now simple queuing
            if project_id not in self.message_queue:
                self.message_queue[project_id] = []
            
            queue = self.message_queue[project_id]
            if len(queue) >= self.max_queue_size:
                queue.pop(0)
            queue.append(payload)
            return

        disconnected = set()
        for connection in connections:
            try:
                await connection.send_json(payload)
            except Exception:
                disconnected.add(connection)
        
        for connection in disconnected:
            self.disconnect(connection, project_id)

    # ... keep existing helper methods like get_queue_size, etc. ...
    def get_queue_size(self, project_id: str) -> int:
        return len(self.message_queue.get(project_id, []))
    
    def clear_queue(self, project_id: str) -> None:
        if project_id in self.message_queue:
            del self.message_queue[project_id]

    def get_connection_count(self, project_id: str) -> int:
        return len(self.active_connections.get(project_id, set()))

    async def send_ping(self, websocket: WebSocket) -> bool:
        try:
            await websocket.send_json({
                "type": "ping",
                "timestamp": datetime.now().isoformat()
            })
            return True
        except Exception:
            return False

    def record_pong(self, websocket: WebSocket) -> None:
        import time
        self.connection_last_pong[websocket] = time.time()

    async def check_connection_health(self, websocket: WebSocket, project_id: str) -> bool:
        """
        Check if WebSocket connection is healthy.
        
        More resilient - allows for temporary network hiccups.
        Returns True if connection is healthy, False otherwise.
        """
        try:
            import time
            # Check if connection is still in active connections
            connections = self.active_connections.get(project_id, set())
            if websocket not in connections:
                logger.debug(f"Connection not found in active connections for project {project_id}")
                return False
            
            current_time = time.time()
            # Default to current time if never ponged (new connection)
            last_pong = self.connection_last_pong.get(websocket, current_time)
            time_since_pong = current_time - last_pong
            
            # Use 2x heartbeat timeout for more lenient health check
            # This handles temporary network hiccups better
            max_allowed = self.heartbeat_timeout * 2
            
            if time_since_pong > max_allowed:
                logger.debug(
                    f"Connection unhealthy for project {project_id}: "
                    f"last pong {time_since_pong:.1f}s ago (max: {max_allowed}s)"
                )
                return False
            
            return True
        except Exception as e:
            # Be lenient on health check errors - assume healthy if we can't check
            logger.debug(f"Error checking connection health (non-fatal): {e}")
            return True

    async def cleanup_dead_connections(self, project_id: str) -> int:
        connections = self.active_connections.get(project_id, set())
        dead = []
        for ws in list(connections):
            if not await self.check_connection_health(ws, project_id):
                dead.append(ws)
        for ws in dead:
            try:
                await ws.close(code=1001)
            except:
                pass
            self.disconnect(ws, project_id)
        return len(dead)

# Global instance
websocket_manager = WebSocketManager()
