-- Seed initial data sources

INSERT INTO data_sources (name, base_url, api_type, is_active, rate_limit_per_hour) VALUES
    ('BrickLink', 'https://api.bricklink.com', 'API', true, 5000),
    ('eBay', 'https://www.ebay.com', 'SCRAPE', false, 100),  -- Disabled until we implement scraper
    ('LEGO', 'https://www.lego.com', 'SCRAPE', false, 60),
    ('Brickset', 'https://brickset.com/api', 'API', false, 1000)
ON CONFLICT (name) DO NOTHING;

-- Verify
SELECT id, name, api_type, is_active FROM data_sources ORDER BY id;
