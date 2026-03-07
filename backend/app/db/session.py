import logging
import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text  # type: ignore - Add text import here
from sqlalchemy.exc import SQLAlchemyError  # type: ignore
from sqlalchemy.orm import Session, sessionmaker  # type: ignore

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./test.db")

# Create engine with enhanced configuration
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL.lower() else {},
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for database sessions with automatic transaction handling"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """Dependency for FastAPI with enhanced error handling"""
    session = SessionLocal()
    try:
        yield session
    except Exception as e:
        session.rollback()
        logger.error(f"Database dependency error: {e}")
        raise
    finally:
        session.close()


def safe_commit(session: Session) -> bool:
    """Safely commit session with error handling"""
    try:
        session.commit()
        return True
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database commit failed: {e}")
        return False
    except Exception as e:
        session.rollback()
        logger.error(f"Unexpected database error: {e}")
        return False


def safe_rollback(session: Session) -> bool:
    """Safely rollback session"""
    try:
        session.rollback()
        return True
    except Exception as e:
        logger.error(f"Database rollback failed: {e}")
        return False


def test_database_connection() -> bool:
    """Test database connection health"""
    try:
        with engine.connect() as conn:
            # Fix: Use text() for raw SQL strings (import moved to top)
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


def get_database_status() -> dict:
    """Get database status for monitoring"""
    try:
        is_healthy = test_database_connection()
        pool_info = engine.pool.status()

        # Fix: Handle pool status properly - it returns a string, not a dict
        if isinstance(pool_info, str):
            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "pool_size": 0,
                "checked_in": 0,
                "checked_out": 0,
                "overflow": 0,
                "invalid": 0,
                "pool_info": pool_info,
            }
        else:
            # If it's actually a dict, use it
            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "pool_size": pool_info.get("pool_size", 0),
                "checked_in": pool_info.get("checkedin", 0),
                "checked_out": pool_info.get("checkedout", 0),
                "overflow": pool_info.get("overflow", 0),
                "invalid": pool_info.get("invalid", 0),
            }
    except Exception as e:
        return {"status": "error", "error": str(e)}
