"""
Pydantic Schemas for Minifigure API

These define the shape of request/response data for the API.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class MinifigureBase(BaseModel):
    """Base minifigure schema with common fields."""
    set_number: str = Field(..., description="Unique set number (e.g., sw0001)")
    name: str = Field(..., description="Minifigure name")
    theme: Optional[str] = Field(None, description="Theme (e.g., Star Wars)")
    subtheme: Optional[str] = Field(None, description="Subtheme")
    year_released: Optional[int] = Field(None, description="Year released", ge=1900, le=2100)
    lego_item_number: Optional[str] = Field(None, description="Official LEGO item number")
    image_url: Optional[str] = Field(None, description="Image URL")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL")
    weight_grams: Optional[float] = Field(None, description="Weight in grams")
    piece_count: Optional[int] = Field(None, description="Number of pieces")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")


class MinifigureCreate(MinifigureBase):
    """Schema for creating a new minifigure."""
    pass


class MinifigureResponse(MinifigureBase):
    """Schema for minifigure responses (includes database fields)."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MinifigureList(BaseModel):
    """Paginated list of minifigures."""
    items: list[MinifigureResponse]
    total: int
    page: int
    page_size: int
    pages: int
