# Production Deployment Guide

This guide covers production-ready features and deployment strategies for OmniDoc.

## ✅ Production Features

OmniDoc includes the following production-ready improvements:

### 1. PostgreSQL Database
- ✅ Migrated from SQLite to PostgreSQL
- ✅ No file-locking issues
- ✅ Better concurrent user support
- ✅ Production-ready scalability

### 2. Celery Task Queue
- ✅ Background job processing with Redis broker
- ✅ Tasks survive server restarts
- ✅ Independent worker scaling
- ✅ Task monitoring capabilities

### 3. Redis Caching
- ✅ Fast caching for document templates
- ✅ Reduced database load
- ✅ Better API response times

### 4. JWT Authentication Infrastructure
- ✅ Token-based authentication ready
- ✅ OAuth2 provider support (Google, GitHub)
- ⚠️ Not yet integrated into API endpoints

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend  │─────▶│  FastAPI App │─────▶│  PostgreSQL │
│  (Next.js)  │      │   (Port 8000)│      │   Database  │
└─────────────┘      └──────────────┘      └─────────────┘
                             │
                             ▼
                      ┌──────────────┐
                      │    Redis      │
                      │  (Broker +    │
                      │   Cache)      │
                      └──────────────┘
                             │
                             ▼
                      ┌──────────────┐
                      │ Celery Worker │
                      │ (Background   │
                      │   Tasks)      │
                      └──────────────┘
```

## 🚀 Quick Start

### 1. Install System Dependencies

```bash
# PostgreSQL
sudo apt-get install postgresql postgresql-contrib  # Ubuntu/Debian
brew install postgresql  # macOS

# Redis
sudo apt-get install redis-server  # Ubuntu/Debian
brew install redis  # macOS

# Start services
sudo systemctl start postgresql redis  # Linux
brew services start postgresql redis   # macOS
```

### 2. Setup Database

```bash
createdb omnidoc
```

### 3. Configure Environment

Update `.env`:

```bash
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/omnidoc

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT (CHANGE IN PRODUCTION!)
JWT_SECRET_KEY=your-very-secure-secret-key-here

# OAuth2 (Optional)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
```

### 4. Install Dependencies

```bash
./scripts/setup.sh
```

### 5. Start Services

**Terminal 1 - Backend:**
```bash
python backend/uvicorn_dev.py
```

**Terminal 2 - Celery Worker:**
```bash
./scripts/start_celery_worker.sh
```

## 📦 Docker Deployment

### Docker Compose Example

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: omnidoc
      POSTGRES_USER: omnidoc
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: .
    command: uvicorn src.web.app:app --host 0.0.0.0 --port 8000
    environment:
      DATABASE_URL: postgresql://omnidoc:${POSTGRES_PASSWORD}@postgres:5432/omnidoc
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    ports:
      - "8000:8000"

  celery-worker:
    build: .
    command: celery -A src.tasks.celery_app worker --loglevel=info
    environment:
      DATABASE_URL: postgresql://omnidoc:${POSTGRES_PASSWORD}@postgres:5432/omnidoc
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis

volumes:
  postgres_data:
```

### Build and Run

```bash
docker-compose up -d
```

## 🔒 Security Checklist

- [ ] Change `JWT_SECRET_KEY` to a strong random value
- [ ] Use strong database passwords
- [ ] Configure Redis authentication
- [ ] Update `ALLOWED_ORIGINS` for production domain
- [ ] Enable HTTPS/SSL
- [ ] Set `ENVIRONMENT=prod`
- [ ] Configure proper logging
- [ ] Set up database backups
- [ ] Configure firewall rules

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

### Logging

Logs are written to `logs/` directory. Configure log rotation in production.

## 🔄 Migration from Development

### Before (Development)
- SQLite database (`context.db`)
- `asyncio.create_task` for background jobs
- No caching
- No authentication

### After (Production)
- PostgreSQL database
- Celery task queue
- Redis caching
- JWT authentication infrastructure

## 📝 Next Steps

1. **Complete Authentication**: Add auth middleware and user management
2. **Monitoring**: Set up logging aggregation and metrics
3. **Load Balancing**: Use nginx for multiple backend instances
4. **SSL/TLS**: Configure HTTPS
5. **Backup Strategy**: Automated database backups

## 📚 Additional Resources

- **Main README**: [README.md](README.md)
- **Backend Setup**: [BACKEND.md](BACKEND.md)
- **Detailed Production Guide**: [PRODUCTION_SETUP.md](PRODUCTION_SETUP.md)
- **Documentation Index**: [DOCS_INDEX.md](DOCS_INDEX.md)
