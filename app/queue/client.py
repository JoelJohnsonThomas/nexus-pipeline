"""
Message queue client using Redis Queue (RQ).
Manages article processing pipeline through queue system.
"""
import os
from redis import Redis
from rq import Queue
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class MessageQueue:
    """
    Message queue for article processing pipeline.
    Uses Redis Queue (RQ) for job management.
    """
    
    def __init__(self, redis_host: str = None, redis_port: int = None):
        """
        Initialize message queue client.
        
        Args:
            redis_host: Redis host (default: from env or 'localhost')
            redis_port: Redis port (default: from env or 6379)
        """
        self.redis_host = redis_host or os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = int(redis_port or os.getenv('REDIS_PORT', 6379))
        
        try:
            # Connect to Redis
            self.redis_conn = Redis(
                host=self.redis_host,
                port=self.redis_port,
                socket_connect_timeout=5
            )
            
            # Create queues for different pipeline stages
            self.extraction_queue = Queue('extraction', connection=self.redis_conn)
            self.summarization_queue = Queue('summarization', connection=self.redis_conn)
            self.embedding_queue = Queue('embedding', connection=self.redis_conn)
            self.email_queue = Queue('email', connection=self.redis_conn)
            
            logger.info(f"Message queue initialized at {self.redis_host}:{self.redis_port}")
        except Exception as e:
            logger.error(f"Failed to initialize message queue: {e}")
            raise
    
    def enqueue_extraction(self, article_id: int, **kwargs) -> Optional[str]:
        """
        Enqueue article for content extraction.
        
        Args:
            article_id: ID of article to extract
            **kwargs: Additional job parameters
        
        Returns:
            Job ID if successful, None otherwise
        """
        try:
            from app.orchestrator.workers import extract_content
            
            job = self.extraction_queue.enqueue(
                extract_content,
                article_id,
                job_timeout='5m',
                **kwargs
            )
            logger.info(f"Enqueued article {article_id} for extraction (job: {job.id})")
            return job.id
        except Exception as e:
            logger.error(f"Error enqueueing extraction for article {article_id}: {e}")
            return None
    
    def enqueue_summarization(self, article_id: int, model: str = None, **kwargs) -> Optional[str]:
        """
        Enqueue article for LLM summarization.
        
        Args:
            article_id: ID of article to summarize
            model: LLM model to use (default: from env)
            **kwargs: Additional job parameters
        
        Returns:
            Job ID if successful, None otherwise
        """
        try:
            from app.orchestrator.workers import generate_summary
            
            job = self.summarization_queue.enqueue(
                generate_summary,
                article_id,
                model=model,
                job_timeout='10m',
                **kwargs
            )
            logger.info(f"Enqueued article {article_id} for summarization (job: {job.id})")
            return job.id
        except Exception as e:
            logger.error(f"Error enqueueing summarization for article {article_id}: {e}")
            return None
    
    def enqueue_embedding(self, article_id: int, **kwargs) -> Optional[str]:
        """
        Enqueue article for embedding generation.
        
        Args:
            article_id: ID of article to embed
            **kwargs: Additional job parameters
        
        Returns:
            Job ID if successful, None otherwise
        """
        try:
            from app.orchestrator.workers import generate_embedding
            
            job = self.embedding_queue.enqueue(
                generate_embedding,
                article_id,
                job_timeout='5m',
                **kwargs
            )
            logger.info(f"Enqueued article {article_id} for embedding (job: {job.id})")
            return job.id
        except Exception as e:
            logger.error(f"Error enqueueing embedding for article {article_id}: {e}")
            return None
    
    def enqueue_email_digest(self, subscription_id: int, **kwargs) -> Optional[str]:
        """
        Enqueue email digest for sending.
        
        Args:
            subscription_id: ID of subscription to send digest for
            **kwargs: Additional job parameters
        
        Returns:
            Job ID if successful, None otherwise
        """
        try:
            from app.orchestrator.workers import send_email_digest
            
            job = self.email_queue.enqueue(
                send_email_digest,
                subscription_id,
                job_timeout='5m',
                **kwargs
            )
            logger.info(f"Enqueued email digest for subscription {subscription_id} (job: {job.id})")
            return job.id
        except Exception as e:
            logger.error(f"Error enqueueing email digest: {e}")
            return None
    
    def get_queue_stats(self) -> dict:
        """Get statistics for all queues"""
        try:
            return {
                'extraction': {
                    'count': len(self.extraction_queue),
                    'failed': self.extraction_queue.failed_job_registry.count
                },
                'summarization': {
                    'count': len(self.summarization_queue),
                    'failed': self.summarization_queue.failed_job_registry.count
                },
                'embedding': {
                    'count': len(self.embedding_queue),
                    'failed': self.embedding_queue.failed_job_registry.count
                },
                'email': {
                    'count': len(self.email_queue),
                    'failed': self.email_queue.failed_job_registry.count
                }
            }
        except Exception as e:
            logger.error(f"Error getting queue stats: {e}")
            return {}
    
    def clear_failed_jobs(self, queue_name: str = None):
        """Clear failed jobs from queue(s)"""
        queues = [self.extraction_queue, self.summarization_queue, self.embedding_queue, self.email_queue]
        queue_names = ['extraction', 'summarization', 'embedding', 'email']
        
        if queue_name:
            queue_map = dict(zip(queue_names, queues))
            if queue_name in queue_map:
                queue_map[queue_name].failed_job_registry.empty()
                logger.info(f"Cleared failed jobs from {queue_name} queue")
        else:
            for queue in queues:
                queue.failed_job_registry.empty()
            logger.info("Cleared all failed jobs")


# Global message queue instance
_message_queue = None


def get_message_queue() -> MessageQueue:
    """Get global message queue instance (singleton pattern)"""
    global _message_queue
    if _message_queue is None:
        _message_queue = MessageQueue()
    return _message_queue
