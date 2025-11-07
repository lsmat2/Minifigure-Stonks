#!/bin/bash
# Start Celery Beat scheduler for periodic tasks

cd "$(dirname "$0")/.."

echo "Starting Celery Beat scheduler..."
echo "  - Daily catalog sync at 2:00 AM UTC"
echo "  - Price updates every 6 hours"
echo "  - Daily snapshot aggregation at 1:00 AM UTC"
echo "  - Weekly cleanup on Sundays at 3:00 AM UTC"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start Celery Beat
# -A: App module
# beat: Run as beat scheduler
# -l: Log level
# --scheduler: Which scheduler backend to use
celery -A app.celery_app beat \
    -l info \
    --scheduler celery.beat:PersistentScheduler

# Note: PersistentScheduler stores schedule in celerybeat-schedule file
# This prevents duplicate tasks if beat restarts
