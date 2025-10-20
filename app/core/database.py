"""
Database configuration and setup
"""

import logging
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from .config import settings

logger = logging.getLogger(__name__)

# Database engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.DEBUG  # Log SQL queries in debug mode
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Metadata for table operations
metadata = MetaData()


def create_tables():
    """Create all database tables"""
    try:
        # Import all models so they're registered with Base.metadata
        from app.models import Tenant, TenantUser, ChatSession, ChatMessage, Widget, WidgetCustomization
        
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Error verifying database tables: {e}")
        raise


def get_db():
    """
    Dependency to get database session
    Use this as a FastAPI dependency
    """
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def check_database_connection():
    """Check if database connection is working"""
    try:
        # Try to connect to the database
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Database connection failed: {e}")
        return False