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
- Python 3.11+
- PostgreSQL 14+
- Redis (for task queue)

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy environment template and configure
cp .env.example .env
# Edit .env with your database and API credentials

# Run development server
uvicorn app.main:app --reload
```

## Project Structure

```
backend/          # FastAPI backend
  app/            # Application code
  requirements.txt
frontend/         # Next.js frontend (coming soon)
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
