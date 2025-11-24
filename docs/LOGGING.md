# Logging System Documentation

## Overview

OmniDoc uses a professional categorized logging system that organizes logs into separate files by category for easier debugging and monitoring.

## Log Categories

The system automatically categorizes logs based on module names:

| Category | Description | Example Modules |
|----------|-------------|----------------|
| **API** | HTTP requests/responses, API errors | `web.routers.*`, `web.app`, `web.health` |
| **Business** | Business logic, coordination, workflow | `coordination.*`, `coordinator`, `workflow` |
| **Agents** | Agent activities (generation, improvement, quality) | `agents.*` |
| **Tasks** | Celery background tasks | `tasks.*`, `celery`, `generation_tasks` |
| **WebSocket** | WebSocket connections and events | `websocket.*` |
| **Database** | Database operations | `context.*`, `context_manager`, `database` |
| **LLM** | LLM API calls and responses | `llm.*`, `provider.*`, `gemini`, `openai`, `ollama` |
| **Error** | All errors across the system (shared) | All modules (ERROR/CRITICAL only) |
| **General** | General application logs | Everything else |

## Log File Structure

Log files are organized by category and date:

```
logs/
├── api_dev_20251124.log          # API requests/responses
├── business_dev_20251124.log      # Business logic
├── agents_dev_20251124.log        # Agent activities
├── tasks_dev_20251124.log         # Background tasks
├── websocket_dev_20251124.log     # WebSocket events
├── database_dev_20251124.log      # Database operations
├── llm_dev_20251124.log           # LLM API calls
├── general_dev_20251124.log      # General logs
└── error_dev_20251124.log         # All errors (shared)
```

## Log Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General informational messages
- **WARNING**: Warning messages (potential issues)
- **ERROR**: Error messages (handled exceptions)
- **CRITICAL**: Critical errors (unhandled exceptions)

## Error Logging

All ERROR and CRITICAL level logs are automatically written to a shared `error_*.log` file in addition to their category-specific log file. This makes it easy to find all errors in one place.

## Usage

### Basic Usage

```python
from src.utils.logger import get_logger

logger = get_logger(__name__)
logger.info("This is an info message")
logger.error("This is an error message")
```

### Explicit Category Override

```python
from src.utils.logger import get_logger, LogCategory

# Force a specific category
logger = get_logger(__name__, category=LogCategory.PERFORMANCE)
```

### Performance Logging

```python
from src.utils.logger import log_performance

@log_performance
def my_function():
    # Function execution time will be logged
    pass
```

## Log Format

### Development (Text Format)
```
2025-11-24 10:30:45 | INFO     | src.web.app | add_request_id:349 | Request started: GET /api/projects
```

### Production (JSON Format)
```json
{
  "timestamp": "2025-11-24T10:30:45.123456",
  "level": "INFO",
  "logger": "src.web.app",
  "message": "Request started: GET /api/projects",
  "module": "app",
  "function": "add_request_id",
  "line": 349
}
```

## Log Rotation

- **Non-Celery processes**: RotatingFileHandler (10MB per file, 5 backups)
- **Celery workers**: FileHandler (to avoid seek errors)

## Configuration

Logging is configured via environment variables:

- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `LOG_FORMAT`: Format type (json, text)
- `LOG_DIR`: Directory for log files (default: `logs/`)
- `ENVIRONMENT`: Environment (dev, prod, test)

## Best Practices

1. **Use appropriate log levels**:
   - DEBUG: Detailed debugging information
   - INFO: Important business events
   - WARNING: Potential issues
   - ERROR: Handled exceptions
   - CRITICAL: Unhandled exceptions

2. **Include context**:
   ```python
   logger.info(f"Processing document {doc_id} for project {project_id}")
   ```

3. **Use structured logging in production**:
   ```python
   logger.info("Document generated", extra={
       'extra_fields': {
           'document_id': doc_id,
           'project_id': project_id,
           'duration': duration
       }
   })
   ```

4. **Log errors with full context**:
   ```python
   logger.error("Failed to generate document", exc_info=True, extra={
       'extra_fields': {
           'document_id': doc_id,
           'project_id': project_id
       }
   })
   ```

## Monitoring

- **API logs**: Monitor request/response patterns, errors
- **Error logs**: Monitor all errors across the system
- **Performance logs**: Monitor slow operations
- **LLM logs**: Monitor API usage and costs
- **Task logs**: Monitor background job execution

## Troubleshooting

### Find all errors
```bash
tail -f logs/error_dev_*.log
```

### Monitor API requests
```bash
tail -f logs/api_dev_*.log
```

### Check agent activities
```bash
tail -f logs/agents_dev_*.log
```

### Monitor background tasks
```bash
tail -f logs/tasks_dev_*.log
```

