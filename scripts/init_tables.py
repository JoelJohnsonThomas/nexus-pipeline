"""
Initialize all database tables from scratch.
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import Base, engine, init_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_all_tables():
    """Create all tables defined in models"""
    try:
        logger.info("🔄 Creating all database tables...")
        
        # Import all models to ensure they're registered
        from app.database import (
            Source, Article, OpenAIArticle, AnthropicArticle, YouTubeVideo,
            ArticleSummary, ArticleEmbedding, EmailSubscription, 
            EmailDelivery, ProcessingQueue
        )
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ All tables created successfully!")
        
        # Verify tables exist
        from sqlalchemy import text, inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        logger.info(f"\n📋 Created tables ({len(tables)}):")
        for table in sorted(tables):
            logger.info(f"   ✓ {table}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_all_tables()
    sys.exit(0 if success else 1)
