"""
Aggregation Tasks

Celery tasks for data aggregation and cleanup:
- Daily price snapshot generation (min/max/avg/median)
- Old listing cleanup
- Data maintenance

These tasks keep the database optimized and create pre-computed analytics.
"""

import logging
from typing import List
from datetime import datetime, timedelta, date
from decimal import Decimal
from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.minifigure import Minifigure
from app.models.price import PriceListing, PriceSnapshot, DataSource

logger = logging.getLogger(__name__)


@celery_app.task(
    name='app.tasks.aggregation_tasks.aggregate_daily_snapshots',
    bind=True,
    max_retries=3
)
def aggregate_daily_snapshots(self, target_date: str = None):
    """
    Aggregate price listings into daily snapshots.

    This task creates summary statistics (min, max, avg, median) for each
    minifigure based on price listings from the specified date.

    Args:
        target_date: Date to aggregate (ISO format YYYY-MM-DD).
                     Defaults to yesterday if not provided.

    Returns:
        dict: Summary of created snapshots
    """
    db: Session = SessionLocal()

    try:
        # Default to yesterday if no date provided
        if target_date:
            agg_date = datetime.fromisoformat(target_date).date()
        else:
            agg_date = (datetime.utcnow() - timedelta(days=1)).date()

        logger.info(f"Aggregating price snapshots for date: {agg_date}")

        # Get date range for the target day
        start_datetime = datetime.combine(agg_date, datetime.min.time())
        end_datetime = datetime.combine(agg_date, datetime.max.time())

        # Get all minifigures that have price listings on this date
        minifigures_with_prices = db.query(Minifigure.id).join(
            PriceListing, PriceListing.minifigure_id == Minifigure.id
        ).filter(
            and_(
                PriceListing.timestamp >= start_datetime,
                PriceListing.timestamp <= end_datetime
            )
        ).distinct().all()

        logger.info(f"Found {len(minifigures_with_prices)} minifigures with price data")

        snapshots_created = 0
        snapshots_updated = 0

        # Process each minifigure
        for (minifig_id,) in minifigures_with_prices:
            # Aggregate prices for this minifigure on this date
            result = _aggregate_prices_for_minifigure(
                db=db,
                minifigure_id=minifig_id,
                agg_date=agg_date,
                start_datetime=start_datetime,
                end_datetime=end_datetime
            )

            if result == 'created':
                snapshots_created += 1
            elif result == 'updated':
                snapshots_updated += 1

        db.commit()

        summary = {
            'date': str(agg_date),
            'snapshots_created': snapshots_created,
            'snapshots_updated': snapshots_updated,
            'total_minifigures': len(minifigures_with_prices)
        }

        logger.info(f"Snapshot aggregation complete: {summary}")
        return summary

    except Exception as e:
        db.rollback()
        logger.error(f"Error aggregating snapshots: {e}", exc_info=True)
        raise self.retry(exc=e)

    finally:
        db.close()


