#!/bin/bash
# Setup script for DOCU-GEN
# Usage: ./scripts/setup.sh
# Uses uv to manage dependencies from pyproject.toml

set -e

echo "🚀 Setting up DOCU-GEN..."

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed"
    echo "Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "📦 Python version: $python_version"

# Create virtual environment (if it doesn't exist)
if [ ! -d ".venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    uv venv
else
    echo ""
    echo "📦 Virtual environment already exists"
fi

# Install dependencies from pyproject.toml
echo ""
echo "📦 Installing dependencies from pyproject.toml..."
echo "   (This installs all dependencies including dev dependencies)"
uv sync --all-extras

# Verify installation
echo ""
echo "✅ Verifying installation..."
uv run python -c "
import sys
packages = [
    'google.generativeai',
    'ratelimit',
    'diskcache',
    'textstat',
    'fastapi',
    'uvicorn',
    'jinja2',
    'pydantic',
    'markdown',
    'pytest'
]
missing = []
for pkg in packages:
    try:
        __import__(pkg.replace('-', '_'))
        print(f'  ✅ {pkg}')
    except ImportError:
        print(f'  ❌ {pkg}')
        missing.append(pkg)

if missing:
    print(f'\n⚠️  Missing packages: {missing}')
    sys.exit(1)
"

echo ""
echo "✅ Setup complete!"
echo ""
echo "💡 Next steps:"
echo "   1. Create .env file: echo 'GEMINI_API_KEY=your_key' > .env"
echo "   2. Run tests: uv run pytest tests/unit"
echo "   3. Run web app: uv run python -m src.web.app"
echo "   4. See README.md for more information"
echo ""
