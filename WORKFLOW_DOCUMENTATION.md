# DOCU-GEN Workflow Documentation

## 📋 Overview

This document describes the complete workflow of DOCU-GEN from application startup to document generation, including all the behind-the-scenes work.

## 🚀 Application Startup

### 1. Server Initialization

**Entry Point**: `uv run python -m src.web.app`

**File**: `src/web/app.py`

#### Step 1: FastAPI Application Creation
```python
app = FastAPI(title="DOCU-GEN API", version="1.0.0", lifespan=lifespan)
```

#### Step 2: Lifespan Event Handler
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global coordinator, context_manager
    context_manager = ContextManager()  # Initialize SQLite database
    coordinator = WorkflowCoordinator(context_manager=context_manager)  # Initialize all agents
    yield
    # Shutdown (cleanup if needed)
```

**What happens during startup:**
1. **ContextManager Initialization**:
   - Creates SQLite database (`context.db`)
   - Initializes database schema for projects, agent outputs, and status
   - Sets up connection pooling

2. **WorkflowCoordinator Initialization**:
   - Loads environment variables and settings
   - **Forces all agents to use Gemini** (hardcoded, ignores env vars)
   - Initializes 21 agents:
     - Requirements Analyst
     - Project Charter Agent
     - User Stories Agent
     - Technical Documentation Agent
     - API Documentation Agent
     - Database Schema Agent
     - Setup Guide Agent
     - Developer Documentation Agent
     - Test Documentation Agent
     - User Documentation Agent
     - Legal Compliance Agent
     - Support Playbook Agent
     - PM Documentation Agent
     - Stakeholder Communication Agent
     - Business Model Agent
     - Marketing Plan Agent
     - Quality Reviewer Agent
     - Document Improver Agent
     - Format Converter Agent
     - Claude CLI Documentation Agent
     - Code Analyst Agent
   - Each agent is initialized with:
     - Gemini provider (hardcoded)
     - Default model: `gemini-2.0-flash`
     - Temperature: 0.7 (Gemini default)
     - Rate limiter (shared across all agents)
     - File manager

3. **WebSocket Manager Initialization**:
   - Creates `WebSocketManager` for real-time progress updates
   - Manages active WebSocket connections per project

#### Step 3: Static Files and Routes
- Serves static files from `src/web/static/`
- Registers API routes:
  - `GET /` - Main HTML page
  - `POST /api/generate` - Start documentation generation
  - `GET /api/status/{project_id}` - Get generation status
  - `GET /api/results/{project_id}` - Get generated documents
  - `GET /api/download/{project_id}/{doc_type}` - Download document
  - `GET /api/preview/{project_id}/{doc_type}` - Preview document
  - `WebSocket /ws/{project_id}` - Real-time progress updates

#### Step 4: Server Start
- Uvicorn starts on `http://0.0.0.0:8000`
- WebSocket support enabled (via `websockets` package)
- Server ready to accept requests

## 📥 Request Flow

### 1. User Submits Request

**Frontend**: User fills form and clicks "Generate Documentation"

**JavaScript** (`src/web/static/js/app.js`):
```javascript
form.addEventListener('submit', async (e) => {
    const userIdea = document.getElementById('userIdea').value;
    const profile = document.querySelector('input[name="profile"]:checked').value;
    
    // Send POST request to /api/generate
    const response = await fetch('/api/generate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({user_idea: userIdea, profile: profile})
    });
    
    const data = await response.json();
    projectId = data.project_id;
    
    // Connect to WebSocket for real-time updates
    connectWebSocket(projectId);
});
```

### 2. API Endpoint Receives Request

**Endpoint**: `POST /api/generate`

**File**: `src/web/app.py`

