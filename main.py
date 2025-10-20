"""
MIRIEL Backend API
FastAPI application with MySQL database support
"""

import logging
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import engine, create_tables
from app.core.logging_config import setup_logging
from app.api.v1 import api_router

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting MIRIEL Backend API...")
    try:
        create_tables()
        logger.info("Database connection verified ✅")
    except Exception as e:
        logger.warning(f"Database connection failed: {e}")
        logger.info("Running in no-database mode for testing")
    yield
    # Shutdown
    logger.info("Shutting down MIRIEL Backend API...")


# Create FastAPI application
app = FastAPI(
    title="MIRIEL Backend API",
    description="Backend API for MIRIEL application",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to MIRIEL Backend API",
        "version": "1.0.0",
        "docs": "/docs",
        "widget_demo": "/demo.html"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "MIRIEL Backend API"}


# Mount static files for widget (must be last to not override routes)
app.mount("/", StaticFiles(directory="public", html=True), name="static")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level="info"
    )