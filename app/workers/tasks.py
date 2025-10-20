"""
Worker tasks for the scraping pipeline

These functions are executed by RQ workers
"""
import logging
from datetime import datetime

from app.core.redis_client import scraper_queue, chunker_queue, vectorizer_queue
from app.services.pipeline import SiteMapParser, Scraper, Chunker, Vectorizer

logger = logging.getLogger(__name__)


def process_pipeline(tenant_id: int, user_id: int, base_url: str, pipeline_job_id: str = None):
    """
    Worker task: Process pipeline - parse sitemap and enqueue scraping tasks
    
    Args:
        tenant_id: Tenant ID
        user_id: User ID who triggered the pipeline
        base_url: Base URL to scrape
        pipeline_job_id: Job ID for tracking (optional, will use current job ID if not provided)
    """
    # Get current job ID from RQ context if not provided
    if not pipeline_job_id:
        from rq import get_current_job
        try:
            current_job = get_current_job()
            pipeline_job_id = current_job.id if current_job else 'unknown'
        except:
            pipeline_job_id = 'unknown'
    
    logger.info(f"🚀 [Pipeline] Starting for tenant {tenant_id}, base_url: {base_url}")
    logger.info(f"   Pipeline Job ID: {pipeline_job_id}")
    
    try:
        # Step 1: Parse sitemap to get URLs
        parser = SiteMapParser(base_url)
        urls = parser.get_urls()
        
        if not urls:
            logger.error(f"❌ [Pipeline] No URLs found in sitemap for {base_url}")
            return {
                "status": "failed",
                "error": "No URLs found in sitemap",
                "tenant_id": tenant_id,
                "base_url": base_url
            }
        
        logger.info(f"✅ [Pipeline] Found {len(urls)} URLs from sitemap")
        
        # Step 2: Enqueue each URL to scraper queue
        enqueued_jobs = []
        for url in urls:
            job = scraper_queue.enqueue(
                'app.workers.tasks.process_scraper',
                url=url,
                tenant_id=tenant_id,
                user_id=user_id,
                pipeline_job_id=pipeline_job_id,
                job_timeout='10m'  # 10 minute timeout per scrape
            )
            enqueued_jobs.append(job.id)
            logger.info(f"📋 [Pipeline] Enqueued scraper job {job.id} for {url}")
        
        logger.info(f"✅ [Pipeline] Enqueued {len(enqueued_jobs)} scraping tasks")
        
        return {
            "status": "success",
            "urls_found": len(urls),
            "jobs_enqueued": len(enqueued_jobs),
            "job_ids": enqueued_jobs,
            "tenant_id": tenant_id,
            "base_url": base_url
        }
        
    except Exception as e:
        logger.error(f"❌ [Pipeline] Error processing pipeline: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "tenant_id": tenant_id,
            "base_url": base_url
        }


def process_scraper(url: str, tenant_id: int, user_id: int, pipeline_job_id: str = None):
    """
    Worker task: Scrape a single URL and enqueue to chunker
    
    Args:
        url: URL to scrape
        tenant_id: Tenant ID
        user_id: User ID
        pipeline_job_id: Original pipeline job ID for tracking
    """
    logger.info(f"🕷️  [Scraper] Starting for URL: {url}")
    logger.info(f"   Pipeline Job ID: {pipeline_job_id}")
    
    try:
        # Step 1: Scrape the URL
        scraper = Scraper(tenant_id=tenant_id, output_dir="scraped_data")
        file_path = scraper.scrape(url)
        
        if not file_path:
            logger.error(f"❌ [Scraper] Failed to scrape {url}")
            return {
                "status": "failed",
                "url": url,
                "error": "Scraping returned no result"
            }
        
        logger.info(f"✅ [Scraper] Successfully scraped to: {file_path}")
        
        # Step 2: Enqueue to chunker queue
        job = chunker_queue.enqueue(
            'app.workers.tasks.process_chunker',
            file_path=file_path,
            tenant_id=tenant_id,
            user_id=user_id,
            url=url,
            pipeline_job_id=pipeline_job_id,
            job_timeout='5m'  # 5 minute timeout per chunk
        )
        
        logger.info(f"📋 [Scraper] Enqueued chunker job {job.id} for {file_path}")
        
        return {
            "status": "success",
            "url": url,
            "file_path": file_path,
            "chunker_job_id": job.id
        }
        
    except Exception as e:
        logger.error(f"❌ [Scraper] Error scraping {url}: {e}")
        return {
            "status": "failed",
            "url": url,
            "error": str(e)
        }


