# Upstash Redis Setup Guide

## Why Upstash?

Upstash is a serverless Redis database that provides:
- **Free tier** with generous limits (10,000 commands/day, 256MB storage)
- **Automatic scaling** - pay only for what you use
- **No server management** - fully managed service
- **Saves memory** on your Oracle Cloud instance (no need to run Redis locally)
- **Global edge network** for low latency
- **REST API** for serverless environments

## Oracle Cloud Free Tier Memory

Oracle Cloud Free Tier provides:
- **2x AMD VM instances**: Each with 1/8 OCPU (~0.25 cores) and **1GB RAM**
- **OR 4x ARM Ampere A1 instances**: Total 4 OCPU and **24GB RAM** (better choice!)

**Recommendation**: Use ARM instances for more memory. With Upstash handling Redis, your server only needs to run:
- FastAPI backend (~200-500MB RAM)
- Celery worker (~200-500MB RAM)
- Nginx (~20-50MB RAM)

Total: ~420MB - 1GB, which fits comfortably in 1GB RAM (AMD) or easily in ARM instances.

## Setup Steps

### 1. Create Upstash Account

1. Go to https://upstash.com
2. Sign up for a free account (GitHub/Google login available)
3. Verify your email if required

### 2. Create a Redis Database

1. Go to https://console.upstash.com
2. Click "Create Database"
3. Choose:
   - **Name**: `omnidoc-redis` (or any name)
   - **Type**: Regional (for lower latency) or Global (for edge network)
   - **Region**: Choose closest to your Oracle Cloud server (e.g., `us-east-1`)
   - **TLS**: Enabled (recommended for production)
4. Click "Create"

### 3. Get Connection Details

After creating the database, you'll see:

1. **Redis URL** (for Celery and standard Redis clients):
   ```
   redis://default:password@endpoint:port
   ```
   Example:
   ```
   redis://default:AXVjAAIncDJlNDY0OGUwNzdkMjc0M2U5OGE2Yzg4ZGUzYWU3YWVlZXAyMzAwNTE@right-loon-30051.upstash.io:6379
   ```

2. **REST URL** (for REST API access):
   ```
   https://right-loon-30051.upstash.io
   ```

3. **REST Token** (for REST API authentication):
   ```
   AXVjAAIncDJlNDY0OGUwNzdkMjc0M2U5OGE2Yzg4ZGUzYWU3YWVlZXAyMzAwNTE
   ```

### 4. Configure Your Application

Update your `.env` file:

```bash
# Upstash Redis Connection (for Celery)
REDIS_URL=redis://default:AXVjAAIncDJlNDY0OGUwNzdkMjc0M2U5OGE2Yzg4ZGUzYWU3YWVlZXAyMzAwNTE@right-loon-30051.upstash.io:6379

# Upstash REST API (optional, for REST-based operations)
UPSTASH_REDIS_REST_URL=https://right-loon-30051.upstash.io
UPSTASH_REDIS_REST_TOKEN=AXVjAAIncDJlNDY0OGUwNzdkMjc0M2U5OGE2Yzg4ZGUzYWU3YWVlZXAyMzAwNTE
```

**Production Connection** (already configured in deployment script):
- Redis URL: `redis://default:AXVjAAIncDJlNDY0OGUwNzdkMjc0M2U5OGE2Yzg4ZGUzYWU3YWVlZXAyMzAwNTE@right-loon-30051.upstash.io:6379`
- REST URL: `https://right-loon-30051.upstash.io`
- REST Token: `AXVjAAIncDJlNDY0OGUwNzdkMjc0M2U5OGE2Yzg4ZGUzYWU3YWVlZXAyMzAwNTE`

## Connection String Format

### Standard Redis URL (for Celery)
```
redis://default:password@endpoint:port
```

### REST API (for serverless/edge functions)
```
UPSTASH_REDIS_REST_URL=https://endpoint.upstash.io
UPSTASH_REDIS_REST_TOKEN=your_token_here
```

## Security Notes

1. **TLS/SSL**: Upstash supports TLS connections. Use `rediss://` instead of `redis://` for secure connections
2. **Password Security**: Never commit your connection string to Git
3. **Environment Variables**: Always use `.env` file (which is in `.gitignore`)
4. **IP Restrictions**: Upstash allows connections from anywhere by default. Consider using Upstash's IP allowlist feature for production.

## Free Tier Limits

Upstash's free tier typically includes:
- **10,000 commands/day** (sufficient for many projects)
- **256MB storage**
- **Unlimited databases**
- **Global edge network**

For OmniDoc, 10,000 commands/day is usually enough unless you're processing many concurrent tasks.

## Monitoring

1. Go to your Upstash dashboard: https://console.upstash.com
2. Click on your database
3. View:
   - Command count (daily limit)
   - Storage usage
   - Connection count
   - Latency metrics
   - Error logs

## Troubleshooting

### Connection Issues

If you can't connect:
1. Check your Redis URL is correct
2. Verify password is included in the URL
3. Check Upstash dashboard for any service issues
4. Verify your IP isn't blocked (if IP restrictions are enabled)
5. Try using `rediss://` (with SSL) instead of `redis://`

### Celery Connection Issues

If Celery can't connect:
1. Verify `REDIS_URL` in `.env` is correct
2. Check Upstash dashboard - is the database active?
3. Test connection manually:
   ```bash
   redis-cli -u "your_redis_url_here" ping
   ```
4. Check Celery logs:
   ```bash
   sudo journalctl -u omnidoc-celery -f
   ```

### Rate Limiting

If you hit the 10,000 commands/day limit:
1. Check Upstash dashboard for usage
2. Consider upgrading to paid tier
3. Optimize your Redis usage (reduce unnecessary operations)

## Migration from Local Redis

If you were using local Redis and want to migrate:

1. Export data from local Redis (if needed):
   ```bash
   redis-cli --rdb dump.rdb
   ```

2. Update `.env` with Upstash connection string:
   ```bash
   REDIS_URL=redis://default:password@endpoint:port
   ```

3. Restart services:
   ```bash
   sudo systemctl restart omnidoc-backend
   sudo systemctl restart omnidoc-celery
   ```

**Note**: Celery tasks are typically transient, so you usually don't need to migrate task data.

## Cost

**Free tier is sufficient for most use cases!**

If you need more:
- Commands: ~$0.20 per 100K commands
- Storage: ~$0.10/GB/month
- Very affordable pay-as-you-go pricing

## Support

- Upstash Docs: https://docs.upstash.com/redis
- Upstash Discord: https://discord.gg/upstash
- Upstash Status: https://status.upstash.com

