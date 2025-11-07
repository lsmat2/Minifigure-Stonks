#!/bin/bash
# Start Celery worker for processing tasks

cd "$(dirname "$0")/.."

echo "Starting Celery worker..."
echo "  - Scraping queue: Fetches data from APIs"
echo "  - Processing queue: Aggregates and cleans data"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start Celery worker with both queues
# -A: App module
# worker: Run as worker
# -Q: Queues to process
# -l: Log level
# --concurrency: Number of worker threads (1 for rate limiting)
celery -A app.celery_app worker \
    -Q scraping,processing \
    -l info \
    --concurrency=2 \
    --max-tasks-per-child=50

# Note: --max-tasks-per-child restarts workers after N tasks to prevent memory leaks
# --concurrency=2 means 2 tasks can run in parallel (adjust based on rate limits)