def process_chunker(file_path: str, tenant_id: int, user_id: int, url: str, pipeline_job_id: str = None):
    """
    Worker task: Process scraped content into chunks
    
    Args:
        file_path: Path to scraped JSON file
        tenant_id: Tenant ID
        user_id: User ID
        url: Original URL
        pipeline_job_id: Original pipeline job ID for tracking
    """
    logger.info(f"✂️  [Chunker] Starting for file: {file_path}")
    logger.info(f"   URL: {url}")
    logger.info(f"   Pipeline Job ID: {pipeline_job_id}")
    
    try:
        # Step 1: Chunk the scraped content
        chunker = Chunker(tenant_id=tenant_id, user_id=user_id)
        chunked_file_path = chunker.chunk(file_path=file_path, url=url)
        
        if not chunked_file_path:
            logger.error(f"❌ [Chunker] Chunking returned no result for {file_path}")
            return {
                "status": "failed",
                "file_path": file_path,
                "url": url,
                "error": "Chunking returned no result"
            }
        
        logger.info(f"✅ [Chunker] Successfully chunked to: {chunked_file_path}")
        
        # Step 2: Enqueue to vectorizer queue
        job = vectorizer_queue.enqueue(
            'app.workers.tasks.process_vectorizer',
            file_path=chunked_file_path,
            tenant_id=tenant_id,
            user_id=user_id,
            url=url,
            pipeline_job_id=pipeline_job_id,
            job_timeout='10m'  # 10 minute timeout per vectorization
        )
        
        logger.info(f"📋 [Chunker] Enqueued vectorizer job {job.id} for {chunked_file_path}")
        
        return {
            "status": "success",
            "file_path": file_path,
            "chunked_file_path": chunked_file_path,
            "url": url,
            "vectorizer_job_id": job.id
        }
        
    except Exception as e:
        logger.error(f"❌ [Chunker] Error processing {file_path}: {e}")
        return {
            "status": "failed",
            "file_path": file_path,
            "error": str(e)
        }


def process_vectorizer(file_path: str, tenant_id: int, user_id: int, url: str, pipeline_job_id: str = None):
    """
    Worker task: Process chunked content for vectorization
    
    Args:
        file_path: Path to chunked JSON file
        tenant_id: Tenant ID
        user_id: User ID
        url: Original URL
        pipeline_job_id: Original pipeline job ID for tracking
    """
    logger.info(f"🔢 [Vectorizer] Starting for file: {file_path}")
    logger.info(f"   URL: {url}")
    logger.info(f"   Pipeline Job ID: {pipeline_job_id}")
    
    try:
        # Step 1: Vectorize the chunked content
        vectorizer = Vectorizer(tenant_id=tenant_id, user_id=user_id)
        result = vectorizer.vectorize(chunked_file_path=file_path, url=url)
        
        if not result:
            logger.error(f"❌ [Vectorizer] Vectorization returned no result for {file_path}")
            return {
                "status": "failed",
                "file_path": file_path,
                "url": url,
                "error": "Vectorization returned no result"
            }
        
        logger.info(f"✅ [Vectorizer] Successfully vectorized {result['chunks_vectorized']} chunks")
        logger.info(f"   Collection: {result['collection']}")
        
        return {
            "status": "success",
            "file_path": file_path,
            "url": url,
            "chunks_vectorized": result['chunks_vectorized'],
            "collection": result['collection']
        }
        
    except Exception as e:
        logger.error(f"❌ [Vectorizer] Error processing {file_path}: {e}")
        return {
            "status": "failed",
            "file_path": file_path,
            "error": str(e)
        }

