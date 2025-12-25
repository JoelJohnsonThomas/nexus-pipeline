"""
Database performance optimization - add indexes for common queries.
Run this script to add indexes to improve query performance.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_performance_indexes():
    """Add indexes to improve query performance"""
    
    indexes = [
        # Articles table indexes
        ("idx_articles_published_at", "CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles(published_at DESC)"),
        ("idx_articles_source_id", "CREATE INDEX IF NOT EXISTS idx_articles_source_id ON articles(source_id)"),
        ("idx_articles_scraped_at", "CREATE INDEX IF NOT EXISTS idx_articles_scraped_at ON articles(scraped_at DESC)"),
        
        # Article summaries indexes
        ("idx_summaries_article_id", "CREATE INDEX IF NOT EXISTS idx_summaries_article_id ON article_summaries(article_id)"),
        ("idx_summaries_created_at", "CREATE INDEX IF NOT EXISTS idx_summaries_created_at ON article_summaries(created_at DESC)"),
        
        # Article embeddings indexes
        ("idx_embeddings_article_id", "CREATE INDEX IF NOT EXISTS idx_embeddings_article_id ON article_embeddings(article_id)"),
        
        # Processing queue indexes
        ("idx_queue_article_id", "CREATE INDEX IF NOT EXISTS idx_queue_article_id ON processing_queue(article_id)"),
        ("idx_queue_status", "CREATE INDEX IF NOT EXISTS idx_queue_status ON processing_queue(status)"),
        
        # Email subscriptions indexes
        ("idx_subscriptions_email", "CREATE INDEX IF NOT EXISTS idx_subscriptions_email ON email_subscriptions(email)"),
        ("idx_subscriptions_active", "CREATE INDEX IF NOT EXISTS idx_subscriptions_active ON email_subscriptions(active)"),
        
        # Sources indexes (already has some, but add composite)
        ("idx_sources_type_active", "CREATE INDEX IF NOT EXISTS idx_sources_type_active ON sources(source_type, active)"),
    ]
    
    logger.info("🔧 Adding performance indexes...")
    
    with engine.connect() as conn:
        created = 0
        skipped = 0
        
        for name, sql in indexes:
            try:
                conn.execute(text(sql))
                conn.commit()
                logger.info(f"  ✅ {name}")
                created += 1
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.info(f"  ⏭️  {name} - already exists")
                    skipped += 1
                else:
                    logger.error(f"  ❌ {name} - {e}")
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("📊 INDEX CREATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total indexes: {len(indexes)}")
    logger.info(f"✅ Created: {created}")
    logger.info(f"⏭️  Skipped: {skipped}")
    logger.info("=" * 60)
    logger.info("")
    logger.info("✅ Database optimization complete!")
    logger.info("")
    logger.info("Performance improvements:")
    logger.info("- Faster article queries by publish date")
    logger.info("- Faster digest generation (recent articles)")
    logger.info("- Faster summary/embedding lookups")
    logger.info("- Faster subscription queries")


if __name__ == "__main__":
    add_performance_indexes()
