# Minifigure-Stonks Project Status

**Last Updated:** 2025-01-23
**Current Phase:** Data Collection Infrastructure - Testing Phase
**Total Commits:** 17

---

## 🎯 Project Overview

A full-stack LEGO minifigure price tracking platform that aggregates data from multiple sources (Brickset, eBay, BrickLink) to provide historical price analytics and trends.

### Tech Stack
- **Backend:** FastAPI + Python 3.11+
- **Database:** PostgreSQL + TimescaleDB (time-series optimization)
- **Task Queue:** Celery + Redis
- **Frontend:** Next.js 14 + TypeScript + Tailwind CSS
- **Deployment:** Docker Compose (local) → Railway/Fly.io (future)

---

## ✅ Completed Components

### 1. Backend API (FastAPI)
**Status:** ✅ Complete and working

**Endpoints Implemented:**
- `GET /v1/health` - Service health check
- `GET /v1/health/db` - Database connectivity check
- `GET /v1/minifigures` - List minifigures (paginated, filterable by theme/year/search)
- `GET /v1/minifigures/{id}` - Get single minifigure details
- `POST /v1/minifigures` - Create minifigure
- `PUT /v1/minifigures/{id}` - Update minifigure
- `DELETE /v1/minifigures/{id}` - Delete minifigure
- `GET /v1/minifigures/{id}/prices` - Get raw price listings with filters
- `GET /v1/minifigures/{id}/price-history` - Get historical price snapshots for charts
- `GET /v1/snapshots` - Query price snapshots with flexible filtering

**Running:**
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Interactive Docs:** http://localhost:8000/v1/docs

### 2. Database Schema
**Status:** ✅ Complete and validated

**Tables:**
- `data_sources` - Platforms we scrape (BrickLink, eBay, Brickset)
- `minifigures` - Core catalog (UUID id, set_number, theme, metadata JSONB)
- `price_listings` - **TimescaleDB hypertable** partitioned by timestamp (7-day chunks)
- `price_snapshots` - Daily aggregates (min/max/avg/median, pre-computed for speed)

**Key Design Decisions:**
- All prices normalized to USD immediately
- Stores `original_price`, `original_currency`, `exchange_rate` for audit trail
- JSONB `extra_data` field (mapped to "metadata" column via `serialization_alias`)
- No sellers table yet (deferred to v2, store `seller_name` as text)

**Database Access:**
```bash
docker exec -it minifig_db psql -U minifig_user -d minifigure_stonks
```

### 3. Frontend UI
**Status:** ✅ Complete and working

**Pages:**
- `/` - Homepage with featured minifigures
- `/minifigures` - Browse page with search, filters, pagination
- `/minifigures/[id]` - Detail page with price history charts

**Components Created:**
- `MinifigureCard` - Reusable card for grid layouts
- `SearchBar` - Debounced search input (300ms delay)
- `Filters` - Theme and year filtering
- `Pagination` - Page navigation
- `PriceChart` - Interactive Recharts visualization (avg/median/min/max)
- `PriceStats` - Statistics cards
- `Navigation` - Site navigation

**Features:**
- Responsive design with dark mode
- SWR for data fetching with caching
- Time range selector (7D/30D/90D/1Y)

**Running:**
```bash
cd frontend
npm run dev
```

**Access:** http://localhost:3000

### 4. Data Collection Infrastructure
**Status:** ✅ Built, ⚠️ Testing blocked by issues

#### Data Source Adapters (Strategy Pattern)

**Base Interface:** `backend/app/scrapers/base.py`
- `DataSourceAdapter` abstract class
- `RateLimitConfig` for ethical scraping
- `ScrapedMinifigure` and `ScrapedPriceListing` dataclasses

**Implemented Adapters:**

1. **Brickset** (`backend/app/scrapers/brickset.py`)
   - **Status:** ✅ API key obtained
   - **Purpose:** Minifigure catalog data (names, themes, images, years)
   - **API:** Free public API v3 (no OAuth)
   - **Rate Limits:** 60 req/min, 3600 req/hour
   - **API Key:** `3-ieOx-CAPX-beMAH` (configured in `.env`)
   - **Get Key:** https://brickset.com/tools/webservices/requestkey