def _aggregate_prices_for_minifigure(
    db: Session,
    minifigure_id: str,
    agg_date: date,
    start_datetime: datetime,
    end_datetime: datetime
) -> str:
    """
    Aggregate prices for a single minifigure on a specific date.

    Returns:
        str: 'created' if new snapshot, 'updated' if existing, 'skipped' if no change
    """
    # Get all price listings for this minifigure on this date
    listings = db.query(PriceListing).filter(
        and_(
            PriceListing.minifigure_id == minifigure_id,
            PriceListing.timestamp >= start_datetime,
            PriceListing.timestamp <= end_datetime
        )
    ).all()

    if not listings:
        return 'skipped'

    # Calculate statistics
    prices = [listing.price_usd for listing in listings]
    prices_sorted = sorted(prices)

    min_price = min(prices)
    max_price = max(prices)
    avg_price = sum(prices) / len(prices)

    # Calculate median
    n = len(prices_sorted)
    if n % 2 == 0:
        median_price = (prices_sorted[n//2 - 1] + prices_sorted[n//2]) / 2
    else:
        median_price = prices_sorted[n//2]

    # Count by condition
    new_count = sum(1 for l in listings if l.condition == 'NEW')
    used_count = sum(1 for l in listings if l.condition == 'USED')
    sealed_count = sum(1 for l in listings if l.condition == 'SEALED')

    # Check if snapshot already exists
    existing_snapshot = db.query(PriceSnapshot).filter(
        and_(
            PriceSnapshot.minifigure_id == minifigure_id,
            PriceSnapshot.date == agg_date
        )
    ).first()

    if existing_snapshot:
        # Update existing snapshot
        existing_snapshot.min_price_usd = min_price
        existing_snapshot.max_price_usd = max_price
        existing_snapshot.avg_price_usd = avg_price
        existing_snapshot.median_price_usd = median_price
        existing_snapshot.listing_count = len(listings)
        existing_snapshot.new_condition_count = new_count
        existing_snapshot.used_condition_count = used_count
        existing_snapshot.sealed_condition_count = sealed_count
        return 'updated'
    else:
        # Create new snapshot
        snapshot = PriceSnapshot(
            minifigure_id=minifigure_id,
            date=agg_date,
            min_price_usd=min_price,
            max_price_usd=max_price,
            avg_price_usd=avg_price,
            median_price_usd=median_price,
            listing_count=len(listings),
            new_condition_count=new_count,
            used_condition_count=used_count,
            sealed_condition_count=sealed_count
        )
        db.add(snapshot)
        return 'created'


@celery_app.task(
    name='app.tasks.aggregation_tasks.aggregate_snapshot_for_minifigure',
    bind=True
)
def aggregate_snapshot_for_minifigure(
    self,
    minifigure_id: str,
    target_date: str = None
):
    """
    Aggregate price snapshot for a single minifigure.

    This is useful for real-time updates when new prices are added.

    Args:
        minifigure_id: UUID of the minifigure
        target_date: Date to aggregate (ISO format). Defaults to today.

    Returns:
        dict: Summary of snapshot creation
    """
    db: Session = SessionLocal()

    try:
        # Default to today if no date provided
        if target_date:
            agg_date = datetime.fromisoformat(target_date).date()
        else:
            agg_date = datetime.utcnow().date()

        logger.info(f"Aggregating snapshot for minifigure {minifigure_id}, date {agg_date}")

        # Get date range
        start_datetime = datetime.combine(agg_date, datetime.min.time())
        end_datetime = datetime.combine(agg_date, datetime.max.time())

        # Aggregate
        result = _aggregate_prices_for_minifigure(
            db=db,
            minifigure_id=minifigure_id,
            agg_date=agg_date,
            start_datetime=start_datetime,
            end_datetime=end_datetime
        )

        db.commit()

        summary = {
            'minifigure_id': minifigure_id,
            'date': str(agg_date),
            'result': result
        }

        logger.info(f"Snapshot aggregation complete: {summary}")
        return summary

    except Exception as e:
        db.rollback()
        logger.error(f"Error aggregating snapshot: {e}", exc_info=True)
        raise self.retry(exc=e)

    finally:
        db.close()


@celery_app.task(
    name='app.tasks.aggregation_tasks.cleanup_old_listings',
    bind=True
)
def cleanup_old_listings(self, days_to_keep: int = 90):
    """
    Clean up old price listings to keep database size manageable.

    Price snapshots are preserved, but individual listings older than
    the retention period are deleted.

    Args:
        days_to_keep: Number of days to retain raw listings (default: 90)

    Returns:
        dict: Summary of cleanup operation
    """
    db: Session = SessionLocal()

    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        logger.info(f"Cleaning up price listings older than {cutoff_date}")

        # Count listings to be deleted
        count = db.query(PriceListing).filter(
            PriceListing.timestamp < cutoff_date
        ).count()

        # Delete old listings
        deleted = db.query(PriceListing).filter(
            PriceListing.timestamp < cutoff_date
        ).delete(synchronize_session=False)

        db.commit()

        summary = {
            'cutoff_date': str(cutoff_date),
            'days_kept': days_to_keep,
            'listings_deleted': deleted
        }

        logger.info(f"Cleanup complete: {summary}")
        return summary

    except Exception as e:
        db.rollback()
        logger.error(f"Error during cleanup: {e}", exc_info=True)
        raise self.retry(exc=e)

    finally:
        db.close()


@celery_app.task(
    name='app.tasks.aggregation_tasks.backfill_snapshots',
    bind=True
)
def backfill_snapshots(self, start_date: str, end_date: str):
    """
    Backfill snapshots for a date range.

    Useful for historical data processing or fixing missing snapshots.

    Args:
        start_date: Start date (ISO format YYYY-MM-DD)
        end_date: End date (ISO format YYYY-MM-DD)

    Returns:
        dict: Summary of backfill operation
    """
    db: Session = SessionLocal()

    try:
        start = datetime.fromisoformat(start_date).date()
        end = datetime.fromisoformat(end_date).date()

        logger.info(f"Backfilling snapshots from {start} to {end}")

        current_date = start
        total_created = 0
        total_updated = 0

        while current_date <= end:
            # Queue daily aggregation task for each date
            result = aggregate_daily_snapshots.apply(
                kwargs={'target_date': str(current_date)}
            )

            if result.successful():
                summary = result.get()
                total_created += summary.get('snapshots_created', 0)
                total_updated += summary.get('snapshots_updated', 0)

            current_date += timedelta(days=1)

        summary = {
            'start_date': str(start),
            'end_date': str(end),
            'total_snapshots_created': total_created,
            'total_snapshots_updated': total_updated
        }

        logger.info(f"Backfill complete: {summary}")
        return summary

    except Exception as e:
        logger.error(f"Error during backfill: {e}", exc_info=True)
        raise self.retry(exc=e)

    finally:
        db.close()
