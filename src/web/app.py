"""
Web Interface for DOCU-GEN
FastAPI web application for documentation generation
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
import asyncio
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Set
from pathlib import Path
import uuid
from datetime import datetime
import json

from src.coordination.coordinator import WorkflowCoordinator
from src.context.context_manager import ContextManager
from src.utils.document_organizer import get_documents_summary
from src.utils.logger import get_logger

logger = get_logger(__name__)


# Global coordinator and context manager
coordinator: Optional[WorkflowCoordinator] = None
context_manager: Optional[ContextManager] = None

# WebSocket connection manager for real-time progress updates
class WebSocketManager:
    """Manages WebSocket connections for real-time progress updates"""
    
    def __init__(self):
        # Map project_id -> Set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, project_id: str):
        """Accept a WebSocket connection for a project"""
        await websocket.accept()
        if project_id not in self.active_connections:
            self.active_connections[project_id] = set()
        self.active_connections[project_id].add(websocket)
        logger.info(f"WebSocket connected for project: {project_id} (total connections: {len(self.active_connections[project_id])})")
    
    def disconnect(self, websocket: WebSocket, project_id: str):
        """Remove a WebSocket connection"""
        if project_id in self.active_connections:
            self.active_connections[project_id].discard(websocket)
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]
        logger.info(f"WebSocket disconnected for project: {project_id}")
    
    async def send_progress(self, project_id: str, message: dict):
        """Send progress update to all connections for a project"""
        if project_id not in self.active_connections:
            return
        
        # Create message with timestamp
        message_with_ts = {
            **message,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to all connected clients for this project
        disconnected = set()
        for connection in self.active_connections[project_id]:
            try:
                await connection.send_json(message_with_ts)
            except Exception as e:
                logger.warning(f"Failed to send WebSocket message: {e}")
                disconnected.add(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection, project_id)

# Global WebSocket manager
websocket_manager = WebSocketManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup
    global coordinator, context_manager
    context_manager = ContextManager()
    coordinator = WorkflowCoordinator(context_manager=context_manager)
    
    yield
    
    # Shutdown (cleanup if needed)


app = FastAPI(title="DOCU-GEN API", version="1.0.0", lifespan=lifespan)

# Serve static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerationRequest(BaseModel):
    """Request model for documentation generation"""
    user_idea: str
    project_id: Optional[str] = None
    profile: Optional[str] = "team"  # "team" or "individual"
    provider_name: Optional[str] = None  # LLM provider: "ollama", "gemini", "openai" (uses env var if None)
    codebase_path: Optional[str] = None  # Optional path to codebase for code analysis (Phase 4)


class GenerationResponse(BaseModel):
    """Response model for documentation generation"""
    project_id: str
    status: str
    message: str


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML page with Tailwind CSS and modern UI"""
    # Try to read template file first
    template_path = Path(__file__).parent / "templates" / "index.html"
    if template_path.exists():
        return FileResponse(template_path)
    
    # Fallback: Return simple message directing to template setup
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>DOCU-GEN - Setup Required</title>
        <meta charset="UTF-8">
    </head>
    <body>
        <h1>DOCU-GEN</h1>
        <p>Template file not found. Please ensure <code>src/web/templates/index.html</code> exists.</p>
        <p>Static files should be in <code>src/web/static/</code></p>
    </body>
    </html>
    """)
    
    # Legacy inline HTML (kept for reference, but not used if template exists)
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>DOCU-GEN - AI Documentation Generator</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 900px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                padding: 40px;
            }
            h1 {
                color: #667eea;
                margin-bottom: 10px;
                font-size: 2.5em;
            }
            .subtitle {
                color: #666;
                margin-bottom: 30px;
                font-size: 1.1em;
            }
            .form-group {
                margin-bottom: 25px;
            }
            label {
                display: block;
                margin-bottom: 8px;
                color: #333;
                font-weight: 600;
            }
            textarea {
                width: 100%;
                min-height: 150px;
                padding: 15px;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                font-size: 16px;
                font-family: inherit;
                resize: vertical;
            }
            textarea:focus {
                outline: none;
                border-color: #667eea;
            }
            button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 15px 40px;
                border-radius: 10px;
                font-size: 18px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s;
                width: 100%;
            }
            button:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
            }
            button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            .status {
                margin-top: 20px;
                padding: 20px;
                border-radius: 10px;
                display: none;
            }
            .status.active {
                display: block;
            }
            .status.info {
                background: #e3f2fd;
                color: #1976d2;
            }
            .status.success {
                background: #e8f5e9;
                color: #388e3c;
            }
            .status.error {
                background: #ffebee;
                color: #d32f2f;
            }
            .progress {
                margin-top: 15px;
                background: #f0f0f0;
                border-radius: 10px;
                height: 30px;
                overflow: hidden;
                display: none;
            }
            .progress.active {
                display: block;
            }
            .progress-bar {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                height: 100%;
                width: 0%;
                transition: width 0.3s;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: 600;
            }
            .results {
                margin-top: 30px;
                display: none;
            }
            .results.active {
                display: block;
            }
            .results h2 {
                color: #667eea;
                margin-bottom: 20px;
            }
            .level-section {
                margin-bottom: 30px;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 10px;
                border-left: 4px solid #667eea;
            }
            .level-section.level-1 {
                border-left-color: #f44336;
                background: #ffebee;
            }
            .level-section.level-2 {
                border-left-color: #2196f3;
                background: #e3f2fd;
            }
            .level-section.level-3 {
                border-left-color: #4caf50;
                background: #e8f5e9;
            }
            .level-section.cross-level {
                border-left-color: #ff9800;
                background: #fff3e0;
            }
            .level-title {
                font-size: 1.2em;
                font-weight: 600;
                margin-bottom: 15px;
                color: #333;
            }
            .results-list {
                list-style: none;
                margin: 0;
                padding: 0;
            }
            .results-list li {
                padding: 12px 15px;
                margin-bottom: 8px;
                background: white;
                border-radius: 8px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .results-list li:hover {
                box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            }
            .download-btn {
                background: #4caf50;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 5px;
                cursor: pointer;
                text-decoration: none;
                font-size: 14px;
            }
            .download-btn:hover {
                background: #45a049;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 DOCU-GEN</h1>
            <p class="subtitle">AI-powered documentation generation from simple ideas</p>
            
            <form id="generateForm">
                <div class="form-group">
                    <label for="userIdea">Enter your project idea:</label>
                    <textarea id="userIdea" name="userIdea" placeholder="e.g., Build a task management application with team collaboration features" required></textarea>
                </div>
                
                <div class="form-group">
                    <label>Select project profile:</label>
                    <div style="display: flex; gap: 20px; margin-top: 8px;">
                        <label style="display: flex; align-items: center; gap: 5px; cursor: pointer;">
                            <input type="radio" name="profile" value="team" checked> Team (All Docs)
                        </label>
                        <label style="display: flex; align-items: center; gap: 5px; cursor: pointer;">
                            <input type="radio" name="profile" value="individual"> Individual (Core Docs)
                        </label>
                    </div>
                </div>
                <button type="submit" id="generateBtn">Generate Documentation</button>
            </form>
            
            <div id="status" class="status"></div>
            <div id="progress" class="progress">
                <div id="progressBar" class="progress-bar">0%</div>
            </div>
            
            <div id="results" class="results">
                <h2>Generated Documents (Organized by Level)</h2>
                <div id="resultsContainer"></div>
            </div>
        </div>
        
        <script>
            const form = document.getElementById('generateForm');
            const statusDiv = document.getElementById('status');
            const progressDiv = document.getElementById('progress');
            const progressBar = document.getElementById('progressBar');
            const resultsDiv = document.getElementById('results');
            const resultsContainer = document.getElementById('resultsContainer');
            const generateBtn = document.getElementById('generateBtn');
            let projectId = null;
            let websocket = null;
            let reconnectAttempts = 0;
            const maxReconnectAttempts = 5;
            
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const userIdea = document.getElementById('userIdea').value;
                const profile = document.querySelector('input[name="profile"]:checked').value;
                
                if (!userIdea.trim()) {
                    showStatus('Please enter a project idea', 'error');
                    return;
                }
                
                generateBtn.disabled = true;
                generateBtn.textContent = 'Generating...';
                showStatus('Starting documentation generation...', 'info');
                progressDiv.classList.add('active');
                resultsDiv.classList.remove('active');
                progressBar.style.width = '0%';
                progressBar.textContent = '0%';
                
                try {
                    const response = await fetch('/api/generate', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({user_idea: userIdea, profile: profile})
                    });
                    
                    const data = await response.json();
                    projectId = data.project_id;
                    
                    showStatus('Documentation generation started! Connecting for real-time updates...', 'info');
                    
                    // Connect to WebSocket for real-time updates
                    connectWebSocket(projectId);
                } catch (error) {
                    showStatus('Error: ' + error.message, 'error');
                    generateBtn.disabled = false;
                    generateBtn.textContent = 'Generate Documentation';
                    progressDiv.classList.remove('active');
                }
            });
            
            function connectWebSocket(projectId) {
                // Close existing connection if any
                if (websocket) {
                    websocket.close();
                }
                
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws/${projectId}`;
                
                websocket = new WebSocket(wsUrl);
                reconnectAttempts = 0;
                
                websocket.onopen = () => {
                    console.log('WebSocket connected');
                    showStatus('Connected! Receiving real-time updates...', 'info');
                };
                
                websocket.onmessage = (event) => {
                    try {
                        const message = JSON.parse(event.data);
                        handleWebSocketMessage(message);
                    } catch (error) {
                        console.error('Error parsing WebSocket message:', error);
                    }
                };
                
                websocket.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    showStatus('Connection error. Falling back to status polling...', 'error');
                    // Fallback to polling if WebSocket fails
                    fallbackToPolling(projectId);
                };
                
                websocket.onclose = () => {
                    console.log('WebSocket disconnected');
                    // Try to reconnect if generation is still in progress
                    if (reconnectAttempts < maxReconnectAttempts) {
                        reconnectAttempts++;
                        setTimeout(() => {
                            console.log(`Reconnecting WebSocket (attempt ${reconnectAttempts})...`);
                            connectWebSocket(projectId);
                        }, 1000 * reconnectAttempts);
                    } else {
                        showStatus('Connection lost. Falling back to status polling...', 'error');
                        fallbackToPolling(projectId);
                    }
                };
            }
            
            function handleWebSocketMessage(message) {
                console.log('WebSocket message:', message);
                
                switch (message.type) {
                    case 'connected':
                        showStatus('Connected! Waiting for updates...', 'info');
                        break;
                    
                    case 'start':
                        showStatus('Documentation generation started!', 'info');
                        progressBar.style.width = '5%';
                        progressBar.textContent = '5%';
                        break;
                    
                    case 'phase':
                        showStatus(message.message || `Phase: ${message.phase}`, 'info');
                        // Update progress based on phase
                        if (message.phase === 'phase_1') {
                            progressBar.style.width = '25%';
                            progressBar.textContent = '25%';
                        } else if (message.phase === 'phase_2') {
                            progressBar.style.width = '60%';
                            progressBar.textContent = '60%';
                        } else if (message.phase === 'phase_3') {
                            progressBar.style.width = '85%';
                            progressBar.textContent = '85%';
                        }
                        break;
                    
                    case 'progress':
                        // Update progress bar
                        const percent = message.progress || 0;
                        progressBar.style.width = percent + '%';
                        progressBar.textContent = percent + '%';
                        if (message.message) {
                            showStatus(message.message, 'info');
                        }
                        break;
                    
                    case 'complete':
                        progressBar.style.width = '100%';
                        progressBar.textContent = '100%';
                        showStatus('Documentation generation complete!', 'success');
                        generateBtn.disabled = false;
                        generateBtn.textContent = 'Generate Documentation';
                        progressDiv.classList.remove('active');
                        
                        // Close WebSocket connection
                        if (websocket) {
                            websocket.close();
                            websocket = null;
                        }
                        
                        // Fetch and display results
                        fetchResults();
                        break;
                    
                    case 'error':
                        showStatus('Error: ' + (message.message || 'Unknown error'), 'error');
                        generateBtn.disabled = false;
                        generateBtn.textContent = 'Generate Documentation';
                        progressDiv.classList.remove('active');
                        
                        // Close WebSocket connection
                        if (websocket) {
                            websocket.close();
                            websocket = null;
                        }
                        break;
                    
                    case 'heartbeat':
                        // Just keep connection alive, no UI update needed
                        break;
                    
                    default:
                        console.log('Unknown message type:', message.type);
                }
            }
            
            // Fallback to polling if WebSocket is not available
            let pollInterval = null;
            function fallbackToPolling(projectId) {
                if (pollInterval) {
                    clearInterval(pollInterval);
                }
                pollInterval = setInterval(() => checkStatus(projectId), 2000);
                checkStatus(projectId);
            }
            
            async function checkStatus(projectId) {
                if (!projectId) return;
                
                try {
                    const response = await fetch(`/api/status/${projectId}`);
                    const data = await response.json();
                    
                    const completed = data.completed_agents.length;
                    const total = 15; // Total number of agents/documents
                    const progressPercent = Math.round((completed / total) * 100);
                    
                    progressBar.style.width = progressPercent + '%';
                    progressBar.textContent = progressPercent + '%';
                    
                    if (data.status === 'complete') {
                        if (pollInterval) {
                            clearInterval(pollInterval);
                            pollInterval = null;
                        }
                        showStatus('Documentation generation complete!', 'success');
                        generateBtn.disabled = false;
                        generateBtn.textContent = 'Generate Documentation';
                        progressDiv.classList.remove('active');
                        
                        // Fetch and display results
                        await fetchResults();
                    } else if (data.status === 'failed') {
                        if (pollInterval) {
                            clearInterval(pollInterval);
                            pollInterval = null;
                        }
                        showStatus('Documentation generation failed', 'error');
                        generateBtn.disabled = false;
                        generateBtn.textContent = 'Generate Documentation';
                        progressDiv.classList.remove('active');
                    }
                } catch (error) {
                    console.error('Error checking status:', error);
                }
            }
            
            async function fetchResults() {
                try {
                    const response = await fetch(`/api/results/${projectId}`);
                    const data = await response.json();
                    
                    resultsContainer.innerHTML = '';
                    
                    // Use organized structure if available, otherwise fall back to files
                    let documentsByLevel = data.documents_by_level;
                    
                    if (!documentsByLevel && data.files) {
                        // Fallback: organize on client side
                        documentsByLevel = {
                            level_1_strategic: { level_name: 'Level 1: Strategic (Entrepreneur)', documents: [] },
                            level_2_product: { level_name: 'Level 2: Product (Product Manager)', documents: [] },
                            level_3_technical: { level_name: 'Level 3: Technical (Programmer)', documents: [] },
                            cross_level: { level_name: 'Cross-Level (Everyone)', documents: [] }
                        };
                        
                        // Simple client-side organization
                        const levelMapping = {
                            'requirements': 'level_1_strategic',
                            'project_charter': 'level_1_strategic',
                            'stakeholder_documentation': 'level_1_strategic',
                            'pm_documentation': 'level_2_product',
                            'user_stories': 'level_2_product',
                            'technical_documentation': 'level_3_technical',
                            'api_documentation': 'level_3_technical',
                            'database_schema': 'level_3_technical',
                            'setup_guide': 'level_3_technical'
                    };
                    
                    for (const [docType, filePath] of Object.entries(data.files)) {
                            const level = levelMapping[docType] || 'cross_level';
                            documentsByLevel[level].documents.push({
                                type: docType,
                                display_name: docType.replace(/_/g, ' ').replace(/\\b\\w/g, l => l.toUpperCase()),
                                file_path: filePath
                            });
                        }
                    }
                    
                    // Render by level
                    const levels = [
                        { key: 'level_1_strategic', emoji: '🎯', class: 'level-1' },
                        { key: 'level_2_product', emoji: '📊', class: 'level-2' },
                        { key: 'level_3_technical', emoji: '💻', class: 'level-3' },
                        { key: 'cross_level', emoji: '🌐', class: 'cross-level' }
                    ];
                    
                    levels.forEach(level => {
                        const levelData = documentsByLevel[level.key];
                        if (levelData && levelData.documents && levelData.documents.length > 0) {
                            const section = document.createElement('div');
                            section.className = `level-section ${level.class}`;
                            
                            const title = document.createElement('div');
                            title.className = 'level-title';
                            title.textContent = `${level.emoji} ${levelData.level_name}`;
                            section.appendChild(title);
                            
                            const list = document.createElement('ul');
                            list.className = 'results-list';
                            
                            levelData.documents.forEach(doc => {
                            const li = document.createElement('li');
                            li.innerHTML = `
                                    <span>${doc.display_name}</span>
                                    <a href="/api/download/${projectId}/${doc.type}" class="download-btn">Download</a>
                            `;
                                list.appendChild(li);
                            });
                            
                            section.appendChild(list);
                            resultsContainer.appendChild(section);
                        }
                    });
                    
                    resultsDiv.classList.add('active');
                } catch (error) {
                    console.error('Error fetching results:', error);
                }
            }
            
            function showStatus(message, type) {
                statusDiv.textContent = message;
                statusDiv.className = 'status active ' + type;
            }
        </script>
    </body>
    </html>
    """
    return html_content


