-- Schema Validation Script
-- Tests all tables, relationships, indexes, and constraints

\echo '=========================================='
\echo 'SCHEMA VALIDATION TEST'
\echo '=========================================='
\echo ''

-- ============================================================================
-- TEST 1: Verify Tables Exist
-- ============================================================================
\echo 'TEST 1: Checking tables exist...'
SELECT
    tablename,
    CASE
        WHEN tablename IN ('data_sources', 'minifigures', 'price_listings', 'price_snapshots')
        THEN '✓'
        ELSE '✗'
    END as status
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
\echo ''

-- ============================================================================
-- TEST 2: Verify TimescaleDB Hypertable
-- ============================================================================
\echo 'TEST 2: Checking TimescaleDB hypertable...'
SELECT
    hypertable_name,
    num_dimensions,
    CASE WHEN is_distributed THEN 'Distributed' ELSE 'Single-node' END as type
FROM timescaledb_information.hypertables
WHERE hypertable_name = 'price_listings';
\echo ''

-- ============================================================================
-- TEST 3: Insert Test Minifigures
-- ============================================================================
\echo 'TEST 3: Inserting test minifigures...'

INSERT INTO minifigures (set_number, name, theme, subtheme, year_released, metadata) VALUES
    ('sw0001', 'Darth Vader (with Cape)', 'Star Wars', 'Classic', 1999, '{"tags": ["villain", "iconic"], "rarity": "common"}'),
    ('sw0215', 'Boba Fett (Cloud City)', 'Star Wars', 'Empire Strikes Back', 2010, '{"tags": ["bounty hunter", "rare"], "rarity": "rare"}'),
    ('hp001', 'Harry Potter', 'Harry Potter', 'Sorcerer''s Stone', 2001, '{"tags": ["protagonist", "wand"], "rarity": "common"}'),
    ('col001', 'Zombie', 'Collectible Minifigures', 'Series 1', 2010, '{"tags": ["undead", "classic"], "rarity": "uncommon"}')
ON CONFLICT (set_number) DO NOTHING;

SELECT COUNT(*) || ' minifigures inserted' as result FROM minifigures;
\echo ''

-- ============================================================================
-- TEST 4: Insert Test Price Listings (Time-series data)
-- ============================================================================
\echo 'TEST 4: Inserting price listings across time...'

-- Get minifigure IDs for reference
WITH minifig_ids AS (
    SELECT id, set_number FROM minifigures WHERE set_number IN ('sw0001', 'sw0215', 'hp001')
),
source_ids AS (
    SELECT id, name FROM data_sources WHERE name = 'BrickLink'
)

-- Insert price data over last 30 days
INSERT INTO price_listings
    (minifigure_id, source_id, timestamp, price_usd, original_price, original_currency, exchange_rate, condition, seller_name, confidence_score, raw_data)
SELECT
    m.id,
    s.id,
    NOW() - (days || ' days')::INTERVAL,
    -- Simulate price fluctuation: base price +/- random variation
    CASE m.set_number
        WHEN 'sw0001' THEN 8.50 + (RANDOM() * 2 - 1)  -- $7.50-$9.50
        WHEN 'sw0215' THEN 45.00 + (RANDOM() * 10 - 5)  -- $40-$50
        WHEN 'hp001' THEN 12.00 + (RANDOM() * 3 - 1.5)  -- $10.50-$13.50
    END,
    NULL,  -- original_price (same as USD for BrickLink)
    'USD',
    1.0,
    CASE WHEN RANDOM() > 0.7 THEN 'USED' ELSE 'NEW' END,
    'seller_' || (RANDOM() * 100)::INT,
    0.95 + (RANDOM() * 0.05),  -- confidence 0.95-1.0
    '{"source": "test_data"}'::jsonb
FROM
    minifig_ids m
    CROSS JOIN source_ids s
    CROSS JOIN generate_series(0, 29) as days;

SELECT COUNT(*) || ' price listings inserted' as result FROM price_listings;
\echo ''

-- ============================================================================
-- TEST 5: Query Time-series Data
-- ============================================================================
\echo 'TEST 5: Querying price history (last 7 days for Darth Vader)...'

SELECT
    DATE(timestamp) as date,
    COUNT(*) as listing_count,
    ROUND(MIN(price_usd)::numeric, 2) as min_price,
    ROUND(MAX(price_usd)::numeric, 2) as max_price,
    ROUND(AVG(price_usd)::numeric, 2) as avg_price
FROM price_listings pl
JOIN minifigures m ON pl.minifigure_id = m.id
WHERE m.set_number = 'sw0001'
    AND timestamp > NOW() - INTERVAL '7 days'
GROUP BY DATE(timestamp)
ORDER BY date DESC
LIMIT 7;
\echo ''

-- ============================================================================
-- TEST 6: Create Price Snapshots (Aggregation)
-- ============================================================================
\echo 'TEST 6: Creating daily price snapshots...'

