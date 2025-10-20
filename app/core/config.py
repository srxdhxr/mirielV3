"""
Application configuration settings
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""
    
    # Database settings (Railway provides DATABASE_URL, local uses individual settings)
    DATABASE_URL: Optional[str] = Field(default=None, description="Full database URL (for Railway)")
    DB_HOST: str = Field(default="localhost", description="Database host")
    DB_PORT: int = Field(default=3306, description="Database port")
    DB_NAME: str = Field(default="miriel_db", description="Database name")
    DB_USER: str = Field(default="root", description="Database user")
    DB_PASSWORD: str = Field(default="your_password_here", description="Database password")
    
    # Application settings
    DEBUG: bool = Field(default=False, description="Debug mode")
    HOST: str = Field(default="0.0.0.0", description="Application host")
    PORT: int = Field(default=8000, description="Application port")
    SECRET_KEY: str = Field(
        default="miriel-super-secret-key-change-in-production-2024", 
        description="Secret key for JWT tokens and encryption"
    )
    
    # JWT settings
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=120, description="Access token expiry in minutes")
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30, description="Refresh token expiry in days")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    
    # CORS settings
    ALLOWED_HOSTS: List[str] = Field(
        default=[
            "http://localhost:3000", 
            "http://127.0.0.1:3000",
            "http://localhost:8080",  # Widget demo server
            "http://127.0.0.1:8080"   # Widget demo server (alternative)
        ], 
        description="Allowed CORS origins"
    )
    
    # Logging settings
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FILE: str = Field(default="logs/app.log", description="Log file path")
    
    # AI API settings
    MISTRAL_API: str = Field(default="", description="Mistral AI API key")
    
    # Redis settincgs
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis URL for Celery")
    
    @property
    def database_url(self) -> str:
        """Get database URL for SQLAlchemy"""
        # Railway provides DATABASE_URL, use it if available
        if self.DATABASE_URL:
            # Railway uses mysql:// but we need mysql+pymysql://
            return self.DATABASE_URL.replace("mysql://", "mysql+pymysql://")
        
        # Local development - construct from individual settings
        from urllib.parse import quote_plus
        encoded_password = quote_plus(self.DB_PASSWORD)
        return f"mysql+pymysql://{self.DB_USER}:{encoded_password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()