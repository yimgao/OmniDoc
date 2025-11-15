# Backend Documentation

Complete guide to the OmniDoc backend architecture, API, and configuration.

## 🏗️ Architecture

The backend is built with **FastAPI** and follows a multi-agent architecture:

```
┌─────────────────┐
│   FastAPI App   │  (src/web/app.py)
│   Port 8000     │
└────────┬────────┘
         │
    ┌────┴────┬──────────────┬─────────────┐
    │         │              │             │
    ▼         ▼              ▼             ▼
┌────────┐ ┌──────────┐ ┌─────────┐ ┌──────────┐
│PostgreSQL│ │  Redis  │ │ Celery │ │   LLM    │
│ Database │ │ (Cache) │ │ Worker │ │ Providers│
└────────┘ └──────────┘ └─────────┘ └──────────┘
```

## 📁 Project Structure

```
src/
├── agents/              # AI agent implementations
│   ├── base_agent.py    # Base agent class
│   ├── generic_document_agent.py
│   ├── requirements_analyst.py
│   └── ...
├── auth/                # Authentication
│   ├── jwt_auth.py     # JWT token management
│   └── oauth2.py       # OAuth2 providers
├── config/              # Configuration
│   ├── settings.py     # Environment settings
│   ├── document_catalog.py  # Document definitions
│   └── quality_rules.json   # Quality rules for each document type
├── context/             # Shared context
│   ├── context_manager.py  # PostgreSQL database manager
│   └── shared_context.py   # Data models
├── coordination/        # Workflow coordination
│   ├── coordinator.py  # WorkflowCoordinator
│   └── workflow_dag.py # Dependency graph
├── llm/                # LLM providers
│   ├── gemini_provider.py
│   ├── openai_provider.py
│   └── ollama_provider.py
├── quality/            # Quality checking
│   ├── quality_checker.py  # Base quality checker
│   └── document_type_quality_checker.py  # Document-type-aware quality checker
├── rate_limit/         # Rate limiting
├── tasks/              # Celery tasks
│   ├── celery_app.py  # Celery configuration
│   └── generation_tasks.py
├── utils/              # Utilities
│   ├── cache.py       # Redis caching
│   ├── logger.py      # Logging
│   └── ...
└── web/                # FastAPI application
    └── app.py         # Main API application
```

## 🚀 Getting Started

### Option 1: Using the Development Script (Recommended)

```bash
python3 backend/uvicorn_dev.py
```

The server will start at `http://localhost:8000` with auto-reload enabled.

### Option 2: Using uvicorn Directly

```bash
uvicorn src.web.app:app --reload --host 0.0.0.0 --port 8000
```

### Option 3: Using uv

```bash
uv run python -m uvicorn src.web.app:app --reload --host 0.0.0.0 --port 8000
```

### Prerequisites

- Python 3.9+
- PostgreSQL 12+
- Redis 6+
- LLM API key (Gemini, OpenAI, or Ollama)

### Installation

```bash
# Run setup script
./scripts/setup.sh

# Or manually
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Required Services

1. **PostgreSQL Database**
   ```bash
   # Install PostgreSQL
   # Ubuntu/Debian:
   sudo apt-get install postgresql
   # macOS:
   brew install postgresql
   
   # Create database
   createdb omnidoc
   ```

2. **Redis** (for Celery and caching)
   ```bash
   # Install Redis
   # Ubuntu/Debian:
   sudo apt-get install redis-server
   # macOS:
   brew install redis
   
   # Start Redis
   sudo systemctl start redis  # Linux
   brew services start redis   # macOS
   ```

### Configuration

Create `.env` file:

```bash
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/omnidoc

# Redis
REDIS_URL=redis://localhost:6379/0

# LLM Provider
LLM_PROVIDER=gemini  # Options: gemini, openai, ollama
GEMINI_API_KEY=your_key_here

# Security
JWT_SECRET_KEY=your-secret-key-here
ENVIRONMENT=dev  # or prod

# CORS
ALLOWED_ORIGINS=http://localhost:3000
```

### Running the Server

```bash
# Development (with auto-reload)
python backend/uvicorn_dev.py

# Production
uvicorn src.web.app:app --host 0.0.0.0 --port 8000 --workers 4
```

### Running Celery Worker

```bash
./scripts/start_celery_worker.sh

