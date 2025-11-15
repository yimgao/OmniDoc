#!/bin/bash
# Oracle Cloud Deployment Script
# This script helps automate the deployment process on Oracle Cloud

set -e

echo "🚀 OmniDoc Oracle Cloud Deployment Script"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo -e "${RED}Please do not run as root. Use a regular user with sudo privileges.${NC}"
   exit 1
fi

# Configuration
APP_DIR="/opt/omnidoc"
APP_USER=$(whoami)

echo -e "${GREEN}Step 1: Installing system dependencies...${NC}"
sudo apt-get update
# Note: PostgreSQL and Redis are NOT installed - we use managed services
# PostgreSQL: Neon (managed PostgreSQL)
# Redis: Upstash (managed Redis)
sudo apt-get install -y git curl wget build-essential

echo -e "${GREEN}Step 2: Installing Node.js 18+...${NC}"
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

echo -e "${GREEN}Step 3: Installing Python 3.9+...${NC}"
sudo apt-get install -y python3.9 python3.9-venv python3-pip

echo -e "${GREEN}Step 4: Configuring Neon Database (Managed PostgreSQL)...${NC}"
echo -e "${YELLOW}We'll use Neon (https://neon.tech) for managed PostgreSQL.${NC}"
echo -e "${YELLOW}This saves memory on your Oracle Cloud instance!${NC}"
echo ""
echo "Production Neon connection string is pre-configured."
echo "If you need to use a different database, you can update it in .env file later."
echo ""
read -p "Enter your Neon DATABASE_URL (or press Enter to use production default): " NEON_DATABASE_URL
NEON_DATABASE_URL=${NEON_DATABASE_URL:-"postgresql://neondb_owner:npg_wUg5P3SnCMcF@ep-divine-meadow-a4epnyhw-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"}

echo -e "${GREEN}Step 5: Configuring Upstash Redis (Managed Redis)...${NC}"
echo -e "${YELLOW}We'll use Upstash (https://upstash.com) for managed Redis.${NC}"
echo -e "${YELLOW}This saves memory on your Oracle Cloud instance!${NC}"
echo ""
echo "Please get your Upstash Redis connection details:"
echo "  1. Go to https://console.upstash.com"
echo "  2. Create or select a Redis database"
echo "  3. Copy the Redis URL (format: redis://default:password@endpoint:port)"
echo ""
# Build Redis URL from REST URL and token
# Format: redis://default:token@hostname:6379
read -p "Enter your Upstash Redis REST URL (or press Enter to use production default): " UPSTASH_REDIS_REST_URL
UPSTASH_REDIS_REST_URL=${UPSTASH_REDIS_REST_URL:-"https://right-loon-30051.upstash.io"}

read -p "Enter your Upstash Redis REST Token (or press Enter to use production default): " UPSTASH_REDIS_REST_TOKEN
UPSTASH_REDIS_REST_TOKEN=${UPSTASH_REDIS_REST_TOKEN:-"AXVjAAIncDJlNDY0OGUwNzdkMjc0M2U5OGE2Yzg4ZGUzYWU3YWVlZXAyMzAwNTE"}

# Extract hostname from REST URL (remove https://)
UPSTASH_HOST=$(echo "$UPSTASH_REDIS_REST_URL" | sed 's|https://||' | sed 's|http://||')
# Build standard Redis URL for Celery
UPSTASH_REDIS_URL="redis://default:${UPSTASH_REDIS_REST_TOKEN}@${UPSTASH_HOST}:6379"

read -p "Enter your Upstash Redis REST URL (or press Enter to use production default): " UPSTASH_REDIS_REST_URL
UPSTASH_REDIS_REST_URL=${UPSTASH_REDIS_REST_URL:-"https://right-loon-30051.upstash.io"}

read -p "Enter your Upstash Redis REST Token (or press Enter to use production default): " UPSTASH_REDIS_REST_TOKEN
UPSTASH_REDIS_REST_TOKEN=${UPSTASH_REDIS_REST_TOKEN:-"AXVjAAIncDJlNDY0OGUwNzdkMjc0M2U5OGE2Yzg4ZGUzYWU3YWVlZXAyMzAwNTE"}

