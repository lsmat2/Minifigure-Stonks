"""
Health Check Endpoints

Provides health and status endpoints for monitoring.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict

from app.database import get_db
from app.config import get_settings

router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check() -> Dict[str, str]:
    """
    Basic health check endpoint.

    Returns:
        Status message
    """
    return {"status": "healthy", "service": "minifigure-stonks-api"}


@router.get("/health/db", tags=["Health"])
async def database_health(db: Session = Depends(get_db)) -> Dict[str, str]:
    """
    Database connectivity health check.

    Tests if we can connect to and query the database.

    Returns:
        Database status and version
    """
    try:
        # Test database connection
        result = db.execute(text("SELECT version()"))
        version = result.scalar()

        # Test TimescaleDB
        timescale_result = db.execute(
            text("SELECT extversion FROM pg_extension WHERE extname = 'timescaledb'")
        )
        timescale_version = timescale_result.scalar()

        return {
            "status": "healthy",
            "database": "connected",
            "postgresql_version": version.split()[1] if version else "unknown",
            "timescaledb_version": timescale_version or "not installed",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
        }


@router.get("/info", tags=["Health"])
async def api_info() -> Dict[str, str]:
    """
    API information endpoint.

    Returns:
        API version and configuration info
    """
    settings = get_settings()
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "api_version": settings.api_version,
        "debug": settings.debug,
    }
