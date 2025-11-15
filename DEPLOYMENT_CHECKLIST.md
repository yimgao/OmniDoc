# Deployment Checklist

Use this checklist before deploying OmniDoc to production.

## Pre-Deployment

### Code Readiness
- [ ] All tests pass (`pytest`)
- [ ] Code coverage meets requirements (>80% for critical paths)
- [ ] No linter errors (`ruff check`, `black --check`)
- [ ] All documentation updated
- [ ] Changelog updated
- [ ] Version numbers updated

### Security
- [ ] Review [SECURITY.md](./SECURITY.md) checklist
- [ ] Environment variables secured (no hardcoded secrets)
- [ ] CORS configured for production domains only
- [ ] Rate limiting configured appropriately
- [ ] Input validation tested
- [ ] SQL injection prevention verified
- [ ] Dependencies updated (check for vulnerabilities)
- [ ] SSL/TLS certificates configured
- [ ] Firewall rules configured

### Database
- [ ] Database migrations tested
- [ ] Backup strategy in place
- [ ] Database connection pooling configured
- [ ] Database credentials secured
- [ ] Connection string uses SSL in production

### Infrastructure
- [ ] PostgreSQL running and accessible
- [ ] Redis running and accessible
- [ ] Celery workers configured and running
- [ ] Nginx/reverse proxy configured
- [ ] SSL certificates installed
- [ ] Domain DNS configured
- [ ] Monitoring and alerting set up

### Configuration
- [ ] `.env` file configured for production
- [ ] `ALLOWED_ORIGINS` set to production domains
- [ ] `DATABASE_URL` configured
- [ ] `REDIS_URL` configured
- [ ] `GEMINI_API_KEY` or other LLM keys configured
- [ ] Logging level set appropriately
- [ ] Error reporting configured (if using Sentry, etc.)

### Testing
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Backward compatibility verified
- [ ] Load testing performed (if applicable)
- [ ] Security testing performed
- [ ] Manual testing completed

## Deployment Steps

1. **Backup Current State**
   ```bash
   # Backup database
   pg_dump omnidoc > backup_$(date +%Y%m%d).sql
   
   # Backup configuration
   cp .env .env.backup
   ```

2. **Update Code**
   ```bash
   git pull origin main
   # or
   git checkout <release-tag>
   ```

3. **Update Dependencies**
   ```bash
   uv sync --all-extras
   # or
   pip install -r requirements.txt
   ```

4. **Run Migrations** (if any)
   ```bash
   # Database migrations are automatic on first run
   # But verify schema is up to date
   ```

5. **Restart Services**
   ```bash
   # Restart API server
   sudo systemctl restart omnidoc-api
   
   # Restart Celery worker
   sudo systemctl restart omnidoc-celery
   ```

6. **Verify Deployment**
   ```bash
   # Check health endpoint
   curl http://localhost:8000/health
   
   # Check readiness
   curl http://localhost:8000/ready
   
   # Check API docs
   curl http://localhost:8000/docs
   ```

## Post-Deployment

### Verification
- [ ] Health check endpoint returns 200
- [ ] Readiness check endpoint returns 200
- [ ] API endpoints respond correctly
- [ ] WebSocket connections work
- [ ] Document generation works end-to-end
- [ ] Monitoring shows normal metrics
- [ ] No errors in logs

### Monitoring
- [ ] Check application logs for errors
- [ ] Verify metrics are being collected
- [ ] Check database connection pool status
- [ ] Monitor Celery task queue
- [ ] Verify rate limiting is working
- [ ] Check response times

### Rollback Plan
- [ ] Know how to rollback if issues occur
- [ ] Database backup available
- [ ] Previous version tagged in git
- [ ] Rollback procedure documented

## Quick Reference Commands

```bash
# Check service status
sudo systemctl status omnidoc-api
sudo systemctl status omnidoc-celery

# View logs
sudo journalctl -u omnidoc-api -f
sudo journalctl -u omnidoc-celery -f

# Test health
curl http://localhost:8000/health
curl http://localhost:8000/ready

# Check database connection
psql $DATABASE_URL -c "SELECT 1"

# Check Redis connection
redis-cli -u $REDIS_URL ping

# Run tests
pytest

# Check code quality
ruff check src/
black --check src/
```

## Emergency Contacts

- **On-call Engineer**: [Contact Info]
- **Database Admin**: [Contact Info]
- **DevOps Team**: [Contact Info]

## Notes

- Always test in staging environment first
- Deploy during low-traffic periods when possible
- Have rollback plan ready
- Monitor closely after deployment
- Document any issues encountered