INSERT INTO price_snapshots (minifigure_id, date, min_price_usd, max_price_usd, avg_price_usd, median_price_usd, listing_count, sources_count, metadata)
SELECT
    pl.minifigure_id,
    DATE(pl.timestamp) as date,
    MIN(pl.price_usd),
    MAX(pl.price_usd),
    AVG(pl.price_usd),
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY pl.price_usd) as median_price,
    COUNT(*) as listing_count,
    COUNT(DISTINCT pl.source_id) as sources_count,
    jsonb_build_object(
        'conditions', jsonb_object_agg(condition, condition_count)
    ) as metadata
FROM price_listings pl
LEFT JOIN LATERAL (
    SELECT condition, COUNT(*) as condition_count
    FROM price_listings pl2
    WHERE pl2.minifigure_id = pl.minifigure_id
        AND DATE(pl2.timestamp) = DATE(pl.timestamp)
    GROUP BY condition
) conditions ON true
WHERE DATE(pl.timestamp) >= CURRENT_DATE - 30
GROUP BY pl.minifigure_id, DATE(pl.timestamp)
ON CONFLICT (minifigure_id, date) DO UPDATE SET
    min_price_usd = EXCLUDED.min_price_usd,
    max_price_usd = EXCLUDED.max_price_usd,
    avg_price_usd = EXCLUDED.avg_price_usd,
    median_price_usd = EXCLUDED.median_price_usd,
    listing_count = EXCLUDED.listing_count,
    sources_count = EXCLUDED.sources_count,
    metadata = EXCLUDED.metadata,
    updated_at = NOW();

SELECT COUNT(*) || ' price snapshots created' as result FROM price_snapshots;
\echo ''

-- ============================================================================
-- TEST 7: Query Price Snapshots (Fast Dashboard Query)
-- ============================================================================
\echo 'TEST 7: Fast price chart query (Boba Fett - last 14 days)...'

SELECT
    ps.date,
    m.name,
    ROUND(ps.min_price_usd::numeric, 2) as min,
    ROUND(ps.avg_price_usd::numeric, 2) as avg,
    ROUND(ps.max_price_usd::numeric, 2) as max,
    ps.listing_count
FROM price_snapshots ps
JOIN minifigures m ON ps.minifigure_id = m.id
WHERE m.set_number = 'sw0215'
ORDER BY ps.date DESC
LIMIT 14;
\echo ''

-- ============================================================================
-- TEST 8: Test Full-text Search
-- ============================================================================
\echo 'TEST 8: Full-text search for "vader"...'

SELECT
    set_number,
    name,
    theme,
    year_released
FROM minifigures
WHERE to_tsvector('english', name) @@ to_tsquery('vader')
ORDER BY year_released;
\echo ''

-- ============================================================================
-- TEST 9: Test JSONB Metadata Queries
-- ============================================================================
\echo 'TEST 9: Find all rare minifigures using JSONB metadata...'

SELECT
    set_number,
    name,
    metadata->>'rarity' as rarity,
    metadata->'tags' as tags
FROM minifigures
WHERE metadata->>'rarity' = 'rare';
\echo ''

-- ============================================================================
-- TEST 10: Verify Indexes
-- ============================================================================
\echo 'TEST 10: Checking indexes exist...'

SELECT
    tablename,
    indexname,
    '✓' as status
FROM pg_indexes
WHERE schemaname = 'public'
    AND tablename IN ('minifigures', 'price_listings', 'price_snapshots')
ORDER BY tablename, indexname;
\echo ''

-- ============================================================================
-- TEST 11: Check Constraints
-- ============================================================================
\echo 'TEST 11: Testing constraints...'

-- Test positive price constraint (should fail)
\echo 'Testing price constraint (negative price should fail)...'
DO $$
BEGIN
    INSERT INTO price_listings (minifigure_id, source_id, timestamp, price_usd, condition)
    SELECT
        (SELECT id FROM minifigures LIMIT 1),
        (SELECT id FROM data_sources LIMIT 1),
        NOW(),
        -10.00,  -- Negative price
        'NEW';
    RAISE EXCEPTION 'Constraint test failed: negative price was allowed!';
EXCEPTION
    WHEN check_violation THEN
        RAISE NOTICE '✓ Price constraint working: negative price rejected';
END $$;
\echo ''

-- ============================================================================
-- SUMMARY
-- ============================================================================
\echo '=========================================='
\echo 'VALIDATION SUMMARY'
\echo '=========================================='
SELECT
    'Tables' as category,
    COUNT(*) as count
FROM pg_tables WHERE schemaname = 'public'
UNION ALL
SELECT
    'Minifigures',
    COUNT(*)
FROM minifigures
UNION ALL
SELECT
    'Price Listings',
    COUNT(*)
FROM price_listings
UNION ALL
SELECT
    'Price Snapshots',
    COUNT(*)
FROM price_snapshots
UNION ALL
SELECT
    'Data Sources',
    COUNT(*)
FROM data_sources
UNION ALL
SELECT
    'Indexes',
    COUNT(*)
FROM pg_indexes WHERE schemaname = 'public';

\echo ''
\echo '=========================================='
\echo 'VALIDATION COMPLETE ✓'
\echo '=========================================='
