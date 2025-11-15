# Oracle Cloud Free Tier Deployment Guide

Complete guide for deploying OmniDoc on Oracle Cloud Infrastructure (OCI) Free Tier.

## 📋 Prerequisites

- Oracle Cloud Free Tier account
- Ubuntu 22.04 LTS instance (Always Free eligible)
- Domain name (optional, but recommended)
- SSH access to your instance

## 🚀 Step-by-Step Deployment

### 1. Initial Server Setup

#### Connect to Your Instance

```bash
ssh ubuntu@<your-server-ip>
```

#### Update System

```bash
sudo apt-get update
sudo apt-get upgrade -y
```

#### Install Basic Tools

```bash
sudo apt-get install -y git curl wget build-essential
```

### 2. Install System Dependencies

#### PostgreSQL

```bash
sudo apt-get install -y postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### Redis

```bash
sudo apt-get install -y redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

#### Node.js 18+

```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

#### Python 3.9+

```bash
sudo apt-get install -y python3.9 python3.9-venv python3-pip
```

### 3. Configure PostgreSQL

```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL prompt:
CREATE DATABASE omnidoc;
CREATE USER omnidoc WITH PASSWORD 'your_strong_password_here';
GRANT ALL PRIVILEGES ON DATABASE omnidoc TO omnidoc;
\q
```

Update PostgreSQL config for remote access (if needed):

```bash
sudo nano /etc/postgresql/*/main/postgresql.conf
# Set: listen_addresses = 'localhost'

sudo nano /etc/postgresql/*/main/pg_hba.conf
# Add: local   all   omnidoc   md5
```

### 4. Configure Redis

```bash
# Set Redis password (recommended)
sudo nano /etc/redis/redis.conf
# Find and uncomment: requirepass your_redis_password_here

sudo systemctl restart redis-server
```

### 5. Deploy Application

#### Clone Repository

```bash
cd /opt
sudo git clone <your-repo-url> omnidoc
sudo chown -R ubuntu:ubuntu omnidoc
cd omnidoc
```

#### Run Setup Script

```bash
./scripts/setup.sh
```

#### Configure Environment

```bash
nano .env
```

Update with production values:

```bash
# Database
DATABASE_URL=postgresql://omnidoc:your_password@localhost:5432/omnidoc

# Redis
REDIS_URL=redis://:your_redis_password@localhost:6379/0

# LLM Provider
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key

# Security (IMPORTANT: Generate strong key!)
JWT_SECRET_KEY=$(openssl rand -hex 32)
ENVIRONMENT=prod

# CORS (Update with your domain)
ALLOWED_ORIGINS=https://omnidoc.info,https://www.omnidoc.info

# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
```

### 6. Install Nginx

```bash
sudo apt-get install -y nginx
```

#### Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/omnidoc
```

Add configuration:

```nginx
# Frontend (Next.js)
server {
    listen 80;
    server_name omnidoc.info www.omnidoc.info;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Backend API (FastAPI)
server {
    listen 80;
    server_name api.omnidoc.info;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/omnidoc /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### 7. Setup SSL with Let's Encrypt

```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d omnidoc.info -d www.omnidoc.info -d api.omnidoc.info
```

Auto-renewal is configured automatically.

### 8. Setup Process Management

#### Option A: systemd (Recommended)

Create backend service:

```bash
sudo nano /etc/systemd/system/omnidoc-backend.service
```

```ini
[Unit]
Description=OmniDoc Backend API
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/omnidoc
Environment="PATH=/opt/omnidoc/.venv/bin"
ExecStart=/opt/omnidoc/.venv/bin/python backend/uvicorn_dev.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Create Celery worker service:

```bash
sudo nano /etc/systemd/system/omnidoc-celery.service
```

```ini
[Unit]
Description=OmniDoc Celery Worker
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/omnidoc
Environment="PATH=/opt/omnidoc/.venv/bin"
ExecStart=/opt/omnidoc/.venv/bin/celery -A src.tasks.celery_app worker --loglevel=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Create frontend service (using PM2):

```bash
sudo npm install -g pm2
cd /opt/omnidoc/frontend
pm2 start npm --name "omnidoc-frontend" -- start
pm2 save
pm2 startup
```

Enable and start services:

```bash
sudo systemctl daemon-reload
sudo systemctl enable omnidoc-backend omnidoc-celery
sudo systemctl start omnidoc-backend omnidoc-celery
```

#### Option B: PM2 (Alternative)

```bash
sudo npm install -g pm2

# Backend
cd /opt/omnidoc
pm2 start backend/uvicorn_dev.py --name "omnidoc-backend" --interpreter .venv/bin/python

# Celery
pm2 start scripts/start_celery_worker.sh --name "omnidoc-celery" --interpreter bash

# Frontend
cd frontend
pm2 start npm --name "omnidoc-frontend" -- start

pm2 save
pm2 startup
```

### 9. Configure Firewall

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
sudo ufw status
```

### 10. Oracle Cloud Security Rules

In Oracle Cloud Console:

1. Go to **Networking** → **Virtual Cloud Networks**
2. Select your VCN
3. Go to **Security Lists**
4. Add Ingress Rules:
   - **HTTP (80)**: Source 0.0.0.0/0
   - **HTTPS (443)**: Source 0.0.0.0/0
   - **SSH (22)**: Source your IP only

### 11. Build Frontend for Production

