"""
Minifigure-Stonks FastAPI Application

Main application entry point with route registration and middleware.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.config import get_settings
from app.api.v1 import health, minifigures, prices

settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="API for tracking LEGO minifigure prices across multiple sources",
    version=settings.app_version,
    docs_url=f"/{settings.api_version}/docs",
    redoc_url=f"/{settings.api_version}/redoc",
    openapi_url=f"/{settings.api_version}/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root redirect to docs
@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to API documentation."""
    return RedirectResponse(url=f"/{settings.api_version}/docs")


# Include routers
app.include_router(
    health.router,
    prefix=f"/{settings.api_version}",
    tags=["Health"],
)

app.include_router(
    minifigures.router,
    prefix=f"/{settings.api_version}/minifigures",
    tags=["Minifigures"],
)

app.include_router(
    prices.router,
    prefix=f"/{settings.api_version}",
    tags=["Prices"],
)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    print(f"🚀 {settings.app_name} v{settings.app_version} starting...")
    print(f"📍 API docs: http://localhost:8000/{settings.api_version}/docs")
    print(f"🗄️  Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'configured'}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    print(f"👋 {settings.app_name} shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
