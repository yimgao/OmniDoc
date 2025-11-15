# Neon Database Setup Guide

## Why Neon?

Neon is a serverless PostgreSQL database that provides:
- **Free tier** with generous limits (usually 0.5GB storage, 1 project)
- **Automatic backups** and point-in-time recovery
- **No server management** - fully managed service
- **Saves memory** on your Oracle Cloud instance (no need to run PostgreSQL locally)
- **Easy scaling** when you need more resources

## Oracle Cloud Free Tier Memory

Oracle Cloud Free Tier provides:
- **2x AMD VM instances**: Each with 1/8 OCPU (~0.25 cores) and **1GB RAM**
- **OR 4x ARM Ampere A1 instances**: Total 4 OCPU and **24GB RAM** (better choice!)

**Recommendation**: Use ARM instances for more memory. With Neon handling the database, your server only needs to run:
- FastAPI backend (~200-500MB RAM)
- Celery worker (~200-500MB RAM)
- Redis (~50-100MB RAM)
- Nginx (~20-50MB RAM)

Total: ~500MB - 1.1GB, which fits comfortably in 1GB RAM (AMD) or easily in ARM instances.

## Setup Steps

### 1. Create Neon Account

1. Go to https://neon.tech
2. Sign up for a free account (GitHub/Google login available)
3. Verify your email if required

### 2. Create a Project

1. Click "Create Project"
2. Choose a project name (e.g., "omnidoc")
3. Select a region closest to your Oracle Cloud server
4. Choose PostgreSQL version (15 or 16 recommended)
5. Click "Create Project"

### 3. Get Connection String

1. After project creation, you'll see a connection string like:
   ```
   postgresql://user:password@ep-xxx-xxx.region.neon.tech/dbname?sslmode=require
   ```
2. Click "Copy" to copy the connection string
3. **Important**: Save this securely - you'll need it for your `.env` file

### 4. Configure Your Application

Update your `.env` file:

```bash
# Neon Database Connection
DATABASE_URL=postgresql://user:password@ep-xxx-xxx.region.neon.tech/dbname?sslmode=require
```

### 5. Initialize Database Tables

Run the database initialization script:

```bash
./scripts/init_database.sh
```

This will create all necessary tables in your Neon database.

## Connection String Format

Neon connection strings typically look like:
```
postgresql://[user]:[password]@[endpoint]/[dbname]?sslmode=require
```

Example:
```
postgresql://neondb_owner:AbCdEf123456@ep-cool-darkness-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
```

## Security Notes

1. **SSL Required**: Neon requires SSL connections (`sslmode=require`)
2. **Password Security**: Never commit your connection string to Git
3. **Environment Variables**: Always use `.env` file (which is in `.gitignore`)
4. **IP Restrictions**: Neon allows connections from anywhere by default. Consider using Neon's IP allowlist feature for production.

## Free Tier Limits

Neon's free tier typically includes:
- **0.5GB storage** (sufficient for many projects)
- **1 project**
- **Automatic backups** (7-day retention)
- **Branching** (for database versioning)

For OmniDoc, 0.5GB is usually enough unless you're storing many large documents.

## Monitoring

1. Go to your Neon dashboard: https://console.neon.tech
2. Click on your project
3. View:
   - Database size
   - Connection count
   - Query performance
   - Backup status

## Troubleshooting

### Connection Issues

If you can't connect:
1. Check your connection string is correct
2. Verify `sslmode=require` is included
3. Check Neon dashboard for any service issues
4. Verify your IP isn't blocked (if IP restrictions are enabled)

### Database Initialization

If `init_database.sh` fails:
1. Verify `DATABASE_URL` in `.env` is correct
2. Check Neon dashboard - is the database active?
3. Try connecting manually with `psql`:
   ```bash
   psql "your_connection_string_here"
   ```

## Migration from Local PostgreSQL

If you were using local PostgreSQL and want to migrate:

1. Export data from local database:
   ```bash
   pg_dump -h localhost -U omnidoc omnidoc > backup.sql
   ```

2. Import to Neon:
   ```bash
   psql "your_neon_connection_string" < backup.sql
   ```

3. Update `.env` with Neon connection string
4. Restart your application

## Cost

**Free tier is sufficient for most use cases!**

If you need more:
- Storage: ~$0.10/GB/month
- Compute: Pay-as-you-go (very affordable)

## Support

- Neon Docs: https://neon.tech/docs
- Neon Discord: https://discord.gg/neondatabase
- Neon Status: https://status.neon.tech

