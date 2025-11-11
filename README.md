# OmniDoc (DOCU-GEN)

AI-powered documentation generation system that creates comprehensive documentation from simple user ideas using multi-agent collaboration. Uses **Google Gemini** for all agents to ensure high-quality documentation generation.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Clone the repository
git clone <repository-url>
cd OmniDoc

# Run setup script (uses uv to sync from pyproject.toml)
./scripts/setup.sh
```

The setup script will:
- Create a virtual environment (`.venv`)
- Install all dependencies from `pyproject.toml`
- Verify installation
- Support both `uv` (recommended) and `pip` fallback

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and configure your Gemini API key
```

**Required Configuration:**
```bash
# In .env file
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Use a different Gemini model (default: gemini-2.0-flash)
GEMINI_DEFAULT_MODEL=gemini-2.0-flash
# Options: gemini-2.0-flash (recommended), gemini-2.5-flash, gemini-2.5-pro
```

**Get Your Gemini API Key:**
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the key to your `.env` file

### 3. Generate Documentation

```bash
# Using CLI
uv run python -c "
from src.coordination.coordinator import WorkflowCoordinator
coordinator = WorkflowCoordinator()
coordinator.generate_all_docs('Build a task management app')
"

# Or use web interface
uv run python -m src.web.app
# Visit http://localhost:8000
```

## 📋 Features

### Core Capabilities

- **21 Documentation Agents**: Requirements, PM, Technical, API, Developer, Stakeholder, User, Test, Quality Review, Format Converter, Business Model, Marketing Plan, Legal Compliance, Database Schema, Setup Guide, User Stories, Support Playbook, and more
- **Hybrid Workflow**: 
  - **Phase 1 (Quality Gates)**: Foundational documents use iterative quality loops (generate → check → improve) to ensure maximum quality
  - **Phase 2 (Parallel Execution)**: Secondary documents generated in parallel using DAG-based async execution (3x faster)
  - **Phase 3 (Final Packaging)**: Cross-referencing, quality review, and format conversion
  - **Phase 4 (Code Analysis)**: Optional codebase analysis and documentation updates
- **LLM Provider**: 
  - **Google Gemini** (all agents) - High-quality cloud-based LLM
  - **Default Model**: `gemini-2.0-flash` (balanced quality and speed)
  - **Configurable**: Support for `gemini-2.5-flash` and `gemini-2.5-pro` via environment variable
- **Format Conversion**: Outputs Markdown, HTML, PDF, DOCX
- **Quality Assurance**: Automated quality checks with document-type-specific criteria
- **Parallel Execution**: Async parallel execution with DAG-based dependencies (3x speedup)
- **Web Interface**: FastAPI web app with real-time progress tracking via WebSocket
- **Error Handling**: Retry logic with exponential backoff
- **Document Templates**: Jinja2-based customizable templates
- **Cross-Referencing**: Automatic linking between documents
- **Intelligent Parsing**: Structured data extraction from requirements
- **Context Management**: SQLite-based shared context across agents (stateless web app)
- **Rate Limiting**: Built-in rate limiting and caching
- **WebSocket Support**: Real-time progress updates (falls back to polling if WebSocket fails)

### LLM Provider Features

- **Gemini Provider** (All Agents):
  - **Default Model**: `gemini-2.0-flash` (recommended balance of quality and speed)
  - **Alternative Models**: `gemini-2.5-flash` (higher quality), `gemini-2.5-pro` (highest quality)
  - **Rate Limit Handling**: Automatic retry with exponential backoff
  - **Token Limits**: 1M TPM (tokens per minute), 15 RPM (requests per minute), 200 RPD (requests per day) on free tier
  - **High-Quality Output**: Optimized for complex documentation tasks
  - **Configurable**: Set `GEMINI_DEFAULT_MODEL` environment variable to use a different model

## 🏗️ Project Structure

