from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from typing import AsyncGenerator
import os

# Database URL from environment variables
DATABASE_URL = (
    f"postgresql+asyncpg://{os.getenv('POSTGRES_USER', 'eve_user')}:"
    f"{os.getenv('POSTGRES_PASSWORD', 'eve_password')}@"
    f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
    f"{os.getenv('POSTGRES_PORT', '5432')}/"
    f"{os.getenv('POSTGRES_DB', 'eve_sde')}"
)

# Create async engine with connection pooling
engine = create_async_engine(
    DATABASE_URL,
    echo=True if os.getenv("ENVIRONMENT") == "development" else False,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,   # Recycle connections after 1 hour
)

# Async session factory
async_session_maker = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions.
    
    Usage:
        @app.get("/items/")
        async def read_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initialize database tables (if needed).
    Note: SDE tables are created by Fuzzwork dump, not by SQLModel.
    """
    async with engine.begin() as conn:
        # SQLModel.metadata.create_all would go here for app-specific tables
        # For SDE tables, we rely on the Fuzzwork dump
        pass


async def close_db():
    """
    Close database connections gracefully on shutdown.
    """
    await engine.dispose()