# Or manually
celery -A src.tasks.celery_app worker --loglevel=info
```

## 📡 API Endpoints

### Document Templates

**GET** `/api/document-templates`
- Get all available document templates
- Cached for 24 hours
- Response: `DocumentCatalogResponse`

### Projects

**POST** `/api/projects`
- Create a new project
- Status: `202 Accepted`
- Body: `ProjectCreateRequest`
- Response: `ProjectCreateResponse`

**GET** `/api/projects/{project_id}/status`
- Get project status
- Response: `ProjectStatusResponse`

**GET** `/api/projects/{project_id}/documents`
- List all generated documents
- Response: `ProjectDocumentsResponse`

**GET** `/api/projects/{project_id}/documents/{document_id}`
- Get specific document content
- Response: `GeneratedDocument`

**GET** `/api/projects/{project_id}/documents/{document_id}/download`
- Download document as file
- Response: `FileResponse`

### WebSocket

**WS** `/ws/{project_id}`
- Real-time progress updates
- Messages: `connected`, `progress`, `complete`, `error`

## 🔧 Core Components

### ContextManager

Manages PostgreSQL database operations:

```python
from src.context.context_manager import ContextManager

context = ContextManager()
context.create_project(project_id, user_idea)
context.update_project_status(project_id, status="complete")
status = context.get_project_status(project_id)
```

**Key Methods:**
- `create_project()` - Create new project
- `get_project_status()` - Get project status
- `update_project_status()` - Update project status
- `save_requirements()` - Save requirements document
- `save_agent_output()` - Save agent output

### WorkflowCoordinator

Orchestrates document generation:

```python
from src.coordination.coordinator import WorkflowCoordinator

coordinator = WorkflowCoordinator(context_manager=context)
results = await coordinator.async_generate_all_docs(
    user_idea="Build a task app",
    project_id="project_123",
    selected_documents=["requirements", "technical_doc"]
)
```

**Features:**
- Dependency resolution
- Parallel execution
- Progress callbacks
- Error handling
- **Quality Review & Improvement**: Automatic quality review and enhancement workflow
  - Each document is reviewed by Quality Reviewer Agent (score 1-10)
  - Documents scoring < 7.0 are automatically improved by Document Improver Agent
  - Uses configurable quality rules from `src/config/quality_rules.json`
- **Context Sharing**: Agents share project context via ContextManager
  - Requirements are parsed and stored in database
  - All agents can access structured project context
  - Ensures consistency across all generated documents

### Celery Tasks

Background task processing:

```python
from src.tasks.generation_tasks import generate_documents_task

# Submit task
task = generate_documents_task.delay(
    project_id="project_123",
    user_idea="Build a task app",
    selected_documents=["requirements"]
)

# Check status
task.status  # PENDING, STARTED, SUCCESS, FAILURE
```

### Redis Caching

Caching utilities:

```python
from src.utils.cache import cache_result, get_cached, set_cached

# Decorator
@cache_result(ttl=3600)
def expensive_function():
    return result

# Manual caching
set_cached("key", value, ttl=3600)
value = get_cached("key")
```

### Quality Reviewer Agent

Reviews document quality and generates structured feedback:

```python
from src.agents.quality_reviewer_agent import QualityReviewerAgent

reviewer = QualityReviewerAgent(provider_name="gemini")

# Generate structured feedback (LLM-as-Judge)
feedback = reviewer.generate_structured_feedback(
    document_content=content,
    document_type="project_charter",
    automated_scores=automated_scores
)

# Returns: {
#   "score": 7.5,  # 1-10 scale
#   "feedback": "...",
#   "suggestion": "...",
#   "missing_sections": [...],
#   "weaknesses": [...],
#   "priority_improvements": [...]
# }
```

### Document Improver Agent

Improves documents based on quality feedback:

```python
from src.agents.document_improver_agent import DocumentImproverAgent

improver = DocumentImproverAgent(provider_name="gemini")

# Improve document
improved_content = improver.improve_document(
    original_document=original,
    document_type="project_charter",
    quality_feedback=feedback_text,
    structured_feedback=structured_feedback_dict
)
```

**Improvement Strategy:**
- Preserves all original content and structure
- Adds missing sections with substantial content
- Expands existing sections with more detail
- Addresses identified weaknesses
- Maintains document consistency

## 🔐 Authentication

### JWT Authentication

```python
from src.auth.jwt_auth import create_access_token, verify_token

# Create token
token = create_access_token(data={"user_id": "123"})

# Verify token
payload = verify_token(token)
```

### OAuth2 Providers

```python
from src.auth.oauth2 import verify_google_token, verify_github_token

# Verify Google token
user_info = await verify_google_token(access_token)

