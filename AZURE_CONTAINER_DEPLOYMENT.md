# Azure Container Deployment Guide

Complete guide for deploying OmniDoc using Docker containers on Azure.

## 📋 Prerequisites

- Azure account
- Docker installed locally (for testing)
- Azure Container Registry (ACR) - free tier available
- Azure App Service (Free F1 or Basic B1)

## 🎯 Why Container Deployment?

✅ **Exact same environment** everywhere (dev, staging, prod)
✅ **Easy local testing** - `docker run` matches production
✅ **Portable** - works on Azure, AWS, GCP, anywhere
✅ **Version control** - Dockerfile tracks your environment
✅ **Same price** as Code deployment

## 🚀 Step-by-Step Setup

### Step 1: Create Azure Container Registry (ACR)

1. Go to Azure Portal
2. **Create a resource** → **Container Registry**
3. Configure:
   ```
   Registry name: omnidocregistry (or your preferred name)
   Subscription: Your subscription
   Resource Group: omnidoc-rg (create new or use existing)
   Location: Same as your App Service
   SKU: Basic (cheapest, $5/month) or Free (if available)
   ```
4. Click **Create**

**Note**: Free tier ACR includes:
- 500MB storage
- 10,000 pulls/day
- Perfect for your use case

### Step 2: Build and Push Docker Image

#### Option A: Build Locally and Push

```bash
# Login to ACR
az acr login --name omnidocregistry

# Build backend image
docker build -t omnidocregistry.azurecr.io/omnidoc-backend:latest .

# Build Celery worker image
docker build -f Dockerfile.celery -t omnidocregistry.azurecr.io/omnidoc-celery:latest .

# Push images
docker push omnidocregistry.azurecr.io/omnidoc-backend:latest
docker push omnidocregistry.azurecr.io/omnidoc-celery:latest
```

#### Option B: Use GitHub Actions (Automatic)

1. Go to your GitHub repository
2. **Settings** → **Secrets and variables** → **Actions**
3. Add secrets:
   ```
   AZURE_REGISTRY: omnidocregistry.azurecr.io
   AZURE_REGISTRY_USERNAME: omnidocregistry
   AZURE_REGISTRY_PASSWORD: [Get from ACR → Access keys]
   ```
4. Push to `main` branch - GitHub Actions will automatically build and push

### Step 3: Create Azure App Service (Backend)

1. **Create a resource** → **Web App**
2. Configure:
   ```
   Name: omnidoc-api
   Publish: Container (not Code!)
   Operating System: Linux
   Region: Same as ACR
   App Service Plan: Free F1 (or Basic B1)
   ```
3. Click **Next: Docker**
4. Configure:
   ```
   Options: Azure Container Registry
   Registry: omnidocregistry
   Image: omnidoc-backend
   Tag: latest
   ```
5. Click **Review + create** → **Create**

### Step 4: Configure Environment Variables

1. Go to your App Service → **Configuration** → **Application settings**
2. Add all environment variables (same as Code deployment):
   ```
   DATABASE_URL=...
   REDIS_URL=...
   GEMINI_API_KEY=...
   # ... (all other variables)
   ```
3. Click **Save**

### Step 5: Create Celery Worker App Service

1. Create another **Web App** (same steps)
2. Name: `omnidoc-celery-worker`
3. **Publish**: Container
4. **Docker**:
   ```
   Registry: omnidocregistry
   Image: omnidoc-celery
   Tag: latest
   ```
5. Same environment variables
6. **Startup Command** (optional, already in Dockerfile):
   ```
   celery -A src.tasks.celery_app worker --loglevel=info --concurrency=1
   ```

### Step 6: Configure Custom Domain

Same as Code deployment:
1. Go to **Custom domains**
2. Add `api.omnidoc.info`
3. Configure DNS in Hostinger
4. SSL automatically configured

## 🔧 Local Testing

Test your container locally before deploying:

```bash
# Build image
docker build -t omnidoc-backend .

# Run container
docker run -p 8000:8000 \
  -e DATABASE_URL="your_db_url" \
  -e REDIS_URL="your_redis_url" \
  -e GEMINI_API_KEY="your_key" \
  omnidoc-backend

# Test
curl http://localhost:8000/health
```

Or use docker-compose:

```bash
# Copy .env.example to .env and fill in values
cp .env.example .env

# Start services
docker-compose up
```

## 📊 Cost Breakdown

### Container Deployment Costs:

| Service | Free Tier | Paid Tier |
|---------|-----------|-----------|
| **App Service F1** | $0/月 | - |
| **App Service Basic B1** | - | $12.41/月 |
| **Azure Container Registry Basic** | - | $5/月 |
| **ACR Free** | $0/月 (500MB, 10K pulls/day) | - |

### Recommended Setup (100% Free):

- **Backend**: App Service F1 (Always Free)
- **Celery**: App Service F1 (Always Free)
- **ACR**: Free tier (500MB storage)
- **Total**: **$0/月**

**Note**: If you exceed ACR free tier limits, Basic tier is only $5/month.

## 🔄 Updating Container

### Manual Update:

```bash
# Rebuild and push
docker build -t omnidocregistry.azurecr.io/omnidoc-backend:latest .
docker push omnidocregistry.azurecr.io/omnidoc-backend:latest

# Restart App Service
az webapp restart --name omnidoc-api --resource-group omnidoc-rg
```

### Automatic Update (GitHub Actions):

Just push to `main` branch - GitHub Actions will:
1. Build new image
2. Push to ACR
3. Deploy to App Service
4. Restart services

## 🐛 Troubleshooting

### Container won't start:

1. Check logs:
   ```bash
   az webapp log tail --name omnidoc-api --resource-group omnidoc-rg
   ```

2. Check container logs in Azure Portal:
   - App Service → **Log stream**

### Image pull errors:

1. Verify ACR credentials in App Service
2. Check ACR access keys
3. Ensure image exists: `az acr repository list --name omnidocregistry`

### Health check failing:

1. Verify port 8000 is exposed
2. Check `/health` endpoint works
3. Review startup command

## 📝 Quick Reference

### Build Commands:

```bash
# Backend
docker build -t omnidocregistry.azurecr.io/omnidoc-backend:latest .

# Celery
docker build -f Dockerfile.celery -t omnidocregistry.azurecr.io/omnidoc-celery:latest .

# Push both
docker push omnidocregistry.azurecr.io/omnidoc-backend:latest
docker push omnidocregistry.azurecr.io/omnidoc-celery:latest
```

### Azure CLI Commands:

```bash
# Login to ACR
az acr login --name omnidocregistry

# List images
az acr repository list --name omnidocregistry

# Restart App Service
az webapp restart --name omnidoc-api --resource-group omnidoc-rg

# View logs
az webapp log tail --name omnidoc-api --resource-group omnidoc-rg
```

## 🔗 Related Documentation

- [Azure Deployment Guide](AZURE_DEPLOYMENT.md) - General Azure guide
- [Azure Free Tier Setup](AZURE_FREE_TIER_SETUP.md) - Free tier specific guide
- [Deployment Options](DEPLOYMENT_OPTIONS.md) - Code vs Container comparison

