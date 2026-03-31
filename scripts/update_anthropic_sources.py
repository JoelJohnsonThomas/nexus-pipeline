"""
Update Anthropic sources to use correct RSS feed URLs
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import engine
from sqlalchemy import text

def update_anthropic_sources():
    """Update Anthropic source URLs to match scraper expectations"""
    print("=" * 60)
    print("Updating Anthropic sources to RSS feed URLs")
    print("=" * 60)
    
    with engine.connect() as conn:
        url_mappings = [
            {
                "old": "https://www.anthropic.com/research",
                "new": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_research.xml",
                "name": "Anthropic Research"
            },
            {
                "old": "https://www.anthropic.com/engineering",
                "new": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_engineering.xml",
                "name": "Anthropic Engineering"
            },
            {
                "old": "https://www.anthropic.com/news",
                "new": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml",
                "name": "Anthropic News"
            }
        ]
        
        for mapping in url_mappings:
            result = conn.execute(text("""
                UPDATE sources 
                SET url = :new_url
                WHERE url = :old_url
            """), {"new_url": mapping["new"], "old_url": mapping["old"]})
            conn.commit()
            
            if result.rowcount > 0:
                print(f"✅ Updated: {mapping['name']}")
            else:
                print(f"⏭️  Not found: {mapping['name']}")
    
    print("\n" + "=" * 60)
    print("✅ Done!")
    print("=" * 60)

if __name__ == "__main__":
    update_anthropic_sources()
