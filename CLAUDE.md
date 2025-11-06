# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Minifigure-Stonks is a platform for tracking up-to-date pricing and availability of Lego Minifigures.

## Claude Instructions

When asked to develop any system, feature, or aspect, make recommendations rather than assumptions and collect feedback.
The interactions should also serve to educate a junior/medium level developer with implementation recommendations,
best practices, and methods of assessing and filling knowledge gaps. Prioritize planning and explanation over implementation.

## Architecture Decisions

### Technology Stack (Approved)
- **Backend**: Python 3.11+ with FastAPI - Superior scraping libraries, async support, strong typing
- **Database**: PostgreSQL + TimescaleDB - Relational data + optimized time-series for price history
- **Task Queue**: Celery + Redis - Async scraping jobs, scheduled updates, rate limiting
- **Frontend**: Next.js 14+ with TypeScript - SSR for SEO, React for charts, type safety
- **Deployment**: Docker Compose (local) → Railway/Fly.io (production)

### Project Structure (Approved)
- **Repository**: Monorepo with backend and frontend directories
- **Growth Strategy**: Start minimal, add directories/files organically as needed
- **Data Sources**: BrickLink (primary), eBay, LEGO.com, Brickset

### Core Architecture Patterns

**Data Collection Layer**
- Strategy Pattern for source-specific adapters
- Interface: `DataSourceAdapter` with `fetch_listings()`, `parse_data()`, `get_rate_limit()`
- Ethical scraping: respect robots.txt, rate limits, exponential backoff

**Data Processing Pipeline**
- Pipeline Pattern: RawDataValidator → DataNormalizer → DuplicateDetector → PriceAnalyzer → DataPersister
- Fuzzy matching for minifigure names across sources
- Confidence scores for matches, manual review queue for low-confidence

**Data Model**
```
Minifigure: id, name, set_number, theme, year, lego_id, image_urls, metadata
PriceListing: minifigure_id, source, price, currency, timestamp, condition, confidence_score
PriceSnapshot: minifigure_id, date, min/max/avg/median_price, listing_count, sources
UserAlert: user_id, minifigure_id, target_price, conditions
```

## Development Commands

### Backend
```bash
# Setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Development server
uvicorn app.main:app --reload

# Run tests
pytest

# Code formatting
black .
ruff check .
```

## Key Implementation Notes

- **Rate Limiting**: Respect API limits - BrickLink has strict quotas
- **Data Quality**: Store raw responses for debugging/reprocessing
- **Historical Data**: Never delete, only mark as superseded
- **Caching**: Redis with 5-15min TTL for API responses
- **Error Handling**: Circuit breakers, retries, graceful degradation
