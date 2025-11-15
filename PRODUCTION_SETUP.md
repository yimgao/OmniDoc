# Production Setup Guide

Complete guide for deploying OmniDoc in production.

## 📋 Prerequisites

- PostgreSQL 12+
- Redis 6+
- Python 3.9+
- Node.js 18+ (for frontend)

## 🚀 Setup Steps

### 1. Install System Dependencies

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib redis-server

# macOS
brew install postgresql redis
```

### 2. Start Services

```bash
# Linux
sudo systemctl start postgresql
sudo systemctl start redis

# macOS
brew services start postgresql
brew services start redis
```

### 3. Create Database

```bash
createdb omnidoc
```

### 4. Configure Environment

Create `.env` file:

```bash
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/omnidoc

# Redis
REDIS_URL=redis://localhost:6379/0

# LLM Provider
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_api_key_here

# Security (IMPORTANT: Change in production!)
JWT_SECRET_KEY=generate-strong-random-key-here
ENVIRONMENT=prod

# CORS
ALLOWED_ORIGINS=https://omnidoc.info,https://www.omnidoc.info
```

### 5. Install Dependencies

```bash
./scripts/setup.sh
```

### 6. Start Services

**Backend:**
```bash
python backend/uvicorn_dev.py
```

**Celery Worker:**
```bash
./scripts/start_celery_worker.sh
```

## 🐳 Docker Deployment

See `README_PRODUCTION.md` for Docker Compose example.

## 🔒 Security Checklist

- [ ] Strong `JWT_SECRET_KEY`
- [ ] Strong database passwords
- [ ] Redis authentication
- [ ] HTTPS/SSL enabled
- [ ] CORS properly configured
- [ ] Environment variables secured
- [ ] Database backups configured
- [ ] Logging configured

## 📊 Monitoring

### Health Checks

```bash
# Backend
curl http://localhost:8000/docs

# Database
psql $DATABASE_URL -c "SELECT 1;"

# Redis
redis-cli ping

# Celery
celery -A src.tasks.celery_app inspect active
```

## 🐛 Troubleshooting

### Database Issues

```bash
# Check PostgreSQL
pg_isready
psql -l | grep omnidoc
```

### Redis Issues

```bash
# Check Redis
redis-cli ping
redis-cli info
```

### Celery Issues

```bash
# Check worker
celery -A src.tasks.celery_app inspect active
celery -A src.tasks.celery_app worker --loglevel=debug
```

## 📚 Additional Resources

- [Main README](README.md)
- [Backend Documentation](BACKEND.md)
- [Production Guide](README_PRODUCTION.md)
- [Documentation Index](DOCS_INDEX.md)
