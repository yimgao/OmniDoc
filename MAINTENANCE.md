# Maintenance Documentation

Complete guide for maintaining and monitoring OmniDoc in production.

## 📋 Maintenance Overview

Regular maintenance tasks ensure:
- System reliability
- Performance optimization
- Security updates
- Data integrity
- Cost optimization

## 🔄 Regular Maintenance Tasks

### Daily Tasks

**Check Service Status:**

```bash
# Backend
sudo systemctl status omnidoc-backend

# Celery Worker
sudo systemctl status omnidoc-celery

# Frontend (PM2)
pm2 status

# Database
sudo systemctl status postgresql

# Redis
sudo systemctl status redis-server

# Nginx
sudo systemctl status nginx
```

**Monitor Logs:**

```bash
# Backend logs
sudo journalctl -u omnidoc-backend --since "1 hour ago" | tail -50

# Celery logs
sudo journalctl -u omnidoc-celery --since "1 hour ago" | tail -50

# Application logs
tail -f logs/*.log

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

**Check Disk Space:**

```bash
df -h
du -sh /opt/omnidoc/*
```

### Weekly Tasks

**Database Maintenance:**

```bash
# Analyze tables for query optimization
psql $DATABASE_URL -c "ANALYZE;"

# Check database size
psql $DATABASE_URL -c "SELECT pg_size_pretty(pg_database_size('omnidoc'));"

# Check table sizes
psql $DATABASE_URL -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

**Clean Old Logs:**

```bash
# Remove logs older than 30 days
find logs/ -name "*.log" -mtime +30 -delete

# Or use logrotate (configured automatically)
sudo logrotate -f /etc/logrotate.d/omnidoc
```

**Review Error Logs:**

```bash
# Count errors in last week
grep -i error logs/*.log | wc -l

# Most common errors
grep -i error logs/*.log | sort | uniq -c | sort -rn | head -10
```

### Monthly Tasks

**Update Dependencies:**

```bash
cd /opt/omnidoc

# Python dependencies
source .venv/bin/activate
pip list --outdated
pip install --upgrade package_name  # Update specific packages

# Frontend dependencies
cd frontend
pnpm outdated
pnpm update  # Update all packages
```

**Database Backup Verification:**

```bash
# Test restore from backup
psql $DATABASE_URL < backups/omnidoc_latest.sql
```

**Performance Review:**

```bash
# Check slow queries
psql $DATABASE_URL -c "
SELECT 
    query,
    calls,
    total_time,
    mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
"
```

**Resource Usage:**

```bash
# CPU and memory
top
htop

# Disk I/O
iostat -x 1

# Network
iftop
```

## 💾 Backup & Recovery

### Database Backups

**Automated Backup Script:**

Create `/opt/omnidoc/scripts/backup_db.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/opt/omnidoc/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
pg_dump $DATABASE_URL > $BACKUP_DIR/omnidoc_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/omnidoc_$DATE.sql

# Keep only last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

# Optional: Upload to cloud storage
# aws s3 cp $BACKUP_DIR/omnidoc_$DATE.sql.gz s3://your-bucket/backups/
```

**Schedule Daily Backups:**

```bash
# Add to crontab
crontab -e

# Daily at 2 AM
0 2 * * * /opt/omnidoc/scripts/backup_db.sh
```

**Restore from Backup:**

```bash
# Stop services
sudo systemctl stop omnidoc-backend omnidoc-celery

# Restore database
gunzip < backups/omnidoc_20241114_020000.sql.gz | psql $DATABASE_URL

# Start services
sudo systemctl start omnidoc-backend omnidoc-celery
```

### Application Data Backups

**Backup Generated Documents:**

```bash
# Backup docs directory
tar -czf backups/docs_$(date +%Y%m%d).tar.gz docs/

# Keep last 7 days
find backups/ -name "docs_*.tar.gz" -mtime +7 -delete
```

## 📊 Monitoring

### Health Checks

**Automated Health Check Script:**

Create `/opt/omnidoc/scripts/health_check.sh`:

```bash
#!/bin/bash

# Check backend
curl -f http://localhost:8000/docs > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Backend API is down"
    exit 1
fi

# Check database
psql $DATABASE_URL -c "SELECT 1;" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Database connection failed"
    exit 1
fi

# Check Redis
redis-cli -a $REDIS_PASSWORD ping > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Redis connection failed"
    exit 1
fi

# Check Celery
celery -A src.tasks.celery_app inspect active > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Celery worker not responding"
    exit 1
fi

echo "✅ All services healthy"
```

**Schedule Health Checks:**

```bash
# Every 5 minutes
*/5 * * * * /opt/omnidoc/scripts/health_check.sh >> /var/log/omnidoc_health.log 2>&1
```

### Performance Monitoring

**Database Performance:**

```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity;

-- Check slow queries
SELECT 
    pid,
    now() - pg_stat_activity.query_start AS duration,
    query
FROM pg_stat_activity
WHERE state = 'active'
ORDER BY duration DESC;

-- Check table bloat
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    n_dead_tup,
    n_live_tup
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC;
```

**Redis Performance:**

```bash
# Check memory usage
redis-cli -a $REDIS_PASSWORD info memory

# Check connected clients
redis-cli -a $REDIS_PASSWORD info clients

# Monitor commands
redis-cli -a $REDIS_PASSWORD monitor
```

**Application Metrics:**

```bash
# Check Celery task stats
celery -A src.tasks.celery_app inspect stats

# Check active tasks
celery -A src.tasks.celery_app inspect active

