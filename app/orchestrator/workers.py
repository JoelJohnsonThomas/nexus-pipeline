"""
Worker functions for RQ (Redis Queue) processing.
These are the actual jobs that get executed by RQ workers.
"""
import sys
import os
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.database import SessionLocal, Article, ArticleSummary, ArticleEmbedding, ProcessingQueue, ProcessingStatus
from app.processing.content_extractor import ContentExtractor
from app.processing.llm_summarizer import LLMSummarizer
from app.processing.embeddings import EmbeddingGenerator
from app.cache import get_redis_client

logger = logging.getLogger(__name__)


def get_db() -> Session:
    """Get database session"""
    return SessionLocal()


def update_processing_status(article_id: int, status: str, stage: str = None, error: str = None):
    """Update processing queue status for an article"""
    db = get_db()
    try:
        queue_entry = db.query(ProcessingQueue).filter(ProcessingQueue.article_id == article_id).first()
        
        if not queue_entry:
            # Create new entry
            queue_entry = ProcessingQueue(
                article_id=article_id,
                status=status,
                current_stage=stage
            )
            db.add(queue_entry)
        else:
            # Update existing
            queue_entry.status = status
            if stage:
                queue_entry.current_stage = stage
            if error:
                queue_entry.error_message = error
                queue_entry.retry_count += 1
        
        db.commit()
    except Exception as e:
        logger.error(f"Failed to update processing status: {e}")
        db.rollback()
    finally:
        db.close()


def extract_content(article_id: int) -> bool:
    """
    Extract full content from an article.
    This is a worker function executed by RQ.
    
    Args:
        article_id: ID of article to process
    
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Starting content extraction for article {article_id}")
    update_processing_status(article_id, ProcessingStatus.EXTRACTING.value, "extraction")
    
    db = get_db()
    try:
        # Get article
        article = db.query(Article).filter(Article.id == article_id).first()
        if not article:
            logger.error(f"Article {article_id} not found")
            update_processing_status(article_id, ProcessingStatus.FAILED.value, error="Article not found")
            return False
        
        # Skip if already has full content
        if article.full_content and len(article.full_content) > 100:
            logger.info(f"Article {article_id} already has full content")
            update_processing_status(article_id, ProcessingStatus.PENDING.value, "summarization")
            # Enqueue summarization
            from app.queue import get_message_queue
            get_message_queue().enqueue_summarization(article_id)
            return True
        
        # Extract content based on source type
        extractor = ContentExtractor()
        result = None
        
        if article.video_id:
            # YouTube video - extract transcript
            logger.info(f"Extracting YouTube transcript for {article.video_id}")
            result = extractor.extract_video_transcript(article.video_id)
            method = 'youtube_transcript'
        else:
            # Web article - extract content
            logger.info(f"Extracting article content from {article.url}")
            result = extractor.extract_article_content(article.url)
            method = result.get('method', 'unknown') if result else 'failed'
        
        if result and result.get('content'):
            # Update article with extracted content
            article.full_content = result['content']
            article.extraction_method = method
            # FIX: Use enum value instead of hardcoded string 'extracted'
            article.processing_status = ProcessingStatus.EXTRACTING.value 
            db.commit()
            
            logger.info(f"✅ Content extracted for article {article_id} ({len(result['content'])} chars)")
            
            # Enqueue for summarization
            from app.queue import get_message_queue
            get_message_queue().enqueue_summarization(article_id)
            update_processing_status(article_id, ProcessingStatus.PENDING.value, "summarization")
            
            return True
        else:
            logger.error(f"Failed to extract content for article {article_id}")
            update_processing_status(article_id, ProcessingStatus.FAILED.value, error="Content extraction failed")
            return False
    
    except Exception as e:
        logger.error(f"Error extracting content for article {article_id}: {e}")
        update_processing_status(article_id, ProcessingStatus.FAILED.value, error=str(e))
        db.rollback()
        return False
    finally:
        db.close()


def generate_summary(article_id: int, model: str = None) -> bool:
    """
    Generate LLM summary for an article.
    This is a worker function executed by RQ.
    
    Args:
        article_id: ID of article to summarize
        model: LLM model to use (optional)
    
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Starting summarization for article {article_id}")
    update_processing_status(article_id, ProcessingStatus.SUMMARIZING.value, "summarization")
    
    db = get_db()
    try:
        # Get article
        article = db.query(Article).filter(Article.id == article_id).first()
        if not article:
            logger.error(f"Article {article_id} not found")
            update_processing_status(article_id, ProcessingStatus.FAILED.value, error="Article not found")
            return False
        
        # Check if already summarized
        existing_summary = db.query(ArticleSummary).filter(
            ArticleSummary.article_id == article_id
        ).first()
        
        if existing_summary:
            logger.info(f"Article {article_id} already has summary")
            update_processing_status(article_id, ProcessingStatus.PENDING.value, "embedding")
            # Enqueue embedding generation
            from app.queue import get_message_queue
            get_message_queue().enqueue_embedding(article_id)
            return True
        
        # Get content to summarize
        content = article.full_content or article.content
        if not content or len(content) < 50:
            logger.warning(f"Article {article_id} has insufficient content for summarization")
            update_processing_status(article_id, ProcessingStatus.FAILED.value, error="Insufficient content")
            return False
        
        # Generate summary
        summarizer = LLMSummarizer(provider='gemini', model=model)
        result = summarizer.summarize(content, article.title)
        
        if result:
            # Save summary to database
            summary = ArticleSummary(
                article_id=article_id,
                model=result['model'],
                summary=result['summary'],
                key_points=result.get('key_points', [])
            )
            db.add(summary)
            
            # FIX: Use enum value instead of hardcoded string 'summarized'
            article.processing_status = ProcessingStatus.SUMMARIZING.value
            db.commit()
            
            logger.info(f"✅ Summary generated for article {article_id}")
            
            # Enqueue for embedding generation
            from app.queue import get_message_queue
            get_message_queue().enqueue_embedding(article_id)
            update_processing_status(article_id, ProcessingStatus.PENDING.value, "embedding")
            
            return True
        else:
            logger.error(f"Failed to generate summary for article {article_id}")
            update_processing_status(article_id, ProcessingStatus.FAILED.value, error="Summarization failed")
            return False
    
    except Exception as e:
        logger.error(f"Error generating summary for article {article_id}: {e}")
        update_processing_status(article_id, ProcessingStatus.FAILED.value, error=str(e))
        db.rollback()
        return False
    finally:
        db.close()


