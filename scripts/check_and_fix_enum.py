"""
Check current enum values and fix if needed.
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

def check_and_fix_enum():
    """Check current enum values and fix"""
    try:
        with engine.connect() as conn:
            # Check current enum values
            logger.info("Checking current enum values...")
            result = conn.execute(text("""
                SELECT enumlabel FROM pg_enum 
                WHERE enumtypid = 'processingstatus'::regtype
                ORDER BY enumsortorder
            """))
            values = [row[0] for row in result]
            logger.info(f"Current values: {values}")
            
            if values and values[0].isupper():
                logger.info("❌ Enum has UPPERCASE values - fixing...")
                
                # Drop CASCADE to remove all dependencies
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
                
                # Add column back
                conn.execute(text("""
                    ALTER TABLE processing_queue 
                    ADD COLUMN status processingstatus NOT NULL DEFAULT 'pending'
                """))
                
                # Create index
                conn.execute(text("CREATE INDEX idx_processing_queue_status ON processing_queue(status)"))
                conn.commit()
                
                logger.info("✅ Fixed! Enum now has lowercase values")
            else:
                logger.info("✅ Enum already has lowercase values")
            
            # Verify final state
            result = conn.execute(text("""
                SELECT enumlabel FROM pg_enum 
                WHERE enumtypid = 'processingstatus'::regtype
                ORDER BY enumsortorder
            """))
            final_values = [row[0] for row in result]
            logger.info(f"✅ Final enum values: {final_values}")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = check_and_fix_enum()
    sys.exit(0 if success else 1)
