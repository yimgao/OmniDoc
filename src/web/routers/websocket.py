"""WebSocket endpoints for real-time updates"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.utils.logger import get_logger
from src.web.websocket_manager import websocket_manager

logger = get_logger(__name__)

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str) -> None:
    """
    WebSocket endpoint for real-time project updates.
    
    Establishes a WebSocket connection to receive live updates about document
    generation progress. Supports heartbeat messages to keep connection alive.
    
    Message types:
    - "connected": Initial connection confirmation
    - "status": Status updates (started, complete, failed, retrying)
    - "progress": Document generation progress
    - "heartbeat": Keep-alive message (every 30 seconds)
    - "error": Error notifications
    
    Args:
        websocket: WebSocket connection
        project_id: Project identifier
    
    Connection limits:
        - Maximum 10 concurrent connections per project
        - Invalid project_id format will close connection with code 1008
    
    Note:
        Connection automatically sends heartbeat every 30 seconds if no messages received.
    """
    # Validate project_id format
    if not project_id or not project_id.startswith("project_") or len(project_id) > 255:
        await websocket.close(code=1008, reason="Invalid project ID format")
        return
    
    # Limit connections per project (max 10 concurrent connections per project)
    active_connections = websocket_manager.active_connections.get(project_id, set())
    if len(active_connections) >= 10:
        await websocket.close(code=1008, reason="Too many concurrent connections for this project")
        logger.warning("WebSocket connection rejected: too many connections for project %s", project_id)
        return
    
        await websocket_manager.connect(websocket, project_id)
    request_id = str(uuid.uuid4())
    logger.info("WebSocket connected: project_id=%s [Request-ID: %s]", project_id, request_id)
    
    try:
        await websocket.send_json(
            {
                "type": "connected",
                "message": "WebSocket connected",
                "project_id": project_id,
                "timestamp": datetime.now().isoformat(),
            }
        )
        
        # Start heartbeat task
        heartbeat_interval = websocket_manager.heartbeat_interval
        last_heartbeat = datetime.now()
        
        while True:
            try:
                # Wait for message with timeout (heartbeat interval)
                message = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=float(heartbeat_interval)
                )
                
                # Parse message
                import json
                try:
                    data = json.loads(message)
                    # Handle pong response
                    if data.get("type") == "pong":
                        websocket_manager.record_pong(websocket)
                        logger.debug("Received pong from project %s", project_id)
                    # Handle ping from client (echo back as pong)
                    elif data.get("type") == "ping":
                        await websocket.send_json({
                            "type": "pong",
                            "timestamp": datetime.now().isoformat()
                        })
                        websocket_manager.record_pong(websocket)
                except (json.JSONDecodeError, KeyError):
                    # Ignore invalid messages
                    pass
                
            except asyncio.TimeoutError:
                # Send heartbeat/ping to keep connection alive
                try:
                    # Check connection health first
                    if not await websocket_manager.check_connection_health(websocket, project_id):
                        logger.warning("Connection health check failed, closing connection for project %s", project_id)
                        break
                    
                    # Send ping
                    ping_sent = await websocket_manager.send_ping(websocket)
                    if ping_sent:
                        last_heartbeat = datetime.now()
                        logger.debug("Sent ping to project %s", project_id)
                except Exception as exc:
                    logger.debug("Failed to send heartbeat/ping: %s", exc)
                    # Connection may have closed, break loop
                    break
            except WebSocketDisconnect:
                break
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected normally: project_id=%s [Request-ID: %s]", project_id, request_id)
    except Exception as exc:
        logger.error(
            "WebSocket error for project_id=%s [Request-ID: %s]: %s",
            project_id,
            request_id,
            exc,
            exc_info=True
        )
        try:
            await websocket.send_json({
                "type": "error",
                "message": "An error occurred",
                "timestamp": datetime.now().isoformat(),
            })
        except Exception:
            pass  # Connection already closed
    finally:
        websocket_manager.disconnect(websocket, project_id)
        logger.info("WebSocket cleanup: project_id=%s [Request-ID: %s]", project_id, request_id)

