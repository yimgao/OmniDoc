# Azure Deployment Guide

Complete guide for deploying OmniDoc on Microsoft Azure.

## 📋 Prerequisites

- Microsoft Azure account (Free tier available)
- Azure App Service or Azure VM
- Domain name (optional, but recommended)
- SSH access (if using VM)

> **💡 Free Tier Note**: See [Azure Free Tier Setup Guide](AZURE_FREE_TIER_SETUP.md) for detailed setup using your free tier quotas (750 hours/month VM, Always Free App Service).

## 🎯 Azure Deployment Options

### Option 1: Azure App Service (Recommended - Easier)

**Pros:**
- ✅ Fully managed platform
- ✅ Automatic scaling
- ✅ Built-in SSL certificates
- ✅ Easy deployment from GitHub
- ✅ Free tier available

**Cons:**
- ⚠️ Less control over the environment
- ⚠️ May have resource limits on free tier

### Option 2: Azure VM (More Control)

**Pros:**
- ✅ Full control over the environment
- ✅ Can run any Linux distribution
- ✅ More flexible configuration
- ✅ Better for complex setups

**Cons:**
- ⚠️ You manage the server
- ⚠️ Need to configure SSL manually
- ⚠️ More setup required

## 🚀 Option 1: Azure App Service Deployment (Recommended - Always Free)

**Best for**: Easy deployment, automatic scaling, no server management

Azure App Service has an **Always Free** tier (F1) that's not shown in your quota because it's unlimited. This is the easiest option.

### Step 1: Create Azure App Service

1. Go to https://portal.azure.com
2. Click **Create a resource**
3. Search for **Web App**
4. Click **Create**
5. Fill in:
   - **Subscription**: Your subscription
   - **Resource Group**: Create new or use existing
   - **Name**: `omnidoc-api` (or your preferred name)
   - **Publish**: **Container** (you chose this)
     - Requires Dockerfile (already created)
     - See [Azure Container Deployment Guide](AZURE_CONTAINER_DEPLOYMENT.md) for detailed steps
   - **Runtime stack**: Python 3.9 or 3.10
   - **Operating System**: Linux
   - **Region**: Choose closest to you
   - **App Service Plan**: 
     - **Plan**: Create new
     - **Pricing tier**: **Free (F1)** - Always Free, unlimited
     - Or **Basic B1** if you need more resources (~$13/month)
6. Click **Review + create** → **Create**

### Step 2: Set Up Azure Container Registry (ACR)

1. **Create a resource** → **Container Registry**
2. Configure:
   ```
   Registry name: omnidocregistry (or your preferred name)
   SKU: Basic ($5/month) or Free (if available - 500MB storage)
   ```
3. Click **Create**
4. Get access credentials: **Settings** → **Access keys**
   - Username: `omnidocregistry`
   - Password: Copy one of the passwords

### Step 3: Build and Push Docker Images

See [Azure Container Deployment Guide](AZURE_CONTAINER_DEPLOYMENT.md) for detailed steps.

Quick version:
```bash
# Login
az acr login --name omnidocregistry

# Build and push
docker build -t omnidocregistry.azurecr.io/omnidoc-backend:latest .
docker push omnidocregistry.azurecr.io/omnidoc-backend:latest
```

### Step 4: Configure App Service for Container

After creating App Service, go to **Deployment Center**:
1. Select **Container Registry** → **Azure Container Registry**
2. Select your registry: `omnidocregistry`
3. Image: `omnidoc-backend`
4. Tag: `latest`
5. Click **Save**

### Step 5: Configure Environment Variables

1. Go to your App Service
2. Navigate to **Configuration** → **Application settings**
3. Add the following environment variables:

