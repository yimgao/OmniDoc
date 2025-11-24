# OmniDoc Dockerfile
# Unified Dockerfile for both API server and Celery worker
# Use Railway's "Custom Start Command" to override for Celery worker

FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY backend/pyproject.toml backend/requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code (backend)
COPY backend/ ./backend/
# Copy shared files (if any)
COPY docker-compose.yml .dockerignore ./

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port (for API server, Celery doesn't need it but Railway may require it)
EXPOSE 8000

# Health check (only for API server)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set PYTHONPATH to include backend directory
ENV PYTHONPATH=/app/backend:$PYTHONPATH

# Default command: API server
# For Celery worker, override in Railway Settings → Deploy → Custom Start Command:
# PYTHONPATH=/app/backend:$PYTHONPATH celery -A src.tasks.celery_app worker --loglevel=info --concurrency=1
CMD ["gunicorn", "src.web.app:app", "--bind", "0.0.0.0:8000", "--workers", "1", "--timeout", "120", "--worker-class", "uvicorn.workers.UvicornWorker", "--chdir", "/app/backend"]