def generate_embedding(article_id: int) -> bool:
    """
    Generate vector embedding for an article.
    This is a worker function executed by RQ.
    
    Args:
        article_id: ID of article to embed
    
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Starting embedding generation for article {article_id}")
    update_processing_status(article_id, ProcessingStatus.EMBEDDING.value, "embedding")
    
    db = get_db()
    try:
        # Get article and summary
        article = db.query(Article).filter(Article.id == article_id).first()
        if not article:
            logger.error(f"Article {article_id} not found")
            update_processing_status(article_id, ProcessingStatus.FAILED.value, error="Article not found")
            return False
        
        # Check if already has embedding
        existing_embedding = db.query(ArticleEmbedding).filter(
            ArticleEmbedding.article_id == article_id
        ).first()
        
        if existing_embedding:
            logger.info(f"Article {article_id} already has embedding")
            update_processing_status(article_id, ProcessingStatus.COMPLETED.value)
            return True
        
        # Get summary to embed (prefer summary over full content)
        summary_obj = db.query(ArticleSummary).filter(
            ArticleSummary.article_id == article_id
        ).first()
        
        text_to_embed = summary_obj.summary if summary_obj else (article.full_content or article.content)
        
        if not text_to_embed or len(text_to_embed) < 10:
            logger.warning(f"Article {article_id} has insufficient text for embedding")
            update_processing_status(article_id, ProcessingStatus.FAILED.value, error="Insufficient text")
            return False
        
        # Generate embedding
        generator = EmbeddingGenerator()
        embedding_vector = generator.generate_embedding(text_to_embed)
        
        if embedding_vector:
            # Save to database
            embedding = ArticleEmbedding(
                article_id=article_id,
                embedding=embedding_vector,
                model=generator.model_name
            )
            db.add(embedding)
            
            # FIX: Use enum value instead of hardcoded string 'completed'
            article.processing_status = ProcessingStatus.COMPLETED.value
            db.commit()
            
            logger.info(f"✅ Embedding generated for article {article_id}")
            update_processing_status(article_id, ProcessingStatus.COMPLETED.value)
            
            # Invalidate cache
            cache = get_redis_client()
            cache.delete('articles:latest', 'articles:all')
            
            return True
        else:
            logger.error(f"Failed to generate embedding for article {article_id}")
            update_processing_status(article_id, ProcessingStatus.FAILED.value, error="Embedding generation failed")
            return False
    
    except Exception as e:
        logger.error(f"Error generating embedding for article {article_id}: {e}")
        update_processing_status(article_id, ProcessingStatus.FAILED.value, error=str(e))
        db.rollback()
        return False
    finally:
        db.close()


def send_email_digest(subscription_id: int) -> bool:
    """
    Send email digest for a subscription.
    This is a worker function executed by RQ.
    
    Args:
        subscription_id: ID of subscription to send digest for
    
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Starting email digest for subscription {subscription_id}")
    
    # This will be implemented when we build the email system in Phase 4
    # For now, just log
    logger.warning("Email digest not implemented yet (Phase 4)")
    return True