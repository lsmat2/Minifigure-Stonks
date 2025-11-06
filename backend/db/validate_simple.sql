-- Simplified Schema Validation
-- Insert test data and verify queries work

\echo '==========================================
'
\echo 'Inserting test price data...'

-- Insert price listings for Darth Vader over 30 days
INSERT INTO price_listings
    (minifigure_id, source_id, timestamp, price_usd, original_currency, condition, seller_name, raw_data)
SELECT
    m.id,
    ds.id,
    NOW() - (day_offset || ' days')::INTERVAL,
    8.50 + (RANDOM() * 2 - 1),  -- Price fluctuates $7.50-$9.50
    'USD',
    'NEW'::condition_type,
    'test_seller_' || (RANDOM() * 10)::INT,
    '{"test": true}'::jsonb
FROM
    minifigures m
    CROSS JOIN data_sources ds
    CROSS JOIN generate_series(0, 29) as day_offset
WHERE m.set_number = 'sw0001'
    AND ds.name = 'BrickLink';

\echo 'Price listings inserted ✓'
\echo ''

\echo 'Last 7 days of Darth Vader prices:'
SELECT
    DATE(timestamp) as date,
    COUNT(*) as listings,
    ROUND(MIN(price_usd)::numeric, 2) as min_usd,
    ROUND(AVG(price_usd)::numeric, 2) as avg_usd,
    ROUND(MAX(price_usd)::numeric, 2) as max_usd
FROM price_listings pl
JOIN minifigures m ON pl.minifigure_id = m.id
WHERE m.set_number = 'sw0001'
    AND timestamp > NOW() - INTERVAL '7 days'
GROUP BY DATE(timestamp)
ORDER BY date DESC;

\echo ''
\echo 'Validation Complete ✓'
