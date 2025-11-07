# Celery Task Queue Documentation

This document explains how to use Celery for async data collection and processing in Minifigure-Stonks.

## Overview

Celery handles:
- **Scraping Tasks**: Fetch data from external APIs (Brickset, eBay)
- **Aggregation Tasks**: Create daily price snapshots, cleanup old data
- **Scheduled Jobs**: Automatic daily/hourly updates via Celery Beat

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   FastAPI   │─────▶│   Celery     │─────▶│   Worker    │
│   Backend   │      │   Broker     │      │   Process   │
└─────────────┘      │   (Redis)    │      └─────────────┘
                     └──────────────┘             │
                            │                     │
                            ▼                     ▼
                     ┌──────────────┐      ┌─────────────┐
                     │ Celery Beat  │      │  PostgreSQL │
                     │  Scheduler   │      │   Database  │
                     └──────────────┘      └─────────────┘
```

## Prerequisites

1. **Redis** must be running (Celery broker)
   ```bash
   # Start via Docker
   docker-compose up -d redis

   # Or install locally
   brew install redis  # macOS
   redis-server
   ```

2. **PostgreSQL** must be running (data storage)
   ```bash
   docker-compose up -d db
   ```

3. **Environment variables** in `backend/.env`:
   ```
   REDIS_URL=redis://localhost:6379/0
   DATABASE_URL=postgresql://...
   BRICKSET_API_KEY=your_key_here
   EBAY_APP_ID=your_app_id_here
   ```

## Running Celery

### Option 1: Run Components Individually

#### 1. Start Celery Worker (processes tasks)
```bash
cd backend
./scripts/start_celery_worker.sh
```

Or manually:
```bash
cd backend
celery -A app.celery_app worker -Q scraping,processing -l info --concurrency=2
```

#### 2. Start Celery Beat (scheduler for periodic tasks)
```bash
cd backend
./scripts/start_celery_beat.sh
```

Or manually:
```bash
cd backend
celery -A app.celery_app beat -l info
```

### Option 2: Run All Services with Docker Compose

```bash
# Start everything (PostgreSQL, Redis, API, Worker, Beat)
docker-compose up -d
```

## Available Tasks

### Scraping Tasks

Located in `app/tasks/scraping_tasks.py`

#### 1. **sync_catalog_from_brickset**
Fetch minifigure catalog from Brickset API.

```python
from app.tasks.scraping_tasks import sync_catalog_from_brickset

# Queue task
task = sync_catalog_from_brickset.delay(
    theme="Star Wars",  # Optional: filter by theme
    year=2023,          # Optional: filter by year
    limit=500           # Optional: max minifigures to fetch
)

# Check status
task.ready()        # True if complete
task.successful()   # True if completed without error
task.get()          # Get result (blocks until complete)
```

**Scheduled**: Daily at 2:00 AM UTC

#### 2. **fetch_prices_for_minifigure**
Fetch price listings for a specific minifigure from eBay.

```python
from app.tasks.scraping_tasks import fetch_prices_for_minifigure

# Queue task
task = fetch_prices_for_minifigure.delay(
    minifigure_id="9eb475d0-9b38-4bc6-941c-20a9a37df7a7",
    condition="NEW"  # Optional: NEW, USED, SEALED
)
```

#### 3. **update_all_prices**
Update prices for multiple minifigures (batch operation).

```python
from app.tasks.scraping_tasks import update_all_prices

# Queue task to update 50 most recent minifigures
task = update_all_prices.delay(batch_size=50)
```

**Scheduled**: Every 6 hours

#### 4. **fetch_prices_for_set_number**
Convenience task to fetch prices by set number (e.g., "sw0001").

```python
from app.tasks.scraping_tasks import fetch_prices_for_set_number

task = fetch_prices_for_set_number.delay(
    set_number="sw0001",
    condition="NEW"
)
```

### Aggregation Tasks

Located in `app/tasks/aggregation_tasks.py`

#### 1. **aggregate_daily_snapshots**
Create daily price snapshots (min/max/avg/median) from price listings.

```python
from app.tasks.aggregation_tasks import aggregate_daily_snapshots

# Aggregate yesterday's prices
task = aggregate_daily_snapshots.delay()

# Or specify a date
task = aggregate_daily_snapshots.delay(target_date="2025-01-15")
```

**Scheduled**: Daily at 1:00 AM UTC

#### 2. **aggregate_snapshot_for_minifigure**
Create snapshot for a single minifigure (real-time updates).

```python
from app.tasks.aggregation_tasks import aggregate_snapshot_for_minifigure

task = aggregate_snapshot_for_minifigure.delay(
    minifigure_id="9eb475d0-9b38-4bc6-941c-20a9a37df7a7",
    target_date="2025-01-15"  # Optional, defaults to today
)
```

#### 3. **cleanup_old_listings**
Delete price listings older than N days (keeps snapshots).

```python
from app.tasks.aggregation_tasks import cleanup_old_listings

# Delete listings older than 90 days
task = cleanup_old_listings.delay(days_to_keep=90)
```

**Scheduled**: Weekly on Sundays at 3:00 AM UTC

#### 4. **backfill_snapshots**
Create snapshots for a date range (historical data processing).

```python
from app.tasks.aggregation_tasks import backfill_snapshots

