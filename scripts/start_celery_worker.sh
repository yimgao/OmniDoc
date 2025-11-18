#!/bin/bash
# Start Celery worker for background task processing
# Usage: ./scripts/start_celery_worker.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run ./scripts/setup.sh first"
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Activate virtual environment or use uv
if command -v uv &> /dev/null; then
    echo "🚀 Starting Celery worker with uv..."
    echo "📝 Logs will be written to logs/celery_worker.log"
    uv run celery -A src.tasks.celery_app worker \
        --loglevel=info \
        --concurrency=2 \
        --max-tasks-per-child=10 \
        --logfile=logs/celery_worker.log \
        --pidfile=logs/celery_worker.pid
else
    echo "🚀 Starting Celery worker..."
    echo "📝 Logs will be written to logs/celery_worker.log"
    source .venv/bin/activate
    celery -A src.tasks.celery_app worker \
        --loglevel=info \
        --concurrency=2 \
        --max-tasks-per-child=10 \
        --logfile=logs/celery_worker.log \
        --pidfile=logs/celery_worker.pid
fi

