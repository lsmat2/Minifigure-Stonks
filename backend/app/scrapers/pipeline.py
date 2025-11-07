"""
Data Processing Pipeline

Implements Pipeline Pattern for processing scraped data:
RawDataValidator → DataNormalizer → DuplicateDetector → DataPersister

Each stage transforms the data and passes it to the next stage.
"""

from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
import logging

from sqlalchemy.orm import Session
from app.scrapers.base import ScrapedMinifigure, ScrapedPriceListing
from app.models.minifigure import Minifigure
from app.models.price import PriceListing, DataSource

logger = logging.getLogger(__name__)


class PipelineStage(ABC):
    """Base class for pipeline stages."""

    def __init__(self, next_stage: Optional['PipelineStage'] = None):
        self.next_stage = next_stage

    @abstractmethod
    async def process(self, data: Any, context: Dict[str, Any]) -> Any:
        """Process data and pass to next stage."""
        pass

    async def execute_next(self, data: Any, context: Dict[str, Any]) -> Any:
        """Execute the next stage in the pipeline."""
        if self.next_stage:
            return await self.next_stage.process(data, context)
        return data


class RawDataValidator(PipelineStage):
    """
    Stage 1: Validate raw scraped data.

    Ensures data meets minimum quality requirements before processing.
    """

    def __init__(self, next_stage: Optional[PipelineStage] = None):
        super().__init__(next_stage)
        self.required_minifig_fields = ['set_number', 'name']
        self.required_price_fields = ['minifigure_set_number', 'price', 'currency']

    async def process(
        self,
        data: List[ScrapedMinifigure | ScrapedPriceListing],
        context: Dict[str, Any]
    ) -> List[ScrapedMinifigure | ScrapedPriceListing]:
        """Validate scraped data."""
        if not data:
            logger.warning("No data to validate")
            return []

        validated = []
        for item in data:
            if self._validate_item(item):
                validated.append(item)
            else:
                logger.warning(f"Invalid data item: {item}")

        logger.info(f"Validated {len(validated)}/{len(data)} items")
        return await self.execute_next(validated, context)

    def _validate_item(self, item: ScrapedMinifigure | ScrapedPriceListing) -> bool:
        """Check if item meets minimum requirements."""
        if isinstance(item, ScrapedMinifigure):
            return all(getattr(item, field, None) for field in self.required_minifig_fields)
        elif isinstance(item, ScrapedPriceListing):
            # Check required fields
            if not all(getattr(item, field, None) for field in self.required_price_fields):
                return False
            # Validate price is positive
            if item.price <= 0:
                return False
            return True
        return False


class DataNormalizer(PipelineStage):
    """
    Stage 2: Normalize data to consistent format.

    - Standardize set numbers
    - Convert currencies to USD
    - Normalize condition values
    """

    # Currency conversion rates (in production, use live API)
    EXCHANGE_RATES = {
        'USD': Decimal('1.00'),
        'EUR': Decimal('1.08'),
        'GBP': Decimal('1.26'),
        'CAD': Decimal('0.74'),
        'AUD': Decimal('0.66'),
    }

    CONDITION_MAPPING = {
        'new': 'NEW',
        'used': 'USED',
        'sealed': 'SEALED',
        'mint': 'NEW',
        'complete': 'USED',
    }

    async def process(
        self,
        data: List[ScrapedMinifigure | ScrapedPriceListing],
        context: Dict[str, Any]
    ) -> List[ScrapedMinifigure | ScrapedPriceListing]:
        """Normalize data."""
        normalized = []

        for item in data:
            if isinstance(item, ScrapedMinifigure):
                normalized.append(self._normalize_minifigure(item))
            elif isinstance(item, ScrapedPriceListing):
                normalized.append(self._normalize_price(item))

        logger.info(f"Normalized {len(normalized)} items")
        return await self.execute_next(normalized, context)

    def _normalize_minifigure(self, item: ScrapedMinifigure) -> ScrapedMinifigure:
        """Normalize minifigure data."""
        # Standardize set number format (lowercase, strip spaces)
        item.set_number = item.set_number.lower().strip()

        # Clean theme/subtheme
        if item.theme:
            item.theme = item.theme.strip()
        if item.subtheme:
            item.subtheme = item.subtheme.strip()

        return item

    def _normalize_price(self, item: ScrapedPriceListing) -> ScrapedPriceListing:
        """Normalize price listing data."""
        # Store original values
        original_price = Decimal(str(item.price))
        original_currency = item.currency

        # Convert to USD
        rate = self.EXCHANGE_RATES.get(item.currency, Decimal('1.00'))
        item.price = float(original_price * rate)
        item.currency = 'USD'

        # Store original values in raw_data
        if not item.raw_data:
            item.raw_data = {}
        item.raw_data['original_price'] = str(original_price)
        item.raw_data['original_currency'] = original_currency
        item.raw_data['exchange_rate'] = str(rate)

        # Normalize condition
        condition_lower = item.condition.lower()
        item.condition = self.CONDITION_MAPPING.get(condition_lower, 'USED')

        # Standardize set number
        item.minifigure_set_number = item.minifigure_set_number.lower().strip()

        return item


