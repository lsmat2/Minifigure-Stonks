-- Minifigure-Stonks Database Schema
-- PostgreSQL + TimescaleDB
-- Design decisions documented in CLAUDE.md

-- ============================================================================
-- ENUMS
-- ============================================================================

CREATE TYPE condition_type AS ENUM ('NEW', 'USED', 'SEALED');
CREATE TYPE api_type AS ENUM ('API', 'SCRAPE', 'RSS');

-- ============================================================================
-- TABLES
-- ============================================================================

-- Data Sources: External platforms we scrape/query
CREATE TABLE data_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,  -- 'BrickLink', 'eBay', etc.
    base_url VARCHAR(500),
    api_type api_type NOT NULL,
    is_active BOOLEAN DEFAULT true,
    rate_limit_per_hour INTEGER,

    -- Scraping tracking (minimal approach)
    last_scraped_at TIMESTAMPTZ,
    last_scrape_success BOOLEAN,
    last_scrape_error TEXT,
    successful_scrapes_count INTEGER DEFAULT 0,
    failed_scrapes_count INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Minifigures: Core catalog
CREATE TABLE minifigures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    set_number VARCHAR(50) NOT NULL UNIQUE,  -- 'sw0001', 'hp001', etc.
    name VARCHAR(500) NOT NULL,
    theme VARCHAR(100),
    subtheme VARCHAR(100),
    year_released INTEGER,
    lego_item_number VARCHAR(50),  -- Official LEGO ID

    -- Images
    image_url VARCHAR(1000),
    thumbnail_url VARCHAR(1000),

    -- Physical properties
    weight_grams DECIMAL(8,2),
    piece_count INTEGER,

    -- Flexible metadata (JSONB for extensibility)
    -- Can store: tags, categories, related_sets, etc.
    metadata JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Indexes
    CONSTRAINT year_released_check CHECK (year_released >= 1900 AND year_released <= 2100)
);

-- Price Listings: Time-series price data (will become hypertable)
CREATE TABLE price_listings (
    id BIGSERIAL,
    minifigure_id UUID NOT NULL REFERENCES minifigures(id) ON DELETE CASCADE,
    source_id INTEGER NOT NULL REFERENCES data_sources(id) ON DELETE CASCADE,

    -- Time-series key field
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Price information (all normalized to USD)
    price_usd DECIMAL(10,2) NOT NULL,
    original_price DECIMAL(10,2),  -- Store original for reference
    original_currency CHAR(3),      -- 'EUR', 'GBP', etc.
    exchange_rate DECIMAL(10,6),    -- Rate used for conversion

    condition condition_type NOT NULL,
    quantity_available INTEGER,

    -- Listing details
    listing_url TEXT,
    seller_name VARCHAR(200),  -- Plain text for now (no FK to sellers table)
    seller_rating DECIMAL(3,2),  -- 0.00 to 5.00

    -- Data quality
    confidence_score DECIMAL(3,2) DEFAULT 1.00,  -- Our matching confidence (0.00 to 1.00)

    -- Raw data for reprocessing
    raw_data JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT price_usd_positive CHECK (price_usd > 0),
    CONSTRAINT confidence_score_range CHECK (confidence_score >= 0 AND confidence_score <= 1),
    CONSTRAINT seller_rating_range CHECK (seller_rating IS NULL OR (seller_rating >= 0 AND seller_rating <= 5))
);

-- Convert to TimescaleDB hypertable (partitioned by timestamp)
-- This will be done in migration, but documenting here:
-- SELECT create_hypertable('price_listings', 'timestamp', chunk_time_interval => INTERVAL '7 days');

-- Price Snapshots: Pre-aggregated daily statistics
CREATE TABLE price_snapshots (
    id BIGSERIAL PRIMARY KEY,
    minifigure_id UUID NOT NULL REFERENCES minifigures(id) ON DELETE CASCADE,
    date DATE NOT NULL,

    -- Aggregate statistics
    min_price_usd DECIMAL(10,2) NOT NULL,
    max_price_usd DECIMAL(10,2) NOT NULL,
    avg_price_usd DECIMAL(10,2) NOT NULL,
    median_price_usd DECIMAL(10,2) NOT NULL,

    -- Counts
    listing_count INTEGER NOT NULL,
    sources_count INTEGER NOT NULL,  -- How many sources had data this day

    -- Breakdown by source, condition, etc. (flexible)
    metadata JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Unique constraint: one snapshot per minifig per day
    CONSTRAINT unique_minifig_date UNIQUE(minifigure_id, date)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Minifigures
CREATE INDEX idx_minifigures_theme ON minifigures(theme);
CREATE INDEX idx_minifigures_year ON minifigures(year_released);
CREATE INDEX idx_minifigures_name ON minifigures USING gin(to_tsvector('english', name));  -- Full-text search
CREATE INDEX idx_minifigures_metadata ON minifigures USING gin(metadata);  -- JSONB index

-- Price Listings (before converting to hypertable)
CREATE INDEX idx_price_listings_minifigure ON price_listings(minifigure_id, timestamp DESC);
CREATE INDEX idx_price_listings_source ON price_listings(source_id, timestamp DESC);
CREATE INDEX idx_price_listings_timestamp ON price_listings(timestamp DESC);
CREATE INDEX idx_price_listings_condition ON price_listings(condition);

-- Price Snapshots
CREATE INDEX idx_price_snapshots_minifigure ON price_snapshots(minifigure_id, date DESC);
CREATE INDEX idx_price_snapshots_date ON price_snapshots(date DESC);

-- ============================================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================================

-- Automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_data_sources_updated_at
    BEFORE UPDATE ON data_sources
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_minifigures_updated_at
    BEFORE UPDATE ON minifigures
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_price_snapshots_updated_at
    BEFORE UPDATE ON price_snapshots
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COMMENTS (Documentation)
-- ============================================================================

COMMENT ON TABLE data_sources IS 'External data sources (BrickLink, eBay, etc.)';
COMMENT ON TABLE minifigures IS 'Core minifigure catalog';
COMMENT ON TABLE price_listings IS 'Time-series price data (TimescaleDB hypertable)';
COMMENT ON TABLE price_snapshots IS 'Pre-aggregated daily price statistics';

COMMENT ON COLUMN minifigures.metadata IS 'Flexible JSONB field for extensibility (tags, categories, etc.)';
COMMENT ON COLUMN price_listings.confidence_score IS 'Data quality score (0.0-1.0) for fuzzy matches';
COMMENT ON COLUMN price_listings.raw_data IS 'Original API response for reprocessing and audit trail';
COMMENT ON COLUMN price_snapshots.metadata IS 'Breakdown by source, condition, etc.';
