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
# Note: PostgreSQL is NOT installed - we use Neon (managed PostgreSQL)
sudo apt-get install -y git curl wget build-essential redis-server

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

echo -e "${GREEN}Step 5: Setting up Redis...${NC}"
read -sp "Enter Redis password: " REDIS_PASSWORD
echo

sudo sed -i "s/# requirepass foobared/requirepass $REDIS_PASSWORD/" /etc/redis/redis.conf
sudo systemctl restart redis-server

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
# Redis Configuration (Local)
# =============================================================================
REDIS_URL=redis://:$REDIS_PASSWORD@localhost:6379/0

# =============================================================================
# Security Configuration
# =============================================================================
JWT_SECRET_KEY=$(openssl rand -hex 32)
ENVIRONMENT=prod

# =============================================================================
# CORS Configuration - Production Domain
# =============================================================================
ALLOWED_ORIGINS=https://omnidoc.info,https://www.omnidoc.info

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
sudo tee /etc/nginx/sites-available/omnidoc > /dev/null <<EOF
# Frontend (Next.js)
server {
    listen 80;
    server_name omnidoc.info www.omnidoc.info;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}

# Backend API (FastAPI)
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
echo -e "${YELLOW}Setting up SSL certificates for omnidoc.info...${NC}"
read -p "Enter your email for Let's Encrypt notifications: " CERTBOT_EMAIL
CERTBOT_EMAIL=${CERTBOT_EMAIL:-"admin@omnidoc.info"}
echo -e "${GREEN}Obtaining SSL certificates...${NC}"
sudo certbot --nginx -d omnidoc.info -d www.omnidoc.info -d api.omnidoc.info --non-interactive --agree-tos --email $CERTBOT_EMAIL --redirect

echo -e "${GREEN}SSL certificates configured!${NC}"
echo -e "${GREEN}Auto-renewal is configured automatically.${NC}"

echo -e "${GREEN}Step 11: Creating systemd services...${NC}"

# Backend service
sudo tee /etc/systemd/system/omnidoc-backend.service > /dev/null <<EOF
[Unit]
Description=OmniDoc Backend API
After=network.target redis.service

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
After=network.target redis.service

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

echo -e "${GREEN}Step 12: Setting up PM2 for frontend...${NC}"
sudo npm install -g pm2

echo -e "${GREEN}Step 13: Configuring firewall...${NC}"
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

echo -e "${GREEN}Step 14: Enabling services...${NC}"
sudo systemctl daemon-reload
sudo systemctl enable omnidoc-backend omnidoc-celery
sudo systemctl start omnidoc-backend omnidoc-celery

# Build frontend
echo -e "${GREEN}Step 14.1: Building frontend...${NC}"
cd $APP_DIR/frontend

# Create frontend .env.local with production API URL
cat > .env.local <<EOF
NEXT_PUBLIC_API_BASE=https://api.omnidoc.info
EOF

npm run build
pm2 start npm --name "omnidoc-frontend" -- start
pm2 save
pm2 startup

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo -e "${GREEN}Production URLs:${NC}"
echo "  Frontend: https://omnidoc.info"
echo "  API: https://api.omnidoc.info"
echo "  API Docs: https://api.omnidoc.info/docs"
echo ""
echo -e "${YELLOW}Important:${NC}"
echo "1. Update GEMINI_API_KEY in .env file with your actual API key"
echo "2. Configure Oracle Cloud security rules to allow HTTP/HTTPS traffic"
echo "3. Ensure DNS records point to this server:"
echo "   - A record: omnidoc.info → $(curl -s ifconfig.me)"
echo "   - A record: www.omnidoc.info → $(curl -s ifconfig.me)"
echo "   - A record: api.omnidoc.info → $(curl -s ifconfig.me)"
echo ""
echo "Check service status:"
echo "  sudo systemctl status omnidoc-backend"
echo "  sudo systemctl status omnidoc-celery"
echo "  sudo systemctl status nginx"
echo "  pm2 status"
echo ""
echo "View logs:"
echo "  sudo journalctl -u omnidoc-backend -f"
echo "  sudo journalctl -u omnidoc-celery -f"
echo "  pm2 logs omnidoc-frontend"