```python
@app.post("/api/generate", response_model=GenerationResponse)
async def generate_docs(request: GenerationRequest):
    # 1. Generate project ID
    project_id = request.project_id or f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    
    # 2. Create project in database
    context_manager.create_project(project_id, request.user_idea)
    context_manager.update_project_status(
        project_id=project_id,
        status="in_progress",
        user_idea=request.user_idea,
        profile=request.profile or "team",
        completed_agents=[]
    )
    
    # 3. Start generation asynchronously (non-blocking)
    asyncio.create_task(
        run_generation_async(
            request.user_idea,
            project_id,
            request.profile,
            request.provider_name,
            request.codebase_path
        )
    )
    
    # 4. Return immediately with project_id
    return GenerationResponse(
        project_id=project_id,
        status="started",
        message="Documentation generation started"
    )
```

**What happens:**
1. **Project Creation**: Creates project record in SQLite database
2. **Status Update**: Sets status to "in_progress"
3. **Async Task**: Starts generation in background (non-blocking)
4. **Immediate Response**: Returns project_id to frontend
5. **WebSocket Connection**: Frontend connects to WebSocket for real-time updates

### 3. Async Generation Task

**Function**: `run_generation_async()`

**File**: `src/web/app.py`

```python
async def run_generation_async(
    user_idea: str,
    project_id: str,
    profile: str = "team",
    provider_name: Optional[str] = None,
    codebase_path: Optional[str] = None
):
    # 1. Get or create coordinator
    local_coordinator = coordinator or WorkflowCoordinator(context_manager=context_manager)
    
    # 2. Send WebSocket message: generation started
    await websocket_manager.send_progress(project_id, {
        "type": "start",
        "message": "Documentation generation started"
    })
    
    # 3. Run generation (async if available, otherwise sync in executor)
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
    
    # 4. Update status in database
    context_manager.update_project_status(
        project_id=project_id,
        status="complete",
        completed_agents=list(results.get("files", {}).keys()),
        results=results
    )
    
    # 5. Send WebSocket message: generation complete
    await websocket_manager.send_progress(project_id, {
        "type": "complete",
        "message": "Documentation generation complete"
    })
```

## 🔄 Document Generation Workflow

### Main Workflow: `generate_all_docs()`

**File**: `src/coordination/coordinator.py`

**Function**: `WorkflowCoordinator.generate_all_docs()`

### Phase 0: Setup

```python
# 1. Generate project ID (if not provided)
project_id = f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

# 2. Initialize results dictionary
results = {
    "project_id": project_id,
    "user_idea": user_idea,
    "profile": profile,
    "files": {},
    "status": {}
}

# 3. Initialize document storage
final_docs = {}  # Store final document content
document_file_paths = {}  # Store file paths
```

### Phase 1: Foundational Documents (Quality Gate)

**Goal**: Generate high-quality foundational documents using iterative quality loops

**Process**: For each foundational document:
1. **Generate V1**: Agent generates initial document
2. **Check Quality**: Quality checker evaluates document (score 0-100)
3. **Improve if Needed**: If score < threshold, Document Improver enhances it
4. **Return Final**: Return final document (V1 or V2)

**Documents Generated:**
1. **Requirements** (threshold: 80.0)
   - Agent: `RequirementsAnalyst`
   - Input: `user_idea`
   - Output: `requirements.md`
   - Quality Loop: Generate → Check → Improve (if score < 80.0)

2. **Project Charter** (Team only, threshold: 75.0)
   - Agent: `ProjectCharterAgent`
   - Input: `requirements_summary`
   - Output: `project_charter.md`
   - Quality Loop: Generate → Check → Improve (if score < 75.0)

3. **User Stories** (threshold: 75.0)
   - Agent: `UserStoriesAgent`
   - Input: `requirements_summary`, `project_charter_summary`
   - Output: `user_stories.md`
   - Quality Loop: Generate → Check → Improve (if score < 75.0)

4. **Technical Documentation** (threshold: 70.0)
   - Agent: `TechnicalDocumentationAgent`
   - Input: `requirements_summary`, `user_stories_summary`
   - Output: `technical_spec.md`
   - Quality Loop: Generate → Check → Improve (if score < 70.0)

**Quality Loop Details** (`_run_agent_with_quality_loop`):