2. **eBay** (`backend/app/scrapers/ebay.py`)
   - **Status:** ⏳ Waiting for API key
   - **Purpose:** Marketplace price data (active + sold listings)
   - **API:** eBay Finding API (free, no OAuth)
   - **Rate Limits:** 100 req/min, 5000 req/day
   - **API Key:** `YOUR_EBAY_APP_ID_HERE` (placeholder in `.env`)
   - **Get Key:** https://developer.ebay.com/signin → https://developer.ebay.com/my/keys
   - **Category:** Searches LEGO Minifigures category ID 19006
   - **Confidence Scoring:** Adjusts based on listing type, seller rating, sold status

3. **BrickLink** (`backend/app/scrapers/bricklink.py`)
   - **Status:** ⏸️ OAuth required (not public API)
   - **Purpose:** Mock implementation for future use
   - **Note:** Deferred to v2 - requires OAuth consumer key/secret + token

#### Data Processing Pipeline (4 Stages)

**File:** `backend/app/scrapers/pipeline.py`

**Stages:**
1. **RawDataValidator** - Ensures minimum quality requirements
2. **DataNormalizer** - Currency conversion, condition mapping, set number standardization
3. **DuplicateDetector** - Prevents duplicate minifigures and price listings
4. **DataPersister** - Saves validated data to database

**Currency Conversion Rates:**
```python
EXCHANGE_RATES = {
    'USD': Decimal('1.00'),
    'EUR': Decimal('1.08'),
    'GBP': Decimal('1.26'),
    'CAD': Decimal('0.74'),
    'AUD': Decimal('0.66'),
}
```

**Condition Mapping:**
```python
CONDITION_MAPPING = {
    'new': 'NEW',
    'used': 'USED',
    'sealed': 'SEALED',
    'mint': 'NEW',
    'complete': 'USED',
}
```

### 5. Celery Task Queue
**Status:** ✅ Built, ⚠️ Not yet tested

#### Configuration (`backend/app/celery_app.py`)
- Redis broker: `redis://localhost:6379/0`
- Two queues: `scraping`, `processing`
- Worker settings: prefetch=1, max_tasks_per_child=100
- Task routing by queue
- Persistent scheduler for Beat

#### Scraping Tasks (`backend/app/tasks/scraping_tasks.py`)

1. **sync_catalog_from_brickset**
   - Fetch minifigure catalog from Brickset
   - Scheduled: Daily at 2:00 AM UTC
   - Args: `theme`, `year`, `limit`
   - Processes through full pipeline

2. **fetch_prices_for_minifigure**
   - Fetch eBay prices for specific minifigure UUID
   - Args: `minifigure_id`, `condition`
   - Fetches both active and sold listings

3. **update_all_prices**
   - Batch price updates for multiple minifigures
   - Scheduled: Every 6 hours
   - Args: `batch_size` (default 50)
   - Staggers requests with 2-second delays

4. **fetch_prices_for_set_number**
   - Convenience task to fetch by set_number (e.g., "sw0001")
   - Args: `set_number`, `condition`

#### Aggregation Tasks (`backend/app/tasks/aggregation_tasks.py`)

1. **aggregate_daily_snapshots**
   - Create daily price snapshots (min/max/avg/median)
   - Scheduled: Daily at 1:00 AM UTC
   - Args: `target_date` (defaults to yesterday)
   - Updates existing or creates new snapshots

2. **aggregate_snapshot_for_minifigure**
   - Real-time snapshot for single minifigure
   - Args: `minifigure_id`, `target_date`

3. **cleanup_old_listings**
   - Delete price listings older than N days
   - Scheduled: Weekly on Sundays at 3:00 AM UTC
   - Args: `days_to_keep` (default 90)
   - Preserves snapshots

4. **backfill_snapshots**
   - Historical data processing for date ranges
   - Args: `start_date`, `end_date`

#### Helper Scripts
- `backend/scripts/start_celery_worker.sh` - Start worker with both queues
- `backend/scripts/start_celery_beat.sh` - Start Beat scheduler

#### Documentation
- `backend/CELERY.md` - Comprehensive guide (architecture, tasks, monitoring, troubleshooting)

---

## ⚠️ Known Issues

### 1. Celery Testing Blocked
**Status:** User attempted to test, encountered "still more issues"

