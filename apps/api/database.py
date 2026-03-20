"""
Database setup and session management.

Falls back to SQLite when PostgreSQL is not available (e.g. Render free tier).
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config import get_settings
import logging

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


settings = get_settings()

# Determine database URL: use SQLite fallback if DATABASE_URL points to
# unavailable PostgreSQL or is the unchanged default localhost value.
_db_url = settings.database_url
_use_sqlite = False

if "localhost" in _db_url and "RENDER" in __import__("os").environ:
    # Running on Render without a real DATABASE_URL — use SQLite
    _db_url = "sqlite+aiosqlite:///./agentreadiness.db"
    _use_sqlite = True

# Engine kwargs differ between PostgreSQL and SQLite
_engine_kwargs = dict(echo=settings.debug)
if not _use_sqlite:
    _engine_kwargs.update(pool_pre_ping=True, pool_size=10, max_overflow=20)

engine = create_async_engine(_db_url, **_engine_kwargs)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Alias for use in background tasks that need their own session
async_session_factory = async_session


async def get_db() -> AsyncSession:
    """Dependency that provides a database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """Create all tables and add any missing columns."""
    if _use_sqlite:
        logger.info("Using SQLite fallback database")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Add columns that may be missing from older table versions.
    # SQLAlchemy create_all only creates new tables, not new columns.
    _migration_columns = [
        ("assessments", "full_name", "VARCHAR(255)"),
        ("assessments", "role", "VARCHAR(100)"),
        ("assessments", "optimization_status", "VARCHAR(50)"),
        ("assessments", "optimization_progress", "FLOAT DEFAULT 0"),
        ("assessments", "optimization_stage", "VARCHAR(255)"),
        ("assessments", "optimization_metadata", "TEXT"),
        ("assessments", "optimization_error", "TEXT"),
        ("assessments", "optimization_zip_path", "VARCHAR(500)"),
    ]
    async with engine.begin() as conn:
        for table, column, col_type in _migration_columns:
            try:
                await conn.execute(
                    __import__("sqlalchemy").text(
                        f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {col_type}"
                    )
                )
            except Exception as e:
                # Column may already exist, or DB doesn't support IF NOT EXISTS
                logger.debug(f"Migration skip {table}.{column}: {e}")


async def close_db():
    """Close the engine."""
    await engine.dispose()