```
OmniDoc/
├── src/                    # Source code
│   ├── agents/            # Documentation agents (20+ agents)
│   ├── context/           # Shared context management (SQLite)
│   ├── coordination/      # Workflow orchestration (Hybrid Workflow)
│   ├── llm/               # LLM provider abstractions
│   │   ├── base_provider.py
│   │   ├── ollama_provider.py    # Ollama local LLM
│   │   ├── gemini_provider.py    # Google Gemini
│   │   ├── openai_provider.py    # OpenAI GPT
│   │   └── provider_factory.py
│   ├── quality/           # Quality checking (document-type-aware)
│   ├── rate_limit/        # Rate limiting & caching
│   ├── utils/             # Utilities (parsers, templates, etc.)
│   └── web/               # Web interface (FastAPI)
├── tests/                 # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── e2e/               # End-to-end tests
├── docs/                  # Generated documentation
├── templates/             # Document templates (Jinja2)
├── prompts/               # System prompts (editable)
├── scripts/               # Setup and utility scripts
│   └── setup.sh           # Main setup script
├── examples/              # Usage examples
├── .env.example           # Environment template
├── pyproject.toml         # Project configuration
└── README.md              # This file
```

## 🔧 Configuration

### Environment Variables

**Required Configuration:**

**Gemini API Key:**
- `GEMINI_API_KEY`: **Required** - Your Google Gemini API key
  - Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

**Optional Configuration:**

**Gemini Model:**
- `GEMINI_DEFAULT_MODEL`: Gemini model to use (default: `gemini-2.0-flash`)
  - Options: `gemini-2.0-flash` (recommended), `gemini-2.5-flash`, `gemini-2.5-pro`
  - `gemini-2.0-flash`: Best balance (15 RPM, 1M TPM, 200 RPD)
  - `gemini-2.5-flash`: Higher quality (10 RPM, 250K TPM, 250 RPD)
  - `gemini-2.5-pro`: Highest quality (2 RPM, 125K TPM, 50 RPD)

**Temperature Control:**
- `TEMPERATURE`: Global temperature (default: `0.3`)
- `GEMINI_TEMPERATURE`: Gemini-specific temperature (default: `0.7`)

**Document Summarization:**
- `MAX_SUMMARY_LENGTH`: Maximum summary length in characters (default: `3000`)

**Application Settings:**
- `ENVIRONMENT`: Environment mode (`dev`, `prod`, `test`)
- `LOG_LEVEL`: Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`)
- `DOCS_DIR`: Output directory for generated docs (default: `docs/`)
- `RATE_LIMIT_PER_MINUTE`: Rate limit for API calls (default: `50`)

**Note**: All agents use Gemini (hardcoded). Environment variables for other providers are ignored.

### Model Configuration

**All agents use Gemini** (hardcoded for consistency and quality). You can configure which Gemini model to use:

#### Method 1: Environment Variable (Recommended)

```bash
# In .env file
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_DEFAULT_MODEL=gemini-2.0-flash  # Optional: default is gemini-2.0-flash
```

#### Method 2: Code Override

```python
from src.coordination.coordinator import WorkflowCoordinator

# All agents will use Gemini (default model: gemini-2.0-flash)
coordinator = WorkflowCoordinator()

# To use a different model, set GEMINI_DEFAULT_MODEL environment variable
# or modify the default in src/llm/gemini_provider.py
```

#### Available Models

| Model | Quality | RPM | TPM | RPD | Best For |
|-------|---------|-----|-----|-----|----------|
| `gemini-2.0-flash` | ⭐⭐⭐⭐ | 15 | 1M | 200 | **Recommended** - Balanced quality and speed |
| `gemini-2.5-flash` | ⭐⭐⭐⭐⭐ | 10 | 250K | 250 | Higher quality, slower |
| `gemini-2.5-pro` | ⭐⭐⭐⭐⭐ | 2 | 125K | 50 | Highest quality, very slow |

**Recommendation**: Use `gemini-2.0-flash` for best balance of quality and speed.

## 🎯 Usage Examples

### Generate All Documentation

```bash
# Using CLI
uv run python -c "
from src.coordination.coordinator import WorkflowCoordinator
coordinator = WorkflowCoordinator()
results = coordinator.generate_all_docs('Build a blog platform with user authentication')
"
```

Or in a Python script:
```python
from src.coordination.coordinator import WorkflowCoordinator

