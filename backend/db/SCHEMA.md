# Database Schema Documentation

## Overview

The Minifigure-Stonks database is designed to efficiently store and query time-series pricing data for LEGO minifigures from multiple sources.

## Entity Relationship Diagram

```
┌─────────────────┐
│  data_sources   │
│─────────────────│
│ id (PK)         │
│ name            │
│ api_type        │
│ is_active       │
│ rate_limit_*    │
│ last_scraped_*  │
└─────────────────┘
         │
         │ 1:N
         ↓
┌─────────────────┐         ┌──────────────────┐
│  minifigures    │         │ price_listings   │
│─────────────────│←────────│──────────────────│
│ id (PK, UUID)   │  1:N    │ id (PK)          │
│ set_number (UK) │         │ minifigure_id FK │
│ name            │         │ source_id FK     │
│ theme           │         │ timestamp ★      │
│ year_released   │         │ price_usd        │
│ metadata        │         │ condition        │
└─────────────────┘         │ confidence_score │
         │                  │ raw_data         │
         │ 1:N              └──────────────────┘
         ↓                    (TimescaleDB Hypertable)
┌─────────────────┐
│ price_snapshots │
│─────────────────│
│ id (PK)         │
│ minifigure_id FK│
│ date (UK)       │
│ min/max/avg_usd │
│ listing_count   │
│ metadata        │
└─────────────────┘

★ = TimescaleDB partition key
UK = Unique constraint
```

## Table Details

### `data_sources`
**Purpose**: Track external platforms we scrape/query

**Key Fields**:
- `name`: BrickLink, eBay, LEGO, Brickset
- `api_type`: API, SCRAPE, or RSS
- `rate_limit_per_hour`: Respect API limits
- `last_scraped_at`, `last_scrape_success`: Minimal scraping tracking

**Design Decision**: Keep scraping metadata in this table rather than separate `scraping_jobs` table for simplicity.

### `minifigures`
**Purpose**: Core catalog of all minifigures

**Key Fields**:
- `id`: UUID for distributed-system friendliness
- `set_number`: Unique identifier like "sw0001" (searchable)
- `metadata`: JSONB for flexible attributes (tags, categories, related sets)

**Indexes**:
- Full-text search on `name` (GIN index)
- Filter by `theme`, `year_released`
- JSONB index on `metadata`

**Why UUID?**
- No ID collisions when merging data from multiple sources
- More secure (can't enumerate all minifigs by incrementing IDs)
- Distributed-system ready

### `price_listings` (TimescaleDB Hypertable)
**Purpose**: Time-series price data - the heart of the system

**Key Fields**:
- `timestamp`: Partition key for TimescaleDB (chunks every 7 days)
- `price_usd`: All prices normalized to USD immediately
- `original_price`, `original_currency`, `exchange_rate`: Audit trail
- `confidence_score`: Our data quality metric (0.0-1.0)
- `raw_data`: Original API response (JSONB) for reprocessing

**TimescaleDB Benefits**:
- Automatic partitioning by time (7-day chunks)
- Compressed older data (10x space savings)
- Fast time-range queries ("last 30 days")
- Continuous aggregates (real-time rollups)

**Currency Design**:
- Normalize to USD immediately (user choice)
- Store original for transparency
- Simpler queries (no on-the-fly conversion)

### `price_snapshots`
**Purpose**: Pre-aggregated daily statistics for fast dashboard queries

**Key Fields**:
- `date`: Daily granularity
- `min/max/avg/median_price_usd`: Statistical summary
- `listing_count`, `sources_count`: Activity metrics
- `metadata`: Breakdown by source, condition (JSONB)

**Why Pre-Aggregate?**
- Dashboard query: "Show 90-day price chart" → Instant (90 rows vs 10,000+ raw listings)
- Updated by daily batch job
- Trade disk space for query speed

**Unique Constraint**: One snapshot per minifigure per day

## Design Patterns

### 1. Normalization vs Denormalization
- **Normalized**: `data_sources` separate table (DRY, easy to update)
- **Denormalized**: `seller_name` in `price_listings` (no sellers table yet)
- **Hybrid**: `price_snapshots` duplicates aggregates for speed

### 2. Flexible Schema (JSONB)
- `metadata` fields allow growth without migrations
- Indexed for queryability
- Example uses:
  ```json
  minifigures.metadata: {
    "tags": ["rare", "exclusive"],
    "related_sets": ["10188", "75192"],
    "official_retirement_date": "2023-12-31"
  }
  ```

### 3. Data Quality Tracking
- `confidence_score`: Fuzzy matching quality (BrickLink says "Darth Vader", eBay says "Dark Vador")
- `raw_data`: Audit trail, reprocessing capability
- Never delete data, only mark as superseded

### 4. Time-Series Optimization
- TimescaleDB hypertable for `price_listings`
- Automatic partitioning (7-day chunks)
- Retention policies (compress/delete old data)
- Continuous aggregates (auto-updating materialized views)

## Query Patterns

### Common Queries & Indexes

```sql
-- 1. "Find all Star Wars minifigs from 2020"
SELECT * FROM minifigures
WHERE theme = 'Star Wars' AND year_released = 2020;
-- Uses: idx_minifigures_theme, idx_minifigures_year

-- 2. "Show price history for last 30 days"
SELECT timestamp, price_usd FROM price_listings
WHERE minifigure_id = '...' AND timestamp > NOW() - INTERVAL '30 days'
ORDER BY timestamp DESC;
-- Uses: idx_price_listings_minifigure (minifigure_id, timestamp)

-- 3. "Search minifigs by name"
SELECT * FROM minifigures
WHERE to_tsvector('english', name) @@ to_tsquery('vader & darth');
-- Uses: idx_minifigures_name (GIN full-text index)

-- 4. "90-day price chart (fast)"
SELECT date, avg_price_usd FROM price_snapshots
WHERE minifigure_id = '...' AND date > CURRENT_DATE - 90
ORDER BY date;
-- Uses: idx_price_snapshots_minifigure
```

## Future Enhancements (v2)

### Deferred to Later
1. **Sellers Table**: Track seller history, ratings, trust scores
2. **Scraping Jobs Table**: Detailed scraping logs and metrics
3. **User Accounts**: Wishlists, alerts, collections
4. **Price Alerts**: Notification system
5. **Multi-Currency Support**: Store all currencies, convert on display

### TimescaleDB Advanced Features
- **Continuous Aggregates**: Auto-update price_snapshots in real-time
- **Compression**: Compress data older than 90 days (10x space savings)
- **Retention Policies**: Auto-delete listings older than 2 years
- **Data Tiering**: Move old data to S3 (cold storage)

## Migration Strategy

Using Alembic for version-controlled schema changes:

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

**Initial Setup**:
1. Create all tables
2. Enable TimescaleDB extension
3. Convert `price_listings` to hypertable
4. Create indexes
5. Seed `data_sources` with initial platforms
