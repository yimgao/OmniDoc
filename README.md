# DOCU-GEN

AI-powered documentation generation system that creates comprehensive documentation from simple user ideas using multi-agent collaboration.

## 🚀 Quick Start

```bash
# Install dependencies
./scripts/setup.sh

# Set API key
echo "GEMINI_API_KEY=your_key" > .env

# Run tests
pytest tests/unit

# Generate documentation (CLI)
python -c "
from src.coordination.coordinator import WorkflowCoordinator
coordinator = WorkflowCoordinator()
coordinator.generate_all_docs('Build a task management app')
"

# Or use web interface
python -m src.web.app
# Visit http://localhost:8000
```

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
├── templates/             # Document templates (Jinja2)
├── prompts/               # System prompts (editable)
├── scripts/               # Setup and utility scripts
└── pyproject.toml         # Project configuration
```

## 📚 Documentation

- **Current Status**: See [CURRENT_STATUS.md](CURRENT_STATUS.md)
- **AutoGen Comparison**: See [AUTOGEN_COMPARISON.md](AUTOGEN_COMPARISON.md)
- **Documentation Index**: See [docs/README.md](docs/README.md)

## 🧪 Testing

```bash
# Run all tests
pytest

# Unit tests only (fast)
pytest tests/unit -m unit

# With coverage
pytest --cov=src --cov-report=html

# Integration tests
pytest tests/integration

# E2E tests (requires API key)
pytest tests/e2e
```

**Current Status:** 102 tests passing, 82% code coverage

## 🎯 Usage Examples

### Generate All Documentation

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
# Start web server
python -m src.web.app

# Visit http://localhost:8000
# Enter your project idea and generate docs!
```

### Switch LLM Provider

```python
# Use OpenAI instead of Gemini
from src.agents.requirements_analyst import RequirementsAnalyst

agent = RequirementsAnalyst(provider_name="openai")
```

## 📝 License

MIT License - see [LICENSE](LICENSE)
