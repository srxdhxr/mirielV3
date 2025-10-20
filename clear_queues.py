#!/usr/bin/env python3
"""
Clear all Redis queues
"""
from app.core.redis_client import redis_conn, pipeline_queue, scraper_queue, chunker_queue, vectorizer_queue

def clear_all_queues():
    """Clear all job queues"""
    print("🧹 Clearing all queues...")
    
    # Empty each queue
    pipeline_queue.empty()
    scraper_queue.empty()
    chunker_queue.empty()
    vectorizer_queue.empty()
    
    # Clear failed job registry
    from rq.registry import FailedJobRegistry
    
    for queue in [pipeline_queue, scraper_queue, chunker_queue, vectorizer_queue]:
        failed_registry = FailedJobRegistry(queue=queue)
        for job_id in failed_registry.get_job_ids():
            failed_registry.remove(job_id)
            print(f"  Removed failed job: {job_id}")
    
    print("✅ All queues cleared!")
    print(f"   Pipeline: {len(pipeline_queue)} jobs")
    print(f"   Scraper: {len(scraper_queue)} jobs")
    print(f"   Chunker: {len(chunker_queue)} jobs")
    print(f"   Vectorizer: {len(vectorizer_queue)} jobs")

if __name__ == "__main__":
    clear_all_queues()

