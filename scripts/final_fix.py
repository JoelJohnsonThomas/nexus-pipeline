"""
Final comprehensive fix for enum and Gemini model issues.
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def final_fix():
    """Fix enum case and verify Gemini model"""
    try:
        logger.info("🔧 Running final comprehensive fix...")
        
        with engine.connect() as conn:
            # 1. Check current enum
            logger.info("\n1️⃣ Checking ProcessingStatus enum...")
            result = conn.execute(text("""
                SELECT enumlabel FROM pg_enum 
                WHERE enumtypid = 'processingstatus'::regtype
                ORDER BY enumsortorder
            """))
            current_values = [row[0] for row in result]
            logger.info(f"   Current values: {current_values}")
            
            # 2. Drop and recreate with lowercase values
            logger.info("\n2️⃣ Fixing enum to lowercase...")
            
            # Drop the status column first
            conn.execute(text("ALTER TABLE processing_queue DROP COLUMN IF EXISTS status CASCADE"))
            conn.commit()
            
            # Drop and recreate enum
            conn.execute(text("DROP TYPE IF EXISTS processingstatus CASCADE"))
            conn.execute(text("""
                CREATE TYPE processingstatus AS ENUM (
                    'pending', 'extracting', 'summarizing', 
                    'embedding', 'completed', 'failed'
                )
            """))
            conn.commit()
            
            # Add column back with enum
            conn.execute(text("""
                ALTER TABLE processing_queue 
                ADD COLUMN status processingstatus NOT NULL DEFAULT 'pending'
            """))
            conn.execute(text("CREATE INDEX idx_processing_queue_status ON processing_queue(status)"))
            conn.commit()
            
            # Verify
            result = conn.execute(text("""
                SELECT enumlabel FROM pg_enum 
                WHERE enumtypid = 'processingstatus'::regtype
                ORDER BY enumsortorder
            """))
            final_values = [row[0] for row in result]
            logger.info(f"   ✅ Fixed! New values: {final_values}")
        
        logger.info("\n3️⃣ Gemini Model Fix:")
        logger.info("   Update your .env file:")
        logger.info("   GEMINI_MODEL=gemini-1.5-flash-latest")
        logger.info("   (or try: gemini-1.5-flash)")
        
        logger.info("\n✅ Database fix complete!")
        logger.info("\nNext steps:")
        logger.info("1. Update .env: GEMINI_MODEL=gemini-1.5-flash-latest")
        logger.info("2. Restart worker: Ctrl+C then 'python scripts/run_workers.py'")
        logger.info("3. Scrape again: 'python run_scrapers_with_pipeline.py --hours 24'")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = final_fix()
    sys.exit(0 if success else 1)
