# Minifigure-Stonks Backend API

FastAPI application for tracking LEGO minifigure prices.

## Setup

### 1. Install Dependencies

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your database credentials
```

### 3. Start Database (Docker)

```bash
# From project root
docker compose up -d
```

### 4. Run Development Server

```bash
# From backend directory
python3 -m uvicorn app.main:app --reload
```

The API will be available at:
- **API Docs**: http://localhost:8000/v1/docs
- **ReDoc**: http://localhost:8000/v1/redoc
- **OpenAPI JSON**: http://localhost:8000/v1/openapi.json

## Project Structure

```
app/
├── __init__.py           # Package init
├── main.py               # FastAPI application entry point
├── config.py             # Configuration management (Pydantic settings)
├── database.py           # Database connection & session management
├── models/               # SQLAlchemy ORM models
│   ├── __init__.py
│   ├── data_source.py    # DataSource model
│   ├── minifigure.py     # Minifigure model
│   └── price.py          # PriceListing & PriceSnapshot models
├── schemas/              # Pydantic schemas (API validation)
│   ├── __init__.py
│   ├── minifigure.py     # Minifigure request/response schemas
│   └── price.py          # Price schemas
└── api/                  # API routes
    └── v1/
        ├── __init__.py
        ├── health.py     # Health check endpoints
        └── minifigures.py # Minifigure CRUD endpoints
```

## API Endpoints

### Health Check
- `GET /v1/health` - Basic health check
- `GET /v1/health/db` - Database connectivity check
- `GET /v1/info` - API information

### Minifigures
- `GET /v1/minifigures/` - List minifigures (with pagination & filters)
- `GET /v1/minifigures/{id}` - Get minifigure by UUID
- `GET /v1/minifigures/set/{set_number}` - Get by set number (e.g., "sw0001")
- `GET /v1/minifigures/themes/list` - List all themes

## Architecture Decisions

### Separation of Concerns

**Models vs Schemas:**
- **Models** (`app/models/`): SQLAlchemy ORM - Database layer
- **Schemas** (`app/schemas/`): Pydantic - API validation layer

This separation allows:
- Different field names (e.g., API uses `camelCase`, DB uses `snake_case`)
- API evolution without database changes
- Clear validation rules for incoming requests

### Configuration Management

Using `pydantic-settings` for type-safe configuration:
- Environment variables loaded automatically
- Type validation on startup
- Single source of truth for settings
- `@lru_cache` ensures singleton pattern

### Database Session Management

FastAPI dependency injection pattern:
```python
@app.get("/items")
def get_items(db: Session = Depends(get_db)):
    return db.query(Item).all()
```

Benefits:
- Automatic session creation/cleanup
- Easy to test (mock `get_db`)
- Follows FastAPI best practices

## Testing the API

### Manual Testing

```bash
# Health check
curl http://localhost:8000/v1/health

# Database health
curl http://localhost:8000/v1/health/db

# List minifigures
curl http://localhost:8000/v1/minifigures/

# Get specific minifigure
curl http://localhost:8000/v1/minifigures/set/sw0001

# List themes
curl http://localhost:8000/v1/minifigures/themes/list
```

### Using Interactive Docs

Navigate to http://localhost:8000/v1/docs for Swagger UI where you can:
- See all endpoints
- Test requests interactively
- View request/response schemas
- Download OpenAPI spec

## Next Steps

1. ✅ FastAPI skeleton created
2. ✅ SQLAlchemy models implemented
3. ✅ Basic CRUD endpoints
4. 🔄 Add price endpoints
5. 🔄 Implement BrickLink API adapter
6. 🔄 Add authentication
7. 🔄 Write tests

## Development

### Code Formatting

```bash
# Format code
black .

# Lint code
ruff check .
```

### Running Tests

```bash
pytest
```

## Educational Notes

### Why FastAPI?
- **Type hints**: Python type annotations for auto-validation
- **Async support**: Handle concurrent requests efficiently
- **Auto-docs**: Swagger/ReDoc generated automatically
- **Fast**: Built on Starlette and Pydantic (very performant)

### SQLAlchemy ORM Benefits
- **Type safety**: IDE autocomplete for models
- **Relationships**: Automatic joins, lazy loading
- **Migration support**: Via Alembic
- **Database agnostic**: Supports PostgreSQL, MySQL, SQLite, etc.

### Pydantic Schemas
- **Validation**: Automatic type checking and coercion
- **Serialization**: Easy JSON conversion
- **Documentation**: OpenAPI schemas generated automatically
- **IDE support**: Full type hints for great DX