coordinator = WorkflowCoordinator()
results = coordinator.generate_all_docs(
    user_idea="Build a blog platform with user authentication",
    profile="team"  # or "individual"
)

# Generates 20+ document types using Hybrid Workflow:
# Phase 1 (Quality Gates):
# - Requirements (iterative quality loop)
# - Project Charter (team only, iterative quality loop)
# - User Stories (iterative quality loop)
# - Technical Specification (iterative quality loop)
#
# Phase 2 (Parallel Execution):
# - API Documentation
# - Database Schema
# - Setup Guide
# - Developer Guide
# - Test Plan
# - User Guide
# - Legal Compliance
# - PM Plan (team only)
# - Stakeholder Summary (team only)
# - Business Model (team only)
# - Marketing Plan (team only)
# - Support Playbook
#
# Phase 3 (Final Packaging):
# - Cross-referencing
# - Quality Review
# - Format conversions (HTML, PDF, DOCX)
```

### Use Web Interface

```bash
# Start the web server
uv run python -m src.web.app

# Visit http://localhost:8000
# Enter your project idea and generate docs!
```

### Multiple Provider Example

See [examples/multi_provider_example.py](examples/multi_provider_example.py) for examples of using different providers.

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Unit tests only (fast)
uv run pytest tests/unit

# Integration tests
uv run pytest tests/integration

# E2E tests (requires API key or Ollama)
uv run pytest tests/e2e

# With coverage
uv run pytest --cov=src --cov-report=html
```

**Current Status:** 100+ tests, 82% code coverage

## 🛠️ Development

### Setup Development Environment

```bash
# Install with dev dependencies
uv sync --all-extras

# Or use setup script
./scripts/setup.sh
```

### Running the Application

```bash
# Activate virtual environment (if not using uv run)
source .venv/bin/activate

# Or use uv run (recommended)
uv run python -m src.web.app
```

### Code Quality

```bash
# Format code
uv run black src tests

# Lint code
uv run ruff check src tests

# Type checking (if using mypy)
uv run mypy src
```

## 🔍 Troubleshooting

### Gemini API Key Issues

```bash
# Verify your API key is set
echo $GEMINI_API_KEY

# Or check .env file
cat .env | grep GEMINI_API_KEY

# Get a new API key from Google AI Studio
# Visit: https://makersuite.google.com/app/apikey
```

### Gemini Rate Limit Errors

If you see rate limit errors:

