"""
Complete database reset and fix for processing_queue table.
This will drop and recreate the processing_queue table properly.
"""
import sys
import os
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def complete_fix():
    """Complete fix for database issues"""
    try:
        logger.info("🔄 Starting complete database fix...")
        
        with engine.connect() as conn:
            # 1. Drop the broken processing_queue table
            logger.info("Dropping processing_queue table...")
            conn.execute(text("DROP TABLE IF EXISTS processing_queue CASCADE"))
            conn.commit()
            
            # 2. Drop and recreate the enum with lowercase values
            logger.info("Recreating processingstatus enum...")
            conn.execute(text("DROP TYPE IF EXISTS processingstatus CASCADE"))
            conn.execute(text("""
                CREATE TYPE processingstatus AS ENUM (
                    'pending', 
                    'extracting', 
                    'summarizing', 
                    'embedding', 
                    'completed', 
                    'failed'
                )
            """))
            conn.commit()
            
            # 3. Recreate processing_queue table
            logger.info("Creating processing_queue table...")
            conn.execute(text("""
                CREATE TABLE processing_queue (
                    id SERIAL PRIMARY KEY,
                    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
                    status processingstatus NOT NULL DEFAULT 'pending',
                    current_stage VARCHAR(50),
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    error_message TEXT,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # 4. Create indexes
            logger.info("Creating indexes...")
            conn.execute(text("CREATE INDEX idx_processing_queue_article_id ON processing_queue(article_id)"))
            conn.execute(text("CREATE INDEX idx_processing_queue_status ON processing_queue(status)"))
            conn.commit()
            
            logger.info("✅ Processing queue table recreated!")
            
            # 5. Verify
            result = conn.execute(text("""
                SELECT column_name, data_type, column_default
                FROM information_schema.columns 
                WHERE table_name = 'processing_queue'
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            logger.info(f"\n✅ Table columns verified:")
            for col in columns:
                logger.info(f"   - {col[0]}: {col[1]} (default: {col[2]})")
        
        logger.info("\n🎉 Complete fix successful!")
        logger.info("\nNext steps:")
        logger.info("1. Enqueue articles: python -c \"from app.queue import get_message_queue; mq = get_message_queue(); mq.enqueue_summarization(1); mq.enqueue_summarization(2); print('Done!')\"")
        logger.info("2. Watch worker process them automatically!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to fix: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = complete_fix()
    sys.exit(0 if success else 1)