# Verify GitHub token
user_info = await verify_github_token(access_token)
```

## 🗄️ Database Schema

### Projects Table

```sql
CREATE TABLE projects (
    project_id VARCHAR(255) PRIMARY KEY,
    user_idea TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

### Project Status Table

```sql
CREATE TABLE project_status (
    project_id VARCHAR(255) PRIMARY KEY,
    status VARCHAR(50) NOT NULL,
    user_idea TEXT,
    profile VARCHAR(50),
    provider_name VARCHAR(100),
    completed_agents TEXT,  -- JSON array
    results TEXT,            -- JSON object
    selected_documents TEXT, -- JSON array
    error TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);
```

### Requirements Table

```sql
CREATE TABLE requirements (
    project_id VARCHAR(255) PRIMARY KEY,
    user_idea TEXT NOT NULL,
    project_overview TEXT,
    core_features TEXT,  -- JSON array
    technical_requirements TEXT,  -- JSON object
    user_personas TEXT,  -- JSON array
    business_objectives TEXT,  -- JSON array
    constraints TEXT,  -- JSON array
    assumptions TEXT,  -- JSON array
    generated_at TIMESTAMP NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);
```

## 🔄 Task Queue (Celery)

### Configuration

Celery is configured in `src/tasks/celery_app.py`:

```python
from celery import Celery

celery_app = Celery(
    "omnidoc",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)
```

### Task Definition

```python
@celery_app.task
def generate_documents_task(project_id, user_idea, selected_documents):
    # Task implementation
    pass
```

### Monitoring

```bash
# Check active tasks
celery -A src.tasks.celery_app inspect active

# Check registered tasks
celery -A src.tasks.celery_app inspect registered

# Monitor in real-time
celery -A src.tasks.celery_app events
```

## 📊 Logging

Logs are written to `logs/` directory:

```python
from src.utils.logger import get_logger

logger = get_logger(__name__)
logger.info("Message")
logger.error("Error message", exc_info=True)
```

**Log Levels:**
- `DEBUG` - Detailed information
- `INFO` - General information
- `WARNING` - Warning messages
- `ERROR` - Error messages
- `CRITICAL` - Critical errors

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_web_app.py
```

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Kill the process using port 8000
lsof -ti:8000 | xargs kill -9

# Or use a different port
BACKEND_PORT=8001 python3 backend/uvicorn_dev.py
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
pg_isready

# Verify database exists
psql -l | grep omnidoc

# Test connection
psql $DATABASE_URL -c "SELECT 1;"

# Check PostgreSQL status
sudo systemctl status postgresql

# View connection logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

### Redis Connection Issues

```bash
# Check Redis is running
redis-cli ping  # Should return PONG

# Test connection
redis-cli info

# With password
redis-cli -a your_password ping

# Check Redis status
sudo systemctl status redis-server

# Monitor Redis
redis-cli -a your_password monitor
```

### Celery Worker Not Processing Tasks

```bash
# Check if Redis is running
redis-cli ping

# Check Celery worker logs
celery -A src.tasks.celery_app worker --loglevel=debug

# Check active tasks
celery -A src.tasks.celery_app inspect active

# Check worker status
celery -A src.tasks.celery_app inspect active

# View worker logs
celery -A src.tasks.celery_app worker --loglevel=debug

# Restart worker
pkill -f "celery.*worker"
./scripts/start_celery_worker.sh
```

### Missing Dependencies

```bash
# Install dependencies
./scripts/setup.sh

# Or manually
pip install -r requirements.txt
# Or with uv
uv sync --all-extras
```

### Configuration File Not Found

```bash
# Generate document definitions from CSV
python3 scripts/csv_to_document_json.py \
  --input JobTrackrAI_Document_Management_Template_v3.csv \
  --output config/document_definitions.json
```

### Quality Rules Configuration

Quality rules are configured in `src/config/quality_rules.json`. This file defines quality requirements for each document type:

**File Structure:**
```json
{
  "Document Name": {
    "min_word_count": 600,
    "required_sections": ["Section 1", "Section 2"],
    "optional_sections": ["Optional Section"],
    "readability_target": "50-65",
    "llm_focus": ["Question 1?", "Question 2?"],
    "auto_fail": ["Critical condition 1"]
  }
}
```

**Fields:**
- `min_word_count`: Minimum word count threshold
- `required_sections`: Array of required section headings
- `optional_sections`: Recommended but not required sections
- `readability_target`: Target readability range (e.g., "50-65")
- `llm_focus`: Questions for LLM to focus on during quality review
- `auto_fail`: Conditions that automatically fail the document

**To customize:**
1. Edit `src/config/quality_rules.json`
2. Add or modify document type entries
3. Restart backend server (rules are loaded on startup)

See [docs/QUALITY_SCORING.md](docs/QUALITY_SCORING.md) for detailed documentation.

## 📚 Additional Resources

- [Production Deployment](PRODUCTION_SETUP.md)
- [Deployment Strategy](DEPLOYMENT_STRATEGY.md) - When to deploy vs. update
- [Security Guide](SECURITY.md)
- [Maintenance Guide](MAINTENANCE.md)
- [API Documentation](http://localhost:8000/docs) (when server is running)
- [Swagger UI](http://localhost:8000/docs) - Interactive API documentation
- [ReDoc](http://localhost:8000/redoc) - Alternative API documentation

