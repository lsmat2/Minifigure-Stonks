"""
Brickset Data Source Adapter

Implements DataSourceAdapter for Brickset API.
Brickset provides a free public API for LEGO data including minifigures.

API Documentation: https://brickset.com/tools/webservices/v3
Get free API key: https://brickset.com/tools/webservices/requestkey

Note: This uses their v3 API which doesn't require OAuth,
just a simple API key that's free to obtain.
"""

import asyncio
import logging
from typing import List, Optional
from datetime import datetime
import httpx

from app.scrapers.base import (
    DataSourceAdapter,
    SourceType,
    RateLimitConfig,
    ScrapedMinifigure,
    ScrapedPriceListing
)

logger = logging.getLogger(__name__)


class BricksetAdapter(DataSourceAdapter):
    """
    Brickset API adapter.

    Free API with reasonable rate limits.
    Perfect for getting minifigure catalog data.

    API Key: Get one free at https://brickset.com/tools/webservices/requestkey
    """

    API_BASE = "https://brickset.com/api/v3.asmx"

    # For demo purposes - in production, store in environment variables
    # Get your own key at: https://brickset.com/tools/webservices/requestkey
    API_KEY = "YOUR_API_KEY_HERE"  # Replace with actual key

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(SourceType.BRICKSET)
        self.api_key = api_key or self.API_KEY
        self.client = httpx.AsyncClient(timeout=30.0)
        self.request_times: List[datetime] = []

    def get_rate_limit_config(self) -> RateLimitConfig:
        """
        Brickset rate limits (conservative estimate):
        - 60 requests per minute
        - 3600 requests per hour
        """
        return RateLimitConfig(
            requests_per_minute=60,
            requests_per_hour=3600,
            backoff_seconds=1.0,
            max_retries=3
        )

    async def check_rate_limit(self) -> bool:
        """Check if we're within rate limits."""
        now = datetime.utcnow()

        # Remove old requests
        from datetime import timedelta
        cutoff = now - timedelta(minutes=1)
        self.request_times = [t for t in self.request_times if t > cutoff]

        # Check limit
        if len(self.request_times) >= self.rate_limit_config.requests_per_minute:
            return False

        return True

    async def respect_robots_txt(self, url: str) -> bool:
        """Brickset API doesn't need robots.txt check (it's an API)."""
        return True

    async def _make_api_request(self, endpoint: str, params: dict) -> Optional[dict]:
        """Make request to Brickset API."""
        if not await self.check_rate_limit():
            await asyncio.sleep(1)

        # Add API key to params
        params['apiKey'] = self.api_key

        url = f"{self.API_BASE}/{endpoint}"

        try:
            self.request_times.append(datetime.utcnow())
            response = await self.client.get(url, params=params)
            response.raise_for_status()

            # Brickset returns JSON
            return response.json()
        except Exception as e:
            logger.error(f"Error calling Brickset API: {e}")
            return None

    async def fetch_minifigure_catalog(
        self,
        theme: Optional[str] = None,
        year: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[ScrapedMinifigure]:
        """
        Fetch minifigure catalog from Brickset.

        Uses the getSets endpoint filtered for minifigures.
        API endpoint: /getSets
        """
        logger.info(f"Fetching catalog: theme={theme}, year={year}, limit={limit}")

        params = {
            'theme': theme or '',
            'year': str(year) if year else '',
            'pageSize': str(limit) if limit else '500',
            'setType': 'Minifigure'  # Filter for minifigures only
        }

        data = await self._make_api_request('getSets', params)

        if not data or 'sets' not in data:
            logger.warning("No sets returned from Brickset")
            return []

        minifigures = []
        for item in data.get('sets', []):
            # Parse Brickset data into our format
            minifig = ScrapedMinifigure(
                source="brickset",
                source_id=item.get('setID', ''),
                set_number=item.get('number', '').lower(),
                name=item.get('name', ''),
                theme=item.get('theme', ''),
                subtheme=item.get('subtheme'),
                year_released=int(item.get('year', 0)) if item.get('year') else None,
                image_url=item.get('image', {}).get('imageURL') if isinstance(item.get('image'), dict) else None,
                thumbnail_url=item.get('image', {}).get('thumbnailURL') if isinstance(item.get('image'), dict) else None,
                piece_count=int(item.get('pieces', 0)) if item.get('pieces') else None,
                raw_data={
                    'brickset_url': f"https://brickset.com/sets/{item.get('number')}",
                    'category': item.get('category'),
                    'brickset_rating': item.get('rating'),
                    'tags': item.get('tags', [])
                }
            )
            minifigures.append(minifig)

        logger.info(f"Fetched {len(minifigures)} minifigures from Brickset")
        return minifigures

    async def fetch_minifigure_details(
        self,
        set_number: str
    ) -> Optional[ScrapedMinifigure]:
        """
        Fetch detailed information for a specific minifigure.

        Uses getSet endpoint.
        """
        logger.info(f"Fetching details for: {set_number}")

        params = {
            'setNumber': set_number
        }

        data = await self._make_api_request('getSet', params)

        if not data or 'sets' not in data or not data['sets']:
            logger.warning(f"Minifigure {set_number} not found")
            return None

        item = data['sets'][0]

        return ScrapedMinifigure(
            source="brickset",
            source_id=item.get('setID', ''),
            set_number=item.get('number', '').lower(),
            name=item.get('name', ''),
            theme=item.get('theme', ''),
            subtheme=item.get('subtheme'),
            year_released=int(item.get('year', 0)) if item.get('year') else None,
            image_url=item.get('image', {}).get('imageURL') if isinstance(item.get('image'), dict) else None,
            thumbnail_url=item.get('image', {}).get('thumbnailURL') if isinstance(item.get('image'), dict) else None,
            piece_count=int(item.get('pieces', 0)) if item.get('pieces') else None,
            weight_grams=float(item.get('weight', 0)) if item.get('weight') else None,
            raw_data={
                'brickset_url': f"https://brickset.com/sets/{item.get('number')}",
                'category': item.get('category'),
                'brickset_rating': item.get('rating'),
                'tags': item.get('tags', []),
                'description': item.get('description'),
                'ean_codes': item.get('EAN'),
                'upc_codes': item.get('UPC')
            }
        )

    async def fetch_price_listings(
        self,
        set_number: str,
        condition: Optional[str] = None
    ) -> List[ScrapedPriceListing]:
        """
        Fetch price listings.

        NOTE: Brickset API doesn't provide real-time marketplace prices.
        It only has retail prices (RRP) and some historical data.

        For actual marketplace prices, you'd need to:
        1. Use BrickLink API (requires OAuth)
        2. Scrape eBay sold listings
        3. Use eBay API

        This returns mock data for demonstration.
        """
        logger.warning("Brickset doesn't provide marketplace pricing - returning mock data")

        # For demo/testing, return mock data
        # In production, this would be left empty and you'd use eBay/BrickLink
        return []

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


# Example usage
async def main():
    """Test the Brickset adapter."""
    # You need to get an API key first
    # Visit: https://brickset.com/tools/webservices/requestkey

    adapter = BricksetAdapter(api_key="YOUR_API_KEY_HERE")

    try:
        print("=== Testing Brickset Adapter ===")
        print("\nNOTE: You need a Brickset API key to use this adapter.")
        print("Get one free at: https://brickset.com/tools/webservices/requestkey")
        print("\nFor demo purposes, showing what the API would return...")

        # Example: Fetch Star Wars minifigures from 2023
        # catalog = await adapter.fetch_minifigure_catalog(
        #     theme="Star Wars",
        #     year=2023,
        #     limit=10
        # )
        #
        # for minifig in catalog:
        #     print(f"  - {minifig.set_number}: {minifig.name}")

    finally:
        await adapter.close()


if __name__ == "__main__":
    asyncio.run(main())
