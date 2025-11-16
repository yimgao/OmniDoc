# OmniDoc Deployment Guide

Complete guide for deploying OmniDoc in production environments.

## 📋 Table of Contents

1. [Deployment Strategy](#deployment-strategy)
2. [Architecture Overview](#architecture-overview)
3. [Backend Deployment](#backend-deployment)
4. [Frontend Deployment (Vercel)](#frontend-deployment-vercel)
5. [Environment Configuration](#environment-configuration)
6. [Pre-Deployment Checklist](#pre-deployment-checklist)
7. [Post-Deployment Verification](#post-deployment-verification)
8. [Troubleshooting](#troubleshooting)

## 🎯 Deployment Strategy

**Recommendation: Deploy First, Then Iterate**

See [DEPLOYMENT_STRATEGY.md](DEPLOYMENT_STRATEGY.md) for detailed strategy on when to deploy vs. when to update UI first.

### Quick Decision Guide

- ✅ **Deploy Now** if:
  - Core functionality works
  - Critical bugs are fixed
  - Basic accessibility is in place
  - You want real user feedback

- ⏸️ **Wait** if:
  - Critical security issues exist
  - Core features are broken
  - No basic error handling

## 🏗️ Architecture Overview

### Production Architecture

```
┌─────────────────┐
│   Frontend      │
│   (Vercel)      │
│ omnidoc.info    │
└────────┬────────┘
         │ HTTPS
         │
┌────────▼────────┐
│   Backend API   │
│  (Container)    │
│ api.omnidoc.info│
└────┬───────┬────┘
     │       │
┌────▼───┐ ┌─▼──────┐
│ Neon   │ │Upstash │
│  DB    │ │ Redis  │
└────────┘ └────────┘
```

### Components

- **Frontend**: Next.js on Vercel (https://omnidoc.info)
- **Backend**: FastAPI (Docker container, deploy to Railway/Render/Fly.io)
- **Database**: Neon (managed PostgreSQL)
- **Cache/Queue**: Upstash (managed Redis)
- **Task Queue**: Celery workers (same container or separate)

## 🚀 Backend Deployment

### Recommended Platforms

The backend is containerized and can be deployed to:

- **Railway** - Easy deployment, $5/month free credit
- **Render** - Free tier available (with limitations)
- **Fly.io** - Free tier available
- **Google Cloud Run** - Pay-as-you-go with free tier

### Deployment Steps

1. **Build Docker Image**:
   ```bash
   docker build -t omnidoc-backend:latest .
   ```

2. **Push to Registry** (if using private registry):
   ```bash
   docker tag omnidoc-backend:latest your-registry/omnidoc-backend:latest
   docker push your-registry/omnidoc-backend:latest
   ```

3. **Deploy to Platform**:
   - Connect your GitHub repository
   - Select Dockerfile
   - Configure environment variables
   - Deploy!

### Environment Variables

See [Environment Configuration](#-environment-configuration) section below for required variables.

## 🌐 Frontend Deployment (Vercel)

### Quick Setup

1. Go to https://vercel.com
2. Import your GitHub repository
3. Configure:
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (or `pnpm build`)
   - **Output Directory**: `.next`
4. Add environment variable:
   ```
   NEXT_PUBLIC_API_BASE=https://api.omnidoc.info
   ```
5. Deploy!

### Custom Domain

1. Go to Project Settings → Domains
2. Add `omnidoc.info` and `www.omnidoc.info`
3. Follow Vercel's DNS instructions

See [VERCEL_DEPLOYMENT.md](VERCEL_DEPLOYMENT.md) for detailed instructions.

## ⚙️ Environment Configuration

### Backend Environment Files

**Development** (`.env.development`):
- Local PostgreSQL and Redis
- DEBUG logging
- Development CORS settings

**Production** (`.env.production`):
- Neon database (managed PostgreSQL)
- Upstash Redis (managed Redis)
- Production CORS settings
- INFO/JSON logging

**Usage**:
```bash
# Development
cp .env.development .env

# Production
cp .env.production .env
# Then update GEMINI_API_KEY and JWT_SECRET_KEY
```

### Frontend Environment Files

**Development** (`frontend/.env.development`):
```
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

**Production** (`frontend/.env.production`):
```
NEXT_PUBLIC_API_BASE=https://api.omnidoc.info
```

**For Vercel**: Set environment variables in Vercel dashboard.

## ✅ Pre-Deployment Checklist

### Code Readiness
- [ ] All tests pass (`pytest`)
- [ ] No linter errors
- [ ] Documentation updated

### Security
- [ ] Review [SECURITY.md](SECURITY.md) checklist
- [ ] Environment variables secured
- [ ] CORS configured for production domains
- [ ] Rate limiting configured
- [ ] SSL/TLS certificates configured

### Database & Services
- [ ] Neon database configured and accessible
- [ ] Upstash Redis configured and accessible
- [ ] Database tables initialized (`./scripts/init_database.sh`)
- [ ] Connection strings tested

### Configuration
- [ ] `.env` file configured for production
- [ ] `GEMINI_API_KEY` set
- [ ] `JWT_SECRET_KEY` generated (use `openssl rand -hex 32`)
- [ ] `ALLOWED_ORIGINS` set to production domains
- [ ] Logging level set appropriately

### Infrastructure
- [ ] Backend services running
- [ ] Celery workers running (if separate)
- [ ] SSL certificates configured
- [ ] DNS configured correctly

See [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for complete checklist.

## 🔍 Post-Deployment Verification

### Health Checks

```bash
# Backend health
curl https://api.omnidoc.info/health

# API documentation
curl https://api.omnidoc.info/docs

# Database connection
psql "$DATABASE_URL" -c "SELECT 1;"

# Redis connection
redis-cli -u "$REDIS_URL" ping
```

### Service Status

Check service status through your deployment platform's dashboard:
- Railway: View logs in the dashboard
- Render: Check service logs
- Fly.io: Use `fly logs`
- Cloud Run: Check logs in GCP Console

### Frontend Verification

1. Visit https://omnidoc.info
2. Test document generation
3. Verify WebSocket connections work
4. Check browser console for errors

## 🐛 Troubleshooting

### Common Issues

**Backend not starting:**
- Check logs in your deployment platform's dashboard
- Verify environment variables are set correctly
- Test database connection: `psql "$DATABASE_URL" -c "SELECT 1;"`
- Ensure all required environment variables are configured

**Celery not processing tasks:**
- Check worker logs in deployment platform
- Verify Redis connection: `redis-cli -u "$REDIS_URL" ping`
- Ensure `REDIS_URL` is correctly configured
- Check if Celery worker is running (if separate container)

**CORS errors:**
- Verify `ALLOWED_ORIGINS` includes your frontend domain
- Check backend logs for CORS errors
- Restart backend service through your deployment platform

**Database connection issues:**
- Verify `DATABASE_URL` is correct
- Check Neon dashboard for service status
- Ensure SSL mode is set: `?sslmode=require`

**Redis connection issues:**
- Verify `REDIS_URL` is correct
- Check Upstash dashboard for service status
- Test connection: `redis-cli -u "$REDIS_URL" ping`

### Getting Help

- Check [MAINTENANCE.md](MAINTENANCE.md) for detailed troubleshooting
- Review logs in `logs/` directory
- Check service status with systemctl
- Verify environment variables are set correctly

## 📚 Additional Resources

### Setup Guides
- [Neon Database Setup](NEON_SETUP.md) - Configure managed PostgreSQL
- [Upstash Redis Setup](UPSTASH_SETUP.md) - Configure managed Redis
- [Vercel Deployment](VERCEL_DEPLOYMENT.md) - Frontend deployment
- [Deployment Workflow](DEPLOYMENT_WORKFLOW.md) - How to update backend after deployment

### Documentation
- [Backend Guide](BACKEND.md) - API and architecture
- [Frontend Guide](FRONTEND.md) - Frontend development
- [Security Guide](SECURITY.md) - Security configuration
- [Maintenance Guide](MAINTENANCE.md) - Operations and maintenance

### Production Domain
- [Production Domain Config](PRODUCTION_DOMAIN.md) - Domain and DNS setup

## 🔄 Migration from Development

### Key Changes

**Before (Development)**:
- Local PostgreSQL
- Local Redis
- SQLite (old)

**After (Production)**:
- Neon (managed PostgreSQL)
- Upstash (managed Redis)
- All data in database (no file storage)

### Migration Steps

1. Export data from local database (if needed):
   ```bash
   pg_dump -h localhost -U omnidoc omnidoc > backup.sql
   ```

2. Import to Neon:
   ```bash
   psql "$DATABASE_URL" < backup.sql
   ```

3. Update `.env` with production connection strings
4. Restart services

## 📝 Next Steps

After deployment:

1. **Monitor**: Set up monitoring and alerting
2. **Backup**: Configure automated backups
3. **Optimize**: Monitor performance and optimize as needed
4. **Iterate**: Use user feedback to prioritize improvements

---

**Need Help?** Check the troubleshooting sections or open an issue on GitHub.

