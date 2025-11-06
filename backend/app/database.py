"""
Database Connection & Session Management

Handles SQLAlchemy engine creation, session management, and connection pooling.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.config import get_settings

settings = get_settings()

# Create SQLAlchemy engine
# echo=True in development shows SQL queries (helpful for learning)
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=5,  # Number of connections to keep open
    max_overflow=10,  # Additional connections when pool is full
)

# Session factory
# autocommit=False: Explicit commits required (safer)
# autoflush=False: Manual flushing for better control
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base class for SQLAlchemy models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session.

    Usage in route:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()

    The session is automatically closed after the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
