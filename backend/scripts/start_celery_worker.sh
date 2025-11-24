#!/bin/bash
# Start Celery worker for background task processing
# Usage: ./backend/scripts/start_celery_worker.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$BACKEND_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Check if virtual environment exists (created at PROJECT_ROOT/.venv by setup.sh)
if [ ! -d "$PROJECT_ROOT/.venv" ]; then
    echo "❌ Virtual environment not found. Please run ./backend/scripts/setup.sh first"
    exit 1
fi

# Create logs directory if it doesn't exist (in PROJECT_ROOT, where we'll write logs)
mkdir -p logs

# Activate virtual environment or use uv
if command -v uv &> /dev/null; then
    echo "🚀 Starting Celery worker with uv..."
    echo "📝 Logs will be written to logs/celery_worker.log"
    PYTHONPATH="$BACKEND_DIR:$PYTHONPATH" uv run celery -A src.tasks.celery_app worker \
        --loglevel=info \
        --concurrency=2 \
        --max-tasks-per-child=10 \
        --logfile=logs/celery_worker.log \
        --pidfile=logs/celery_worker.pid
else
    echo "🚀 Starting Celery worker..."
    echo "📝 Logs will be written to logs/celery_worker.log"
    source .venv/bin/activate
    PYTHONPATH="$BACKEND_DIR:$PYTHONPATH" celery -A src.tasks.celery_app worker \
        --loglevel=info \
        --concurrency=2 \
        --max-tasks-per-child=10 \
        --logfile=logs/celery_worker.log \
        --pidfile=logs/celery_worker.pid
fi

