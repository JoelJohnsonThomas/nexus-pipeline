"""
Interactive script to add news sources to the database.
"""
import sys
import logging

from app.database import get_db_session
from app.models import Source, SourceType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_youtube_channel():
    """Add a YouTube channel source"""
    print("\n📺 Adding YouTube Channel")
    print("-" * 40)
    
    name = input("Channel name: ").strip()
    
    print("\nYou can provide:")
    print("1. Channel ID (e.g., UC_x5XG1OV2P6uZZ5FSM9Ttw)")
    print("2. Channel URL (e.g., https://www.youtube.com/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw)")
    print("3. RSS feed URL (e.g., https://www.youtube.com/feeds/videos.xml?channel_id=...)")
    
    url = input("\nChannel ID/URL: ").strip()
    
    if not url:
        print("❌ URL cannot be empty")
        return
    
    # If it's just a channel ID, convert to RSS URL
    if url.startswith("UC") and "/" not in url:
        from app.scrapers.youtube_scraper import YouTubeScraper
        url = YouTubeScraper.get_channel_rss_url(url)
        print(f"Converted to RSS URL: {url}")
    
    try:
        with get_db_session() as session:
            source = Source(
                name=name,
                source_type=SourceType.YOUTUBE,
                url=url,
                active=True
            )
            session.add(source)
            session.commit()
            
            print(f"\n✅ YouTube channel '{name}' added successfully!")
            print(f"   Source ID: {source.id}")
    
    except Exception as e:
        logger.error(f"❌ Error adding source: {e}")


def add_blog():
    """Add a blog source"""
    print("\n📝 Adding Blog")
    print("-" * 40)
    
    name = input("Blog name: ").strip()
    
    print("\nYou can provide:")
    print("1. Blog post URL (for single article)")
    print("2. RSS feed URL (e.g., https://blog.example.com/feed)")
    
    url = input("\nBlog URL: ").strip()
    
    if not url:
        print("❌ URL cannot be empty")
        return
    
    try:
        with get_db_session() as session:
            source = Source(
                name=name,
                source_type=SourceType.BLOG,
                url=url,
                active=True
            )
            session.add(source)
            session.commit()
            
            print(f"\n✅ Blog '{name}' added successfully!")
            print(f"   Source ID: {source.id}")
    
    except Exception as e:
        logger.error(f"❌ Error adding source: {e}")


def list_sources():
    """List all sources"""
    print("\n📋 Current Sources")
    print("=" * 60)
    
    with get_db_session() as session:
        sources = session.query(Source).all()
        
        if not sources:
            print("No sources found. Add some sources first!")
            return
        
        for source in sources:
            status = "✅ Active" if source.active else "❌ Inactive"
            print(f"\nID: {source.id}")
            print(f"Name: {source.name}")
            print(f"Type: {source.source_type.value}")
            print(f"URL: {source.url}")
            print(f"Status: {status}")
            print("-" * 60)


def toggle_source_status():
    """Toggle source active status"""
    list_sources()
    
    try:
        source_id = int(input("\nEnter source ID to toggle: "))
        
        with get_db_session() as session:
            source = session.query(Source).filter(Source.id == source_id).first()
            
            if not source:
                print(f"❌ Source with ID {source_id} not found")
                return
            
            source.active = not source.active
            session.commit()
            
            status = "activated" if source.active else "deactivated"
            print(f"\n✅ Source '{source.name}' {status}")
    
    except ValueError:
        print("❌ Invalid source ID")
    except Exception as e:
        logger.error(f"❌ Error toggling source: {e}")


def main():
    """Main menu"""
    while True:
        print("\n" + "=" * 60)
        print("AI NEWS AGGREGATOR - SOURCE MANAGEMENT")
        print("=" * 60)
        print("\n1. Add YouTube channel")
        print("2. Add blog")
        print("3. List all sources")
        print("4. Toggle source active/inactive")
        print("5. Exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == '1':
            add_youtube_channel()
        elif choice == '2':
            add_blog()
        elif choice == '3':
            list_sources()
        elif choice == '4':
            toggle_source_status()
        elif choice == '5':
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid option")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
