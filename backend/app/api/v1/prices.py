"""
Price API Endpoints

Provides access to price listings and historical snapshots.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID

from app.database import get_db
from app.models.price import PriceListing, PriceSnapshot, ConditionType
from app.models.minifigure import Minifigure
from app.schemas.price import (
    PriceListingResponse,
    PriceSnapshotResponse,
    PriceHistoryResponse
)

router = APIRouter()


@router.get(
    "/minifigures/{minifigure_id}/prices",
    response_model=List[PriceListingResponse],
    tags=["Prices"]
)
async def get_minifigure_prices(
    minifigure_id: UUID = Path(..., description="Minifigure UUID"),
    condition: Optional[ConditionType] = Query(None, description="Filter by condition (NEW, USED, SEALED)"),
    source_id: Optional[int] = Query(None, description="Filter by data source ID"),
    start_date: Optional[datetime] = Query(None, description="Start date for price listings"),
    end_date: Optional[datetime] = Query(None, description="End date for price listings"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    db: Session = Depends(get_db)
) -> List[PriceListingResponse]:
    """
    Get price listings for a specific minifigure.

    Returns raw price listing data with optional filtering by:
    - Condition (NEW/USED/SEALED)
    - Data source
    - Date range

    Results are ordered by timestamp descending (newest first).
    """
    # Verify minifigure exists
    minifigure = db.query(Minifigure).filter(Minifigure.id == minifigure_id).first()
    if not minifigure:
        raise HTTPException(status_code=404, detail=f"Minifigure {minifigure_id} not found")

    # Build query with filters
    query = db.query(PriceListing).filter(PriceListing.minifigure_id == minifigure_id)

    if condition:
        query = query.filter(PriceListing.condition == condition)

    if source_id:
        query = query.filter(PriceListing.source_id == source_id)

    if start_date:
        query = query.filter(PriceListing.timestamp >= start_date)

    if end_date:
        query = query.filter(PriceListing.timestamp <= end_date)

    # Order by newest first and apply limit
    listings = query.order_by(PriceListing.timestamp.desc()).limit(limit).all()

    return listings


@router.get(
    "/minifigures/{minifigure_id}/price-history",
    response_model=PriceHistoryResponse,
    tags=["Prices"]
)
async def get_minifigure_price_history(
    minifigure_id: UUID = Path(..., description="Minifigure UUID"),
    start_date: Optional[date] = Query(None, description="Start date for history"),
    end_date: Optional[date] = Query(None, description="End date for history"),
    db: Session = Depends(get_db)
) -> PriceHistoryResponse:
    """
    Get historical price snapshots for a specific minifigure.

    Returns daily aggregated statistics (min/max/avg/median prices, listing counts).
    Optimized for charting and trend analysis.

    If no date range specified, returns all available history.
    """
    # Verify minifigure exists and get details
    minifigure = db.query(Minifigure).filter(Minifigure.id == minifigure_id).first()
    if not minifigure:
        raise HTTPException(status_code=404, detail=f"Minifigure {minifigure_id} not found")

    # Build snapshot query
    query = db.query(PriceSnapshot).filter(PriceSnapshot.minifigure_id == minifigure_id)

    if start_date:
        query = query.filter(PriceSnapshot.date >= start_date)

    if end_date:
        query = query.filter(PriceSnapshot.date <= end_date)

    # Order chronologically
    snapshots = query.order_by(PriceSnapshot.date.asc()).all()

    return PriceHistoryResponse(
        minifigure_id=minifigure.id,
        minifigure_name=minifigure.name,
        set_number=minifigure.set_number,
        snapshots=snapshots
    )


@router.get(
    "/snapshots",
    response_model=List[PriceSnapshotResponse],
    tags=["Prices"]
)
async def get_price_snapshots(
    minifigure_id: Optional[UUID] = Query(None, description="Filter by minifigure UUID"),
    snapshot_date: Optional[date] = Query(None, alias="date", description="Filter by specific date"),
    start_date: Optional[date] = Query(None, description="Start date for date range"),
    end_date: Optional[date] = Query(None, description="End date for date range"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Results per page"),
    db: Session = Depends(get_db)
) -> List[PriceSnapshotResponse]:
    """
    Query price snapshots with flexible filtering.

    Use cases:
    - Get snapshots for a specific minifigure over time
    - Get snapshots for a specific date across multiple minifigures
    - Analytics and comparison queries

    Results are paginated and ordered by date descending (newest first).
    """
    query = db.query(PriceSnapshot)

    # Apply filters
    if minifigure_id:
        query = query.filter(PriceSnapshot.minifigure_id == minifigure_id)

    if snapshot_date:
        query = query.filter(PriceSnapshot.date == snapshot_date)

    if start_date:
        query = query.filter(PriceSnapshot.date >= start_date)

    if end_date:
        query = query.filter(PriceSnapshot.date <= end_date)

    # Apply pagination
    offset = (page - 1) * page_size
    snapshots = query.order_by(PriceSnapshot.date.desc()).offset(offset).limit(page_size).all()

    return snapshots
