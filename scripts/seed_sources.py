"""
Seed all sources into the database.
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, Source, SourceType
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_sources():
    """Create all source records"""
    db = SessionLocal()
    try:
        logger.info("🌱 Seeding sources...")
        
        sources = [
            # YouTube channels
            {"name": "OpenAI", "source_type": SourceType.YOUTUBE, "url": "https://www.youtube.com/@OpenAI"},
            {"name": "Anthropic", "source_type": SourceType.YOUTUBE, "url": "https://www.youtube.com/@AnthropicAI"},
            {"name": "Google DeepMind", "source_type": SourceType.YOUTUBE, "url": "https://www.youtube.com/@Google"},
            {"name": "Two Minute Papers", "source_type": SourceType.YOUTUBE, "url": "https://www.youtube.com/@TwoMinutePapers"},
            {"name": "Yannic Kilcher", "source_type": SourceType.YOUTUBE, "url": "https://www.youtube.com/@YannicKilcher"},
            
            # OpenAI and Anthropic
            {"name": "OpenAI", "source_type": SourceType.OPENAI, "url": "https://openai.com/news/rss.xml"},
            {"name": "Anthropic research", "source_type": SourceType.ANTHROPIC, "url": "https://www.anthropic.com/research"},
            
            # Blogs
            {"name": "Google Blog", "source_type": SourceType.BLOG, "url": "https://blog.google/rss"},
        ]
        
        created = 0
        skipped = 0
        
        for source_data in sources:
            # Check if exists
            existing = db.query(Source).filter(
                Source.name == source_data["name"],
                Source.source_type == source_data["source_type"]
            ).first()
            
            if existing:
                logger.info(f"  ⏭️  {source_data['name']} ({source_data['source_type'].value}) - already exists")
                skipped += 1
            else:
                source = Source(**source_data)
                db.add(source)
                logger.info(f"  ✅ {source_data['name']} ({source_data['source_type'].value}) - created")
                created += 1
        
        db.commit()
        
        logger.info(f"\n✅ Seeding complete!")
        logger.info(f"   Created: {created}")
        logger.info(f"   Skipped: {skipped}")
        logger.info(f"   Total: {created + skipped}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to seed sources: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = seed_sources()
    sys.exit(0 if success else 1)
