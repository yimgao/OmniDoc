#!/bin/bash
# Setup script for DOCU-GEN
# Usage: ./scripts/setup.sh
# Uses uv to manage dependencies from pyproject.toml
# All packages are installed in a virtual environment

set -e

# Get the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project root
cd "$PROJECT_ROOT"

echo "🚀 Setting up DOCU-GEN..."
echo "📁 Project root: $PROJECT_ROOT"

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    echo "Please install Python 3.9 or higher"
    exit 1
fi

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "📦 Python version: $python_version"

# Check if uv is installed, if not, offer to install it
if ! command -v uv &> /dev/null; then
    echo ""
    echo "⚠️  uv is not installed"
    echo "📦 uv is a fast Python package installer (recommended)"
    echo ""
    # Check if we're in an interactive terminal
    if [ -t 0 ]; then
        read -p "Do you want to install uv? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "📦 Installing uv..."
            curl -LsSf https://astral.sh/uv/install.sh | sh
            # Add uv to PATH for current session
            export PATH="$HOME/.cargo/bin:$PATH"
            # Verify uv is now available
            if command -v uv &> /dev/null; then
                USE_UV=true
                echo "✅ uv installed successfully"
            else
                echo "⚠️  uv installation may require shell restart. Falling back to pip + venv"
                USE_UV=false
            fi
        else
            echo "⚠️  Falling back to pip + venv"
            USE_UV=false
        fi
    else
        # Non-interactive mode, fall back to pip
        echo "⚠️  Non-interactive mode detected. Falling back to pip + venv"
        USE_UV=false
    fi
else
    USE_UV=true
    echo "✅ uv is installed"
fi

# Create virtual environment
if [ "$USE_UV" = true ]; then
    # Use uv to create and manage venv
    if [ ! -d ".venv" ]; then
        echo ""
        echo "📦 Creating virtual environment with uv..."
        uv venv
    else
        echo ""
        echo "📦 Virtual environment already exists"
    fi
    
    # Install dependencies from pyproject.toml
    # uv sync automatically installs the package in editable mode
    echo ""
    echo "📦 Installing dependencies from pyproject.toml..."
    echo "   (This installs the project in editable mode and all dependencies)"
    uv sync --all-extras
else
    # Fallback to standard venv + pip
    if [ ! -d ".venv" ]; then
        echo ""
        echo "📦 Creating virtual environment..."
        python3 -m venv .venv
    else
        echo ""
        echo "📦 Virtual environment already exists"
    fi
    
    # Activate virtual environment
    echo "📦 Activating virtual environment..."
    source .venv/bin/activate
    
    # Upgrade pip
    echo "📦 Upgrading pip..."
    pip install --upgrade pip
    
    # Install the project and all dependencies from pyproject.toml
    echo ""
    echo "📦 Installing project and dependencies from pyproject.toml..."
    pip install -e ".[dev,openai,anthropic,full]"
fi

# Verify installation
echo ""
echo "✅ Verifying installation..."
if [ "$USE_UV" = true ]; then
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
    'requests',  # New Ollama provider dependency
    'pytest'
]
missing = []
for pkg in packages:
    try:
        pkg_name = pkg.replace('.', '_').replace('-', '_')
        if '.' in pkg:
            # Handle packages with dots like google.generativeai
            parts = pkg.split('.')
            mod = __import__(parts[0])
            for part in parts[1:]:
                mod = getattr(mod, part)
        else:
            __import__(pkg_name)
        print(f'  ✅ {pkg}')
    except ImportError as e:
        print(f'  ❌ {pkg} - {e}')
        missing.append(pkg)

if missing:
    print(f'\n⚠️  Missing packages: {missing}')
    sys.exit(1)
else:
    print('\n✅ All core packages installed successfully!')
"
else
    python -c "
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
    'requests',  # New Ollama provider dependency
    'pytest'
]
missing = []
for pkg in packages:
    try:
        pkg_name = pkg.replace('.', '_').replace('-', '_')
        if '.' in pkg:
            # Handle packages with dots like google.generativeai
            parts = pkg.split('.')
            mod = __import__(parts[0])
            for part in parts[1:]:
                mod = getattr(mod, part)
        else:
            __import__(pkg_name)
        print(f'  ✅ {pkg}')
    except ImportError as e:
        print(f'  ❌ {pkg} - {e}')
        missing.append(pkg)

if missing:
    print(f'\n⚠️  Missing packages: {missing}')
    sys.exit(1)
else:
    print('\n✅ All core packages installed successfully!')
"
fi

# Verify Ollama provider can be imported
echo ""
echo "✅ Verifying Ollama provider..."
if [ "$USE_UV" = true ]; then
    uv run python -c "
try:
    from src.llm.ollama_provider import OllamaProvider
    from src.llm.provider_factory import ProviderFactory
    print('  ✅ OllamaProvider imported successfully')
    
    # Check if it's registered in the factory
    providers = ProviderFactory.get_available_providers()
    if 'ollama' in providers:
        print('  ✅ Ollama provider registered in ProviderFactory')
    else:
        print('  ⚠️  Ollama provider not found in ProviderFactory')
        print(f'     Available providers: {providers}')
except ImportError as e:
    print(f'  ❌ Failed to import OllamaProvider: {e}')
    sys.exit(1)
"
else
    python -c "
try:
    from src.llm.ollama_provider import OllamaProvider
    from src.llm.provider_factory import ProviderFactory
    print('  ✅ OllamaProvider imported successfully')
    
    # Check if it's registered in the factory
    providers = ProviderFactory.get_available_providers()
    if 'ollama' in providers:
        print('  ✅ Ollama provider registered in ProviderFactory')
    else:
        print('  ⚠️  Ollama provider not found in ProviderFactory')
        print(f'     Available providers: {providers}')
except ImportError as e:
    print(f'  ❌ Failed to import OllamaProvider: {e}')
    sys.exit(1)
"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "💡 Next steps:"
echo "   1. Create .env file with your API keys:"
echo "      - For Gemini: echo 'LLM_PROVIDER=gemini' > .env && echo 'GEMINI_API_KEY=your_key' >> .env"
echo "      - For Ollama: echo 'LLM_PROVIDER=ollama' > .env && echo 'OLLAMA_DEFAULT_MODEL=dolphin3' >> .env"
echo "      - For OpenAI: echo 'LLM_PROVIDER=openai' > .env && echo 'OPENAI_API_KEY=your_key' >> .env"
echo ""
echo "   2. Activate virtual environment:"
if [ "$USE_UV" = true ]; then
    echo "      source .venv/bin/activate  # or use 'uv run' prefix for commands"
else
    echo "      source .venv/bin/activate"
fi
echo ""
echo "   3. Run tests:"
if [ "$USE_UV" = true ]; then
    echo "      uv run pytest tests/unit"
else
    echo "      pytest tests/unit"
fi
echo ""
echo "   4. Run web app:"
if [ "$USE_UV" = true ]; then
    echo "      uv run python -m src.web.app"
else
    echo "      python -m src.web.app"
fi
echo ""
echo "   5. See README.md for more information"
echo ""