@app.post("/api/generate", response_model=GenerationResponse)
async def generate_docs(request: GenerationRequest):
    """Start documentation generation (async)"""
    try:
        project_id = request.project_id or f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Create project in database and set initial status
        context_manager.create_project(project_id, request.user_idea)
        context_manager.update_project_status(
            project_id=project_id,
            status="in_progress",
            user_idea=request.user_idea,
            profile=request.profile or "team",
            provider_name=request.provider_name or "default",
            completed_agents=[]
        )
        
        # Start generation asynchronously (non-blocking)
        # Use asyncio.create_task to run in background
        asyncio.create_task(
            run_generation_async(
                request.user_idea,
                project_id,
                request.profile,
                request.provider_name,
                request.codebase_path
            )
        )
        
        return GenerationResponse(
            project_id=project_id,
            status="started",
            message="Documentation generation started"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def run_generation_async(
    user_idea: str,
    project_id: str,
    profile: str = "team",
    provider_name: Optional[str] = None,
    codebase_path: Optional[str] = None
):
    """Run documentation generation asynchronously and update status in database"""
    local_context_manager = context_manager if context_manager else ContextManager()
    
    try:
        # Create a new coordinator with the specified provider
        if provider_name:
            local_coordinator = WorkflowCoordinator(
                context_manager=local_context_manager,
                provider_name=provider_name
            )
        else:
            if coordinator:
                local_coordinator = coordinator
            else:
                local_coordinator = WorkflowCoordinator(context_manager=local_context_manager)
        
        # Use async version if available, otherwise run sync in executor
        if hasattr(local_coordinator, 'async_generate_all_docs'):
            results = await local_coordinator.async_generate_all_docs(
                user_idea, project_id, profile, codebase_path=codebase_path
            )
        else:
            # Fallback: run sync version in executor
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: local_coordinator.generate_all_docs(
                    user_idea, project_id, profile, codebase_path=codebase_path
                )
            )
        
        # Update status in database
        local_context_manager.update_project_status(
            project_id=project_id,
            status="complete",
            completed_agents=list(results.get("files", {}).keys()),
            results=results
        )
    except Exception as e:
        local_context_manager.update_project_status(
            project_id=project_id,
            status="failed",
            error=str(e)
        )


