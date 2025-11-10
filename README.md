# OmniDoc (DOCU-GEN)

AI-powered documentation generation system that creates comprehensive documentation from simple user ideas using multi-agent collaboration. Supports multiple LLM providers including Gemini, OpenAI, and **Ollama (local LLM)**.

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
- Verify installation and Ollama provider setup
- Support both `uv` (recommended) and `pip` fallback

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and configure your LLM provider
# Options: Ollama (local, no API key), Gemini, or OpenAI
```

**For Ollama (Recommended for Development):**
```bash
# In .env file
LLM_PROVIDER=ollama
OLLAMA_DEFAULT_MODEL=dolphin3
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MAX_TOKENS=8192

# Make sure Ollama is running
ollama serve

# Pull the model
ollama pull dolphin3
```

**For Gemini:**
```bash
# In .env file
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
```

**For OpenAI:**
```bash
# In .env file
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here
```

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

- **20+ Documentation Agents**: Requirements, PM, Technical, API, Developer, Stakeholder, User, Test, Quality Review, Format Converter, Business Model, Marketing Plan, Legal Compliance, Database Schema, Setup Guide, User Stories, Support Playbook, and more
- **Hybrid Workflow**: 
  - **Phase 1 (Quality Gates)**: Foundational documents use iterative quality loops (generate → check → improve) to ensure maximum quality
  - **Phase 2 (Parallel Execution)**: Secondary documents generated in parallel for maximum speed (3x faster)
  - **Phase 3 (Final Packaging)**: Cross-referencing, quality review, and format conversion
- **Multi-LLM Support**: 
  - **Ollama** (local, no API key required) - Recommended for development
  - **Google Gemini** (cloud-based) - Recommended for production
  - **OpenAI GPT** (cloud-based)
  - Extensible architecture for other providers
- **Hybrid Mode**: Automatically uses Gemini for critical/complex agents and Ollama for others (80% cost savings)
- **Format Conversion**: Outputs Markdown, HTML, PDF, DOCX
- **Quality Assurance**: Automated quality checks with document-type-specific criteria
- **Parallel Execution**: 3x speedup for independent agents
- **Web Interface**: FastAPI web app with real-time progress tracking
- **Error Handling**: Retry logic with exponential backoff
- **Document Templates**: Jinja2-based customizable templates
- **Cross-Referencing**: Automatic linking between documents
- **Intelligent Parsing**: Structured data extraction from requirements
- **Context Management**: SQLite-based shared context across agents
- **Rate Limiting**: Built-in rate limiting and caching

### LLM Provider Features

- **Ollama Provider**: 
  - Local LLM support (no API costs)
  - Configurable token limits (default: 8192 tokens)
  - Supports all Ollama models (dolphin3, mixtral, llama2, mistral, etc.)
  - Automatic connection handling with retry logic
  - Dynamic timeout calculation based on output length
- **Gemini Provider**:
  - Rate limit handling with automatic retry
  - Support for multiple Gemini models
  - High-quality output for complex tasks
- **OpenAI Provider**:
  - Full GPT-4 and GPT-3.5 support
  - Configurable models and parameters

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

**Key Configuration Options:**

**LLM Provider:**
- `LLM_PROVIDER`: Choose provider (`ollama`, `gemini`, `openai`)
- `GEMINI_API_KEY`: Gemini API key (if using Gemini)
- `OPENAI_API_KEY`: OpenAI API key (if using OpenAI)

**Ollama Configuration:**
- `OLLAMA_DEFAULT_MODEL`: Model name for Ollama (default: `dolphin3`)
- `OLLAMA_BASE_URL`: Ollama server URL (default: `http://localhost:11434`)
- `OLLAMA_MAX_TOKENS`: Max output tokens for Ollama (default: `8192`)
- `OLLAMA_TIMEOUT`: Request timeout in seconds (default: `600`)

**Temperature Control:**
- `TEMPERATURE`: Global temperature (default: `0.7`)
- `OLLAMA_TEMPERATURE`: Ollama-specific temperature (default: `0.3`)
- `GEMINI_TEMPERATURE`: Gemini-specific temperature (default: `0.7`)
- `OPENAI_TEMPERATURE`: OpenAI-specific temperature (default: `0.7`)

**Document Summarization:**
- `MAX_SUMMARY_LENGTH`: Maximum summary length in characters (default: `3000`)

**Application Settings:**
- `ENVIRONMENT`: Environment mode (`dev`, `prod`, `test`)
- `LOG_LEVEL`: Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`)
- `DOCS_DIR`: Output directory for generated docs (default: `docs/`)
- `RATE_LIMIT_PER_MINUTE`: Rate limit for API calls (default: `60`)

### Switching LLM Providers

#### Method 1: Edit .env File (Recommended)

```bash
# Edit .env file
nano .env