```python
def _run_agent_with_quality_loop(
    agent_instance,
    agent_type: AgentType,
    generate_kwargs: dict,
    output_filename: str,
    project_id: str,
    quality_threshold: float = 80.0
) -> tuple:
    # Step 1: GENERATE V1
    v1_file_path = agent_instance.generate_and_save(**generate_kwargs)
    v1_content = file_manager.read_file(v1_file_path)
    
    # Step 2: CHECK V1 QUALITY
    quality_result = quality_reviewer.check_quality(v1_content, agent_type)
    score = quality_result.get("overall_score", 0)
    
    # Step 3: DECIDE AND IMPROVE
    if score >= quality_threshold:
        return v1_file_path, v1_content  # V1 is good enough
    else:
        # Step 3a: Get feedback
        feedback_report = quality_reviewer.generate({agent_type.value: v1_content})
        
        # Step 3b: Improve V1 -> V2
        v2_file_path = document_improver.improve_and_save(
            original_document=v1_content,
            quality_feedback=feedback_report,
            output_filename=output_filename,
            project_id=project_id
        )
        v2_content = file_manager.read_file(v2_file_path)
        return v2_file_path, v2_content
```

**Context Management:**
- Each document is saved to SQLite database via `ContextManager`
- Document content and metadata stored for later use
- Dependencies tracked for Phase 2

### Phase 2: Secondary Documents (Parallel DAG Execution)

**Goal**: Generate all remaining documents in parallel for maximum speed

**Process**: 
1. **DAG Configuration**: Load task dependencies from `workflow_dag.py`
2. **Task Creation**: Create async tasks for each document
3. **Dependency Resolution**: Resolve dependencies from Phase 1 and Phase 2
4. **Parallel Execution**: Execute independent tasks in parallel using `AsyncParallelExecutor`
5. **Dependency Waiting**: Wait for dependencies before executing dependent tasks

**Documents Generated** (depends on profile):

**Team Profile** (all documents):
- API Documentation
- Database Schema
- Setup Guide
- Developer Documentation
- Test Documentation
- User Documentation
- Legal Compliance
- Support Playbook
- PM Documentation
- Stakeholder Communication
- Business Model
- Marketing Plan

**Individual Profile** (core documents only):
- API Documentation
- Database Schema
- Setup Guide
- Developer Documentation
- Test Documentation
- User Documentation
- Legal Compliance
- Support Playbook

**DAG Structure** (`workflow_dag.py`):

```python
PHASE2_TASKS_CONFIG = {
    "api_doc": Phase2Task(
        task_id="api_doc",
        agent_type=AgentType.API_DOCUMENTATION,
        dependencies=[AgentType.TECHNICAL_DOCUMENTATION],  # Depends on Phase 1
        kwargs_builder="simple_tech"
    ),
    "db_schema": Phase2Task(
        task_id="db_schema",
        agent_type=AgentType.DATABASE_SCHEMA,
        dependencies=[AgentType.TECHNICAL_DOCUMENTATION],  # Depends on Phase 1
        kwargs_builder="simple_tech"
    ),
    "setup_guide": Phase2Task(
        task_id="setup_guide",
        agent_type=AgentType.SETUP_GUIDE,
        dependencies=[AgentType.API_DOCUMENTATION, AgentType.TECHNICAL_DOCUMENTATION],  # Depends on Phase 2
        kwargs_builder="with_api"
    ),
    # ... more tasks
}
```

**Parallel Execution** (`AsyncParallelExecutor`):

```python
# 1. Create executor
executor = AsyncParallelExecutor(max_workers=8)

# 2. Add tasks with dependencies
for task in phase2_tasks:
    task_coro = create_async_task_coro(task)()
    dep_task_ids = dependency_map.get(task.task_id, [])
    executor.add_task(
        task_id=task.task_id,
        coro=task_coro,
        dependencies=dep_task_ids
    )

# 3. Execute all tasks (respecting dependencies)
parallel_results = asyncio.run(executor.execute())
```

**Task Execution Flow**:
1. **Check Dependencies**: For each task, check if all dependencies are complete
2. **Execute Ready Tasks**: Execute all tasks with met dependencies in parallel
3. **Wait for Completion**: Wait for at least one task to complete
4. **Update Dependencies**: Mark completed tasks, check for new ready tasks
5. **Repeat**: Continue until all tasks are complete

