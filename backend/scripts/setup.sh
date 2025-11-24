#!/bin/bash
# Complete setup script for OmniDoc
# Sets up backend, frontend, and database
# Usage: ./backend/scripts/setup.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the script directory, backend root, and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$BACKEND_DIR/.." && pwd)"

# Change to project root for shared operations, backend dir for backend operations
cd "$PROJECT_ROOT"

echo -e "${BLUE}🚀 Setting up OmniDoc...${NC}"
echo -e "${BLUE}📁 Project root: $PROJECT_ROOT${NC}"
echo ""

# =============================================================================
# Check Prerequisites
# =============================================================================
echo -e "${BLUE}📋 Checking prerequisites...${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    echo "Please install Python 3.9 or higher"
    exit 1
fi
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}  ✅ Python ${python_version}${NC}"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    echo "Please install Node.js 18 or higher from https://nodejs.org/"
    exit 1
fi
node_version=$(node --version)
echo -e "${GREEN}  ✅ Node.js ${node_version}${NC}"

# Check npm or pnpm
if command -v pnpm &> /dev/null; then
    PACKAGE_MANAGER="pnpm"
    pnpm_version=$(pnpm --version)
    echo -e "${GREEN}  ✅ pnpm ${pnpm_version}${NC}"
elif command -v npm &> /dev/null; then
    PACKAGE_MANAGER="npm"
    npm_version=$(npm --version)
    echo -e "${GREEN}  ✅ npm ${npm_version}${NC}"
else
    echo -e "${RED}❌ Neither npm nor pnpm is installed${NC}"
    echo "Please install npm (comes with Node.js) or pnpm"
    exit 1
fi

# Check PostgreSQL
if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}  ⚠️  PostgreSQL client (psql) is not installed${NC}"
    echo "    Database setup will be skipped. Install PostgreSQL to continue."
    HAS_POSTGRES=false
else
    psql_version=$(psql --version | awk '{print $3}')
    echo -e "${GREEN}  ✅ PostgreSQL client ${psql_version}${NC}"
    HAS_POSTGRES=true
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}  ⚠️  uv is not installed (optional but recommended)${NC}"
    if [ -t 0 ]; then
        read -p "    Do you want to install uv? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "    📦 Installing uv..."
            curl -LsSf https://astral.sh/uv/install.sh | sh
            export PATH="$HOME/.cargo/bin:$PATH"
            if command -v uv &> /dev/null; then
                USE_UV=true
                echo -e "${GREEN}    ✅ uv installed successfully${NC}"
            else
                echo -e "${YELLOW}    ⚠️  uv installation may require shell restart. Falling back to pip${NC}"
                USE_UV=false
            fi
        else
            USE_UV=false
        fi
    else
        USE_UV=false
    fi
else
    USE_UV=true
    uv_version=$(uv --version)
    echo -e "${GREEN}  ✅ uv ${uv_version}${NC}"
fi

echo ""

# =============================================================================
# Setup Backend
# =============================================================================
echo -e "${BLUE}🐍 Setting up backend (Python)...${NC}"

# Change to backend directory for Python setup
cd "$BACKEND_DIR"

# Create virtual environment
if [ "$USE_UV" = true ]; then
    if [ ! -d "$PROJECT_ROOT/.venv" ]; then
        echo "  📦 Creating virtual environment with uv..."
        cd "$PROJECT_ROOT"
        uv venv
        cd "$BACKEND_DIR"
    else
        echo "  📦 Virtual environment already exists"
    fi
    
    echo "  📦 Installing Python dependencies..."
    cd "$PROJECT_ROOT"
    uv sync --all-extras --directory backend
    cd "$BACKEND_DIR"
else
    if [ ! -d "$PROJECT_ROOT/.venv" ]; then
        echo "  📦 Creating virtual environment..."
        cd "$PROJECT_ROOT"
        python3 -m venv .venv
        cd "$BACKEND_DIR"
    else
        echo "  📦 Virtual environment already exists"
    fi
    
    echo "  📦 Activating virtual environment..."
    source "$PROJECT_ROOT/.venv/bin/activate"
    
    echo "  📦 Upgrading pip..."
    pip install --upgrade pip
    
    echo "  📦 Installing Python dependencies..."
    pip install -e ".[dev,openai,anthropic,full]"
fi

# Return to project root
cd "$PROJECT_ROOT"

# Verify backend installation
echo "  ✅ Verifying backend installation..."
if [ "$USE_UV" = true ]; then
    uv run python -c "
import sys
import importlib
packages = [
    'google.generativeai',
    'fastapi',
    'uvicorn',
    'psycopg2',
    'pydantic',
    'slowapi',  # Rate limiting
    'celery',  # Task queue
    'redis',  # Redis client
]
missing = []
for pkg in packages:
    try:
        importlib.import_module(pkg)
        print(f'    ✅ {pkg}')
    except ImportError:
        print(f'    ❌ {pkg}')
        missing.append(pkg)
