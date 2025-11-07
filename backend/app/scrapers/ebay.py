"""
eBay Data Source Adapter

Implements DataSourceAdapter for eBay Finding API.
eBay provides a free Finding API for searching active and sold listings.

API Documentation: https://developer.ebay.com/devzone/finding/Concepts/FindingAPIGuide.html
Get free API key: https://developer.ebay.com/signin

Note: This uses eBay's Finding API which is free and doesn't require OAuth.
For more advanced features, you can upgrade to Browse API.
"""

import asyncio
import logging
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
import httpx
from urllib.parse import urlencode

from app.scrapers.base import (
    DataSourceAdapter,
    SourceType,
    RateLimitConfig,
    ScrapedMinifigure,
    ScrapedPriceListing
)

logger = logging.getLogger(__name__)


class EBayAdapter(DataSourceAdapter):
    """
    eBay Finding API adapter.

    Perfect for getting real marketplace price data:
    - Active listings (current prices)
    - Sold listings (historical prices)
    - Multiple conditions (new, used)

    API Key: Get one free at https://developer.ebay.com/signin
    """

    # eBay Finding API endpoint
    API_BASE = "https://svcs.ebay.com/services/search/FindingService/v1"

    # For demo - in production, store in environment variables
    # Get your own at: https://developer.ebay.com/signin
    APP_ID = "YOUR_EBAY_APP_ID_HERE"

    # eBay category IDs for LEGO Minifigures
    MINIFIGURE_CATEGORY = "19006"  # LEGO Minifigures category

    def __init__(self, app_id: Optional[str] = None):
        super().__init__(SourceType.EBAY)
        self.app_id = app_id or self.APP_ID
        self.client = httpx.AsyncClient(timeout=30.0)
        self.request_times: List[datetime] = []

    def get_rate_limit_config(self) -> RateLimitConfig:
        """
        eBay Finding API rate limits:
        - 5,000 calls per day per app
        - Approximately 3-4 calls per second sustained
        - Conservative: 100 requests per minute
        """
        return RateLimitConfig(
            requests_per_minute=100,
            requests_per_hour=5000,
            requests_per_day=5000,
            backoff_seconds=0.6,
            max_retries=3
        )

    async def check_rate_limit(self) -> bool:
        """Check if we're within rate limits."""
        now = datetime.utcnow()

        # Remove old requests
        from datetime import timedelta
        cutoff = now - timedelta(minutes=1)
        self.request_times = [t for t in self.request_times if t > cutoff]

        if len(self.request_times) >= self.rate_limit_config.requests_per_minute:
            return False

        return True

    async def respect_robots_txt(self, url: str) -> bool:
        """eBay API doesn't need robots.txt check (it's an API)."""
        return True

    async def _make_api_request(
        self,
        operation: str,
        params: dict
    ) -> Optional[dict]:
        """Make request to eBay Finding API."""
        if not await self.check_rate_limit():
            await asyncio.sleep(1)

        # Build query parameters
        query_params = {
            'OPERATION-NAME': operation,
            'SERVICE-VERSION': '1.0.0',
            'SECURITY-APPNAME': self.app_id,
            'RESPONSE-DATA-FORMAT': 'JSON',
            'REST-PAYLOAD': '',
            **params
        }

        url = f"{self.API_BASE}?{urlencode(query_params)}"

        try:
            self.request_times.append(datetime.utcnow())
            response = await self.client.get(url)
            response.raise_for_status()

            data = response.json()
            return data
        except Exception as e:
            logger.error(f"Error calling eBay API: {e}")
            return None

    def _parse_ebay_item(self, item: dict, minifigure_set_number: str) -> Optional[ScrapedPriceListing]:
        """Parse eBay item into ScrapedPriceListing."""
        try:
            # Extract selling status
            selling_status = item.get('sellingStatus', [{}])[0]
            current_price = selling_status.get('currentPrice', [{}])[0]

            # Get price and currency
            price_value = float(current_price.get('__value__', 0))
            currency = current_price.get('@currencyId', 'USD')

            # Determine condition
            condition_info = item.get('condition', [{}])[0]
            condition_name = condition_info.get('conditionDisplayName', ['Used'])[0]

            # Map eBay condition to our standard
            condition_map = {
                'New': 'NEW',
                'New other': 'NEW',
                'Used': 'USED',
                'For parts or not working': 'USED',
            }
            condition = condition_map.get(condition_name, 'USED')

            # Get listing info
            listing_info = item.get('listingInfo', [{}])[0]
            listing_type = listing_info.get('listingType', [''])[0]

            # Check if sold
            is_sold = selling_status.get('sellingState', [''])[0] == 'EndedWithSales'

            # Get seller info
            seller_info = item.get('sellerInfo', [{}])[0]
            seller_name = seller_info.get('sellerUserName', [''])[0]

            # Feedback score as rating (convert to percentage)
            feedback_score = int(seller_info.get('feedbackScore', [0])[0])
            positive_feedback = float(seller_info.get('positiveFeedbackPercent', [0])[0])

            # Timestamp
            timestamp = datetime.utcnow()
            end_time = listing_info.get('endTime', [''])[0]
            if end_time:
                try:
                    timestamp = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                except:
                    pass

            # Get item ID and URL
            item_id = item.get('itemId', [''])[0]
            view_url = item.get('viewItemURL', [''])[0]

            # Calculate confidence score
            confidence = 1.0
            if not is_sold:
                confidence *= 0.8  # Active listings are less reliable than sold
            if listing_type == 'Auction':
                confidence *= 0.9  # Auctions can have volatile prices
            if positive_feedback < 95:
                confidence *= 0.9  # Lower seller rating

            return ScrapedPriceListing(
                source="ebay",
                source_id=item_id,
                minifigure_set_number=minifigure_set_number,
                timestamp=timestamp,
                price=price_value,
                currency=currency,
                condition=condition,
                quantity_available=1,  # eBay doesn't always provide quantity
                seller_name=seller_name,
                seller_rating=positive_feedback,
                url=view_url,
                confidence_score=confidence,
                raw_data={
                    'listing_type': listing_type,
                    'is_sold': is_sold,
                    'feedback_score': feedback_score,
                    'location': item.get('location', [''])[0],
                    'title': item.get('title', [''])[0],
                    'image_url': item.get('galleryURL', [''])[0]
                }
            )
        except Exception as e:
            logger.error(f"Error parsing eBay item: {e}")
            return None

    async def fetch_minifigure_catalog(
        self,
        theme: Optional[str] = None,
        year: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[ScrapedMinifigure]:
        """
        eBay doesn't provide catalog data, only marketplace listings.
        Use Brickset for catalog data instead.
        """
        logger.warning("eBay doesn't provide catalog data - use Brickset adapter instead")
        return []

    async def fetch_minifigure_details(
        self,
        set_number: str
    ) -> Optional[ScrapedMinifigure]:
        """
        eBay doesn't provide catalog details.
        Use Brickset for minifigure details instead.
        """
        logger.warning("eBay doesn't provide catalog details - use Brickset adapter instead")
        return None

    async def fetch_price_listings(
        self,
        set_number: str,
        condition: Optional[str] = None
    ) -> List[ScrapedPriceListing]:
        """
        Fetch price listings from eBay.

        Searches for both active and sold listings to get comprehensive price data.
        """
        logger.info(f"Fetching eBay prices for: {set_number}, condition={condition}")

        all_listings = []

        # Build search keywords
        keywords = f"LEGO minifigure {set_number}"

        # Fetch active listings
        active_listings = await self._search_active_listings(
            keywords=keywords,
            condition=condition,
            limit=25
        )
        all_listings.extend(active_listings)

        # Fetch sold listings (for historical price data)
        sold_listings = await self._search_sold_listings(
            keywords=keywords,
            condition=condition,
            limit=25
        )
        all_listings.extend(sold_listings)

        # Add set_number to all listings
        for listing in all_listings:
            listing.minifigure_set_number = set_number

        logger.info(f"Found {len(all_listings)} eBay listings for {set_number}")
        return all_listings

    async def _search_active_listings(
        self,
        keywords: str,
        condition: Optional[str] = None,
        limit: int = 100
    ) -> List[ScrapedPriceListing]:
        """Search for active (current) listings."""
        params = {
            'keywords': keywords,
            'categoryId': self.MINIFIGURE_CATEGORY,
            'paginationInput.entriesPerPage': str(min(limit, 100)),
            'sortOrder': 'PricePlusShippingLowest'
        }

        # Add condition filter if specified
        if condition:
            condition_map = {
                'NEW': '1000',  # New
                'USED': '3000',  # Used
            }
            if condition.upper() in condition_map:
                params['itemFilter(0).name'] = 'Condition'
                params['itemFilter(0).value'] = condition_map[condition.upper()]

        data = await self._make_api_request('findItemsAdvanced', params)

        if not data:
            return []

        # Parse results
        search_result = data.get('findItemsAdvancedResponse', [{}])[0]
        search_result = search_result.get('searchResult', [{}])[0]

        items = search_result.get('item', [])

        listings = []
        for item in items:
            listing = self._parse_ebay_item(item, "")  # Set number added later
            if listing:
                listings.append(listing)

        return listings

    async def _search_sold_listings(
        self,
        keywords: str,
        condition: Optional[str] = None,
        limit: int = 100
    ) -> List[ScrapedPriceListing]:
        """Search for sold/completed listings (historical prices)."""
        params = {
            'keywords': keywords,
            'categoryId': self.MINIFIGURE_CATEGORY,
            'paginationInput.entriesPerPage': str(min(limit, 100)),
            'sortOrder': 'EndTimeSoonest',
            'itemFilter(0).name': 'SoldItemsOnly',
            'itemFilter(0).value': 'true'
        }

        # Add condition filter
        filter_index = 1
        if condition:
            condition_map = {
                'NEW': '1000',
                'USED': '3000',
            }
            if condition.upper() in condition_map:
                params[f'itemFilter({filter_index}).name'] = 'Condition'
                params[f'itemFilter({filter_index}).value'] = condition_map[condition.upper()]

        data = await self._make_api_request('findCompletedItems', params)

        if not data:
            return []

        # Parse results
        search_result = data.get('findCompletedItemsResponse', [{}])[0]
        search_result = search_result.get('searchResult', [{}])[0]

        items = search_result.get('item', [])

        listings = []
        for item in items:
            listing = self._parse_ebay_item(item, "")
            if listing:
                listings.append(listing)

        return listings

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


# Example usage
async def main():
    """Test the eBay adapter."""
    # You need an eBay API key first
    # Visit: https://developer.ebay.com/signin

    adapter = EBayAdapter(app_id="YOUR_APP_ID_HERE")

    try:
        print("=== Testing eBay Adapter ===")
        print("\nNOTE: You need an eBay App ID to use this adapter.")
        print("Get one free at: https://developer.ebay.com/signin")
        print("\nSearching for LEGO minifigure prices on eBay...")

        # Example: Fetch prices for Darth Vader minifigure
        # prices = await adapter.fetch_price_listings("sw0001")
        #
        # print(f"\nFound {len(prices)} price listings")
        # for price in prices[:5]:
        #     status = "SOLD" if price.raw_data.get('is_sold') else "ACTIVE"
        #     print(f"  - ${price.price:.2f} {price.condition} ({status}) - {price.seller_name}")

    finally:
        await adapter.close()


if __name__ == "__main__":
    asyncio.run(main())
