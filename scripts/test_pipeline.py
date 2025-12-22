"""
Pipeline test script.
Tests the end-to-end pipeline from extraction to embedding.
"""
import sys
import os
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from app.database import SessionLocal, Article
from app.orchestrator.pipeline import ArticlePipeline
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_pipeline():
    """Test the processing pipeline with existing articles"""
    logger.info("=" * 60)
    logger.info("PIPELINE TEST")
    logger.info("=" * 60)
    
    # Create pipeline
    pipeline = ArticlePipeline()
    
    # Get pipeline status
    logger.info("\n📊 Current Pipeline Status:")
    status = pipeline.get_pipeline_status()
    
    if status.get('queues'):
        logger.info("\nQueue Status:")
        for queue_name, stats in status['queues'].items():
            logger.info(f"  {queue_name:15} - {stats['count']} jobs pending, {stats['failed']} failed")
    
    if status.get('processing_stats'):
        logger.info("\nProcessing Status:")
        for status_name, count in status['processing_stats'].items():
            logger.info(f"  {status_name:15} - {count} articles")
    
    # Get a few recent articles
    logger.info("\n🔍 Finding articles to process...")
    db = SessionLocal()
    try:
        articles = db.query(Article).filter(
            Article.processing_status.in_(['pending', 'failed'])
        ).limit(5).all()
        
        if not articles:
            logger.warning("No articles found to process!")
            logger.info("\nTip: Run the scrapers first to get some articles:")
            logger.info("  python run_scrapers.py --hours 168")
            return
        
        logger.info(f"Found {len(articles)} articles to process")
        
        # Process articles
        logger.info("\n🚀 Starting pipeline processing...")
        for article in articles:
            logger.info(f"\n  Processing: {article.title[:60]}...")
            pipeline.process_article(article.id)
        
        logger.info("\n✅ Articles enqueued for processing!")
        logger.info("\nTo process them, start workers in a separate terminal:")
        logger.info("  python scripts/run_workers.py")
        
        logger.info("\nOr run in burst mode (processes and exits):")
        logger.info("  python scripts/run_workers.py --burst")
        
        logger.info("\nMonitor progress:")
        logger.info("  python scripts/test_pipeline.py")
        
    finally:
        db.close()


if __name__ == "__main__":
    test_pipeline()