**Async Agent Execution**:
- Agents with `async_generate_and_save()` method use native async (best performance)
- Agents with `async_generate()` method use async generation with sync file I/O
- Other agents run sync methods in thread pool executor

### Phase 3: Final Packaging

**Goal**: Cross-reference, review, and convert documents

**Steps**:
1. **Cross-Referencing**: 
   - Agent: `CrossReferencer`
   - Process: Scans all documents, creates links between related sections
   - Output: Updated documents with cross-references

2. **Quality Review**:
   - Agent: `QualityReviewerAgent`
   - Process: Reviews all documents, generates quality report
   - Output: Quality report (for logging, not for improvement)

3. **Format Conversion**:
   - Agent: `FormatConverterAgent`
   - Process: Converts Markdown to HTML, PDF, DOCX
   - Output: Multiple format versions of each document

4. **Document Organization**:
   - Process: Organizes documents by level (Strategic, Product, Technical, Cross-Level)
   - Output: Organized document structure for UI display

### Phase 4: Code Analysis (Optional)

**Goal**: Analyze codebase and update documentation to match actual code

**Condition**: Only if `codebase_path` is provided

**Process**:
1. **Code Analysis**:
   - Agent: `CodeAnalystAgent`
   - Process: Analyzes codebase structure, APIs, database schemas
   - Output: Code analysis report

2. **Documentation Update**:
   - Process: Updates API and Developer documentation based on code analysis
   - Output: Updated documents matching actual code

## 🔍 Behind the Scenes

### 1. Agent Initialization

**All 21 agents are initialized during WorkflowCoordinator startup:**

```python
# Each agent is initialized with:
- provider_name="gemini"  # Hardcoded, always Gemini
- rate_limiter=shared_rate_limiter  # Shared across all agents
- model_name=None  # Uses default from GeminiProvider (gemini-2.0-flash)
- temperature=None  # Uses default from settings (0.7 for Gemini)
```

**Agent List:**
1. RequirementsAnalyst
2. ProjectCharterAgent
3. UserStoriesAgent
4. TechnicalDocumentationAgent
5. APIDocumentationAgent
6. DatabaseSchemaAgent
7. SetupGuideAgent
8. DeveloperDocumentationAgent
9. TestDocumentationAgent
10. UserDocumentationAgent
11. LegalComplianceAgent
12. SupportPlaybookAgent
13. PMDocumentationAgent
14. StakeholderCommunicationAgent
15. BusinessModelAgent
16. MarketingPlanAgent
17. QualityReviewerAgent
18. DocumentImproverAgent
19. FormatConverterAgent
20. ClaudeCLIDocumentationAgent
21. CodeAnalystAgent

### 2. LLM Provider (Gemini)

**All agents use Gemini** (hardcoded in Coordinator)

**Provider**: `GeminiProvider`
- **Model**: `gemini-2.0-flash` (default, or `GEMINI_DEFAULT_MODEL` env var)
- **API**: Google Generative AI API
- **Rate Limiting**: Built-in rate limiting (50 requests/minute, configurable)
- **Retry Logic**: Exponential backoff for rate limits and errors
- **Timeout**: Dynamic timeout based on `max_tokens`

**API Call Flow**:
```python
# BaseAgent._call_llm()
1. Prepare prompt (with system prompt and user input)
2. Apply rate limiting (RequestQueue)
3. Call GeminiProvider.generate()
4. Handle rate limits (retry with exponential backoff)
5. Clean response (remove markdown code blocks if present)
6. Return cleaned text
```

### 2. Rate Limiting

**Component**: `RequestQueue` (sync) and `AsyncRequestQueue` (async)

**Features**:
- Configurable rate limit (default: 50 requests/minute)
- Safety margin (95% of max rate to avoid hitting limits)
- Request queuing for rate limit compliance
- Caching to reduce API calls

**Process**:
```python
# RequestQueue.execute()
1. Check cache (if result exists, return immediately)
2. Check rate limit (if at limit, wait until window clears)
3. Execute request
4. Cache result
5. Return result
```

### 3. Context Management

