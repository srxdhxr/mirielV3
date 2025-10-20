"""
Pydantic schemas for task queue messages
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class PipelineTriggerRequest(BaseModel):
    """Request to trigger scraping pipeline"""
    base_url: str = Field(..., description="Base URL to scrape")


class PipelineTriggerResponse(BaseModel):
    """Response from pipeline trigger"""
    job_id: str
    tenant_id: int
    user_id: int
    base_url: str
    status: str = "pipeline_triggered"
    created_at: str
    message: str = "Pipeline triggered successfully"


class PipelineTask(BaseModel):
    """Task for pipeline queue"""
    tenant_id: int
    user_id: int
    base_url: str
    created_at: str
    status: str = "pipeline_created"


class ScraperTask(BaseModel):
    """Task for scraper queue"""
    url: str
    tenant_id: int
    user_id: int
    pipeline_job_id: str  # Track which pipeline this belongs to


class ChunkerTask(BaseModel):
    """Task for chunker queue"""
    file_path: str
    tenant_id: int
    user_id: int
    url: str  # Original URL
    pipeline_job_id: str  # Track which pipeline this belongs to

