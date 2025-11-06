"""
Pydantic Schemas for Price API

Response schemas for price listings and snapshots.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal


class PriceListingResponse(BaseModel):
    """Schema for price listing responses."""
    id: int
    minifigure_id: UUID
    source_id: int
    timestamp: datetime
    price_usd: Decimal = Field(..., description="Price in USD")
    original_price: Optional[Decimal] = Field(None, description="Original price")
    original_currency: Optional[str] = Field(None, description="Original currency code")
    condition: str = Field(..., description="Condition (NEW, USED, SEALED)")
    quantity_available: Optional[int] = None
    seller_name: Optional[str] = None
    seller_rating: Optional[Decimal] = None
    confidence_score: Optional[Decimal] = Field(None, description="Data quality score")

    model_config = ConfigDict(from_attributes=True)


class PriceSnapshotResponse(BaseModel):
    """Schema for price snapshot responses."""
    id: int
    minifigure_id: UUID
    date: date
    min_price_usd: Decimal
    max_price_usd: Decimal
    avg_price_usd: Decimal
    median_price_usd: Decimal
    listing_count: int
    sources_count: int
    extra_data: Optional[dict] = Field(default_factory=dict, alias="metadata")

    model_config = ConfigDict(from_attributes=True)


class PriceHistoryResponse(BaseModel):
    """Response for price history queries."""
    minifigure_id: UUID
    minifigure_name: str
    set_number: str
    snapshots: list[PriceSnapshotResponse]
