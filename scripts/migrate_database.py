"""
Database migration script.
Applies migrations and creates new tables for the pipeline.
"""
import sys
import os
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import Base, engine, SessionLocal
from app.database.models import Source, Article
from app.database.models_extended import (
    ArticleSummary, ArticleEmbedding, EmailSubscription,
    EmailDelivery, ProcessingQueue
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_pgvector_available():
    """Check if pgvector extension is available"""
    try:
        with engine.connect() as conn:
            # Try to create the extension
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
            logger.info("✅ pgvector extension is available and enabled")
            return True
    except Exception as e:
        logger.warning(f"⚠️ pgvector extension not available: {e}")
        logger.warning("⚠️ Vector embeddings will NOT work without pgvector!")
        logger.warning("⚠️ To fix: Restart Docker with 'docker-compose down && docker-compose up -d'")
        return False


def add_processing_columns():
    """Add processing columns to articles table"""
    try:
        with engine.connect() as conn:
            # Check if columns already exist
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='articles' AND column_name='processing_status'
            """))
            
            if result.fetchone():
                logger.info("✅ Processing columns already exist")
                return True
            
            # Add columns
            logger.info("Adding processing columns to articles table...")
            conn.execute(text("""
                ALTER TABLE articles 
                ADD COLUMN IF NOT EXISTS processing_status VARCHAR(20) DEFAULT 'pending' NOT NULL,
                ADD COLUMN IF NOT EXISTS full_content TEXT,
                ADD COLUMN IF NOT EXISTS extraction_method VARCHAR(50)
            """))
            conn.commit()
            
            # Create index
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_articles_processing_status 
                ON articles(processing_status)
            """))
            conn.commit()
            
            logger.info("✅ Processing columns added successfully")
            return True
    except Exception as e:
        logger.error(f"❌ Failed to add processing columns: {e}")
        return False


def run_migration():
    """Run database migration"""
    try:
        logger.info("🔄 Starting database migration...")
        logger.info("=" * 60)
        
        # Step 1: Check and enable pgvector (non-fatal if fails)
        logger.info("\n📦 Step 1: Checking pgvector extension...")
        pgvector_available = check_pgvector_available()
        
        # Step 2: Add new columns to existing tables
        logger.info("\n📝 Step 2: Adding processing columns to articles table...")
        if not add_processing_columns():
            logger.error("❌ Failed to add processing columns")
            return False
        
        # Step 3: Create all new tables
        logger.info("\n🗄️  Step 3: Creating new tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ All tables created/verified")
        
        # Step 4: Verify tables exist
        logger.info("\n🔍 Step 4: Verifying database schema...")
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        logger.info(f"\n📊 Database tables ({len(tables)} total):")
        for table in sorted(tables):
            logger.info(f"  ✓ {table}")
        
        # Check for new tables
        new_tables = ['article_summaries', 'article_embeddings', 'email_subscriptions', 
                     'email_deliveries', 'processing_queue']
        
        missing = [t for t in new_tables if t not in tables]
        if missing:
            logger.warning(f"⚠️ Missing tables: {missing}")
            return False
        else:
            logger.info("\n✅ All new tables created successfully!")
        
        # Final summary
        logger.info("\n" + "=" * 60)
        logger.info("MIGRATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"✅ Processing columns: Added")
        logger.info(f"✅ New tables: {len(new_tables)} created")
        if pgvector_available:
            logger.info(f"✅ pgvector: Enabled and ready")
        else:
            logger.info(f"⚠️  pgvector: NOT AVAILABLE - Vector search disabled")
            logger.info(f"   Fix: Run 'docker-compose down && docker-compose up -d'")
        logger.info("=" * 60)
        
        logger.info("\n✅ Migration completed successfully!")
        if not pgvector_available:
            logger.warning("\n⚠️  IMPORTANT: Restart Docker to enable vector search!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