**What Was Attempted:**
1. ✅ Docker services started (`docker-compose up -d`)
2. ✅ Redis connectivity verified (`docker exec -it minifig_redis redis-cli ping` → PONG)
3. ⚠️ Celery worker startup - **issue occurred here**

**Unknown Details:**
- What error message appeared when starting worker?
- Did worker fail to start, or did it start but task failed?
- Was there a Python import error, connection error, or task execution error?

**Next Steps for Debugging:**
1. Try starting worker and capture full error output:
   ```bash
   cd backend
   source venv/bin/activate
   celery -A app.celery_app worker -Q scraping,processing -l debug
   ```

2. Check for common issues:
   - Missing Python dependencies?
   - Database connection from Celery tasks?
   - Environment variables loaded in Celery context?
   - Import errors in task files?

### 2. eBay API Key Not Yet Obtained
**Status:** User waiting for API key approval

**Action Required:**
- Check email for eBay developer account confirmation
- Once received, add to `backend/.env`:
  ```
  EBAY_APP_ID=your_actual_app_id_here
  ```

### 3. Metadata Serialization Bug (RESOLVED)
**Previous Issue:** Pydantic validation error when fetching minifigures

**Error:**
```
pydantic_core._pydantic_core.ValidationError: 4 validation errors for MinifigureList
items.0.metadata
  Input should be a valid dictionary [type=dict_type, input_value=MetaData(), input_type=MetaData]
```

**Root Cause:** Pydantic using `alias="metadata"` accessed SQLAlchemy `Base.metadata` instead of JSONB column

**Fix Applied:** Changed `alias="metadata"` to `serialization_alias="metadata"` in `backend/app/schemas/minifigure.py:25`

**Status:** ✅ Resolved and working

---

## 📁 File Structure

```
Minifigure-Stonks/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI app entry point
│   │   ├── celery_app.py              # Celery configuration
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   ├── health.py
│   │   │       │   ├── minifigures.py
│   │   │       │   └── snapshots.py
│   │   │       └── router.py
│   │   ├── db/
│   │   │   ├── session.py             # Database session management
│   │   │   ├── SCHEMA.md              # Database schema documentation
│   │   │   └── migrations/            # Alembic migrations
│   │   ├── models/
│   │   │   ├── minifigure.py          # Minifigure ORM model
│   │   │   └── price.py               # PriceListing, PriceSnapshot, DataSource models
│   │   ├── schemas/
│   │   │   ├── minifigure.py          # Pydantic schemas for minifigures
│   │   │   └── price.py               # Pydantic schemas for prices
│   │   ├── scrapers/
│   │   │   ├── base.py                # DataSourceAdapter interface
│   │   │   ├── pipeline.py            # 4-stage data processing pipeline
│   │   │   ├── bricklink.py           # BrickLink adapter (mock)
│   │   │   ├── brickset.py            # Brickset adapter (working)
│   │   │   └── ebay.py                # eBay adapter (waiting for API key)
│   │   └── tasks/
│   │       ├── scraping_tasks.py      # Celery scraping tasks
│   │       └── aggregation_tasks.py   # Celery aggregation tasks
│   ├── scripts/
│   │   ├── start_celery_worker.sh     # Start Celery worker
│   │   └── start_celery_beat.sh       # Start Beat scheduler
│   ├── requirements.txt               # Python dependencies
│   ├── .env                           # Environment variables (gitignored)
│   ├── .env.example                   # Example environment config
│   ├── CELERY.md                      # Celery documentation
│   └── alembic.ini                    # Alembic configuration
├── frontend/
│   ├── app/
│   │   ├── layout.tsx                 # Root layout
│   │   ├── page.tsx                   # Homepage
│   │   └── minifigures/
│   │       ├── page.tsx               # Browse page
│   │       └── [id]/
│   │           └── page.tsx           # Detail page
│   ├── components/
│   │   ├── MinifigureCard.tsx
│   │   ├── SearchBar.tsx
│   │   ├── Filters.tsx
│   │   ├── Pagination.tsx
│   │   ├── PriceChart.tsx
│   │   ├── PriceStats.tsx
│   │   └── Navigation.tsx
│   ├── lib/
│   │   └── api.ts                     # API client functions
│   ├── package.json
│   └── next.config.js
├── docker-compose.yml                 # PostgreSQL + Redis services
├── .gitignore
├── CLAUDE.md                          # Claude Code instructions
└── PROJECT_STATUS.md                  # This file

```

