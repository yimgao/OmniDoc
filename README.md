# DOCU-GEN: Documentation Generation System

AI-powered documentation generation system that creates comprehensive documentation from simple user ideas.

## 🎯 Project Overview

DOCU-GEN uses **Google Gemini API (free tier)** and **AutoGen framework** to automatically generate:
- Project management documentation
- Technical specifications
- API documentation
- Developer guides
- Stakeholder presentations

All from a single natural language input!

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Google Gemini API key (free from [Google AI Studio](https://aistudio.google.com/))
- Mac M1 Air 8GB RAM compatible (or any system with Python)

### Setup

1. **Install uv (fast Python package manager):**
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew (macOS)
brew install uv

# Or with pip (if you have Python)
pip install uv
```

2. **Clone and navigate to project:**
```bash
cd /Users/yiming/dev_code/git/auto-repo-agents
```

3. **Install dependencies with uv:**
```bash
# Option 1: Use setup script (recommended)
./setup.sh

# Option 2: Manual setup with uv
uv venv                    # Create virtual environment
uv pip install -e .        # Install dependencies
uv pip install -e ".[full]" # Install optional dependencies
```

4. **Set up Google Gemini API:**
   - Visit [Google AI Studio](https://aistudio.google.com/)
   - Sign in and create a free API key
   - Create `.env` file in project root:
   ```bash
   GEMINI_API_KEY=your_api_key_here
   ```

5. **Test Phase 1 (Requirements Analyst):**
```bash
# With uv (recommended - no venv activation needed)
uv run python test_phase1.py

# Or activate venv first
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python test_phase1.py
```

## 📋 Current Phase: Phase 1

**Goal:** Single Agent Documentation Generator (MVP)

- ✅ Requirements Analyst agent
- ✅ Google Gemini 1.5 Flash integration
- ✅ Rate limiting (60 req/min)
- ✅ Basic quality checks
- ✅ File writing capability

### Test It:

```python
from src.agents.requirements_analyst_v2 import generate_requirements

# Generate requirements from a simple idea
result = generate_requirements("I want to build an e-commerce platform")
print(f"Requirements saved to: {result}")
```

## 🏗️ Project Structure

```
auto-repo-agents/
├── src/
│   ├── agents/              # Agent implementations
│   │   ├── requirements_analyst_v2.py
│   ├── quality/              # Quality checking
│   │   └── basic_checks.py
│   ├── rate_limit/          # Rate limiting
│   │   └── queue_manager.py
│   └── context/             # Shared context (Phase 2+)
├── config/                  # Configuration files
├── templates/               # Document templates
├── docs/                    # Generated documentation
├── tests/                   # Test files
├── pyproject.toml          # Project configuration & dependencies (uv)
├── requirements.txt        # Legacy dependencies (backup)
├── test_phase1.py          # Phase 1 test script
└── README.md
```

## ⚠️ Risk Mitigation

All identified risks have solutions implemented:

1. **Rate Limiting** ✅ - Request queue limits to 60 req/min
2. **Quality** ✅ - Automated quality checks (word count, completeness, readability)
3. **Documentation Quality** ✅ - Quality scoring system
4. **Cost** ✅ - Free tier usage with monitoring

## 📚 Documentation

See `project.pland.claude` for complete project plan, architecture, and roadmap.

## 🛠️ Development

### Phase 1 Status: ✅ In Progress

- [x] Project structure
- [x] Rate limiting system
- [x] Quality checks
- [x] Requirements Analyst agent
- [ ] AutoGen integration (simplified version for Phase 1)
- [ ] Full test suite

## 📝 License

See LICENSE file.
