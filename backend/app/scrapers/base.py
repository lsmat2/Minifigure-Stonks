"""
Base DataSourceAdapter Interface

Defines the contract that all data source adapters must implement.
Uses Strategy Pattern for source-specific implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class SourceType(str, Enum):
    """Data source types."""
    BRICKLINK = "bricklink"
    EBAY = "ebay"
    LEGO = "lego"
    BRICKSET = "brickset"


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: Optional[int] = None
    backoff_seconds: float = 1.0
    max_retries: int = 3


@dataclass
class ScrapedMinifigure:
    """Raw minifigure data from a source."""
    source: str
    source_id: str
    set_number: str
    name: str
    theme: Optional[str] = None
    subtheme: Optional[str] = None
    year_released: Optional[int] = None
    image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    weight_grams: Optional[float] = None
    piece_count: Optional[int] = None
    raw_data: Dict[str, Any] = None


@dataclass
class ScrapedPriceListing:
    """Raw price listing data from a source."""
    source: str
    source_id: str
    minifigure_set_number: str
    timestamp: datetime
    price: float
    currency: str
    condition: str
    quantity_available: Optional[int] = None
    seller_name: Optional[str] = None
    seller_rating: Optional[float] = None
    url: Optional[str] = None
    raw_data: Dict[str, Any] = None
    confidence_score: float = 1.0


class DataSourceAdapter(ABC):
    """
    Abstract base class for data source adapters.

    Each data source (BrickLink, eBay, etc.) implements this interface
    to provide a consistent way to fetch and parse data.
    """

    def __init__(self, source_type: SourceType):
        self.source_type = source_type
        self.rate_limit_config = self.get_rate_limit_config()

    @abstractmethod
    def get_rate_limit_config(self) -> RateLimitConfig:
        """Return rate limiting configuration for this source."""
        pass

    @abstractmethod
    async def fetch_minifigure_catalog(
        self,
        theme: Optional[str] = None,
        year: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[ScrapedMinifigure]:
        """
        Fetch minifigure catalog from the source.

        Args:
            theme: Filter by theme (e.g., "Star Wars")
            year: Filter by release year
            limit: Maximum number of results

        Returns:
            List of scraped minifigure data
        """
        pass

    @abstractmethod
    async def fetch_minifigure_details(
        self,
        set_number: str
    ) -> Optional[ScrapedMinifigure]:
        """
        Fetch detailed information for a specific minifigure.

        Args:
            set_number: Minifigure set number (e.g., "sw0001")

        Returns:
            Scraped minifigure data or None if not found
        """
        pass

    @abstractmethod
    async def fetch_price_listings(
        self,
        set_number: str,
        condition: Optional[str] = None
    ) -> List[ScrapedPriceListing]:
        """
        Fetch current price listings for a minifigure.

        Args:
            set_number: Minifigure set number
            condition: Filter by condition (NEW, USED, SEALED)

        Returns:
            List of scraped price listings
        """
        pass

    @abstractmethod
    async def check_rate_limit(self) -> bool:
        """
        Check if we're within rate limits.

        Returns:
            True if we can make a request, False if we should wait
        """
        pass

    @abstractmethod
    async def respect_robots_txt(self, url: str) -> bool:
        """
        Check if URL is allowed by robots.txt.

        Args:
            url: URL to check

        Returns:
            True if allowed, False if disallowed
        """
        pass