class DuplicateDetector(PipelineStage):
    """
    Stage 3: Detect and handle duplicate entries.

    - Checks for existing minifigures
    - Prevents duplicate price listings
    """

    def __init__(self, db: Session, next_stage: Optional[PipelineStage] = None):
        super().__init__(next_stage)
        self.db = db

    async def process(
        self,
        data: List[ScrapedMinifigure | ScrapedPriceListing],
        context: Dict[str, Any]
    ) -> List[ScrapedMinifigure | ScrapedPriceListing]:
        """Filter out duplicates."""
        unique = []

        for item in data:
            if isinstance(item, ScrapedMinifigure):
                if not self._is_duplicate_minifigure(item):
                    unique.append(item)
            elif isinstance(item, ScrapedPriceListing):
                if not self._is_duplicate_price(item):
                    unique.append(item)

        logger.info(f"Filtered to {len(unique)} unique items (removed {len(data) - len(unique)} duplicates)")
        return await self.execute_next(unique, context)

    def _is_duplicate_minifigure(self, item: ScrapedMinifigure) -> bool:
        """Check if minifigure already exists."""
        existing = self.db.query(Minifigure).filter(
            Minifigure.set_number == item.set_number
        ).first()
        return existing is not None

    def _is_duplicate_price(self, item: ScrapedPriceListing) -> bool:
        """Check if price listing is a duplicate."""
        # Get data source
        source = self.db.query(DataSource).filter(
            DataSource.name == item.source
        ).first()

        if not source:
            return False

        # Find minifigure
        minifig = self.db.query(Minifigure).filter(
            Minifigure.set_number == item.minifigure_set_number
        ).first()

        if not minifig:
            logger.warning(f"Minifigure {item.minifigure_set_number} not found for price listing")
            return True  # Skip if minifigure doesn't exist

        # Check for recent duplicate (within last hour, same seller, same price)
        one_hour_ago = datetime.utcnow().replace(tzinfo=None) - timedelta(hours=1)

        existing = self.db.query(PriceListing).filter(
            PriceListing.minifigure_id == minifig.id,
            PriceListing.source_id == source.id,
            PriceListing.timestamp >= one_hour_ago,
            PriceListing.price_usd == Decimal(str(item.price)),
            PriceListing.seller_name == item.seller_name
        ).first()

        return existing is not None


class DataPersister(PipelineStage):
    """
    Stage 4: Persist data to database.

    Final stage that saves validated, normalized, unique data.
    """

    def __init__(self, db: Session):
        super().__init__(None)  # Final stage, no next
        self.db = db

    async def process(
        self,
        data: List[ScrapedMinifigure | ScrapedPriceListing],
        context: Dict[str, Any]
    ) -> Dict[str, int]:
        """Save data to database."""
        saved_count = 0
        error_count = 0

        for item in data:
            try:
                if isinstance(item, ScrapedMinifigure):
                    self._save_minifigure(item)
                elif isinstance(item, ScrapedPriceListing):
                    self._save_price_listing(item)
                saved_count += 1
            except Exception as e:
                logger.error(f"Error saving item: {e}", exc_info=True)
                error_count += 1

        self.db.commit()
        logger.info(f"Saved {saved_count} items ({error_count} errors)")

        return {
            'saved': saved_count,
            'errors': error_count,
            'total': len(data)
        }

    def _save_minifigure(self, item: ScrapedMinifigure):
        """Save minifigure to database."""
        minifig = Minifigure(
            set_number=item.set_number,
            name=item.name,
            theme=item.theme,
            subtheme=item.subtheme,
            year_released=item.year_released,
            image_url=item.image_url,
            thumbnail_url=item.thumbnail_url,
            weight_grams=item.weight_grams,
            piece_count=item.piece_count,
            extra_data=item.raw_data or {}
        )
        self.db.add(minifig)

    def _save_price_listing(self, item: ScrapedPriceListing):
        """Save price listing to database."""
        # Get data source
        source = self.db.query(DataSource).filter(
            DataSource.name == item.source
        ).first()

        if not source:
            logger.error(f"Data source {item.source} not found")
            return

        # Find minifigure
        minifig = self.db.query(Minifigure).filter(
            Minifigure.set_number == item.minifigure_set_number
        ).first()

        if not minifig:
            logger.error(f"Minifigure {item.minifigure_set_number} not found")
            return

        # Create price listing
        price = PriceListing(
            minifigure_id=minifig.id,
            source_id=source.id,
            timestamp=item.timestamp,
            price_usd=Decimal(str(item.price)),
            original_price=Decimal(str(item.raw_data.get('original_price', item.price))),
            original_currency=item.raw_data.get('original_currency', 'USD'),
            condition=item.condition,
            quantity_available=item.quantity_available,
            seller_name=item.seller_name,
            seller_rating=Decimal(str(item.seller_rating)) if item.seller_rating else None,
            confidence_score=Decimal(str(item.confidence_score)),
            raw_data=item.raw_data or {}
        )
        self.db.add(price)


# Import for timedelta
from datetime import timedelta
