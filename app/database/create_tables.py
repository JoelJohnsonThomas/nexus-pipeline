#!/usr/bin/env python3
"""
Database initialization script.
Creates all tables and optionally adds default sources.
"""
import sys
import json
import logging
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import init_db, get_db_session
from app.database.models import Source, SourceType
from app.database.repository import SourceRepository

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_youtube_channels():
    """Load YouTube channels from config file"""
    config_file = Path(__file__).parent / "config" / "youtube_channels.json"
    try:
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('channels', [])
    except Exception as e:
        logger.error(f"Error loading YouTube channels: {e}")
    return []


def add_default_sources():
    """Add default sources to the database"""
    logger.info("\n📝 Adding default sources...")
    
    sources_added = 0
    sources_skipped = 0
    
    # Add OpenAI source
    openai_source = SourceRepository.create_source(
        name="OpenAI News",
        source_type=SourceType.OPENAI,
        url="https://openai.com/news/rss.xml",
        active=True
    )
    if openai_source:
        sources_added += 1
        logger.info(f"  ✅ Added: OpenAI News")
    else:
        sources_skipped += 1
        logger.info(f"  ⏭️  Skipped (exists): OpenAI News")
    
    # Add Anthropic sources (Research, Engineering, News)
    anthropic_feeds = {
        "Anthropic Research": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_research.xml",
        "Anthropic Engineering": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_engineering.xml",
        "Anthropic News": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml"
    }
    
    for name, url in anthropic_feeds.items():
        source = SourceRepository.create_source(
            name=name,
            source_type=SourceType.ANTHROPIC,
            url=url,
            active=True
        )
        if source:
            sources_added += 1
            logger.info(f"  ✅ Added: {name}")
        else:
            sources_skipped += 1
            logger.info(f"  ⏭️  Skipped (exists): {name}")
    
    # Add YouTube channels from config
    youtube_channels = load_youtube_channels()
    for channel in youtube_channels:
        channel_name = channel.get('name')
        channel_id = channel.get('channel_id')
        
        if not channel_id:
            continue
        
        # Create RSS feed URL
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        
        source = SourceRepository.create_source(
            name=f"YouTube: {channel_name}",
            source_type=SourceType.YOUTUBE,
            url=rss_url,
            active=True
        )
        if source:
            sources_added += 1
            logger.info(f"  ✅ Added: YouTube: {channel_name}")
        else:
            sources_skipped += 1
            logger.info(f"  ⏭️  Skipped (exists): YouTube: {channel_name}")
    
    logger.info(f"\n📊 Summary: {sources_added} added, {sources_skipped} skipped")


def main():
    """Main initialization function"""
    print("=" * 60)
    print("DATABASE INITIALIZATION")
    print("=" * 60)
    
    try:
        # Create tables
        logger.info("\n🔨 Creating database tables...")
        init_db()
        
        # Add default sources
        add_default_sources()
        
        # Verify
        logger.info("\n🔍 Verifying database...")
        all_sources = SourceRepository.get_all_sources(active_only=False)
        logger.info(f"  Total sources in database: {len(all_sources)}")
        
        # Show sources by type
        for source_type in SourceType:
            sources = SourceRepository.get_sources_by_type(source_type)
            logger.info(f"  - {source_type.value}: {len(sources)} sources")
        
        print("\n" + "=" * 60)
        print("✅ DATABASE INITIALIZATION COMPLETE!")
        print("=" * 60)
        print("\nNext steps:")
        print("  1. Run scrapers: python run_scrapers.py")
        print("  2. Check database for articles")
        
        return 0
        
    except Exception as e:
        logger.error(f"\n❌ Error initializing database: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
