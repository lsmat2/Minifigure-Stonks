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

### Docker Environment
```bash
# Start all services (PostgreSQL + TimescaleDB + Redis)
docker-compose up -d

# View logs
docker-compose logs -f [service_name]

# Stop services
docker-compose down

# Rebuild after Dockerfile changes
docker-compose up -d --build

# Access database
docker exec -it minifig_db psql -U minifig_user -d minifigure_stonks

# Access Redis CLI
docker exec -it minifig_redis redis-cli
```

### Backend
```bash
# Setup (if not using Docker)
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

## Performance Optimization Checklist (Pre-Production)

Before deploying to production, review and optimize:

1. **Database Driver**: Replace `psycopg2-binary` with `psycopg2` in requirements.txt
   - Binary version is development convenience only
   - Production needs compiled version for 20-30% better performance
   - Requires: `apt-get install libpq-dev` (Ubuntu) or `brew install postgresql` (Mac)

2. **Database Indexes**: Review query patterns and add indexes
   - `minifigures(set_number)` - frequently queried
   - `price_listings(minifigure_id, timestamp)` - for time-series queries
   - `price_listings(source, timestamp)` - for source-specific analytics

3. **Query Optimization**: Use `.explain()` to identify slow queries
   - Consider materialized views for complex analytics
   - Implement database query result caching

4. **Celery Workers**: Configure proper concurrency
   - Development: 1-2 workers
   - Production: Scale based on scraping volume (start with 4-8)

5. **Redis Configuration**:
   - Set maxmemory policy (`allkeys-lru` for cache eviction)
   - Enable persistence if needed (RDB snapshots)

6. **API Response Caching**: Implement cache headers and ETags
   - Static data (minifigure catalog): 24h cache
   - Price data: 5-15min cache
   - Analytics: 1h cache

7. **Frontend Optimization** (when implemented):
   - Image optimization (WebP format, lazy loading)
   - Code splitting and tree shaking
   - CDN for static assets