echo -e "${GREEN}Step 6: Cloning repository...${NC}"
if [ ! -d "$APP_DIR" ]; then
    sudo mkdir -p $APP_DIR
    read -p "Enter GitHub repository URL (or press Enter for default): " REPO_URL
    REPO_URL=${REPO_URL:-"https://github.com/yimgao/OmniDoc.git"}
    sudo git clone $REPO_URL $APP_DIR
    sudo chown -R $APP_USER:$APP_USER $APP_DIR
else
    echo -e "${YELLOW}Directory $APP_DIR already exists. Skipping clone.${NC}"
fi

cd $APP_DIR

echo -e "${GREEN}Step 7: Running setup script...${NC}"
./scripts/setup.sh

echo -e "${GREEN}Step 8: Configuring environment...${NC}"
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file with production settings...${NC}"
    
    # Use Neon DATABASE_URL (production default is pre-configured)
    DB_URL="$NEON_DATABASE_URL"
    echo -e "${GREEN}✅ Using Neon DATABASE_URL${NC}"
    
    cat > .env <<EOF
# =============================================================================
# Database Configuration (Neon - Managed PostgreSQL)
# =============================================================================
# Get your connection string from: https://console.neon.tech
# Format: postgresql://user:password@ep-xxx.region.neon.tech/dbname?sslmode=require
DATABASE_URL=$DB_URL

# =============================================================================
# Redis Configuration (Upstash - Managed Redis)
# =============================================================================
# Get your Redis URL from: https://console.upstash.com
# Format: redis://default:password@endpoint:port
REDIS_URL=$UPSTASH_REDIS_URL

# Upstash REST API (for REST-based Redis operations if needed)
UPSTASH_REDIS_REST_URL=$UPSTASH_REDIS_REST_URL
UPSTASH_REDIS_REST_TOKEN=$UPSTASH_REDIS_REST_TOKEN

# =============================================================================
# Security Configuration
# =============================================================================
JWT_SECRET_KEY=$(openssl rand -hex 32)
ENVIRONMENT=prod

# =============================================================================
# CORS Configuration - Production Domain
# =============================================================================
ALLOWED_ORIGINS=https://omnidoc.info,https://www.omnidoc.info,https://*.vercel.app

# =============================================================================
# LLM Provider Configuration
# =============================================================================
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here

# =============================================================================
# Backend Configuration
# =============================================================================
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# =============================================================================
# Logging Configuration
# =============================================================================
LOG_LEVEL=INFO
LOG_FORMAT=json
EOF
    echo -e "${GREEN}.env file created.${NC}"
    if [ -z "$NEON_DATABASE_URL" ]; then
        echo -e "${YELLOW}⚠️  Please update DATABASE_URL with your Neon connection string!${NC}"
    fi
    echo -e "${YELLOW}⚠️  Please update GEMINI_API_KEY with your actual API key.${NC}"
    read -p "Press Enter to continue..."
fi

echo -e "${GREEN}Step 9: Initializing database tables...${NC}"
if [ -n "$NEON_DATABASE_URL" ] || [ -f .env ]; then
    echo "  📦 Running database initialization script..."
    if [ -f scripts/init_database.sh ]; then
        chmod +x scripts/init_database.sh
        ./scripts/init_database.sh || echo -e "${YELLOW}⚠️  Database initialization failed. You can run it manually later with: ./scripts/init_database.sh${NC}"
    else
        echo -e "${YELLOW}⚠️  init_database.sh not found. Tables will be created on first run.${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Skipping database initialization. Please set DATABASE_URL in .env first.${NC}"
fi

echo -e "${GREEN}Step 10: Installing Nginx...${NC}"
sudo apt-get install -y nginx

