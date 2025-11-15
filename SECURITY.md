# Security Considerations

This document outlines security measures implemented in OmniDoc and considerations for deployment.

## Authentication & Authorization

### Current State
- **No authentication required** - API is currently open
- **No user sessions** - Stateless API design
- **No authorization checks** - All endpoints accessible to anyone

### Planned Improvements
- OAuth2 with JWT tokens (see `src/auth/` directory)
- User-based project ownership
- Role-based access control (RBAC)

## Input Validation

### Implemented
- ✅ **Request validation** - Pydantic models validate all inputs
- ✅ **Length limits** - `user_idea` limited to 5000 characters
- ✅ **Format validation** - `project_id` and `document_id` format checked
- ✅ **Type checking** - Type hints and validation on all endpoints
- ✅ **SQL injection prevention** - Parameterized queries (psycopg2)

### Security Measures
```python
# Example: Input validation in projects.py
user_idea: str = Field(..., min_length=1, max_length=5000)
selected_documents: List[str] = Field(default_factory=list)

# Format validation
if not project_id or not project_id.startswith("project_") or len(project_id) > 255:
    raise HTTPException(status_code=400, detail="Invalid project ID format.")
```

## Rate Limiting

### Implemented
- ✅ **slowapi** - Rate limiting on all endpoints
- ✅ **Per-IP limits** - Limits based on client IP address
- ✅ **Endpoint-specific limits**:
  - Document templates: 100/minute
  - Project creation: 10/minute
  - Status checks: 60/minute
  - Downloads: 30/minute

### Configuration
```python
@limiter.limit("10/minute")
async def create_project(...):
    ...
```

## CORS Configuration

### Current Settings
- **Allowed origins**: Configurable via `ALLOWED_ORIGINS` environment variable
- **Default**: `http://localhost:3000`
- **Credentials**: Enabled
- **Methods**: All methods allowed
- **Headers**: All headers allowed

### Security Recommendation
In production, restrict to specific domains:
```python
ALLOWED_ORIGINS = [
    "https://omnidoc.info",
    "https://www.omnidoc.info",
]
```

**Production Domain:** `https://omnidoc.info/`

## Database Security

### Implemented
- ✅ **Connection pooling** - Prevents connection exhaustion
- ✅ **Parameterized queries** - Prevents SQL injection
- ✅ **Connection string from env** - No hardcoded credentials
- ✅ **Connection cleanup** - Proper resource management

### Recommendations
- Use environment variables for database credentials
- Enable SSL/TLS for database connections in production
- Use read-only database user for queries when possible
- Regular database backups

## Redis Security

### Current State
- **No authentication** - Redis accessible without password (development)
- **No encryption** - Connections not encrypted

### Production Recommendations
- Enable Redis AUTH (password)
- Use Redis ACLs for fine-grained access control
- Enable TLS/SSL for Redis connections
- Restrict Redis to localhost or VPN
- Use Redis Sentinel for high availability

## WebSocket Security

### Implemented
- ✅ **Connection limits** - Max 10 connections per project
- ✅ **Project ID validation** - Invalid IDs rejected
- ✅ **Error handling** - Graceful error handling and cleanup

### Recommendations
- Add authentication to WebSocket connections
- Implement rate limiting for WebSocket messages
- Add message size limits
- Monitor for abuse patterns

## File System Security

### Implemented
- ✅ **Path validation** - File paths validated before access
- ✅ **Error handling** - File read errors handled gracefully
- ✅ **Content type** - Markdown files served with correct MIME type

### Recommendations
- Sanitize file paths to prevent directory traversal
- Restrict file access to specific directories
- Implement file size limits
- Scan uploaded files for malware (if file uploads added)

## Environment Variables

### Security Best Practices
- Never commit `.env` files to version control
- Use secrets management (e.g., Kubernetes secrets, AWS Secrets Manager)
- Rotate credentials regularly
- Use different credentials for dev/staging/production

### Sensitive Variables
- `DATABASE_URL` - Contains database credentials
- `REDIS_URL` - Contains Redis connection info
- `GEMINI_API_KEY` - API key for LLM provider
- `JWT_SECRET_KEY` - Secret for JWT signing (when implemented)

## Logging & Monitoring

### Implemented
- ✅ **Request ID tracking** - All requests have unique IDs
- ✅ **Structured logging** - Consistent log format
- ✅ **Error logging** - Full stack traces for errors
- ✅ **Rate limit logging** - Rate limit violations logged

### Security Considerations
- **Don't log sensitive data** - API keys, passwords, tokens
- **Sanitize user input in logs** - Prevent log injection
- **Rotate log files** - Prevent disk space issues
- **Monitor for suspicious patterns** - Failed auth attempts, rate limit violations

## Dependencies

### Security Updates
- Regularly update dependencies to patch vulnerabilities
- Use `pip-audit` or `safety` to check for known vulnerabilities
- Monitor security advisories for dependencies

### Current Dependencies
- FastAPI - Web framework
- Celery - Task queue
- PostgreSQL - Database
- Redis - Cache and message broker
- psycopg2 - Database adapter

## Deployment Security

### Recommendations
1. **HTTPS/SSL** - Always use HTTPS in production
2. **Firewall** - Restrict access to necessary ports only
3. **Network isolation** - Use private networks for database/Redis
4. **Regular updates** - Keep OS and dependencies updated
5. **Backup strategy** - Regular database backups
6. **Monitoring** - Set up alerts for security events
7. **Incident response** - Have a plan for security incidents

## Security Checklist

Before deploying to production:

- [ ] Enable authentication (OAuth2/JWT)
- [ ] Configure CORS for specific domains
- [ ] Enable Redis authentication
- [ ] Use SSL/TLS for all connections
- [ ] Set up rate limiting (already implemented)
- [ ] Configure firewall rules
- [ ] Set up monitoring and alerts
- [ ] Review and update dependencies
- [ ] Perform security audit
- [ ] Set up backup and recovery
- [ ] Document incident response procedures

## Reporting Security Issues

If you discover a security vulnerability, please:
1. **Do not** create a public GitHub issue
2. Email security concerns to the maintainers
3. Provide detailed information about the vulnerability
4. Allow time for the issue to be addressed before disclosure

## 📚 Additional Resources

- [Deployment Strategy](DEPLOYMENT_STRATEGY.md) - Security considerations in deployment
- [Production Setup](PRODUCTION_SETUP.md) - Production security configuration
- [Backend Documentation](BACKEND.md) - Backend security implementation
- [Maintenance Guide](MAINTENANCE.md) - Security monitoring and maintenance