# Check scheduled tasks
celery -A src.tasks.celery_app inspect scheduled
```

## 🔧 Troubleshooting

### Service Won't Start

**Backend Issues:**

```bash
# Check logs
sudo journalctl -u omnidoc-backend -n 100

# Test manually
cd /opt/omnidoc
source .venv/bin/activate
python backend/uvicorn_dev.py

# Check port availability
sudo lsof -i :8000
```

**Celery Issues:**

```bash
# Check logs
sudo journalctl -u omnidoc-celery -n 100

# Test manually
cd /opt/omnidoc
source .venv/bin/activate
celery -A src.tasks.celery_app worker --loglevel=debug

# Check Redis connection
redis-cli -a $REDIS_PASSWORD ping
```

### Database Issues

**Connection Problems:**

```bash
# Test connection
psql $DATABASE_URL -c "SELECT 1;"

# Check PostgreSQL is running
sudo systemctl status postgresql

# Check connection limits
psql $DATABASE_URL -c "SHOW max_connections;"
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"
```

**Performance Issues:**

```bash
# Check for locks
psql $DATABASE_URL -c "
SELECT 
    pid,
    locktype,
    relation::regclass,
    mode,
    granted
FROM pg_locks
WHERE NOT granted;
"

# Kill long-running queries
psql $DATABASE_URL -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'active' AND query_start < now() - interval '5 minutes';"
```

### Redis Issues

**Memory Issues:**

```bash
# Check memory usage
redis-cli -a $REDIS_PASSWORD info memory

# Clear cache if needed
redis-cli -a $REDIS_PASSWORD FLUSHDB

# Check for large keys
redis-cli -a $REDIS_PASSWORD --bigkeys
```

**Connection Issues:**

```bash
# Test connection
redis-cli -a $REDIS_PASSWORD ping

# Check Redis is running
sudo systemctl status redis-server

# Check configuration
redis-cli -a $REDIS_PASSWORD CONFIG GET "*"
```

## 🔄 Updates & Upgrades

### Application Updates

```bash
cd /opt/omnidoc

# Backup first
./scripts/backup_db.sh

# Pull latest code
git pull origin main

# Update dependencies
./scripts/setup.sh

# Restart services
sudo systemctl restart omnidoc-backend omnidoc-celery
pm2 restart omnidoc-frontend
```

### System Updates

```bash
# Update system packages
sudo apt-get update
sudo apt-get upgrade -y

# Update PostgreSQL (if needed)
sudo apt-get install postgresql-15

# Update Redis (if needed)
sudo apt-get install redis-server
```

### Dependency Updates

**Python Dependencies:**

```bash
# Check outdated packages
pip list --outdated

# Update specific package
pip install --upgrade package_name

# Update all packages (careful!)
pip list --outdated | cut -d ' ' -f1 | xargs -n1 pip install --upgrade
```

**Node.js Dependencies:**

```bash
cd frontend

# Check outdated packages
pnpm outdated

# Update specific package
pnpm update package_name

# Update all packages
pnpm update
```

## 📈 Performance Optimization

### Database Optimization

**Regular Vacuum:**

```sql
-- Vacuum and analyze
VACUUM ANALYZE;

-- Vacuum specific table
VACUUM ANALYZE project_status;

-- Check for bloat
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    n_dead_tup,
    n_live_tup,
    round(n_dead_tup::numeric / NULLIF(n_live_tup, 0) * 100, 2) AS dead_ratio
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY dead_ratio DESC;
```

**Index Optimization:**

```sql
-- Check unused indexes
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;

-- Check missing indexes
SELECT 
    schemaname,
    tablename,
    seq_scan,
    seq_tup_read,
    idx_scan,
    seq_tup_read / seq_scan AS avg_seq_read
FROM pg_stat_user_tables
WHERE seq_scan > 0
ORDER BY avg_seq_read DESC;
```

### Redis Optimization

**Memory Management:**

```bash
# Set max memory
redis-cli -a $REDIS_PASSWORD CONFIG SET maxmemory 256mb
redis-cli -a $REDIS_PASSWORD CONFIG SET maxmemory-policy allkeys-lru

# Monitor memory
redis-cli -a $REDIS_PASSWORD info memory | grep used_memory_human
```

## 🗑️ Cleanup Tasks

### Old Projects

```sql
-- Delete projects older than 90 days
DELETE FROM projects 
WHERE updated_at < NOW() - INTERVAL '90 days';

-- Or archive instead of delete
```

### Old Logs

```bash
# Remove logs older than 30 days
find logs/ -name "*.log" -mtime +30 -delete

# Compress old logs
find logs/ -name "*.log" -mtime +7 -exec gzip {} \;
```

### Cache Cleanup

```bash
# Clear Redis cache
redis-cli -a $REDIS_PASSWORD FLUSHDB

# Or clear specific patterns
redis-cli -a $REDIS_PASSWORD --scan --pattern "cache:*" | xargs redis-cli -a $REDIS_PASSWORD DEL
```

## 📚 Additional Resources

- [PostgreSQL Maintenance](https://www.postgresql.org/docs/current/maintenance.html)
- [Redis Administration](https://redis.io/docs/management/)
- [Systemd Service Management](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [PM2 Documentation](https://pm2.keymetrics.io/docs/usage/quick-start/)
- [Deployment Strategy](DEPLOYMENT_STRATEGY.md) - Maintenance considerations
- [Production Setup](PRODUCTION_SETUP.md) - Production maintenance procedures
- [Security Guide](SECURITY.md) - Security monitoring

