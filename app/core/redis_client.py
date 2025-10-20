"""
Redis connection and queue management
"""
import logging
from redis import Redis
from rq import Queue

from app.core.config import settings

logger = logging.getLogger(__name__)

# Redis connection (decode_responses must be False for RQ)
redis_conn = Redis.from_url(settings.REDIS_URL, decode_responses=False)

# Define queues
pipeline_queue = Queue('pipeline', connection=redis_conn)
scraper_queue = Queue('scraper', connection=redis_conn)
chunker_queue = Queue('chunker', connection=redis_conn)
vectorizer_queue = Queue('vectorizer', connection=redis_conn)

logger.info("Redis queues initialized")

