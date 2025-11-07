"""
BrickLink Data Source Adapter

Implements DataSourceAdapter interface for BrickLink.
Demonstrates ethical scraping with rate limiting and robots.txt respect.

NOTE: This is a simplified implementation for MVP. In production:
- Use BrickLink's official API with OAuth
- Implement proper authentication
- Handle pagination and complex queries
- Add retry logic with exponential backoff
"""

import asyncio
import logging
from typing import List, Optional
from datetime import datetime, timedelta
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin
import httpx
from bs4 import BeautifulSoup

from app.scrapers.base import (
    DataSourceAdapter,
    SourceType,
    RateLimitConfig,
    ScrapedMinifigure,
    ScrapedPriceListing
)

logger = logging.getLogger(__name__)


class BrickLinkAdapter(DataSourceAdapter):
    """
    BrickLink data source adapter.

    Rate limits:
    - 120 requests per minute (BrickLink API limit)
    - 7200 requests per hour
    - Respects robots.txt

    For MVP, this uses mock data. In production, implement:
    1. BrickLink API OAuth authentication
    2. Real HTML scraping with BeautifulSoup
    3. Proper pagination handling
    """

    BASE_URL = "https://www.bricklink.com"
    API_BASE = "https://api.bricklink.com/api/store/v1"

    def __init__(self):
        super().__init__(SourceType.BRICKLINK)
        self.client = httpx.AsyncClient(timeout=30.0)
        self.robots_parser = RobotFileParser()
        self.robots_parser.set_url(urljoin(self.BASE_URL, "/robots.txt"))

        # Rate limiting state
        self.request_times: List[datetime] = []
        self.last_request_time: Optional[datetime] = None

    def get_rate_limit_config(self) -> RateLimitConfig:
        """Return BrickLink rate limiting configuration."""
        return RateLimitConfig(
            requests_per_minute=120,
            requests_per_hour=7200,
            backoff_seconds=0.5,
            max_retries=3
        )

    async def check_rate_limit(self) -> bool:
        """
        Check if we're within rate limits.

        Returns True if we can make a request, False if we should wait.
        """
        now = datetime.utcnow()

        # Remove requests older than 1 minute
        cutoff = now - timedelta(minutes=1)
        self.request_times = [t for t in self.request_times if t > cutoff]

        # Check if we're under the limit
        if len(self.request_times) >= self.rate_limit_config.requests_per_minute:
            logger.warning("Rate limit reached, waiting...")
            return False

        # Add backoff delay between requests
        if self.last_request_time:
            elapsed = (now - self.last_request_time).total_seconds()
            if elapsed < self.rate_limit_config.backoff_seconds:
                await asyncio.sleep(self.rate_limit_config.backoff_seconds - elapsed)

        return True

    async def respect_robots_txt(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt."""
        try:
            # Try to read robots.txt (cached after first read)
            if not self.robots_parser.mtime:
                await self._fetch_robots_txt()

            return self.robots_parser.can_fetch("*", url)
        except Exception as e:
            logger.warning(f"Error checking robots.txt: {e}")
            # If we can't check, err on the side of caution and allow
            return True

    async def _fetch_robots_txt(self):
        """Fetch and parse robots.txt."""
        try:
            response = await self.client.get(urljoin(self.BASE_URL, "/robots.txt"))
            self.robots_parser.parse(response.text.splitlines())
        except Exception as e:
            logger.error(f"Error fetching robots.txt: {e}")

    async def _make_request(self, url: str) -> Optional[str]:
        """
        Make HTTP request with rate limiting and error handling.
        """
        # Check rate limit
        if not await self.check_rate_limit():
            await asyncio.sleep(1)  # Wait and try again
            if not await self.check_rate_limit():
                raise Exception("Rate limit exceeded")

        # Check robots.txt
        if not await self.respect_robots_txt(url):
            logger.warning(f"URL disallowed by robots.txt: {url}")
            return None

        # Make request
        try:
            self.request_times.append(datetime.utcnow())
            self.last_request_time = datetime.utcnow()

            response = await self.client.get(url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    async def fetch_minifigure_catalog(
        self,
        theme: Optional[str] = None,
        year: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[ScrapedMinifigure]:
        """
        Fetch minifigure catalog from BrickLink.

        For MVP, returns mock data. In production:
        - Use BrickLink API /items/MINIFIG endpoint
        - Or scrape catalog pages with BeautifulSoup
        - Handle pagination
        - Parse HTML structure
        """
        logger.info(f"Fetching catalog: theme={theme}, year={year}, limit={limit}")

        # Mock data for MVP demonstration
        mock_data = [
            ScrapedMinifigure(
                source="bricklink",
                source_id="sw0001",
                set_number="sw0001",
                name="Darth Vader",
                theme="Star Wars",
                subtheme="Episode IV",
                year_released=1999,
                image_url="https://img.bricklink.com/ItemImage/MN/0/sw0001.png",
                thumbnail_url="https://img.bricklink.com/ItemImage/MN/0/sw0001.t1.png",
                piece_count=4,
                raw_data={"catalog_url": f"{self.BASE_URL}/v2/catalog/catalogitem.page?M=sw0001"}
            ),
            ScrapedMinifigure(
                source="bricklink",
                source_id="sw0002",
                set_number="sw0002",
                name="Stormtrooper",
                theme="Star Wars",
                subtheme="Episode IV",
                year_released=1999,
                image_url="https://img.bricklink.com/ItemImage/MN/0/sw0002.png",
                thumbnail_url="https://img.bricklink.com/ItemImage/MN/0/sw0002.t1.png",
                piece_count=4,
                raw_data={"catalog_url": f"{self.BASE_URL}/v2/catalog/catalogitem.page?M=sw0002"}
            ),
        ]

        # Apply filters
        filtered = mock_data
        if theme:
            filtered = [m for m in filtered if m.theme and theme.lower() in m.theme.lower()]
        if year:
            filtered = [m for m in filtered if m.year_released == year]
        if limit:
            filtered = filtered[:limit]

        return filtered

    async def fetch_minifigure_details(
        self,
        set_number: str
    ) -> Optional[ScrapedMinifigure]:
        """
        Fetch detailed information for a specific minifigure.

        For MVP, returns mock data. In production:
        - Use BrickLink API /items/MINIFIG/{item_no} endpoint
        - Or scrape catalog detail page
        - Parse all available metadata
        """
        logger.info(f"Fetching details for: {set_number}")

        # Mock data
        if set_number.lower() == "sw0001":
            return ScrapedMinifigure(
                source="bricklink",
                source_id="sw0001",
                set_number="sw0001",
                name="Darth Vader",
                theme="Star Wars",
                subtheme="Episode IV",
                year_released=1999,
                image_url="https://img.bricklink.com/ItemImage/MN/0/sw0001.png",
                thumbnail_url="https://img.bricklink.com/ItemImage/MN/0/sw0001.t1.png",
                weight_grams=3.2,
                piece_count=4,
                raw_data={
                    "catalog_url": f"{self.BASE_URL}/v2/catalog/catalogitem.page?M=sw0001",
                    "appears_in_sets": ["7150-1", "7152-1"],
                    "category": "Star Wars > Episode IV/V/VI"
                }
            )

        return None

    async def fetch_price_listings(
        self,
        set_number: str,
        condition: Optional[str] = None
    ) -> List[ScrapedPriceListing]:
        """
        Fetch current price listings for a minifigure.

        For MVP, returns mock data. In production:
        - Use BrickLink API /items/MINIFIG/{item_no}/price_guide
        - Or scrape price guide pages
        - Handle different conditions (NEW/USED)
        - Parse seller information
        """
        logger.info(f"Fetching prices for: {set_number}, condition={condition}")

        # Mock price listings
        mock_listings = [
            ScrapedPriceListing(
                source="bricklink",
                source_id="listing_1",
                minifigure_set_number=set_number,
                timestamp=datetime.utcnow(),
                price=25.99,
                currency="USD",
                condition="NEW",
                quantity_available=3,
                seller_name="BrickMaster123",
                seller_rating=99.8,
                confidence_score=1.0,
                raw_data={"feedback_count": 5432, "country": "USA"}
            ),
            ScrapedPriceListing(
                source="bricklink",
                source_id="listing_2",
                minifigure_set_number=set_number,
                timestamp=datetime.utcnow(),
                price=22.50,
                currency="USD",
                condition="NEW",
                quantity_available=1,
                seller_name="MinifigStore",
                seller_rating=100.0,
                confidence_score=1.0,
                raw_data={"feedback_count": 12000, "country": "Germany"}
            ),
            ScrapedPriceListing(
                source="bricklink",
                source_id="listing_3",
                minifigure_set_number=set_number,
                timestamp=datetime.utcnow(),
                price=18.75,
                currency="USD",
                condition="USED",
                quantity_available=2,
                seller_name="LegoCollector",
                seller_rating=98.5,
                confidence_score=0.95,
                raw_data={"feedback_count": 234, "country": "UK"}
            ),
        ]

        # Filter by condition if specified
        if condition:
            condition_upper = condition.upper()
            mock_listings = [l for l in mock_listings if l.condition == condition_upper]

        return mock_listings

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


# Example usage and testing
async def main():
    """Test the BrickLink adapter."""
    adapter = BrickLinkAdapter()

    try:
        # Test catalog fetch
        print("=== Fetching Catalog ===")
        catalog = await adapter.fetch_minifigure_catalog(theme="Star Wars", limit=5)
        print(f"Found {len(catalog)} minifigures")
        for minifig in catalog:
            print(f"  - {minifig.set_number}: {minifig.name}")

        # Test detail fetch
        print("\n=== Fetching Details ===")
        details = await adapter.fetch_minifigure_details("sw0001")
        if details:
            print(f"  Name: {details.name}")
            print(f"  Theme: {details.theme}")
            print(f"  Year: {details.year_released}")

        # Test price fetch
        print("\n=== Fetching Prices ===")
        prices = await adapter.fetch_price_listings("sw0001")
        print(f"Found {len(prices)} price listings")
        for price in prices:
            print(f"  - ${price.price} {price.condition} from {price.seller_name}")

    finally:
        await adapter.close()


if __name__ == "__main__":
    asyncio.run(main())