**Component**: `ContextManager` (SQLite database)

**Storage**:
- **Projects**: Project metadata (project_id, user_idea, status, created_at, updated_at)
- **Agent Outputs**: Document content and metadata for each agent
- **Project Status**: Generation status, completed agents, results

**Process**:
```python
# ContextManager.save_agent_output()
1. Get or create project record
2. Save agent output to database
3. Update project status
4. Store document content and metadata
```

### 4. Quality Checking

**Component**: `QualityChecker` and `DocumentTypeQualityChecker`

**Process**:
```python
# QualityChecker.check_quality()
1. Check word count (minimum threshold)
2. Check sections (required sections present)
3. Check readability (Flesch reading ease score)
4. Calculate overall score (weighted average)
5. Return quality result
```

**Document-Type-Specific Checks**:
- Each document type has specific required sections
- Quality thresholds vary by document type
- Checklists are defined in `DocumentTypeQualityChecker`

### 5. Document Improvement

**Component**: `DocumentImproverAgent`

**Process**:
```python
# DocumentImproverAgent.improve_and_save()
1. Receive original document and quality feedback
2. Generate improvement prompt (with feedback)
3. Call LLM to generate improved version
4. Save improved document (overwrite original)
5. Return file path
```

### 6. File Management

**Component**: `FileManager`

**Process**:
```python
# FileManager.write_file()
1. Create directory if needed
2. Write file content
3. Return file path

# FileManager.read_file()
1. Read file content
2. Return file content as string
```

### 7. WebSocket Communication

**Component**: `WebSocketManager`

**Process**:
```python
# WebSocket Connection
1. Client connects to /ws/{project_id}
2. Server accepts connection
3. Server sends progress updates:
   - "start": Generation started
   - "phase": Phase change (phase_1, phase_2, phase_3)
   - "progress": Progress update (percentage)
   - "complete": Generation complete
   - "error": Error occurred
4. Client receives updates in real-time
5. Client updates UI (progress bar, status message)
```

## 📊 Data Flow

### 1. User Idea → Requirements

```
User Idea (string)
    ↓
RequirementsAnalyst.generate()
    ↓
LLM Call (Gemini)
    ↓
Requirements Document (Markdown)
    ↓
ContextManager.save_agent_output()
    ↓
SQLite Database
    ↓
Parsed Requirements (features, personas, objectives)
```

### 2. Requirements → Other Documents

```
Requirements Document
    ↓
ContextManager.get_agent_output()
    ↓
Requirements Summary (dict)
    ↓
Other Agents (Technical, API, etc.)
    ↓
LLM Call (Gemini)
    ↓
Generated Document (Markdown)
    ↓
ContextManager.save_agent_output()
    ↓
SQLite Database
```

### 3. Document → Final Formats

```
Markdown Document
    ↓
FormatConverterAgent.convert()
    ↓
HTML, PDF, DOCX
    ↓
FileManager.write_file()
    ↓
File System (docs/)
```

## 🔄 Error Handling

### 1. LLM API Errors

**Retry Logic**: `@retry_with_backoff` decorator
- **Max Retries**: 3
- **Initial Delay**: 2.0 seconds
- **Backoff Factor**: 2.0 (exponential backoff)
- **Exceptions**: ConnectionError, TimeoutError, RequestException

**Process**:
```python
# Retry with exponential backoff
Attempt 1: Immediate
Attempt 2: Wait 2.0 seconds
Attempt 3: Wait 4.0 seconds
Attempt 4: Wait 8.0 seconds (if max_retries > 3)
```

### 2. Rate Limit Errors

**Handling**: Automatic retry with exponential backoff
- **Detection**: Check for 429 status code or "rate limit" in error message
- **Action**: Wait and retry
- **Fallback**: Return error if all retries fail

### 3. Quality Check Errors

**Handling**: Fallback to base quality checker
- **Detection**: Document-type-specific checker fails
- **Action**: Use generic quality checker
- **Fallback**: Assume score 0 (triggers improvement)

### 4. Improvement Errors