if missing:
    sys.exit(1)
"
else
    source .venv/bin/activate
    python -c "
import sys
import importlib
packages = [
    'google.generativeai',
    'fastapi',
    'uvicorn',
    'psycopg2',
    'pydantic',
    'slowapi',  # Rate limiting
    'celery',  # Task queue
    'redis',  # Redis client
]
missing = []
for pkg in packages:
    try:
        importlib.import_module(pkg)
        print(f'    ✅ {pkg}')
    except ImportError:
        print(f'    ❌ {pkg}')
        missing.append(pkg)
if missing:
    sys.exit(1)
"
fi

echo -e "${GREEN}  ✅ Backend setup complete!${NC}"
echo ""

# =============================================================================
# Setup Frontend
# =============================================================================
echo -e "${BLUE}⚛️  Setting up frontend (Next.js)...${NC}"

cd "$PROJECT_ROOT/frontend"

# Install dependencies
if [ "$PACKAGE_MANAGER" = "pnpm" ]; then
    echo "  📦 Installing dependencies with pnpm..."
    pnpm install
else
    echo "  📦 Installing dependencies with npm..."
    npm install
fi

echo -e "${GREEN}  ✅ Frontend setup complete!${NC}"
echo ""

# =============================================================================
# Setup Database
# =============================================================================
cd "$PROJECT_ROOT"

if [ "$HAS_POSTGRES" = true ]; then
    echo -e "${BLUE}🗄️  Setting up PostgreSQL database...${NC}"
    
    # Check if database exists
    DB_NAME="omnidoc"
    DB_URL="${DATABASE_URL:-postgresql://localhost/$DB_NAME}"
    
    # Extract connection info from DATABASE_URL if set
    if [ -n "$DATABASE_URL" ]; then
        # Parse DATABASE_URL: postgresql://user:pass@host:port/dbname
        DB_INFO=$(echo "$DATABASE_URL" | sed 's|postgresql://||' | sed 's|@| |' | awk '{print $1, $2}')
        DB_USER=$(echo "$DB_INFO" | awk '{print $1}' | cut -d: -f1)
        DB_HOST=$(echo "$DB_INFO" | awk '{print $2}' | cut -d: -f1)
        DB_PORT=$(echo "$DB_INFO" | awk '{print $2}' | cut -d: -f2 | cut -d/ -f1)
    else
        DB_USER="${USER:-postgres}"
        DB_HOST="localhost"
        DB_PORT="5432"
    fi
    
    # Try to create database (will fail silently if exists)
    echo "  📦 Creating database '$DB_NAME' (if not exists)..."
    if psql -h "$DB_HOST" -p "${DB_PORT:-5432}" -U "$DB_USER" -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
        echo -e "${GREEN}    ✅ Database '$DB_NAME' already exists${NC}"
    else
        if createdb -h "$DB_HOST" -p "${DB_PORT:-5432}" -U "$DB_USER" "$DB_NAME" 2>/dev/null; then
            echo -e "${GREEN}    ✅ Database '$DB_NAME' created${NC}"
        else
            echo -e "${YELLOW}    ⚠️  Could not create database automatically${NC}"
            echo "    Please create it manually: createdb $DB_NAME"
        fi
    fi
    
    # Initialize database tables (will be created automatically on first run)
    echo "  📦 Database tables will be created automatically on first run"
    echo -e "${GREEN}  ✅ Database setup complete!${NC}"
else
    echo -e "${YELLOW}⚠️  Skipping database setup (PostgreSQL not found)${NC}"
    echo "    Please install PostgreSQL and run database setup manually"
fi

echo ""

# =============================================================================
# Setup Environment File
# =============================================================================
echo -e "${BLUE}⚙️  Setting up environment configuration...${NC}"

if [ ! -f ".env" ]; then
    echo "  📝 Creating .env file from template..."
    cat > .env << 'ENVEOF'
# =============================================================================
# OmniDoc Environment Configuration
# =============================================================================

# -----------------------------------------------------------------------------
# Environment Mode
# -----------------------------------------------------------------------------
ENVIRONMENT=dev

# -----------------------------------------------------------------------------
# Database Configuration (PostgreSQL)
# -----------------------------------------------------------------------------
DATABASE_URL=postgresql://localhost/omnidoc

# -----------------------------------------------------------------------------
# LLM Provider Configuration
# -----------------------------------------------------------------------------
LLM_PROVIDER=gemini
TEMPERATURE=0.3