---

## 🔑 Environment Configuration

### backend/.env (Current State)

```env
# Database
DATABASE_URL=postgresql://minifig_user:minifig_dev_password@localhost:5432/minifigure_stonks

# Redis
REDIS_URL=redis://localhost:6379/0

# API Keys
BRICKSET_API_KEY=3-ieOx-CAPX-beMAH              # ✅ WORKING

# TODO: Add eBay App ID when received
EBAY_APP_ID=YOUR_EBAY_APP_ID_HERE                # ⏳ WAITING

# BrickLink API (OAuth - not needed for MVP, skip for now)
# BRICKLINK_CONSUMER_KEY=your_consumer_key
# BRICKLINK_CONSUMER_SECRET=your_consumer_secret
# BRICKLINK_TOKEN_VALUE=your_token_value
# BRICKLINK_TOKEN_SECRET=your_token_secret

# Application
DEBUG=True
API_VERSION=v1
```

---

## 🚀 How to Run (Working Services)

### Start Database and Redis
```bash
docker-compose up -d
docker ps  # Verify minifig_db and minifig_redis are running
```

### Start Backend API
```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# Access: http://localhost:8000/v1/docs
```

### Start Frontend
```bash
cd frontend
npm run dev
# Access: http://localhost:3000
```

### Start Celery (When Issues Resolved)
```bash
# Terminal 1: Worker
cd backend
./scripts/start_celery_worker.sh

# Terminal 2: Beat (optional, for scheduled tasks)
cd backend
./scripts/start_celery_beat.sh
```

---

## 🧪 Testing Steps (When Celery Fixed)

### Test 1: Brickset Catalog Sync
```python
from app.tasks.scraping_tasks import sync_catalog_from_brickset

task = sync_catalog_from_brickset.delay(theme="Star Wars", limit=10)
print(f"Task ID: {task.id}")
print(f"Status: {task.status}")

result = task.get(timeout=120)
print(result)  # Should show: {'saved': X, 'errors': 0, 'total': X}
```

### Test 2: Verify Database
```bash
docker exec -it minifig_db psql -U minifig_user -d minifigure_stonks
```

```sql
SELECT COUNT(*) FROM minifigures;
SELECT set_number, name, theme FROM minifigures LIMIT 5;
\q
```

### Test 3: eBay Price Fetch (After API Key)
```python
from app.tasks.scraping_tasks import fetch_prices_for_set_number

task = fetch_prices_for_set_number.delay("sw0001")
result = task.get(timeout=120)
print(result)
```

### Test 4: Price Aggregation
```python
from app.tasks.aggregation_tasks import aggregate_daily_snapshots
from datetime import datetime, timedelta

yesterday = (datetime.utcnow() - timedelta(days=1)).date()
task = aggregate_daily_snapshots.delay(target_date=str(yesterday))
result = task.get(timeout=60)
print(result)
```

---

## 📝 Git Commit History (Last 5)

```
55c8107 Add Celery task queue for async scraping and data processing
77a1520 Add eBay adapter for marketplace price data
21f0114 Add Brickset adapter with free public API
823b33a Implement data collection infrastructure with scraping adapters
048d260 Add network startup scripts for local WiFi access
```

---

## 🎯 Next Steps (Priority Order)

### Immediate (Unblock Testing)
1. **Debug Celery worker startup issue**
   - Capture full error output when starting worker
   - Check Python dependencies (celery, redis packages installed?)
   - Verify database connection from Celery context
   - Test task imports manually
   - Check `.env` file is loaded in Celery worker process

2. **Get eBay API key**
   - Check email for developer account approval
   - Add to `.env` when received
   - Test eBay price fetching

### Short-term (After Testing Works)
3. **Validate data collection pipeline**
   - Fetch real minifigure data from Brickset
   - Fetch real price data from eBay
   - Verify data normalization (currency conversion, conditions)
   - Test duplicate detection
   - Confirm data appears in frontend

4. **Test scheduled tasks**
   - Run Celery Beat
   - Verify tasks execute at scheduled times
   - Monitor logs for errors

5. **Add admin API endpoints** (optional)
   - `POST /v1/admin/sync-catalog` - Trigger catalog sync
   - `POST /v1/admin/fetch-prices/{id}` - Trigger price fetch
   - `POST /v1/admin/aggregate-snapshots` - Trigger aggregation
   - Useful for manual testing and debugging

