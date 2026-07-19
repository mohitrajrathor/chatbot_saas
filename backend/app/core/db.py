import logging
from typing import Generator
from sqlmodel import create_engine, Session
from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_sync_url(url: str) -> str:
    """Convert async database URL to a sync-compatible database URL."""
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    elif url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg2://")
    return url


def _create_sync_engine(url: str):
    """
    Attempt to create a sync engine.
    If the primary sync driver fails, try fallback drivers.
    """
    sync_url = _get_sync_url(url)
    try:
        return create_engine(sync_url, echo=settings.DEBUG, pool_pre_ping=True)
    except Exception as e:
        logger.warning(f"Failed to create engine with psycopg2 driver ({e}). Attempting fallback driver...")
        fallback_url = sync_url.replace("+psycopg2://", "+psycopg://")
        return create_engine(fallback_url, echo=settings.DEBUG, pool_pre_ping=True)


engine = _create_sync_engine(settings.DATABASE_URL)


def get_db_session() -> Generator[Session, None, None]:
    """
    Initialize a synchronous database session with error handling and rollback.
    """
    session = Session(engine)
    try:
        yield session
    except Exception as exc:
        logger.error(f"Database session error occurred: {exc}")
        session.rollback()
        raise
    finally:
        session.close()


