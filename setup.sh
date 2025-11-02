#!/bin/bash
# Setup script for DOCU-GEN Phase 1 using uv

echo "🚀 Setting up DOCU-GEN Phase 1 with uv..."
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed!"
    echo ""
    echo "📦 Installing uv..."
    echo "   Run: curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "   Or: brew install uv (on macOS)"
    echo ""
    echo "   Then restart your terminal and run this script again."
    exit 1
fi

echo "✅ uv found: $(uv --version)"
echo ""

# Check Python version
if command -v python3 &> /dev/null; then
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    echo "📦 Python version: $python_version"
fi

echo ""
echo "📦 Creating virtual environment with uv..."
uv venv

echo ""
echo "📦 Installing dependencies directly into .venv..."
# Install dependencies directly (no editable install needed for Phase 1)
# This ensures packages go to .venv without build issues
uv pip install --python .venv/bin/python \
    google-generativeai>=0.3.0 \
    ratelimit>=2.2.1 \
    diskcache>=5.6.3 \
    textstat>=0.7.3 \
    python-dotenv>=1.0.0 \
    pyautogen>=0.2.0 \
    langchain>=0.1.0 \
    jinja2>=3.1.2

echo ""
echo "✅ Verifying installation in .venv..."
echo "Testing key package imports..."
.venv/bin/python -c "
import sys
try:
    import google.generativeai
    print('  ✅ google-generativeai')
except ImportError as e:
    print(f'  ❌ google-generativeai: {e}')
    sys.exit(1)

try:
    import pyautogen
    print('  ✅ pyautogen (installed, API may differ by version)')
except ImportError as e:
    print(f'  ⚠️  pyautogen: {e} (optional for Phase 1 - using direct Gemini API)')

try:
    import ratelimit
    print('  ✅ ratelimit')
except ImportError as e:
    print(f'  ❌ ratelimit: {e}')
    sys.exit(1)

try:
    import textstat
    print('  ✅ textstat')
except ImportError as e:
    print(f'  ⚠️  textstat: {e}')

try:
    import diskcache
    print('  ✅ diskcache')
except ImportError as e:
    print(f'  ❌ diskcache: {e}')
    sys.exit(1)

print('✅ All critical packages installed in .venv!')
"

echo ""
echo "🔍 Verifying .venv location..."
site_packages=$(find .venv/lib -name "site-packages" -type d 2>/dev/null | head -1)
if [ -n "$site_packages" ]; then
    package_count=$(ls -1 "$site_packages" 2>/dev/null | grep -E "^(google|autogen|ratelimit|textstat|diskcache)" | wc -l)
    echo "✅ Found $package_count key packages in: $site_packages"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📦 Virtual environment is active. Dependencies installed in: .venv/"
echo ""
echo "💡 To reactivate later:"
echo "   source .venv/bin/activate"
echo ""
echo "⚠️  IMPORTANT: Set up your Gemini API key:"
echo "   1. Get API key from: https://aistudio.google.com/"
echo "   2. Create .env file with: GEMINI_API_KEY=your_key_here"
echo ""
echo "🧪 To test Phase 1, run:"
echo "   uv run python test_phase1.py"
echo "   Or activate venv and run: python test_phase1.py"
echo ""

