# Minifigure-Stonks

Platform for tracking up-to-date pricing and availability of Lego Minifigures across multiple data sources.

## Project Status

🚧 **In Development** - Phase 1: Foundation

Currently implementing:
- Backend API with FastAPI
- PostgreSQL + TimescaleDB for time-series price data
- BrickLink API integration

## Technology Stack

**Backend:**
- Python 3.11+ with FastAPI
- PostgreSQL + TimescaleDB
- SQLAlchemy ORM
- Celery + Redis for task queue

**Frontend** (Coming Soon):
- Next.js 14+ with TypeScript
- Recharts for data visualization

## Quick Start

### Prerequisites

**Choose one:**

**Option 1: Docker** (Recommended - easier setup)
- Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) for Mac
- Includes Docker Engine + Docker Compose

**Option 2: Local Services** (No Docker)
- Python 3.11+
- PostgreSQL 14+ with TimescaleDB extension
- Redis

### Option 1: Docker Development (Recommended)

#### First-time setup:
1. Install Docker Desktop: https://www.docker.com/products/docker-desktop/
2. Start Docker Desktop app
3. Verify installation:
   ```bash
   docker --version
   docker compose version
   ```

#### Daily usage:
```bash
# Start all services (PostgreSQL + TimescaleDB + Redis)
# New Docker: use "docker compose" (space, not hyphen)
docker compose up -d
# OR for older Docker: docker-compose up -d
# OR use Makefile: make up

# Verify services are running
docker compose ps

# View logs
docker compose logs -f

# Stop services
docker compose down

# Stop and remove all data
docker compose down -v
```

The database will be available at `localhost:5432` and Redis at `localhost:6379`.

**Database Credentials:**
- User: `minifig_user`
- Password: `minifig_dev_password`
- Database: `minifigure_stonks`

### Option 2: Local Development (Without Docker)

```bash
# Install PostgreSQL + TimescaleDB + Redis
brew install postgresql@14 redis timescaledb
brew services start postgresql@14
brew services start redis

# Setup backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Create database
createdb minifigure_stonks
psql -d minifigure_stonks -c "CREATE EXTENSION timescaledb;"

# Run development server (once FastAPI app is created)
uvicorn app.main:app --reload
```

## Project Structure

```
backend/
  app/                    # Application code (coming soon)
  db/
    init/                 # Database initialization scripts
      01-enable-timescaledb.sql
  Dockerfile              # Backend container definition
  requirements.txt        # Python dependencies
  .env.example           # Environment template
docker-compose.yml        # Multi-service orchestration
frontend/                 # Next.js frontend (coming soon)
CLAUDE.md                 # AI assistant guidance
```

## Data Sources

- **BrickLink**: Primary marketplace API (official API)
- **eBay**: Auction data (planned)
- **LEGO.com**: Official retail pricing (planned)
- **Brickset**: Catalog data (planned)

## Features

### Current
- None yet - building foundation

### Planned
- Price tracking with historical charts
- Market analytics and trends
- Price alerts
- Collection management
