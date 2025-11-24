# OmniDoc

AI-powered documentation generation system that creates comprehensive documentation from simple user ideas using multi-agent collaboration.

## 🎯 What is OmniDoc?

OmniDoc is an intelligent documentation generator that takes your project idea and automatically creates a complete set of professional documents including:

- **Requirements & Planning**: Requirements documents, project charters, user stories
- **Business Documents**: Business models, marketing plans, stakeholder communications
- **Technical Documentation**: Technical specs, API documentation, database schemas
- **Developer Resources**: Developer guides, test documentation, setup guides
- **User Documentation**: User guides, support playbooks, legal compliance

All generated from a simple description of your project idea!

### ✨ Key Features

- **🤖 Multi-Agent Collaboration**: Specialized AI agents work together to generate comprehensive documentation
- **✅ Quality Assurance**: Automatic quality review and improvement workflow ensures high-quality output
- **📊 Configurable Quality Rules**: Document-type-specific quality rules via `quality_rules.json`
- **🔄 Context Sharing**: Agents share project context for consistent, coherent documentation
- **⚡ Real-time Updates**: WebSocket-based progress tracking during document generation
- **🌍 Multi-language Support**: Frontend supports English, Chinese, Japanese, Korean, and Spanish

## 📋 Table of Contents

- [What is OmniDoc?](#-what-is-omnidoc)
- [Quick Start](#-quick-start)
- [Testing](#testing)
- [Monitoring](#monitoring)
- [Features](#-features)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Usage Examples](#-usage-examples)
- [Configuration](#-configuration)
- [Troubleshooting](#-troubleshooting)
- [Documentation](#-documentation)

## 🚀 Quick Start

> **💡 Production Deployment**: Frontend is deployed on [Vercel](https://vercel.com), backend on [Railway](https://railway.app). See [Railway Deployment](RAILWAY_DEPLOYMENT.md) and [Vercel Deployment](VERCEL_DEPLOYMENT.md) for details.

### 1. Prerequisites

- **Python 3.9+**
- **Node.js 18+** (for frontend)
- **PostgreSQL** (database) - **Recommended: Use [Neon](https://neon.tech) (free managed PostgreSQL)** or local PostgreSQL
- **Redis** (for task queue and caching) - **Recommended: Use [Upstash](https://upstash.com) (free managed Redis)** or local Redis

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd OmniDoc

# Run the setup script (installs everything)
./scripts/setup.sh
```

The setup script will:
- ✅ Check all prerequisites
- ✅ Set up Python backend environment
- ✅ Install frontend dependencies
- ✅ Configure database (local PostgreSQL or Neon)
- ✅ Create `.env` file with defaults

**💡 Tip**: For production, use [Neon](https://neon.tech) for managed PostgreSQL - it's free and saves server memory! See [Neon Setup Guide](NEON_SETUP.md)

### 3. Configuration

Edit `.env` file and add your API keys:

```bash
# Required: LLM Provider
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here

# Database
# Option 1: Local PostgreSQL (auto-configured by setup script)
DATABASE_URL=postgresql://localhost/omnidoc

# Option 2: Neon (recommended for production - free managed PostgreSQL)
# Get connection string from: https://console.neon.tech
# DATABASE_URL=postgresql://user:password@ep-xxx.region.neon.tech/dbname?sslmode=require

# Redis (auto-configured by setup script)
REDIS_URL=redis://localhost:6379/0
```

**Get your Gemini API key:** [Google AI Studio](https://aistudio.google.com/app/apikey)

### 4. Start the Application

**Terminal 1 - Backend Server:**
```bash
python backend/uvicorn_dev.py
# Server runs at http://localhost:8000
```

**Terminal 2 - Celery Worker (for background tasks):**
```bash
./scripts/start_celery_worker.sh
```

**Terminal 3 - Frontend (for development):**
```bash
cd frontend
pnpm dev  # or npm run dev
# Frontend runs at http://localhost:3000
```

### 5. Use the Application

- **Web Interface**: Visit `http://localhost:3000` (development) or `https://omnidoc.info` (production)
- **API**: Visit `http://localhost:8000/docs` for interactive API documentation (development) or `https://api.omnidoc.info/docs` (production)

**Production URLs:**
- Frontend: `https://omnidoc.info`
- API: `https://api.omnidoc.info`

## 📚 Documentation

All documentation is organized in the `docs/` directory:

### Core Documentation
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture and design
- **[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)** - Development guide and best practices
- **[docs/DEPENDENCIES.md](docs/DEPENDENCIES.md)** - Document dependencies reference
- **[docs/UI_GUIDE.md](docs/UI_GUIDE.md)** - UI development guide and improvements
- **[docs/PERFORMANCE.md](docs/PERFORMANCE.md)** - Performance optimization guide
- **[docs/CHANGELOG.md](docs/CHANGELOG.md)** - Recent changes and improvements

### Testing
- **[tests/README.md](tests/README.md)** - Testing guide and test structure

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend  │─────▶│  FastAPI App │─────▶│  PostgreSQL │
│  (Next.js)  │      │   (Port 8000)│      │   Database  │
└─────────────┘      └──────────────┘      └─────────────┘
                             │
                             ▼
                      ┌──────────────┐
                      │    Redis      │
                      │  (Broker +    │
                      │   Cache)      │
                      └──────────────┘
                             │
                             ▼
                      ┌──────────────┐
                      │ Celery Worker │
                      │ (Background   │
                      │   Tasks)      │
                      └──────────────┘
```

## ✨ Key Features

### 🤖 Multi-Agent System
- **21+ Specialized Agents**: Each agent specializes in a specific document type
- **Intelligent Workflow**: Sequential approval for strategic docs, parallel execution for technical docs
- **Context Sharing**: Agents share project context via ContextManager for consistent documentation
- **Quality Assurance**: Automatic quality review and improvement workflow
  - Quality Reviewer Agent checks each document (score 1-10)
  - Document Improver Agent enhances documents below quality threshold (< 7.0)
  - Configurable quality rules via `src/config/quality_rules.json`

### 🔄 Production-Ready Infrastructure
- **PostgreSQL Database**: Robust, scalable database (migrated from SQLite)
- **Celery Task Queue**: Background job processing with Redis
- **Redis Caching**: Fast caching for better performance
- **JWT Authentication**: Ready for user authentication (infrastructure in place)

### 🌐 Multiple LLM Providers
- **Gemini** (default): Google's powerful models
- **Ollama**: Local models for privacy and speed
- **OpenAI**: GPT models support

### 📊 Real-Time Progress
- **WebSocket Updates**: Real-time progress tracking
- **Automatic Fallback**: Falls back to HTTP polling if WebSocket fails

## 📋 Project Structure

```
OmniDoc/
├── src/                    # Source code
│   ├── agents/            # Documentation agents
│   ├── auth/              # Authentication (JWT, OAuth2)
│   ├── config/            # Configuration management
│   ├── context/           # Database context (PostgreSQL)
│   ├── coordination/      # Workflow orchestration
│   ├── llm/               # LLM provider abstractions
│   ├── quality/           # Quality checking
│   ├── tasks/             # Celery background tasks
│   ├── utils/             # Utilities (cache, parsers, etc.)
│   └── web/               # FastAPI web application
├── frontend/              # Next.js frontend
├── docs/                  # Generated documentation output
├── scripts/               # Setup and utility scripts
│   ├── setup.sh           # Main setup script
│   └── start_celery_worker.sh  # Celery worker starter
├── config/                # Configuration files
│   └── document_definitions.json  # Document catalog
├── .env                   # Environment configuration
├── pyproject.toml         # Python dependencies
└── README.md              # This file
```

## 🔧 Configuration

### Environment Variables

See `.env` file for all configuration options. Key settings:

```bash
# LLM Provider
LLM_PROVIDER=gemini  # Options: gemini, ollama, openai
GEMINI_API_KEY=your_key_here

# Database
DATABASE_URL=postgresql://localhost/omnidoc

# Redis
REDIS_URL=redis://localhost:6379/0

# Authentication (optional)
JWT_SECRET_KEY=your-secret-key
GOOGLE_CLIENT_ID=your_google_client_id
GITHUB_CLIENT_ID=your_github_client_id
```

## 🎯 Usage Examples

### Using the Web Interface

1. Start backend and frontend
2. Visit `http://localhost:3000`
3. Enter your project idea
4. Select documents to generate
5. Watch real-time progress
6. Download generated documents

### Using the API

```bash
# Create a project
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "user_idea": "Build a task management app",
    "selected_documents": ["requirements", "technical_doc", "api_doc"]
  }'

# Check project status
curl http://localhost:8000/api/projects/{project_id}/status

# Get generated documents
curl http://localhost:8000/api/projects/{project_id}/documents
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Unit tests only
pytest tests/unit

# Integration tests
pytest tests/integration

# With coverage
pytest --cov=src --cov-report=html
```

## 🛠️ Development

### Setup Development Environment

```bash
./scripts/setup.sh
```

### Code Quality

```bash
# Format code
black src tests

# Lint code
ruff check src tests
```

## 🐛 Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
pg_isready

# Verify database exists
psql -l | grep omnidoc

# Test connection
psql $DATABASE_URL -c "SELECT 1;"
```

### Redis Connection Issues

```bash
# Check Redis is running
redis-cli ping  # Should return PONG

# Test connection
redis-cli info
```

### Celery Worker Not Processing

```bash
# Check Celery worker status
celery -A src.tasks.celery_app inspect active

# Check worker logs
celery -A src.tasks.celery_app worker --loglevel=debug
```

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for more troubleshooting tips.

## 📦 Dependencies

### Backend
- FastAPI - Web framework
- Celery - Task queue
- PostgreSQL (psycopg2) - Database
- Redis - Cache and broker
- Multiple LLM providers (Gemini, Ollama, OpenAI)

### Frontend
- Next.js 16 - React framework
- TypeScript - Type safety
- Tailwind CSS - Styling
- SWR - Data fetching

See `pyproject.toml` and `frontend/package.json` for complete dependency lists.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with multi-agent collaboration
- Supports multiple LLM providers
- Production-ready infrastructure
- Designed for comprehensive documentation generation

---

**Need Help?** Check out:
- [Architecture Documentation](docs/ARCHITECTURE.md) - System design and components
- [Development Guide](docs/DEVELOPMENT.md) - Development best practices
- [UI Guide](docs/UI_GUIDE.md) - UI development guidelines
- [Performance Guide](docs/PERFORMANCE.md) - Optimization strategies
- [API Documentation](http://localhost:8000/docs) (when server is running)