# Backfill January 2025
task = backfill_snapshots.delay(
    start_date="2025-01-01",
    end_date="2025-01-31"
)
```

## Scheduled Tasks (Celery Beat)

Configured in `app/celery_app.py` → `celery_app.conf.beat_schedule`

| Task | Schedule | Description |
|------|----------|-------------|
| `sync-catalog-daily` | Daily 2:00 AM UTC | Fetch up to 500 minifigures from Brickset |
| `update-prices-periodic` | Every 6 hours | Update prices for 50 minifigures from eBay |
| `aggregate-snapshots-daily` | Daily 1:00 AM UTC | Aggregate previous day's price listings |
| `cleanup-old-listings-weekly` | Sundays 3:00 AM UTC | Delete listings older than 90 days |

## Monitoring Tasks

### Using Python Shell

```python
from app.celery_app import celery_app

# Inspect active tasks
i = celery_app.control.inspect()
i.active()       # Currently running tasks
i.scheduled()    # Tasks scheduled to run soon
i.registered()   # All registered task names
i.stats()        # Worker statistics
```

### Using Celery CLI

```bash
# Monitor worker in real-time
celery -A app.celery_app events

# List registered tasks
celery -A app.celery_app inspect registered

# View active tasks
celery -A app.celery_app inspect active

# View scheduled tasks (from Beat)
celery -A app.celery_app inspect scheduled
```

### Using Flower (Web-based monitoring)

```bash
# Install Flower
pip install flower

# Start Flower dashboard
celery -A app.celery_app flower

# Access at http://localhost:5555
```

## Manual Task Execution (Testing)

### From FastAPI Endpoint

You can trigger tasks via API endpoints (to be implemented):

```bash
# Sync catalog
curl -X POST http://localhost:8000/v1/admin/sync-catalog

# Fetch prices for minifigure
curl -X POST http://localhost:8000/v1/admin/fetch-prices/9eb475d0-9b38-4bc6-941c-20a9a37df7a7

# Aggregate snapshots
curl -X POST http://localhost:8000/v1/admin/aggregate-snapshots
```

### From Python Shell

```python
from app.tasks.scraping_tasks import sync_catalog_from_brickset
from app.tasks.aggregation_tasks import aggregate_daily_snapshots

# Execute synchronously (blocks)
result = sync_catalog_from_brickset(theme="Star Wars", limit=10)
print(result)

# Execute asynchronously (returns immediately)
task = sync_catalog_from_brickset.delay(theme="Star Wars", limit=10)
print(f"Task ID: {task.id}")
print(f"Status: {task.status}")

# Wait for result
result = task.get(timeout=60)
print(result)
```

## Troubleshooting

### Worker Not Starting

1. Check Redis is running:
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

2. Check environment variables:
   ```bash
   cat backend/.env | grep REDIS_URL
   ```

3. Check for port conflicts:
   ```bash
   lsof -i :6379
   ```

### Tasks Failing

1. Check worker logs for errors:
   ```bash
   # Worker shows detailed error traces
   ```

2. Check database connection:
   ```bash
   # Test PostgreSQL connection
   psql $DATABASE_URL -c "SELECT 1"
   ```

3. Verify API keys are set:
   ```bash
   cat backend/.env | grep API_KEY
   ```

### Rate Limiting Issues

If you hit API rate limits:

1. **Reduce concurrency**:
   ```bash
   celery -A app.celery_app worker --concurrency=1
   ```

2. **Adjust schedule** in `app/celery_app.py`:
   ```python
   # Change from every 6 hours to every 12 hours
   'schedule': crontab(minute=0, hour='*/12')
   ```

3. **Add delays** between tasks in `scraping_tasks.py`:
   ```python
   countdown=queued * 5  # Wait 5 seconds between each task
   ```

## Production Considerations

### Scaling Workers

Run multiple worker processes:

```bash
# Terminal 1: Worker for scraping queue
celery -A app.celery_app worker -Q scraping -l info --concurrency=2

# Terminal 2: Worker for processing queue
celery -A app.celery_app worker -Q processing -l info --concurrency=4

# Terminal 3: Beat scheduler
celery -A app.celery_app beat -l info
```

### Reliability

1. **Task retries**: Configured with exponential backoff in task decorators
2. **Dead letter queue**: Failed tasks after max retries are logged
3. **Result backend**: Redis stores task results for 1 hour
4. **Persistent schedule**: Celery Beat uses persistent scheduler to prevent duplicate tasks

### Monitoring in Production

1. **Flower**: Web-based monitoring dashboard
2. **Sentry**: Error tracking and alerting
3. **CloudWatch/DataDog**: Metrics and logging
4. **Health checks**: Monitor worker process health

## Next Steps

Once you have the **eBay API key**:

1. Add it to `backend/.env`:
   ```
   EBAY_APP_ID=your_ebay_app_id_here
   ```

2. Test price fetching:
   ```python
   from app.tasks.scraping_tasks import fetch_prices_for_set_number
   task = fetch_prices_for_set_number.delay("sw0001")
   result = task.get()
   print(result)
   ```

3. Monitor scheduled tasks to ensure they run automatically

## Resources

- [Celery Documentation](https://docs.celeryq.dev/)
- [Redis Documentation](https://redis.io/docs/)
- [Flower Documentation](https://flower.readthedocs.io/)
