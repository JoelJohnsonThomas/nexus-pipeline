"""
Article processing pipeline orchestrator.
Coordinates the flow of articles through extraction, summarization, and embedding.
"""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session

from app.database import SessionLocal, Article
from app.queue import get_message_queue
from app.cache import get_redis_client

logger = logging.getLogger(__name__)


class ArticlePipeline:
    """Orchestrates article processing through the pipeline"""
    
    def __init__(self):
        self.message_queue = get_message_queue()
        self.cache = get_redis_client()
    
    def process_article(self, article_id: int) -> bool:
        """
        Start processing an article through the full pipeline.
        
        This enqueues the article for extraction, which then automatically
        chains to summarization and embedding through the worker functions.
        
        Args:
            article_id: ID of article to process
        
        Returns:
            True if successfully enqueued
        """
        try:
            # Enqueue for extraction (first stage)
            job_id = self.message_queue.enqueue_extraction(article_id)
            
            if job_id:
                logger.info(f"Article {article_id} enqueued for processing (job: {job_id})")
                return True
            else:
                logger.error(f"Failed to enqueue article {article_id}")
                return False
        
        except Exception as e:
            logger.error(f"Error enqueueing article {article_id}: {e}")
            return False
    
    def process_articles_batch(self, article_ids: List[int]) -> dict:
        """
        Process multiple articles in batch.
        
        Args:
            article_ids: List of article IDs to process
        
        Returns:
            Dict with 'enqueued' and 'failed' counts
        """
        results = {'enqueued': 0, 'failed': 0}
        
        for article_id in article_ids:
            if self.process_article(article_id):
                results['enqueued'] += 1
            else:
                results['failed'] += 1
        
        logger.info(f"Batch processing: {results['enqueued']} enqueued, {results['failed']} failed")
        return results
    
    def process_new_articles(self, hours_back: int = 24) -> dict:
        """
        Process all articles from the last N hours that haven't been processed yet.
        
        Args:
            hours_back: How many hours back to look for new articles
        
        Returns:
            Dict with processing statistics
        """
        from datetime import datetime, timedelta
        
        db = SessionLocal()
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
            
            # Find articles that need processing
            articles = db.query(Article).filter(
                Article.scraped_at >= cutoff_time,
                Article.processing_status.in_(['pending', 'failed'])
            ).all()
            
            article_ids = [a.id for a in articles]
            logger.info(f"Found {len(article_ids)} articles to process from last {hours_back} hours")
            
            if not article_ids:
                return {'enqueued': 0, 'failed': 0, 'found': 0}
            
            results = self.process_articles_batch(article_ids)
            results['found'] = len(article_ids)
            
            return results
        
        finally:
            db.close()
    
    def get_pipeline_status(self) -> dict:
        """Get current status of the processing pipeline"""
        try:
            # Get queue stats
            queue_stats = self.message_queue.get_queue_stats()
            
            # Get processing stats from database
            db = SessionLocal()
            try:
                from app.database import ProcessingQueue
                from sqlalchemy import func
                
                status_counts = db.query(
                    ProcessingQueue.status,
                    func.count(ProcessingQueue.id)
                ).group_by(ProcessingQueue.status).all()
                
                processing_stats = {status: count for status, count in status_counts}
            finally:
                db.close()
            
            return {
                'queues': queue_stats,
                'processing_stats': processing_stats
            }
        
        except Exception as e:
            logger.error(f"Error getting pipeline status: {e}")
            return {}
    
    def clear_failed_jobs(self, queue_name: str = None):
        """Clear failed jobs from queue(s)"""
        self.message_queue.clear_failed_jobs(queue_name)
    
    def retry_failed_articles(self, max_retries: int = 3) -> dict:
        """
        Retry articles that failed processing (up to max_retries attempts).
        
        Args:
            max_retries: Maximum number of retry attempts
        
        Returns:
            Dict with retry statistics
        """
        db = SessionLocal()
        try:
            from app.database import ProcessingQueue, ProcessingStatus
            
            # Find failed articles with retries remaining
            failed_entries = db.query(ProcessingQueue).filter(
                ProcessingQueue.status == ProcessingStatus.FAILED.value,
                ProcessingQueue.retry_count < max_retries
            ).all()
            
            logger.info(f"Found {len(failed_entries)} failed articles to retry")
            
            article_ids = [entry.article_id for entry in failed_entries]
            
            if not article_ids:
                return {'retried': 0, 'found': 0}
            
            results = self.process_articles_batch(article_ids)
            results['found'] = len(article_ids)
            
            return results
        
        finally:
            db.close()
