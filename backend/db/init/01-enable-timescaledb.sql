-- Enable TimescaleDB extension
-- This runs automatically when the database container first starts

\c minifigure_stonks;

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Verify extension is loaded
SELECT extname, extversion FROM pg_extension WHERE extname = 'timescaledb';

-- Print confirmation
\echo 'TimescaleDB extension enabled successfully'
