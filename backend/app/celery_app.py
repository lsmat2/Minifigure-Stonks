"""
Celery Application Configuration

This module configures Celery for async task processing:
- Scraping jobs (fetch catalog and prices)
- Data pipeline processing
- Price snapshot aggregation
- Scheduled periodic tasks

Celery Beat Schedule:
- Daily catalog sync from Brickset
- Hourly price updates from eBay
- Daily price snapshot aggregation
"""

from celery import Celery
from celery.schedules import crontab
import os

# Initialize Celery app
celery_app = Celery(
    'minifigure_stonks',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    include=[
        'app.tasks.scraping_tasks',
        'app.tasks.aggregation_tasks'
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task result settings
    result_expires=3600,  # Results expire after 1 hour
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,

    # Worker settings
    worker_prefetch_multiplier=1,  # One task at a time for rate limiting
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks (prevent memory leaks)

    # Task routing
    task_routes={
        'app.tasks.scraping_tasks.*': {'queue': 'scraping'},
        'app.tasks.aggregation_tasks.*': {'queue': 'processing'},
    },

    # Retry settings
    task_acks_late=True,  # Acknowledge task after completion, not on start
    task_reject_on_worker_lost=True,  # Requeue if worker dies

    # Rate limiting (global)
    task_default_rate_limit='100/m',  # 100 tasks per minute max
)

# Celery Beat Schedule for Periodic Tasks
celery_app.conf.beat_schedule = {
    # Sync full catalog from Brickset daily at 2 AM UTC
    'sync-catalog-daily': {
        'task': 'app.tasks.scraping_tasks.sync_catalog_from_brickset',
        'schedule': crontab(hour=2, minute=0),  # 2:00 AM UTC daily
        'kwargs': {
            'limit': 500,  # Fetch up to 500 minifigures per sync
        },
    },

    # Update prices from eBay every 6 hours
    'update-prices-periodic': {
        'task': 'app.tasks.scraping_tasks.update_all_prices',
        'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
        'kwargs': {
            'batch_size': 50,  # Process 50 minifigures per batch
        },
    },

    # Aggregate price snapshots daily at 1 AM UTC
    'aggregate-snapshots-daily': {
        'task': 'app.tasks.aggregation_tasks.aggregate_daily_snapshots',
        'schedule': crontab(hour=1, minute=0),  # 1:00 AM UTC daily
    },

    # Clean old price listings (keep last 90 days) weekly
    'cleanup-old-listings-weekly': {
        'task': 'app.tasks.aggregation_tasks.cleanup_old_listings',
        'schedule': crontab(day_of_week=0, hour=3, minute=0),  # Sunday 3 AM UTC
        'kwargs': {
            'days_to_keep': 90,
        },
    },
}


if __name__ == '__main__':
    celery_app.start()
