"""
Minifigure ORM Model

Maps to the minifigures table.
"""

from sqlalchemy import Column, String, Integer, Numeric, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class Minifigure(Base):
    """LEGO minifigure catalog entry."""

    __tablename__ = "minifigures"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    set_number = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(500), nullable=False)
    theme = Column(String(100), index=True)
    subtheme = Column(String(100))
    year_released = Column(Integer, index=True)
    lego_item_number = Column(String(50))

    # Images
    image_url = Column(String(1000))
    thumbnail_url = Column(String(1000))

    # Physical properties
    weight_grams = Column(Numeric(8, 2))
    piece_count = Column(Integer)

    # Flexible metadata (using extra_data instead of metadata which is reserved)
    extra_data = Column("metadata", JSONB, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    price_listings = relationship("PriceListing", back_populates="minifigure", cascade="all, delete-orphan")
    price_snapshots = relationship("PriceSnapshot", back_populates="minifigure", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Minifigure(id={self.id}, set_number='{self.set_number}', name='{self.name}')>"
