"""
Scraping Tasks

Celery tasks for fetching data from external sources:
- Brickset: Minifigure catalog data
- eBay: Price listings
- Pipeline processing: Validate, normalize, deduplicate, persist

These tasks run asynchronously and respect rate limits.
"""

import asyncio
import logging
from typing import List, Optional
from datetime import datetime
import os

from celery import Task
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.scrapers.brickset import BricksetAdapter
from app.scrapers.ebay import EBayAdapter
from app.scrapers.pipeline import (
    RawDataValidator,
    DataNormalizer,
    DuplicateDetector,
    DataPersister
)
from app.models.minifigure import Minifigure

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task that provides database session."""
    _db: Optional[Session] = None

    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        """Clean up database session after task completes."""
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(
    name='app.tasks.scraping_tasks.sync_catalog_from_brickset',
    bind=True,
    base=DatabaseTask,
    max_retries=3,
    default_retry_delay=300  # 5 minutes
)
def sync_catalog_from_brickset(
    self,
    theme: Optional[str] = None,
    year: Optional[int] = None,
    limit: Optional[int] = 500
):
    """
    Sync minifigure catalog from Brickset API.

    This task fetches minifigure metadata (names, themes, images) from Brickset
    and processes them through the data pipeline.

    Args:
        theme: Filter by LEGO theme (e.g., "Star Wars", "Harry Potter")
        year: Filter by release year
        limit: Maximum number of minifigures to fetch

    Returns:
        dict: Summary of processed data
    """
    logger.info(f"Starting Brickset catalog sync: theme={theme}, year={year}, limit={limit}")

    try:
        # Get API key from environment
        api_key = os.getenv('BRICKSET_API_KEY')
        if not api_key:
            logger.error("BRICKSET_API_KEY not set in environment")
            return {'error': 'Missing API key', 'processed': 0}

        # Initialize adapter
        adapter = BricksetAdapter(api_key=api_key)

        # Fetch catalog data (async call wrapped in sync context)
        async def fetch():
            return await adapter.fetch_minifigure_catalog(
                theme=theme,
                year=year,
                limit=limit
            )

        scraped_data = asyncio.run(fetch())
        logger.info(f"Fetched {len(scraped_data)} minifigures from Brickset")

        if not scraped_data:
            logger.warning("No data fetched from Brickset")
            return {'processed': 0, 'errors': 0}

        # Build processing pipeline
        pipeline = RawDataValidator(
            next_stage=DataNormalizer(
                next_stage=DuplicateDetector(
                    db=self.db,
                    next_stage=DataPersister(db=self.db)
                )
            )
        )

        # Process data through pipeline
        async def process():
            return await pipeline.process(scraped_data, context={
                'source': 'brickset',
                'sync_time': datetime.utcnow()
            })

        result = asyncio.run(process())

        # Close adapter
        asyncio.run(adapter.close())

        logger.info(f"Catalog sync complete: {result}")
        return result

    except Exception as e:
        logger.error(f"Error syncing catalog from Brickset: {e}", exc_info=True)
        # Retry with exponential backoff
        raise self.retry(exc=e)


@celery_app.task(
    name='app.tasks.scraping_tasks.fetch_prices_for_minifigure',
    bind=True,
    base=DatabaseTask,
    max_retries=3,
    default_retry_delay=60  # 1 minute
)
def fetch_prices_for_minifigure(
    self,
    minifigure_id: str,
    condition: Optional[str] = None
):
    """
    Fetch price listings for a specific minifigure from eBay.

    Args:
        minifigure_id: UUID of the minifigure
        condition: Filter by condition (NEW, USED, SEALED)

    Returns:
        dict: Summary of fetched prices
    """
    logger.info(f"Fetching prices for minifigure {minifigure_id}, condition={condition}")

    try:
        # Get minifigure from database
        minifig = self.db.query(Minifigure).filter(Minifigure.id == minifigure_id).first()
        if not minifig:
            logger.error(f"Minifigure {minifigure_id} not found")
            return {'error': 'Minifigure not found', 'processed': 0}

        # Get API key from environment
        app_id = os.getenv('EBAY_APP_ID')
        if not app_id:
            logger.error("EBAY_APP_ID not set in environment")
            return {'error': 'Missing API key', 'processed': 0}

        # Initialize eBay adapter
        adapter = EBayAdapter(app_id=app_id)

        # Fetch price listings
        async def fetch():
            return await adapter.fetch_price_listings(
                set_number=minifig.set_number,
                condition=condition
            )

        price_listings = asyncio.run(fetch())
        logger.info(f"Fetched {len(price_listings)} price listings from eBay")

        if not price_listings:
            logger.info(f"No price listings found for {minifig.set_number}")
            asyncio.run(adapter.close())
            return {'processed': 0, 'errors': 0}

        # Build processing pipeline
        pipeline = RawDataValidator(
            next_stage=DataNormalizer(
                next_stage=DuplicateDetector(
                    db=self.db,
                    next_stage=DataPersister(db=self.db)
                )
            )
        )

        # Process data through pipeline
        async def process():
            return await pipeline.process(price_listings, context={
                'source': 'ebay',
                'minifigure_id': minifigure_id,
                'fetch_time': datetime.utcnow()
            })

        result = asyncio.run(process())

        # Close adapter
        asyncio.run(adapter.close())

        logger.info(f"Price fetch complete: {result}")
        return result

    except Exception as e:
        logger.error(f"Error fetching prices for {minifigure_id}: {e}", exc_info=True)
        raise self.retry(exc=e)


@celery_app.task(
    name='app.tasks.scraping_tasks.update_all_prices',
    bind=True,
    base=DatabaseTask,
    max_retries=2
)
def update_all_prices(self, batch_size: int = 50):
    """
    Update prices for all minifigures in the catalog.

    This task fetches the most recent minifigures and queues individual
    price fetch tasks for each one.

    Args:
        batch_size: Number of minifigures to update per batch

    Returns:
        dict: Summary of queued tasks
    """
    logger.info(f"Starting batch price update for {batch_size} minifigures")

    try:
        # Get recent minifigures (prioritize recently added)
        minifigures = self.db.query(Minifigure).order_by(
            Minifigure.created_at.desc()
        ).limit(batch_size).all()

        logger.info(f"Found {len(minifigures)} minifigures to update")

        # Queue individual price fetch tasks
        queued = 0
        for minifig in minifigures:
            # Queue task with rate limiting (stagger requests)
            fetch_prices_for_minifigure.apply_async(
                args=[str(minifig.id)],
                countdown=queued * 2  # Wait 2 seconds between each task
            )
            queued += 1

        logger.info(f"Queued {queued} price fetch tasks")
        return {
            'queued': queued,
            'batch_size': batch_size
        }

    except Exception as e:
        logger.error(f"Error in batch price update: {e}", exc_info=True)
        raise self.retry(exc=e)


@celery_app.task(
    name='app.tasks.scraping_tasks.fetch_prices_for_set_number',
    bind=True,
    base=DatabaseTask,
    max_retries=3
)
def fetch_prices_for_set_number(
    self,
    set_number: str,
    condition: Optional[str] = None
):
    """
    Fetch price listings for a specific set number from eBay.

    This is a convenience task that finds the minifigure by set_number
    and then fetches prices.

    Args:
        set_number: LEGO set number (e.g., "sw0001")
        condition: Filter by condition (NEW, USED, SEALED)

    Returns:
        dict: Summary of fetched prices
    """
    logger.info(f"Fetching prices for set_number {set_number}")

    try:
        # Find minifigure by set number
        minifig = self.db.query(Minifigure).filter(
            Minifigure.set_number == set_number.lower()
        ).first()

        if not minifig:
            logger.warning(f"Minifigure {set_number} not found in database")
            return {'error': 'Minifigure not found', 'processed': 0}

        # Delegate to the main price fetch task
        return fetch_prices_for_minifigure(str(minifig.id), condition)

    except Exception as e:
        logger.error(f"Error fetching prices for {set_number}: {e}", exc_info=True)
        raise self.retry(exc=e)