```bash
# Database (Neon)
DATABASE_URL=postgresql://neondb_owner:npg_wUg5P3SnCMcF@ep-divine-meadow-a4epnyhw-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require

# Redis (Upstash)
REDIS_URL=redis://default:AXVjAAIncDJlNDY0OGUwNzdkMjc0M2U5OGE2Yzg4ZGUzYWU3YWVlZXAyMzAwNTE@right-loon-30051.upstash.io:6379
UPSTASH_REDIS_REST_URL=https://right-loon-30051.upstash.io
UPSTASH_REDIS_REST_TOKEN=AXVjAAIncDJlNDY0OGUwNzdkMjc0M2U5OGE2Yzg4ZGUzYWU3YWVlZXAyMzAwNTE

# LLM Provider
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here

# Environment
ENVIRONMENT=prod
LOG_LEVEL=INFO
LOG_FORMAT=json

# CORS
ALLOWED_ORIGINS=https://omnidoc.info,https://www.omnidoc.info,https://*.vercel.app

# Security
JWT_SECRET_KEY=your-secret-key-generate-with-openssl-rand-hex-32
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Rate Limiting (Gemini Free Tier)
RATE_LIMIT_PER_MINUTE=2
RATE_LIMIT_PER_DAY=50

# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
```

4. Click **Save**

### Step 3: Configure Startup Command

1. Go to **Configuration** → **General settings**
2. Set **Startup Command**:
```bash
gunicorn src.web.app:app --bind 0.0.0.0:8000 --workers 2 --timeout 120 --worker-class uvicorn.workers.UvicornWorker
```

Or if using Azure's default Python setup:
```bash
python -m uvicorn src.web.app:app --host 0.0.0.0 --port 8000
```

### Step 7: Set Up Automatic Deployment (GitHub Actions)

1. Go to GitHub repository → **Settings** → **Secrets and variables** → **Actions**
2. Add secrets:
   ```
   AZURE_REGISTRY: omnidocregistry.azurecr.io
   AZURE_REGISTRY_USERNAME: omnidocregistry
   AZURE_REGISTRY_PASSWORD: [From ACR Access keys]
   ```
3. Push to `main` - GitHub Actions will automatically build and deploy

Or use Azure's built-in GitHub integration:
1. Go to **Deployment Center**
2. Select **GitHub Actions**
3. Authorize and select repository
4. Azure will create workflow automatically

1. Go to **Deployment Center**
2. Select **GitHub** as source
3. Authorize Azure to access your GitHub
4. Select:
   - **Organization**: Your GitHub username
   - **Repository**: OmniDoc
   - **Branch**: main
   - **Build provider**: GitHub Actions (recommended)
5. Click **Save**

Azure will automatically:
- Build your application
- Deploy on every push to main
- Handle dependencies

### Step 8: Configure Custom Domain

1. Go to **Custom domains**
2. Click **Add custom domain**
3. Enter `api.omnidoc.info`
4. Follow DNS configuration instructions
5. Azure will automatically configure SSL

### Step 9: Set Up Celery Worker (Container) (Separate App Service)

For background tasks, create a second App Service:

1. Create another Web App (same steps as above)
2. Name it `omnidoc-celery-worker`
3. Set **Startup Command**:
```bash
celery -A src.tasks.celery_app worker --loglevel=info
```
4. Use the same environment variables
5. Deploy from the same GitHub repository

## 🖥️ Option 2: Azure VM Deployment (750 Hours/Month Free)

**Best for**: Full control, custom configuration, using your free VM quota

You have **750 hours/month** of B1s VM free (enough for 24/7 operation).

### Step 1: Create Azure VM

1. Go to Azure Portal
2. Click **Create a resource** → **Virtual Machine**
3. Configure:
   - **Subscription**: Your subscription
   - **Resource Group**: Create new
   - **VM name**: `omnidoc-backend`
   - **Image**: Ubuntu 22.04 LTS
   - **Size**: **Standard_B1s** (1 vCPU, 1 GB RAM) - **FREE 750 hours/month**
     - This is perfect for OmniDoc backend
     - You can run both backend and Celery worker on the same VM
   - **Authentication**: SSH public key (recommended)
   - **Public inbound ports**: Allow SSH (22)
