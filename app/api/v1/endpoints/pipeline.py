"""
Pipeline trigger endpoint
"""
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.core.database import get_db
from app.models.tenant_user import TenantUser
from app.models.tenant import Tenant
from app.schemas.tasks import PipelineTriggerResponse
from app.core.redis_client import pipeline_queue

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/trigger", response_model=PipelineTriggerResponse, status_code=202)
def trigger_pipeline(
    current_user: TenantUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trigger scraping pipeline for the authenticated user's tenant
    
    This endpoint:
    1. Gets the authenticated user from JWT token
    2. Retrieves tenant's website_url from database
    3. Enqueues a pipeline task to Redis
    4. Returns job tracking information
    
    The pipeline will:
    - Parse sitemap to get all URLs
    - Scrape each URL
    - Chunk the content
    - (Future: vectorize and index)
    
    Status: 202 Accepted (task queued, processing asynchronously)
    """
    logger.info(f"🚀 Pipeline trigger requested by user {current_user.id} (tenant {current_user.tenant_id})")
    
    try:
        # Get tenant from database
        tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
        
        if not tenant:
            logger.error(f"❌ Tenant {current_user.tenant_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        # Check if tenant has a website URL
        if not tenant.website_url:
            logger.error(f"❌ Tenant {current_user.tenant_id} has no website_url")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant does not have a website URL configured"
            )
        
        base_url = tenant.website_url
        logger.info(f"   Base URL: {base_url}")
        
        # Prepare task data
        created_at = datetime.utcnow().isoformat()
        
        # Enqueue to pipeline queue
        job = pipeline_queue.enqueue(
            'app.workers.tasks.process_pipeline',
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            base_url=base_url,
            pipeline_job_id='',  
            job_timeout='30m' 
        )
        
        logger.info(f"✅ Pipeline job enqueued: {job.id}")
        
        return PipelineTriggerResponse(
            job_id=job.id,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            base_url=base_url,
            status="pipeline_triggered",
            created_at=created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error triggering pipeline: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger pipeline: {str(e)}"
        )


@router.get("/status/{job_id}")
def get_job_status(
    job_id: str,
    current_user: TenantUser = Depends(get_current_user)
):
    """
    Get the status of a pipeline job
    
    Returns:
        Job status, position in queue, and result if completed
    """
    from rq.job import Job
    from app.core.redis_client import redis_conn
    
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        
        return {
            "job_id": job.id,
            "status": job.get_status(),
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "ended_at": job.ended_at.isoformat() if job.ended_at else None,
            "result": job.result,
            "exc_info": job.exc_info if job.is_failed else None
        }
        
    except Exception as e:
        logger.error(f"Error fetching job status: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}"
        )

