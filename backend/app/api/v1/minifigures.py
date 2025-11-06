"""
Minifigure API Endpoints

CRUD operations for minifigures.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from uuid import UUID

from app.database import get_db
from app.models import Minifigure
from app.schemas.minifigure import MinifigureResponse, MinifigureList
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/", response_model=MinifigureList, tags=["Minifigures"])
async def list_minifigures(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    theme: str = Query(None, description="Filter by theme"),
    year: int = Query(None, description="Filter by year"),
    search: str = Query(None, description="Search by name"),
    db: Session = Depends(get_db),
) -> MinifigureList:
    """
    List minifigures with pagination and filtering.

    - **page**: Page number (starts at 1)
    - **page_size**: Number of items per page (max 100)
    - **theme**: Filter by theme (exact match)
    - **year**: Filter by year released
    - **search**: Full-text search on name
    """
    query = db.query(Minifigure)

    # Apply filters
    if theme:
        query = query.filter(Minifigure.theme == theme)
    if year:
        query = query.filter(Minifigure.year_released == year)
    if search:
        # Simple search (could be improved with full-text search)
        query = query.filter(Minifigure.name.ilike(f"%{search}%"))

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    # Calculate total pages
    pages = (total + page_size - 1) // page_size

    return MinifigureList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{minifigure_id}", response_model=MinifigureResponse, tags=["Minifigures"])
async def get_minifigure(
    minifigure_id: UUID,
    db: Session = Depends(get_db),
) -> MinifigureResponse:
    """
    Get a specific minifigure by ID.

    - **minifigure_id**: UUID of the minifigure
    """
    minifigure = db.query(Minifigure).filter(Minifigure.id == minifigure_id).first()

    if not minifigure:
        raise HTTPException(status_code=404, detail="Minifigure not found")

    return minifigure


@router.get("/set/{set_number}", response_model=MinifigureResponse, tags=["Minifigures"])
async def get_minifigure_by_set_number(
    set_number: str,
    db: Session = Depends(get_db),
) -> MinifigureResponse:
    """
    Get a minifigure by set number.

    - **set_number**: Set number (e.g., "sw0001")
    """
    minifigure = db.query(Minifigure).filter(Minifigure.set_number == set_number).first()

    if not minifigure:
        raise HTTPException(status_code=404, detail="Minifigure not found")

    return minifigure


@router.get("/themes/list", response_model=List[str], tags=["Minifigures"])
async def list_themes(db: Session = Depends(get_db)) -> List[str]:
    """
    Get list of all unique themes.

    Returns a list of all themes that have minifigures.
    """
    themes = db.query(Minifigure.theme).distinct().filter(Minifigure.theme.isnot(None)).all()
    return [theme[0] for theme in themes]
