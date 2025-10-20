#!/usr/bin/env python3
"""
RQ Worker Script

Start workers to process tasks from Redis queues

Usage:
    # Process all queues
    python worker.py

    # Process specific queue
    python worker.py pipeline
    python worker.py scraper
    python worker.py chunker
    python worker.py vectorizer
"""
import os
import sys
import logging
from rq import Worker, SimpleWorker

# Fix macOS fork safety issue
os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'

from app.core.redis_client import redis_conn, pipeline_queue, scraper_queue, chunker_queue, vectorizer_queue
from app.core.logging_config import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


def main():
    """Start RQ worker"""
    
    # Determine which queues to listen to
    if len(sys.argv) > 1:
        queue_name = sys.argv[1]
        
        if queue_name == 'pipeline':
            queues = [pipeline_queue]
        elif queue_name == 'scraper':
            queues = [scraper_queue]
        elif queue_name == 'chunker':
            queues = [chunker_queue]
        elif queue_name == 'vectorizer':
            queues = [vectorizer_queue]
        else:
            logger.error(f"Unknown queue: {queue_name}")
            logger.info("Available queues: pipeline, scraper, chunker, vectorizer")
            sys.exit(1)
    else:
        # Listen to all queues (in priority order)
        queues = [pipeline_queue, scraper_queue, chunker_queue, vectorizer_queue]
    
    queue_names = [q.name for q in queues]
    logger.info(f"🚀 Starting worker for queues: {', '.join(queue_names)}")
    
    # Use SimpleWorker to avoid macOS fork issues
    # SimpleWorker runs jobs in the same process (no forking)
    worker = SimpleWorker(queues, connection=redis_conn)
    
    logger.info("👂 Worker listening for jobs... (SimpleWorker, no-fork mode)")
    worker.work(with_scheduler=True)


if __name__ == '__main__':
    main()

