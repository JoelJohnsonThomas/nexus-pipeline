"""
Fix enum case sensitivity issue.
Recreates the processingstatus enum with lowercase values.
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


def fix_enum_case():
    """Fix ProcessingStatus enum to use lowercase values"""
    try:
        logger.info("🔄 Fixing ProcessingStatus enum case...")
        
        with engine.connect() as conn:
            # Drop the existing enum type (CASCADE removes dependencies)
            logger.info("Dropping existing enum...")
            conn.execute(text("DROP TYPE IF EXISTS processingstatus CASCADE"))
            conn.commit()
            
            # Create new enum with lowercase values
            logger.info("Creating enum with lowercase values...")
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
            
            logger.info("✅ Enum created with lowercase values")
        
        # Recreate the processing_queue table using SQLAlchemy models
        logger.info("Recreating processing_queue table...")
        from app.database import Base
        Base.metadata.create_all(bind=engine, tables=[Base.metadata.tables.get('processing_queue')])
        
        logger.info("✅ Processing queue table recreated")
        
        # Verify
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT enumlabel FROM pg_enum 
                WHERE enumtypid = 'processingstatus'::regtype
                ORDER BY enumsortorder
            """))
            values = [row[0] for row in result]
            logger.info(f"✅ Enum values: {values}")
            
            # Check table exists
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'processing_queue'
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            logger.info(f"✅ Table columns: {[c[0] for c in columns]}")
        
        logger.info("✅ Enum case fixed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to fix enum: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = fix_enum_case()
    sys.exit(0 if success else 1)