# For Ollama (local)
LLM_PROVIDER=ollama
OLLAMA_DEFAULT_MODEL=dolphin3

# For Gemini (cloud)
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here

# For OpenAI (cloud)
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here
```

#### Method 2: In Code

```python
# Use Ollama (local)
from src.coordination.coordinator import WorkflowCoordinator

coordinator = WorkflowCoordinator(provider_name="ollama")

# Use Gemini (cloud)
coordinator = WorkflowCoordinator(provider_name="gemini")

# Use OpenAI (cloud)
coordinator = WorkflowCoordinator(provider_name="openai")
```

#### Hybrid Mode (Mixed Providers) - Recommended for Production

The system supports **Hybrid Mode** which automatically uses Gemini for critical/complex agents and Ollama for others. This balances quality with cost.

**Automatic Hybrid Mode:**
- When `LLM_PROVIDER=ollama` and `GEMINI_API_KEY` is set
- Key agents (technical, API, database, requirements) use Gemini
- Other agents use Ollama (free)
- **Cost savings: ~80% while maintaining quality for critical docs**

**Example:**
```python
# Hybrid mode is automatic when using Ollama with Gemini API key
coordinator = WorkflowCoordinator(
    provider_name="ollama",  # Default: Ollama
    # Key agents automatically use Gemini if GEMINI_API_KEY is set
)

# Or explicitly configure:
coordinator = WorkflowCoordinator(
    provider_name="ollama",
    provider_config={
        "technical_agent": "gemini",      # Complex docs use Gemini
        "api_agent": "gemini",            # API docs use Gemini
        "database_schema_agent": "gemini", # Database design uses Gemini
        "requirements_analyst": "gemini",  # Requirements use Gemini
        # Others use Ollama (default)
    }
)
```

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

### Ollama Connection Issues

```bash
# Check if Ollama is running
ollama serve

# Verify model is available
ollama list

# Pull the model if needed
ollama pull dolphin3

# For better quality, use a larger model
ollama pull mixtral
# Then update .env: OLLAMA_DEFAULT_MODEL=mixtral
```

### Ollama Timeout Errors

If you see timeout errors with Ollama:

```bash
# Increase timeout in .env
OLLAMA_TIMEOUT=1200  # 20 minutes

# Or use a faster model
OLLAMA_DEFAULT_MODEL=dolphin3  # Smaller, faster model
```

### Ollama 500 Errors

If you see 500 Internal Server Error from Ollama:

```bash
# Check Ollama logs
ollama serve

# Verify model is properly loaded
ollama list

# Try restarting Ollama
# On macOS/Linux: pkill ollama && ollama serve
# On Windows: Stop Ollama service and restart

# Use a smaller model if memory is limited
ollama pull dolphin3
```

### Google GenerativeAI Import Error

```bash
# Fix the import error
pip uninstall google -y
pip install google-generativeai

# Or reinstall all dependencies
uv sync
```

### Low Quality Scores

If generated documents have low quality scores:

1. **Use a better model**: Switch to Gemini or upgrade Ollama model (e.g., `mixtral`)
2. **Enable Hybrid Mode**: Use Gemini for critical agents, Ollama for others
3. **Adjust temperature**: Lower temperature (0.3) for more consistent output
4. **Check quality thresholds**: Quality gates in Phase 1 will automatically improve documents

## 📦 Dependencies

### Core Dependencies
- `google-generativeai>=0.3.0` - Gemini provider
- `requests>=2.31.0` - HTTP client (for Ollama)
- `fastapi>=0.100.0` - Web framework
- `uvicorn>=0.23.0` - ASGI server
- `python-dotenv>=1.0.0` - Environment variables
- `jinja2>=3.1.2` - Template engine
- `pydantic>=2.0.0` - Data validation
- `markdown>=3.5.0` - Markdown processing
- `weasyprint>=60.0` - PDF generation
- `python-docx>=1.1.0` - DOCX generation

### Optional Dependencies
- `openai>=1.0.0` - OpenAI provider (install with `uv sync --extra openai`)
- `anthropic>=0.18.0` - Anthropic provider (install with `uv sync --extra anthropic`)

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

## 📚 Additional Resources

- **Configuration Guide**: See [src/config/README.md](src/config/README.md) for detailed configuration options
- **Examples**: See [examples/](examples/) directory for usage examples
- **Generated Docs**: See [docs/](docs/) directory for generated documentation index
