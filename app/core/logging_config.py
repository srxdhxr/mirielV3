"""
Logging configuration for the application
"""

import logging
import logging.config
import os
from datetime import datetime
from .config import settings


def setup_logging():
    """Setup application logging configuration"""
    
    # Ensure logs directory exists
    os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)
    
    # Logging configuration
    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "detailed",
                "filename": settings.LOG_FILE,
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8",
            },
        },
        "loggers": {
            "": {  # Root logger
                "level": settings.LOG_LEVEL,
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "uvicorn": {
                "level": "WARNING",  # Suppress startup messages
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "uvicorn.error": {
                "level": "WARNING",  # Suppress startup messages
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",  # Show HTTP request logs
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "level": "ERROR",  # Only show SQL errors
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "sqlalchemy.engine.Engine": {
                "level": "ERROR",  # Suppress SQL query logs
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "watchfiles.main": {
                "level": "ERROR",  # Suppress file change detection logs
                "handlers": ["console", "file"],
                "propagate": False,
            },
        },
    }
    
    # Apply logging configuration
    logging.config.dictConfig(LOGGING_CONFIG)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {settings.LOG_LEVEL}, File: {settings.LOG_FILE}")