# -----------------------------------------------------------------------------
# Gemini Configuration
# -----------------------------------------------------------------------------
GEMINI_API_KEY=your_gemini_api_key_here

# -----------------------------------------------------------------------------
# Web Application Configuration
# -----------------------------------------------------------------------------
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# -----------------------------------------------------------------------------
# Document Configuration
# -----------------------------------------------------------------------------
DOCUMENT_CONFIG_PATH="$BACKEND_DIR/config/document_definitions.json"
DOCS_DIR=docs
MAX_SUMMARY_LENGTH=3000

# -----------------------------------------------------------------------------
# Logging Configuration
# -----------------------------------------------------------------------------
LOG_LEVEL=DEBUG
LOG_FORMAT=text
LOG_DIR=logs
ENVEOF
    echo -e "${GREEN}  ✅ .env file created${NC}"
    echo -e "${YELLOW}  ⚠️  Please edit .env and add your API keys!${NC}"
else
    echo -e "${GREEN}  ✅ .env file already exists${NC}"
    
    # Check if DATABASE_URL is set
    if ! grep -q "^DATABASE_URL=" .env; then
        echo "  📝 Adding DATABASE_URL to .env..."
        if grep -q "# Database Configuration" .env; then
            sed -i.bak '/# Database Configuration/a\
DATABASE_URL=postgresql://localhost/omnidoc
' .env
        else
            echo "" >> .env
            echo "# Database Configuration" >> .env
            echo "DATABASE_URL=postgresql://localhost/omnidoc" >> .env
        fi
        echo -e "${GREEN}    ✅ DATABASE_URL added${NC}"
    fi
fi

echo ""

# =============================================================================
# Verify Document Definitions
# =============================================================================
echo -e "${BLUE}📄 Checking document definitions...${NC}"

# Check for document definitions (in backend/config/)
if [ ! -f "$BACKEND_DIR/config/document_definitions.json" ]; then
    echo -e "${YELLOW}  ⚠️  document_definitions.json not found${NC}"
    if [ -f "$PROJECT_ROOT/JobTrackrAI_Document_Management_Template_v3.csv" ] || [ -f "$PROJECT_ROOT/Document_Management_Template.csv" ]; then
        echo "  📦 Generating from CSV..."
        CSV_FILE="$PROJECT_ROOT/JobTrackrAI_Document_Management_Template_v3.csv"
        [ ! -f "$CSV_FILE" ] && CSV_FILE="$PROJECT_ROOT/Document_Management_Template.csv"
        if [ "$USE_UV" = true ]; then
            cd "$PROJECT_ROOT"
            uv run python "$BACKEND_DIR/scripts/csv_to_document_json.py" \
                --input "$CSV_FILE" \
                --output "$BACKEND_DIR/config/document_definitions.json" 2>/dev/null || \
            echo -e "${YELLOW}    ⚠️  csv_to_document_json.py not found. Skipping CSV generation.${NC}"
        else
            cd "$PROJECT_ROOT"
            source .venv/bin/activate
            python "$BACKEND_DIR/scripts/csv_to_document_json.py" \
                --input "$CSV_FILE" \
                --output "$BACKEND_DIR/config/document_definitions.json" 2>/dev/null || \
            echo -e "${YELLOW}    ⚠️  csv_to_document_json.py not found. Skipping CSV generation.${NC}"
        fi
        echo -e "${GREEN}    ✅ Document definitions check complete${NC}"
    else
        echo -e "${YELLOW}    ⚠️  CSV file not found. Please generate document_definitions.json manually${NC}"
    fi
else
    echo -e "${GREEN}  ✅ Document definitions found${NC}"
fi

echo ""

# =============================================================================
# Summary
# =============================================================================
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo -e "${BLUE}💡 Next steps:${NC}"
echo ""
echo "  1. Configure your .env file:"
echo "     - Add your GEMINI_API_KEY (or other LLM provider keys)"
echo "     - Update DATABASE_URL if needed"
echo ""
echo "  2. Start the backend server:"
if [ "$USE_UV" = true ]; then
    echo "     cd $PROJECT_ROOT"
    echo "     uv run python backend/uvicorn_dev.py"
else
    echo "     cd $PROJECT_ROOT"
    echo "     source .venv/bin/activate"
    echo "     python backend/uvicorn_dev.py"
fi
echo ""
echo "  3. Start the frontend (in a new terminal):"
echo "     cd $PROJECT_ROOT/frontend"
if [ "$PACKAGE_MANAGER" = "pnpm" ]; then
    echo "     pnpm dev"
else
    echo "     npm run dev"
fi
echo ""
echo "  4. Open your browser:"
echo "     http://localhost:3000"
echo ""
echo -e "${BLUE}📚 For more information, see README.md and README_BACKEND.md${NC}"
echo ""