**Handling**: Fallback to original document
- **Detection**: Document improvement fails
- **Action**: Log error, return original document
- **Fallback**: Use V1 document (even if quality is low)

## 📈 Performance Optimization

### 1. Parallel Execution

**Phase 2**: All secondary documents generated in parallel
- **Max Workers**: 8 (configurable)
- **Speedup**: ~3x faster than sequential execution
- **Dependencies**: Respected (tasks wait for dependencies)

### 2. Async Execution

**Agents**: Native async support for Phase 2 agents
- **Method**: `async_generate()` and `async_generate_and_save()`
- **Benefit**: True async I/O, no thread pool overhead
- **Fallback**: Sync methods run in thread pool executor

### 3. Caching

**Rate Limiter**: Caches API responses
- **Key**: Function name + arguments
- **Benefit**: Reduces API calls for identical requests
- **Limit**: 100 cached entries (FIFO eviction)

### 4. Rate Limiting

**Request Queue**: Prevents API rate limit errors
- **Rate**: 50 requests/minute (configurable)
- **Safety Margin**: 95% of max rate
- **Benefit**: Avoids rate limit errors, ensures API compliance

## 🎯 Summary

### Application Startup
1. FastAPI application created
2. ContextManager initialized (SQLite database)
3. WorkflowCoordinator initialized (21 agents, all using Gemini)
4. WebSocket manager initialized
5. Server starts on port 8000

### Request Flow
1. User submits form
2. Frontend sends POST request to `/api/generate`
3. Server creates project in database
4. Server starts async generation task
5. Server returns project_id immediately
6. Frontend connects to WebSocket for real-time updates

### Document Generation
1. **Phase 1**: Foundational documents with quality gates (sequential)
2. **Phase 2**: Secondary documents in parallel (DAG-based, async)
3. **Phase 3**: Final packaging (cross-ref, review, convert)
4. **Phase 4**: Code analysis (optional, if codebase_path provided)

### Behind the Scenes
1. **LLM Provider**: Gemini (all agents, hardcoded)
2. **Rate Limiting**: Request queue with caching
3. **Context Management**: SQLite database for persistence
4. **Quality Checking**: Document-type-specific quality checks
5. **Document Improvement**: Automatic improvement for low-quality documents
6. **File Management**: File system for document storage
7. **WebSocket Communication**: Real-time progress updates

### Error Handling
1. **Retry Logic**: Exponential backoff for API errors
2. **Rate Limit Handling**: Automatic retry with waiting
3. **Quality Check Fallback**: Generic checker if specific checker fails
4. **Improvement Fallback**: Original document if improvement fails

### Performance
1. **Parallel Execution**: Phase 2 documents generated in parallel (~3x speedup)
2. **Async Execution**: Native async support for Phase 2 agents
3. **Caching**: API response caching to reduce calls
4. **Rate Limiting**: Prevents API rate limit errors

## 🔗 Key Components

### Core Components
- **WorkflowCoordinator**: Orchestrates the entire workflow
- **ContextManager**: Manages project context and status (SQLite)
- **BaseAgent**: Base class for all agents
- **GeminiProvider**: LLM provider for Gemini API
- **QualityChecker**: Quality assessment for documents
- **DocumentImproverAgent**: Improves low-quality documents
- **AsyncParallelExecutor**: Parallel task execution with dependencies

### Supporting Components
- **FileManager**: File system operations
- **RequestQueue**: Rate limiting and request queuing
- **CrossReferencer**: Cross-references between documents
- **FormatConverterAgent**: Converts documents to multiple formats
- **DocumentOrganizer**: Organizes documents by level
- **WebSocketManager**: Real-time progress updates

## 📝 Notes

- **All agents use Gemini**: Hardcoded in Coordinator, cannot be changed via env vars
- **Quality Gates**: Phase 1 documents use iterative quality loops
- **Parallel Execution**: Phase 2 documents use DAG-based parallel execution
- **Async Support**: Phase 2 agents have native async support
- **WebSocket**: Real-time progress updates (falls back to polling if WebSocket fails)
- **Database**: SQLite for project context and status (stateless web app)
- **Error Handling**: Comprehensive retry logic and fallbacks

