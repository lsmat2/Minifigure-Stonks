"""
Price ORM Models

Maps to price_listings and price_snapshots tables.
"""

from sqlalchemy import Column, Integer, BigInteger, String, Numeric, DateTime, Date, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class ConditionType(str, enum.Enum):
    """Minifigure condition enumeration matching database ENUM."""
    NEW = "NEW"
    USED = "USED"
    SEALED = "SEALED"


class PriceListing(Base):
    """Individual price listing from a data source (time-series data)."""

    __tablename__ = "price_listings"

    id = Column(BigInteger, primary_key=True, index=True)
    minifigure_id = Column(UUID(as_uuid=True), ForeignKey("minifigures.id", ondelete="CASCADE"), nullable=False, index=True)
    source_id = Column(Integer, ForeignKey("data_sources.id", ondelete="CASCADE"), nullable=False, index=True)

    # Time-series key
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    # Price (normalized to USD)
    price_usd = Column(Numeric(10, 2), nullable=False)
    original_price = Column(Numeric(10, 2))
    original_currency = Column(String(3))
    exchange_rate = Column(Numeric(10, 6))

    condition = Column(SQLEnum(ConditionType, name="condition_type"), nullable=False, index=True)
    quantity_available = Column(Integer)

    # Listing details
    listing_url = Column(String)
    seller_name = Column(String(200))
    seller_rating = Column(Numeric(3, 2))

    # Data quality
    confidence_score = Column(Numeric(3, 2), default=1.00)

    # Raw data for reprocessing
    raw_data = Column(JSONB)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    minifigure = relationship("Minifigure", back_populates="price_listings")
    source = relationship("DataSource", back_populates="price_listings")

    def __repr__(self):
        return f"<PriceListing(id={self.id}, price=${self.price_usd}, timestamp={self.timestamp})>"


class PriceSnapshot(Base):
    """Pre-aggregated daily price statistics."""

    __tablename__ = "price_snapshots"

    id = Column(BigInteger, primary_key=True, index=True)
    minifigure_id = Column(UUID(as_uuid=True), ForeignKey("minifigures.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    # Aggregate statistics
    min_price_usd = Column(Numeric(10, 2), nullable=False)
    max_price_usd = Column(Numeric(10, 2), nullable=False)
    avg_price_usd = Column(Numeric(10, 2), nullable=False)
    median_price_usd = Column(Numeric(10, 2), nullable=False)

    # Counts
    listing_count = Column(Integer, nullable=False)
    sources_count = Column(Integer, nullable=False)

    # Metadata
    metadata = Column(JSONB, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    minifigure = relationship("Minifigure", back_populates="price_snapshots")

    def __repr__(self):
        return f"<PriceSnapshot(id={self.id}, date={self.date}, avg=${self.avg_price_usd})>"
