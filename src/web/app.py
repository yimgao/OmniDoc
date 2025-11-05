"""
Web Interface for DOCU-GEN
FastAPI web application for documentation generation
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict
from pathlib import Path
import uuid
from datetime import datetime

from src.coordination.coordinator import WorkflowCoordinator
from src.context.context_manager import ContextManager
from src.utils.document_organizer import get_documents_summary


# Global coordinator and context manager
coordinator: Optional[WorkflowCoordinator] = None
context_manager: Optional[ContextManager] = None
project_status: Dict[str, Dict] = {}


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


class GenerationResponse(BaseModel):
    """Response model for documentation generation"""
    project_id: str
    status: str
    message: str


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML page"""
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
            let pollInterval = null;
            
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
                
                try {
                    const response = await fetch('/api/generate', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({user_idea: userIdea, profile: profile})
                    });
                    
                    const data = await response.json();
                    projectId = data.project_id;
                    
                    showStatus('Documentation generation started! Checking progress...', 'info');
                    
                    // Start polling for status
                    pollInterval = setInterval(checkStatus, 2000);
                    checkStatus();
                } catch (error) {
                    showStatus('Error: ' + error.message, 'error');
                    generateBtn.disabled = false;
                    generateBtn.textContent = 'Generate Documentation';
                    progressDiv.classList.remove('active');
                }
            });
            
            async function checkStatus() {
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
                        clearInterval(pollInterval);
                        showStatus('Documentation generation complete!', 'success');
                        generateBtn.disabled = false;
                        generateBtn.textContent = 'Generate Documentation';
                        progressDiv.classList.remove('active');
                        
                        // Fetch and display results
                        await fetchResults();
                    } else if (data.status === 'failed') {
                        clearInterval(pollInterval);
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
async def generate_docs(request: GenerationRequest, background_tasks: BackgroundTasks):
    """Start documentation generation"""
    try:
        project_id = request.project_id or f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Start generation in background
        background_tasks.add_task(
            run_generation,
            request.user_idea,
            project_id,
            request.profile
        )
        
        project_status[project_id] = {
            "status": "in_progress",
            "user_idea": request.user_idea,
            "profile": request.profile,
            "started_at": datetime.now().isoformat(),
            "completed_agents": []
        }
        
        return GenerationResponse(
            project_id=project_id,
            status="started",
            message="Documentation generation started"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def run_generation(user_idea: str, project_id: str, profile: str = "team"):
    """Run documentation generation in background"""
    try:
        results = coordinator.generate_all_docs(user_idea, project_id, profile)
        
        project_status[project_id] = {
            "status": "complete",
            "user_idea": user_idea,
            "started_at": project_status[project_id]["started_at"],
            "completed_at": datetime.now().isoformat(),
            "results": results,
            "completed_agents": list(results.get("files", {}).keys())
        }
    except Exception as e:
        project_status[project_id] = {
            "status": "failed",
            "error": str(e),
            "started_at": project_status[project_id]["started_at"],
            "failed_at": datetime.now().isoformat()
        }


@app.get("/api/status/{project_id}")
async def get_status(project_id: str):
    """Get generation status"""
    if project_id not in project_status:
        raise HTTPException(status_code=404, detail="Project not found")
    
    status = project_status[project_id]
    return {
        "project_id": project_id,
        "status": status["status"],
        "completed_agents": status.get("completed_agents", []),
        "error": status.get("error")
    }


@app.get("/api/results/{project_id}")
async def get_results(project_id: str):
    """Get generation results with documents organized by level"""
    if project_id not in project_status:
        raise HTTPException(status_code=404, detail="Project not found")
    
    status = project_status[project_id]
    if status["status"] != "complete":
        raise HTTPException(status_code=400, detail="Generation not complete")
    
    results = status.get("results", {})
    
    # Ensure documents_by_level is included
    if "documents_by_level" not in results and "files" in results:
        results["documents_by_level"] = get_documents_summary(results["files"])
    
    return results


@app.get("/api/download/{project_id}/{doc_type}")
async def download_document(project_id: str, doc_type: str):
    """Download a generated document"""
    if project_id not in project_status:
        raise HTTPException(status_code=404, detail="Project not found")
    
    status = project_status[project_id]
    if status["status"] != "complete":
        raise HTTPException(status_code=400, detail="Generation not complete")
    
    results = status.get("results", {})
    files = results.get("files", {})
    
    if doc_type not in files:
        raise HTTPException(status_code=404, detail="Document not found")
    
    file_path = Path(files[doc_type])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type='application/octet-stream'
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