### Medium-term
6. **Improve error handling**
   - Add Sentry or error logging
   - Better retry logic for failed tasks
   - Alert on repeated failures

7. **Add monitoring**
   - Flower dashboard for Celery monitoring
   - Health check endpoints for Celery workers
   - Metrics for API performance

8. **Optimize performance**
   - Add database indexes
   - Implement API response caching
   - Optimize frontend data fetching

### Long-term
9. **Deploy to production**
   - Containerize with Docker
   - Deploy to Railway/Fly.io
   - Configure production environment variables
   - Set up CI/CD pipeline

10. **Add features**
    - User authentication
    - Watchlist functionality
    - Price alerts
    - Advanced analytics
    - BrickLink OAuth integration

---

## 🐛 Debugging Resources

### Check Service Status
```bash
# PostgreSQL
docker ps | grep minifig_db
docker exec -it minifig_db psql -U minifig_user -d minifigure_stonks -c "SELECT 1"

# Redis
docker ps | grep minifig_redis
docker exec -it minifig_redis redis-cli ping

# Backend API
curl http://localhost:8000/v1/health
curl http://localhost:8000/v1/health/db
```

### Check Logs
```bash
# Docker services
docker-compose logs -f db
docker-compose logs -f redis

# Backend API (if running in background)
# Check terminal where uvicorn is running

# Celery worker
# Check terminal where worker is running
```

### Common Issues

**Port Already in Use:**
```bash
# Find process using port 8000
lsof -ti:8000 | xargs kill -9

# Find process using port 6379 (Redis)
lsof -ti:6379 | xargs kill -9
```

**Database Connection Error:**
```bash
# Restart database
docker-compose restart db

# Check connection string in .env
cat backend/.env | grep DATABASE_URL
```

**Celery Worker Won't Start:**
```bash
# Check Redis connection
docker exec -it minifig_redis redis-cli ping

# Try with verbose logging
cd backend
celery -A app.celery_app worker -Q scraping,processing -l debug

# Check for import errors
python -c "from app.celery_app import celery_app; print('OK')"
python -c "from app.tasks import scraping_tasks; print('OK')"
```

---

## 📚 Documentation References

- **Backend API:** http://localhost:8000/v1/docs (when running)
- **Celery Guide:** `backend/CELERY.md`
- **Database Schema:** `backend/db/SCHEMA.md`
- **Claude Instructions:** `CLAUDE.md`

---

## 💡 Important Technical Notes

### SQLAlchemy Metadata Alias
**Critical Fix Applied:**
- Use `serialization_alias="metadata"` NOT `alias="metadata"` in Pydantic schemas
- This prevents Pydantic from accessing `Base.metadata` when reading from ORM
- File: `backend/app/schemas/minifigure.py:25`

### TimescaleDB Hypertable
- `price_listings` table is a TimescaleDB hypertable
- Partitioned by `timestamp` with 7-day chunks
- Optimized for time-series queries
- Run `SELECT create_hypertable('price_listings', 'timestamp');` after table creation

### Data Pipeline Flow
```
External API → Adapter → ScrapedData
                           ↓
                    RawDataValidator
                           ↓
                    DataNormalizer (USD conversion, condition mapping)
                           ↓
                    DuplicateDetector
                           ↓
                    DataPersister → Database
```

### Celery Task Routing
- `scraping_tasks.*` → `scraping` queue (lower concurrency for rate limits)
- `aggregation_tasks.*` → `processing` queue (higher concurrency ok)

---

## 🔄 Session Continuity

**When Resuming:**
1. Read this file to understand current state
2. Check `⚠️ Known Issues` section for blockers
3. Review `🎯 Next Steps` for what to work on
4. Run `git log --oneline -5` to see recent commits
5. Check `.env` file for API keys status
6. Start Docker services: `docker-compose up -d`

**Last Working State:**
- ✅ Frontend UI fully functional at http://localhost:3000
- ✅ Backend API fully functional at http://localhost:8000
- ✅ Database schema created and validated
- ⚠️ Celery infrastructure built but not yet tested
- ⏳ Waiting for eBay API key
- ❓ Unknown Celery worker startup issue needs debugging

---

**End of Status Document**
