"""
Add Anthropic sources directly using SQL to avoid enum issues
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import engine
from sqlalchemy import text

def add_anthropic_sources_sql():
    """Add Anthropic sources using raw SQL"""
    print("=" * 60)
    print("Adding Anthropic sources")
    print("=" * 60)
    
    with engine.connect() as conn:
        sources = [
            ('Anthropic Research', 'https://www.anthropic.com/research'),
            ('Anthropic Engineering', 'https://www.anthropic.com/engineering'),
            ('Anthropic News', 'https://www.anthropic.com/news')
        ]
        
        for name, url in sources:
            # Check if exists
            result = conn.execute(text("""
                SELECT id FROM sources WHERE url = :url
            """), {"url": url})
            
            if result.fetchone():
                print(f"⏭️  Exists: {name}")
            else:
                # Insert new source
                conn.execute(text("""
                    INSERT INTO sources (name, url, source_type, active, created_at)
                    VALUES (:name, :url, 'ANTHROPIC'::sourcetype, true, NOW())
                """), {"name": name, "url": url})
                conn.commit()
                print(f"✅ Added: {name}")
    
    print("\n" + "=" * 60)
    print("✅ Done!")
    print("=" * 60)

if __name__ == "__main__":
    add_anthropic_sources_sql()
