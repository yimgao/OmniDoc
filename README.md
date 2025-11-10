# DOCU-GEN

AI-powered documentation generation system that creates comprehensive documentation from simple user ideas using multi-agent collaboration.

## 🚀 Quick Start

```bash
# Install dependencies (uses uv to sync from pyproject.toml)
./scripts/setup.sh

# Set API key
echo "GEMINI_API_KEY=your_key" > .env

# Run tests (uv run automatically uses the correct environment)
uv run pytest tests/unit

# Generate documentation (CLI)
uv run python -c "
from src.coordination.coordinator import WorkflowCoordinator
coordinator = WorkflowCoordinator()
coordinator.generate_all_docs('Build a task management app')
"

# Or use web interface
uv run python -m src.web.app
# Visit http://localhost:8000
```

**Note:** This project uses `uv` to manage dependencies from `pyproject.toml`. 
- Use `uv run <command>` to run commands in the project environment
- No need to activate virtual environment manually
- Dependencies are managed via `pyproject.toml`

## 📋 Features

- **10 Documentation Agents**: Requirements, PM, Technical, API, Developer, Stakeholder, User, Test, Quality Review, Format Converter
- **Multi-LLM Support**: Works with Gemini, OpenAI, and extensible to others
- **Format Conversion**: Outputs Markdown, HTML, PDF, DOCX
- **Quality Assurance**: Automated quality checks and scoring
- **Parallel Execution**: 3x speedup for independent agents
- **Web Interface**: FastAPI web app with real-time progress
- **Error Handling**: Retry logic with exponential backoff
- **Document Templates**: Jinja2-based customizable templates
- **Cross-Referencing**: Automatic linking between documents
- **Intelligent Parsing**: Structured data extraction from requirements

## 🏗️ Project Structure

```
docu-gen/
├── src/                    # Source code
│   ├── agents/            # Documentation agents (10 agents)
│   ├── context/           # Shared context management (SQLite)
│   ├── coordination/      # Workflow orchestration
│   ├── llm/               # LLM provider abstractions
│   ├── quality/           # Quality checking
│   ├── rate_limit/        # Rate limiting & caching
│   ├── utils/             # Utilities (parsers, templates, etc.)
│   └── web/               # Web interface (FastAPI)
├── tests/                 # Test suite (102 tests, 82% coverage)
├── docs/                  # Generated documentation
│   └── README.md         # Documentation index
├── templates/             # Document templates (Jinja2)
├── prompts/               # System prompts (editable)
├── scripts/               # Setup and utility scripts
└── pyproject.toml         # Project configuration
```

## 📚 Documentation

- **Current Status**: See [CURRENT_STATUS.md](CURRENT_STATUS.md) for detailed status and next steps
- **Documentation Index**: See [docs/README.md](docs/README.md) for generated documentation

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Unit tests only (fast)
uv run pytest tests/unit -m unit

# With coverage
uv run pytest --cov=src --cov-report=html

# Integration tests
uv run pytest tests/integration

# E2E tests (requires API key)
uv run pytest tests/e2e
```

**Current Status:** 102 tests passing, 82% code coverage

## 🎯 Usage Examples

### Generate All Documentation

```bash
# Using uv run
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
    "Build a blog platform with user authentication"
)

# Generates 10 document types:
# - Requirements
# - PM Plan
# - Technical Spec
# - API Documentation
# - Developer Guide
# - Stakeholder Summary
# - User Guide
# - Test Plan
# - Quality Review
# - Format conversions (HTML, PDF, DOCX)
```

### Use Web Interface

```bash
# Use uv run (recommended - no activation needed)
uv run python -m src.web.app

# Visit http://localhost:8000
# Enter your project idea and generate docs!
```

**Note:** 
- This project uses `uv` to manage dependencies from `pyproject.toml`
- `uv run` automatically uses the correct Python environment
- No need to activate virtual environment manually

### Switch LLM Provider

```python
# Use OpenAI instead of Gemini
from src.agents.requirements_analyst import RequirementsAnalyst

agent = RequirementsAnalyst(provider_name="openai")
```

## 📝 License

MIT License - see [LICENSE](LICENSE)
