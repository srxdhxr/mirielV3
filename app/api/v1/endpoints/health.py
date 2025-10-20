"""
Health check endpoints
"""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db, check_database_connection

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check"""
    logger.info("Health check requested")
    return {
        "status": "healthy",
        "service": "MIRIEL Backend API",
        "version": "1.0.0"
    }