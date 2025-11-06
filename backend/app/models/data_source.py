"""
DataSource ORM Model

Maps to the data_sources table.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class APIType(str, enum.Enum):
    """API type enumeration matching database ENUM."""
    API = "API"
    SCRAPE = "SCRAPE"
    RSS = "RSS"


class DataSource(Base):
    """External data source (BrickLink, eBay, etc.)."""

    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    base_url = Column(String(500))
    api_type = Column(SQLEnum(APIType, name="api_type"), nullable=False)
    is_active = Column(Boolean, default=True)
    rate_limit_per_hour = Column(Integer)

    # Scraping tracking
    last_scraped_at = Column(DateTime(timezone=True))
    last_scrape_success = Column(Boolean)
    last_scrape_error = Column(String)
    successful_scrapes_count = Column(Integer, default=0)
    failed_scrapes_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    price_listings = relationship("PriceListing", back_populates="source")

    def __repr__(self):
        return f"<DataSource(id={self.id}, name='{self.name}', type={self.api_type})>"