echo -e "${GREEN}Step 10.1: Configuring Nginx...${NC}"
echo -e "${YELLOW}Note: Frontend is deployed on Vercel, only backend API is configured here.${NC}"
sudo tee /etc/nginx/sites-available/omnidoc > /dev/null <<EOF
# Backend API (FastAPI)
# Frontend is deployed on Vercel at https://omnidoc.info
server {
    listen 80;
    server_name api.omnidoc.info;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/omnidoc /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx

echo -e "${GREEN}Step 10.2: Setting up SSL with Let's Encrypt...${NC}"
sudo apt-get install -y certbot python3-certbot-nginx
echo -e "${YELLOW}Setting up SSL certificates for API endpoint...${NC}"
echo -e "${YELLOW}Note: Frontend SSL is handled by Vercel.${NC}"
read -p "Enter your email for Let's Encrypt notifications: " CERTBOT_EMAIL
CERTBOT_EMAIL=${CERTBOT_EMAIL:-"admin@omnidoc.info"}
echo -e "${GREEN}Obtaining SSL certificates for API...${NC}"
sudo certbot --nginx -d api.omnidoc.info --non-interactive --agree-tos --email $CERTBOT_EMAIL --redirect

echo -e "${GREEN}SSL certificates configured!${NC}"
echo -e "${GREEN}Auto-renewal is configured automatically.${NC}"

echo -e "${GREEN}Step 11: Creating systemd services...${NC}"

# Backend service
sudo tee /etc/systemd/system/omnidoc-backend.service > /dev/null <<EOF
[Unit]
Description=OmniDoc Backend API
After=network.target

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/.venv/bin"
ExecStart=$APP_DIR/.venv/bin/python backend/uvicorn_dev.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Celery service
sudo tee /etc/systemd/system/omnidoc-celery.service > /dev/null <<EOF
[Unit]
Description=OmniDoc Celery Worker
After=network.target

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/.venv/bin"
ExecStart=$APP_DIR/.venv/bin/celery -A src.tasks.celery_app worker --loglevel=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}Step 12: Configuring firewall...${NC}"
echo -e "${YELLOW}Note: Frontend is deployed on Vercel, skipping PM2 setup.${NC}"
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

echo -e "${GREEN}Step 13: Enabling services...${NC}"
sudo systemctl daemon-reload
sudo systemctl enable omnidoc-backend omnidoc-celery
sudo systemctl start omnidoc-backend omnidoc-celery

echo -e "${GREEN}Step 14: Frontend deployment reminder...${NC}"
echo -e "${YELLOW}⚠️  Frontend should be deployed to Vercel!${NC}"
echo -e "${YELLOW}See VERCEL_DEPLOYMENT.md for instructions.${NC}"
echo ""
echo "Quick steps:"
echo "  1. Go to https://vercel.com"
echo "  2. Import your GitHub repository"
echo "  3. Set root directory to 'frontend'"
echo "  4. Add environment variable: NEXT_PUBLIC_API_BASE=https://api.omnidoc.info"
echo "  5. Deploy!"

echo -e "${GREEN}✅ Backend deployment complete!${NC}"
echo ""
echo -e "${GREEN}Production URLs:${NC}"
echo "  Frontend: https://omnidoc.info (deploy to Vercel - see VERCEL_DEPLOYMENT.md)"
echo "  API: https://api.omnidoc.info"
echo "  API Docs: https://api.omnidoc.info/docs"
echo ""
echo -e "${YELLOW}Important Next Steps:${NC}"
echo "1. Update GEMINI_API_KEY in .env file with your actual API key"
echo "2. Deploy frontend to Vercel (see VERCEL_DEPLOYMENT.md)"
echo "3. Configure Oracle Cloud security rules to allow HTTP/HTTPS traffic"
echo "4. Ensure DNS records point correctly:"
echo "   - Frontend (Vercel): omnidoc.info, www.omnidoc.info → Vercel DNS"
echo "   - Backend API: api.omnidoc.info → $(curl -s ifconfig.me)"
echo ""
echo "Check service status:"
echo "  sudo systemctl status omnidoc-backend"
echo "  sudo systemctl status omnidoc-celery"
echo "  sudo systemctl status nginx"
echo ""
echo "View logs:"
echo "  sudo journalctl -u omnidoc-backend -f"
echo "  sudo journalctl -u omnidoc-celery -f"
echo "  sudo journalctl -u nginx -f"