1. **Check your usage**: Visit [Google AI Studio](https://makersuite.google.com/app/apikey) to check your rate limit usage
2. **Wait and retry**: The system automatically retries with exponential backoff
3. **Use a different model**: Switch to `gemini-2.5-flash` (10 RPM) or `gemini-2.5-pro` (2 RPM) if you're hitting limits
4. **Reduce rate limit**: Set `RATE_LIMIT_PER_MINUTE=30` in `.env` to stay well below limits

### Gemini API Errors

If you see API errors:

1. **Check API key**: Verify your `GEMINI_API_KEY` is valid
2. **Check model availability**: Ensure the model name is correct (e.g., `gemini-2.0-flash`)
3. **Check rate limits**: Visit [Google AI Studio](https://makersuite.google.com/app/apikey) to check your quota
4. **Review logs**: Check application logs for detailed error messages

### Low Quality Scores

If generated documents have low quality scores:

1. **Use a better model**: Switch to `gemini-2.5-flash` or `gemini-2.5-pro` via `GEMINI_DEFAULT_MODEL`
2. **Adjust temperature**: Lower temperature (0.3) for more consistent output
3. **Quality gates**: Phase 1 documents automatically improve if quality is below threshold
4. **Check prompts**: Review system prompts in `src/prompts/system_prompts.py`

### WebSocket Connection Issues

If WebSocket fails to connect:

1. **Check WebSocket support**: Ensure `websockets` package is installed (`uv sync`)
2. **Fallback to polling**: The system automatically falls back to HTTP polling if WebSocket fails
3. **Check browser console**: Look for WebSocket connection errors in browser console
4. **Verify server**: Ensure the server is running and accessible

## 📦 Dependencies

### Core Dependencies
- `google-generativeai>=0.3.0` - Gemini provider (required)
- `fastapi>=0.100.0` - Web framework
- `uvicorn>=0.23.0` - ASGI server
- `websockets>=12.0` - WebSocket support for real-time updates
- `python-dotenv>=1.0.0` - Environment variables
- `jinja2>=3.1.2` - Template engine
- `pydantic>=2.0.0` - Data validation
- `markdown>=3.5.0` - Markdown processing
- `weasyprint>=60.0` - PDF generation
- `python-docx>=1.1.0` - DOCX generation
- `aiohttp>=3.9.0` - Async HTTP client
- `requests>=2.31.0` - HTTP client

See [pyproject.toml](pyproject.toml) for complete dependency list.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `uv run pytest`
5. Submit a pull request

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with multi-agent collaboration
- Supports multiple LLM providers for flexibility
- Designed for comprehensive documentation generation
- Hybrid workflow ensures both quality and speed

---

**Note:** This project uses `uv` to manage dependencies from `pyproject.toml`. 
- Use `uv run <command>` to run commands in the project environment
- No need to activate virtual environment manually
- Dependencies are managed via `pyproject.toml`

## 🎯 Key Features

### All Agents Use Gemini
- **Hardcoded**: All 21 agents use Gemini (cannot be changed via environment variables)
- **Default Model**: `gemini-2.0-flash` (balanced quality and speed)
- **Configurable**: Set `GEMINI_DEFAULT_MODEL` environment variable to use a different model
- **Benefits**: Consistent quality, no local model dependencies, cloud-based scalability

### Hybrid Workflow
- **Phase 1**: Quality gates with iterative improvement for foundational documents
- **Phase 2**: Parallel execution with DAG-based dependencies for maximum speed
- **Phase 3**: Final packaging with cross-referencing and format conversion
- **Phase 4**: Optional code analysis and documentation updates

### Real-Time Progress Updates
- **WebSocket**: Real-time progress updates via WebSocket
- **Fallback**: Automatic fallback to HTTP polling if WebSocket fails
- **Progress Tracking**: Phase-based progress tracking (Phase 1: 25%, Phase 2: 60%, Phase 3: 85%)

### Quality Assurance
- **Document-Type-Specific**: Quality checks tailored to each document type
- **Automatic Improvement**: Low-quality documents are automatically improved
- **Quality Thresholds**: Configurable quality thresholds for each document type
- **Quality Reports**: Comprehensive quality reports for all documents

## 📚 Additional Resources

- **Workflow Documentation**: See [WORKFLOW_DOCUMENTATION.md](WORKFLOW_DOCUMENTATION.md) for detailed workflow documentation
- **Configuration Guide**: See [src/config/README.md](src/config/README.md) for detailed configuration options
- **Examples**: See [examples/](examples/) directory for usage examples
- **Generated Docs**: See [docs/](docs/) directory for generated documentation index

## 🔄 Workflow Overview

DOCU-GEN uses a **Hybrid Workflow** that combines quality gates with parallel execution:

1. **Phase 1 (Quality Gates)**: Foundational documents (Requirements, Project Charter, User Stories, Technical Documentation) are generated with iterative quality loops to ensure maximum quality
2. **Phase 2 (Parallel Execution)**: Secondary documents are generated in parallel using DAG-based async execution for maximum speed
3. **Phase 3 (Final Packaging)**: Cross-referencing, quality review, and format conversion
4. **Phase 4 (Code Analysis)**: Optional codebase analysis and documentation updates

See [WORKFLOW_DOCUMENTATION.md](WORKFLOW_DOCUMENTATION.md) for detailed workflow documentation.

## ⚙️ Architecture

- **All Agents Use Gemini**: Hardcoded in Coordinator for consistency and quality
- **Async Execution**: Phase 2 agents use native async support for better performance
- **DAG-Based Dependencies**: Phase 2 tasks use directed acyclic graph for dependency management
- **Quality Gates**: Phase 1 documents use iterative quality loops (generate → check → improve)
- **Stateless Web App**: Uses SQLite database for project context and status
- **WebSocket Support**: Real-time progress updates (falls back to polling if WebSocket fails)