```bash
cd /opt/omnidoc/frontend
npm run build
```

Update `.env` for production:

```bash
# In frontend/.env.local
NEXT_PUBLIC_API_URL=https://api.omnidoc.info
```

### 12. Setup Logging

```bash
# Create logs directory
mkdir -p /opt/omnidoc/logs
chmod 755 /opt/omnidoc/logs

# Setup log rotation
sudo nano /etc/logrotate.d/omnidoc
```

Add:

```
/opt/omnidoc/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 ubuntu ubuntu
    sharedscripts
}
```

## 🔒 Security Checklist

- [ ] Strong `JWT_SECRET_KEY` generated
- [ ] Strong PostgreSQL password
- [ ] Redis password configured
- [ ] Firewall configured (UFW)
- [ ] Oracle Cloud security rules configured
- [ ] SSL/HTTPS enabled (Let's Encrypt)
- [ ] `ALLOWED_ORIGINS` updated with production domain
- [ ] `ENVIRONMENT=prod` set
- [ ] Database backups configured
- [ ] Log rotation configured
- [ ] SSH key authentication (disable password auth)
- [ ] Regular system updates scheduled

## 📊 Monitoring

### Check Service Status

```bash
# Backend
sudo systemctl status omnidoc-backend

# Celery
sudo systemctl status omnidoc-celery

# Frontend (if using PM2)
pm2 status

# Database
sudo systemctl status postgresql

# Redis
sudo systemctl status redis-server

# Nginx
sudo systemctl status nginx
```

### View Logs

```bash
# Backend logs
sudo journalctl -u omnidoc-backend -f

# Celery logs
sudo journalctl -u omnidoc-celery -f

# Application logs
tail -f /opt/omnidoc/logs/*.log

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Health Checks

```bash
# Backend API
curl http://localhost:8000/docs

# Database
psql $DATABASE_URL -c "SELECT 1;"

# Redis
redis-cli -a your_password ping

# Celery
cd /opt/omnidoc
.venv/bin/celery -A src.tasks.celery_app inspect active
```

## 🔄 Maintenance

### Update Application

```bash
cd /opt/omnidoc
git pull origin main
./scripts/setup.sh  # Reinstall dependencies if needed

# Restart services
sudo systemctl restart omnidoc-backend omnidoc-celery
pm2 restart omnidoc-frontend  # If using PM2
```

### Database Backup

```bash
# Create backup script
sudo nano /opt/omnidoc/scripts/backup_db.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/opt/omnidoc/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
pg_dump $DATABASE_URL > $BACKUP_DIR/omnidoc_$DATE.sql
# Keep only last 7 days
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
```

```bash
chmod +x /opt/omnidoc/scripts/backup_db.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add: 0 2 * * * /opt/omnidoc/scripts/backup_db.sh
```

## 🐛 Troubleshooting

### Service Won't Start

```bash
# Check logs
sudo journalctl -u omnidoc-backend -n 50

# Check environment variables
sudo systemctl show-environment

# Test manually
cd /opt/omnidoc
source .venv/bin/activate
python backend/uvicorn_dev.py
```

### Database Connection Issues

```bash
# Test connection
psql $DATABASE_URL -c "SELECT 1;"

# Check PostgreSQL is running
sudo systemctl status postgresql

# Check connection string in .env
cat .env | grep DATABASE_URL
```

### Redis Connection Issues

```bash
# Test connection
redis-cli -a your_password ping

# Check Redis is running
sudo systemctl status redis-server
```

### Nginx Issues

```bash
# Test configuration
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/error.log

# Reload configuration
sudo systemctl reload nginx
```

## 📝 Oracle Cloud Specific Notes

### Always Free Tier Limits

- **Compute**: 2 AMD-based VMs (1/8 OCPU, 1GB RAM each) OR 4 ARM-based VMs (up to 24GB total)
- **Storage**: 200GB block storage
- **Network**: 10TB egress per month

### Recommended Instance Type

For OmniDoc, use:
- **VM.Standard.A1.Flex** (ARM-based)
- 2 OCPUs, 12GB RAM
- This gives you enough resources for:
  - PostgreSQL
  - Redis
  - Backend API
  - Celery Worker
  - Frontend (Next.js)

### Resource Optimization

```bash
# Limit PostgreSQL memory (if needed)
sudo nano /etc/postgresql/*/main/postgresql.conf
# shared_buffers = 256MB
# effective_cache_size = 1GB

# Limit Redis memory
sudo nano /etc/redis/redis.conf
# maxmemory 256mb
# maxmemory-policy allkeys-lru
```

## 🚀 Quick Start Commands

```bash
# Start all services
sudo systemctl start omnidoc-backend omnidoc-celery
pm2 start omnidoc-frontend

# Stop all services
sudo systemctl stop omnidoc-backend omnidoc-celery
pm2 stop omnidoc-frontend

# Restart all services
sudo systemctl restart omnidoc-backend omnidoc-celery
pm2 restart omnidoc-frontend

# View all logs
sudo journalctl -u omnidoc-backend -f &
sudo journalctl -u omnidoc-celery -f &
pm2 logs omnidoc-frontend
```

## 📚 Additional Resources

- [Main README](README.md)
- [Production Setup](PRODUCTION_SETUP.md)
- [Backend Documentation](README_BACKEND.md)
- [Oracle Cloud Documentation](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm)