def run_generation(
    user_idea: str,
    project_id: str,
    profile: str = "team",
    provider_name: Optional[str] = None,
    codebase_path: Optional[str] = None
):
    """Run documentation generation in background (sync version, kept for backward compatibility)"""
    local_context_manager = context_manager if context_manager else ContextManager()
    
    try:
        if provider_name:
            local_coordinator = WorkflowCoordinator(
                context_manager=local_context_manager,
                provider_name=provider_name
            )
            results = local_coordinator.generate_all_docs(
                user_idea, project_id, profile, codebase_path=codebase_path
            )
        else:
            if coordinator:
                results = coordinator.generate_all_docs(
                    user_idea, project_id, profile, codebase_path=codebase_path
                )
            else:
                local_coordinator = WorkflowCoordinator(context_manager=local_context_manager)
                results = local_coordinator.generate_all_docs(
                    user_idea, project_id, profile, codebase_path=codebase_path
                )
        
        local_context_manager.update_project_status(
            project_id=project_id,
            status="complete",
            completed_agents=list(results.get("files", {}).keys()),
            results=results
        )
    except Exception as e:
        local_context_manager.update_project_status(
            project_id=project_id,
            status="failed",
            error=str(e)
        )


@app.get("/api/status/{project_id}")
async def get_status(project_id: str):
    """Get generation status from database"""
    status = context_manager.get_project_status(project_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {
        "project_id": project_id,
        "status": status["status"],
        "completed_agents": status.get("completed_agents", []),
        "error": status.get("error")
    }


@app.get("/api/results/{project_id}")
async def get_results(project_id: str):
    """Get generation results with documents organized by level from database
    
    Returns documents organized by level (L1: Strategic, L2: Product, L3: Technical, Cross-Level)
    with metadata including file paths, display names, file sizes, and generation timestamps.
    """
    status = context_manager.get_project_status(project_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if status["status"] != "complete":
        raise HTTPException(status_code=400, detail="Generation not complete")
    
    results = status.get("results", {})
    files = results.get("files", {})
    
    # Get documents organized by level
    # Always regenerate from files to ensure correct format (handles data migration)
    if files:
        try:
            # Validate that files is a dict of str -> str
            if isinstance(files, dict) and all(isinstance(v, str) for v in files.values()):
                results["documents_by_level"] = get_documents_summary(files)
            else:
                logger.warning(f"Invalid files format in results for project {project_id}, skipping documents_by_level generation")
        except Exception as e:
            logger.error(f"Error generating documents_by_level for project {project_id}: {e}")
            # Continue without documents_by_level rather than failing
    
    # Enhance documents with metadata (file size, modification time, etc.)
    if "documents_by_level" in results:
        from src.utils.file_manager import FileManager
        file_manager = FileManager()
        
        # Add metadata to each document
        for level_key in ["level_1_strategic", "level_2_product", "level_3_technical", "cross_level"]:
            if level_key in results["documents_by_level"]:
                documents = results["documents_by_level"][level_key].get("documents", [])
                for doc in documents:
                    file_path = doc.get("file_path")
                    
                    # Handle case where file_path might be a dict (from old data format)
                    if isinstance(file_path, dict):
                        # Try to extract path from dict
                        file_path = file_path.get("path") or file_path.get("file_path") or file_path.get("value")
                        if not file_path or not isinstance(file_path, str):
                            logger.warning(f"Invalid file_path format in document {doc.get('type', 'unknown')}: {file_path}")
                            continue
                    
                    # Skip if file_path is not a string
                    if not isinstance(file_path, str):
                        logger.warning(f"file_path is not a string for document {doc.get('type', 'unknown')}: {type(file_path)}")
                        continue
                    
                    # Skip if file_path is empty
                    if not file_path:
                        continue
                    
                    try:
                        path_obj = Path(file_path)
                        if path_obj.exists():
                            # Get file size
                            file_size = path_obj.stat().st_size
                            doc["file_size"] = file_size
                            doc["file_size_human"] = _format_file_size(file_size)
                            
                            # Get modification time
                            mtime = path_obj.stat().st_mtime
                            doc["modified_at"] = datetime.fromtimestamp(mtime).isoformat()
                            
                            # Get file extension
                            doc["file_extension"] = path_obj.suffix.lower()
                    except (TypeError, OSError, ValueError) as e:
                        logger.warning(f"Could not get metadata for {file_path}: {e}")
    
    # Add summary statistics
    total_size = 0
    if files:
        for path in files.values():
            # Handle case where path might not be a string
            if isinstance(path, str):
                try:
                    path_obj = Path(path)
                    if path_obj.exists():
                        total_size += path_obj.stat().st_size
                except (TypeError, OSError, ValueError) as e:
                    logger.debug(f"Could not get size for {path}: {e}")
            elif isinstance(path, dict):
                # Try to extract path from dict
                path_str = path.get("path") or path.get("file_path") or path.get("value")
                if path_str and isinstance(path_str, str):
                    try:
                        path_obj = Path(path_str)
                        if path_obj.exists():
                            total_size += path_obj.stat().st_size
                    except (TypeError, OSError, ValueError) as e:
                        logger.debug(f"Could not get size for {path_str}: {e}")
    
    results["summary"] = {
        "total_documents": len(files),
        "total_size": total_size,
        "generated_at": status.get("updated_at"),
        "profile": status.get("profile", "team")
    }
    
    return results


def _format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


@app.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    """WebSocket endpoint for real-time progress updates"""
    await websocket_manager.connect(websocket, project_id)
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "message": "WebSocket connected",
            "project_id": project_id,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep connection alive and listen for messages
        while True:
            # Wait for messages from client (optional, for bidirectional communication)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                # Echo back or handle client messages if needed
                # For now, we just keep the connection alive
            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                await websocket.send_json({
                    "type": "heartbeat",
                    "timestamp": datetime.now().isoformat()
                })
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, project_id)
    except Exception as e:
        logger.error(f"WebSocket error for project {project_id}: {e}", exc_info=True)
        websocket_manager.disconnect(websocket, project_id)


@app.get("/api/preview/{project_id}/{doc_type}")
async def preview_document(project_id: str, doc_type: str):
    """Preview a generated document (returns markdown content)"""
    status = context_manager.get_project_status(project_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if status["status"] != "complete":
        raise HTTPException(status_code=400, detail="Generation not complete")
    
    results = status.get("results", {})
    files = results.get("files", {})
    
    if doc_type not in files:
        raise HTTPException(status_code=404, detail="Document not found")
    
    file_path = Path(files[doc_type])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Read file content
    try:
        content = file_path.read_text(encoding='utf-8')
        return Response(content=content, media_type='text/markdown')
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


@app.get("/api/download/{project_id}/{doc_type}")
async def download_document(project_id: str, doc_type: str):
    """Download a generated document from database"""
    status = context_manager.get_project_status(project_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if status["status"] != "complete":
        raise HTTPException(status_code=400, detail="Generation not complete")
    
    results = status.get("results", {})
    files = results.get("files", {})
    
    if doc_type not in files:
        raise HTTPException(status_code=404, detail="Document not found")
    
    file_path = Path(files[doc_type])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine media type based on file extension
    media_type_map = {
        '.pdf': 'application/pdf',
        '.html': 'text/html',
        '.md': 'text/markdown',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.txt': 'text/plain',
    }
    
    file_ext = file_path.suffix.lower()
    media_type = media_type_map.get(file_ext, 'application/octet-stream')
    
    # Set appropriate headers for secure PDF download
    headers = {}
    
    # For PDF files, set content-disposition for download
    if file_ext == '.pdf':
        headers['Content-Disposition'] = f'attachment; filename="{file_path.name}"'
        headers['Content-Type'] = 'application/pdf'
        headers['X-Content-Type-Options'] = 'nosniff'
    else:
        headers['Content-Disposition'] = f'inline; filename="{file_path.name}"'
    
    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type=media_type,
        headers=headers
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