4. Click **Review + create** → **Create**

### Step 2: Connect to VM

```bash
ssh azureuser@<your-vm-ip>
```

### Step 3: Run Deployment Script

The Oracle Cloud deployment script can be adapted for Azure. Key differences:

1. **No need to install PostgreSQL/Redis** (using Neon and Upstash)
2. **Use Azure's built-in firewall** instead of UFW
3. **Use Azure Application Gateway** or **Azure Front Door** for load balancing

### Step 4: Manual Setup (Similar to Oracle Cloud)

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install basic tools
sudo apt-get install -y git curl wget build-essential

# Install Node.js (if needed)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Python
sudo apt-get install -y python3.9 python3.9-venv python3-pip

# Clone repository
git clone https://github.com/yimgao/OmniDoc.git
cd OmniDoc

# Run setup
./scripts/setup.sh

# Configure environment
cp .env.production .env
# Edit .env with your values

# Initialize database
./scripts/init_database.sh

# Install Nginx
sudo apt-get install -y nginx

# Configure Nginx (see Oracle Cloud guide for config)
# Configure SSL with Let's Encrypt
# Set up systemd services
```

## 🔧 Azure-Specific Configuration

### Using Azure Database for PostgreSQL (Alternative to Neon)

If you prefer Azure's managed PostgreSQL:

1. Create **Azure Database for PostgreSQL**:
   - Go to **Create a resource** → **Azure Database for PostgreSQL**
   - Choose **Flexible Server** (cheaper)
   - Configure:
     - **Server name**: `omnidoc-db`
     - **Region**: Same as your App Service/VM
     - **PostgreSQL version**: 15
     - **Compute + storage**: Burstable B1ms (Free tier eligible)
   - Set **Admin username** and **password**
   - Click **Create**

2. Get connection string:
   ```
   postgresql://admin:password@omnidoc-db.postgres.database.azure.com/omnidoc?sslmode=require
   ```

3. Update `DATABASE_URL` in App Service/VM environment variables

### Using Azure Cache for Redis (Alternative to Upstash)

If you prefer Azure's managed Redis:

1. Create **Azure Cache for Redis**:
   - Go to **Create a resource** → **Azure Cache for Redis**
   - Configure:
     - **DNS name**: `omnidoc-redis`
     - **Pricing tier**: Basic C0 (Free tier) or Standard
     - **Region**: Same as your App Service/VM
   - Click **Create**

2. Get connection string from **Access keys**:
   ```
   redis://:password@omnidoc-redis.redis.cache.windows.net:6380?ssl=true
   ```

3. Update `REDIS_URL` in App Service/VM environment variables

## 🌐 DNS Configuration (Hostinger)

Same as Oracle Cloud deployment:

1. Login to Hostinger
2. Go to DNS management
3. Add A record:
   - **Type**: A
   - **Name**: `api`
   - **Value**: [Azure App Service IP or VM IP]
   - **TTL**: 3600

For App Service, you can also use CNAME:
- **Type**: CNAME
- **Name**: `api`
- **Value**: `omnidoc-api.azurewebsites.net`

## 🔒 SSL/TLS Configuration

### Azure App Service

SSL is automatically configured when you add a custom domain. Azure provides free SSL certificates.

### Azure VM

Use Let's Encrypt (same as Oracle Cloud):

```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d api.omnidoc.info
```

## 📊 Monitoring

### Azure App Service

1. Go to **Monitoring** → **Metrics**
2. View:
   - CPU usage
   - Memory usage
   - HTTP requests
   - Response time

### Azure VM

1. Go to **Monitoring** → **Metrics**
2. View VM performance metrics
3. Set up **Azure Monitor** for application logs

## 💰 Cost Comparison & Free Tier Analysis

### Your Azure Free Tier Quota (12 months)

Based on your Azure free account, you have:

✅ **Virtual Machines, BS Series, B1s**: 750 hours/month (FREE)
- Perfect for running the backend API
- 1 vCPU, 1 GB RAM
- Enough for OmniDoc backend + Celery worker

✅ **Azure Database for PostgreSQL, Flexible Server B1MS**: 750 hours/month (FREE)
- 1 vCPU, 2 GB RAM
- 32 GB storage included
- Alternative to Neon (but Neon is still recommended - see below)

✅ **Storage**: 100 GB total (various types)
✅ **Data Transfer**: 15 GB/month outbound

### Recommended Setup (Based on Your Free Tier)

#### Option A: Use Azure Free Resources (100% Free)

- **Backend**: Azure VM B1s (750 hours/month FREE)
- **Celery Worker**: Same VM (run both on one instance)
- **Database**: Azure Database for PostgreSQL B1MS (750 hours/month FREE)
- **Redis**: Upstash (free tier) - Azure Cache not in free tier

**Cost**: $0/month (completely free for 12 months)

#### Option B: Hybrid (Recommended - More Reliable)

- **Backend**: Azure VM B1s (750 hours/month FREE)
- **Celery Worker**: Same VM
- **Database**: Neon (free tier) - More reliable, better free tier
- **Redis**: Upstash (free tier) - More reliable, better free tier

**Cost**: $0/month (completely free)

**Why Option B?**
- Neon and Upstash have better free tiers (no time limits)
- Azure Database free tier expires after 12 months
- Easier to manage (managed services)
- Better performance and reliability

### Azure App Service

**Note**: Azure App Service Free tier (F1) is **Always Free** (not shown in your quota list because it's unlimited). You can also use this instead of VM:

- **Backend**: Azure App Service F1 (Always Free)
- **Celery Worker**: Separate App Service F1 (Always Free)
- **Database**: Neon (free tier)
- **Redis**: Upstash (free tier)

**Cost**: $0/month (completely free, no expiration)

## 🔄 Migration from Oracle Cloud

If you're currently on Oracle Cloud and want to migrate:

1. **Export data** (if needed):
   ```bash
   pg_dump $DATABASE_URL > backup.sql
   ```

2. **Update DNS** in Hostinger:
   - Change `api.omnidoc.info` A record to Azure IP

3. **Deploy to Azure** (follow steps above)

4. **Import data** (if needed):
   ```bash
   psql $NEW_DATABASE_URL < backup.sql
   ```

5. **Update frontend** `.env`:
   ```bash
   NEXT_PUBLIC_API_BASE=https://api.omnidoc.info
   ```

6. **Test** and verify everything works

7. **Shut down** Oracle Cloud instance (after confirming Azure works)

## 📝 Quick Start Commands

### App Service

```bash
# View logs
az webapp log tail --name omnidoc-api --resource-group your-resource-group

# Restart
az webapp restart --name omnidoc-api --resource-group your-resource-group

# View environment variables
az webapp config appsettings list --name omnidoc-api --resource-group your-resource-group
```

### VM

```bash
# SSH into VM
ssh azureuser@<vm-ip>

# Check services
sudo systemctl status omnidoc-backend
sudo systemctl status omnidoc-celery

# View logs
sudo journalctl -u omnidoc-backend -f
```

## 🔗 Related Documentation

- [Azure App Service Documentation](https://docs.microsoft.com/azure/app-service/)
- [Azure VM Documentation](https://docs.microsoft.com/azure/virtual-machines/)
- [Azure Free Tier](https://azure.microsoft.com/free/)
- [Deployment Guide](DEPLOYMENT.md)
- [Hostinger DNS Setup](HOSTINGER_DNS_SETUP.md)

## 💡 Tips

1. **Start with App Service** - Easier to set up and manage
2. **Use GitHub Actions** - Automatic deployment on push
3. **Monitor costs** - Set up budget alerts in Azure
4. **Use Azure CLI** - Faster than portal for repeated tasks
5. **Test locally first** - Use Azure CLI to test before deploying

