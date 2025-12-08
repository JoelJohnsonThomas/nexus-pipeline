"""
Seed script to add Google Blog News source to the database.
"""
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import get_db_session, Source, SourceType, init_db
from app.database.repository import SourceRepository

def seed_google_source():
    """Add Google Blog source if it doesn't exist"""
    print("=" * 60)
    print("SEEDING GOOGLE BLOG SOURCE")
    print("=" * 60)

    RSS_URL = "https://blog.google/rss"
    NAME = "Google Blog"
    
    try:
        # Check if source exists
        existing = SourceRepository.get_source_by_url(RSS_URL)
        
        if existing:
            print(f"✅ Source already exists: {existing.name} (ID: {existing.id})")
            return
            
        print(f"Adding new source: {NAME}")
        
        with get_db_session() as session:
            source = Source(
                name=NAME,
                source_type=SourceType.BLOG, 
                url=RSS_URL,
                active=True
            )
            session.add(source)
            session.commit()
            
            print(f"✅ Successfully added source: {NAME}")
            print(f"   ID: {source.id}")
            print(f"   URL: {source.url}")

    except Exception as e:
        print(f"❌ Error seeding source: {e}")
        # Try to init db if table doesn't exist
        try:
             print("Attempting to initialize DB...")
             init_db()
             seed_google_source()
        except Exception as e2:
             print(f"❌ Error initializing DB: {e2}")

if __name__ == "__main__":
    seed_google_source()
