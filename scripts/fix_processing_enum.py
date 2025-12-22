"""
Quick fix script for ProcessingStatus enum.
Adds the enum type to the database.
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


def fix_processing_status_enum():
    """Add ProcessingStatus enum to database"""
    try:
        logger.info("🔄 Fixing ProcessingStatus enum...")
        
        with engine.connect() as conn:
            # Check if enum exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_type WHERE typname = 'processingstatus'
                )
            """))
            enum_exists = result.fetchone()[0]
            
            if enum_exists:
                logger.info("✅ ProcessingStatus enum already exists")
                
                # List current values
                result = conn.execute(text("""
                    SELECT enumlabel FROM pg_enum 
                    WHERE enumtypid = 'processingstatus'::regtype
                    ORDER BY enumsortorder
                """))
                values = [row[0] for row in result]
                logger.info(f"   Current values: {values}")
                
                # Add missing values
                required_values = ['pending', 'extracting', 'summarizing', 'embedding', 'completed', 'failed']
                for value in required_values:
                    if value not in values:
                        logger.info(f"   Adding value: {value}")
                        try:
                            conn.execute(text(f"ALTER TYPE processingstatus ADD VALUE '{value}'"))
                            conn.commit()
                        except Exception as e:
                            logger.warning(f"   Could not add {value}: {e}")
            else:
                logger.info("Creating ProcessingStatus enum...")
                conn.execute(text("""
                    CREATE TYPE processingstatus AS ENUM (
                        'pending', 'extracting', 'summarizing', 'embedding', 'completed', 'failed'
                    )
                """))
                conn.commit()
                logger.info("✅ ProcessingStatus enum created")
            
            # Update the processing_queue table to use the enum
            logger.info("\n🔄 Updating processing_queue table...")
            
            # First, check if the column exists
            result = conn.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'processing_queue' AND column_name = 'status'
            """))
            column_info = result.fetchone()
            
            if column_info:
                logger.info(f"   Current status column type: {column_info[1]}")
                
                if column_info[1] != 'USER-DEFINED':
                    # Need to convert the column
                    logger.info("   Converting status column to enum type...")
                    conn.execute(text("""
                        ALTER TABLE processing_queue 
                        ALTER COLUMN status TYPE processingstatus 
                        USING status::processingstatus
                    """))
                    conn.commit()
                    logger.info("✅ Status column updated to enum type")
                else:
                    logger.info("✅ Status column already uses enum type")
            else:
                logger.warning("⚠️ Status column not found in processing_queue table")
        
        logger.info("\n✅ ProcessingStatus enum fix complete!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to fix enum: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = fix_processing_status_enum()
    sys.exit(0 if success else 1)
