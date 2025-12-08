#!/usr/bin/env python3
"""
Scraper runner script that executes all scrapers and saves results to database.
"""
import sys
import argparse
import logging
import json
from pathlib import Path
from datetime import datetime

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.scrapers.youtube_scraper import YouTubeScraper
from app.scrapers.openai_scraper import OpenAIScraper

from app.scrapers.anthropic_scraper import AnthropicScraper
from app.scrapers.google_scraper import GoogleScraper
from app.database.repository import ArticleRepository, SourceRepository
from app.database.models import SourceType


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def load_youtube_channels(config_file: Path):
    """Load YouTube channels from config file"""
    try:
        if not config_file.exists():
            logging.warning(f"YouTube channels config not found: {config_file}")
            return []
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            channels = config.get('channels', [])
            logging.info(f"Loaded {len(channels)} YouTube channels from config")
            return channels
    except Exception as e:
        logging.error(f"Error loading YouTube channels config: {e}")
        return []


def save_youtube_videos(channel_name: str, channel_id: str, videos: list) -> dict:
    """Save YouTube videos to database"""
    stats = {"created": 0, "duplicates": 0, "errors": 0}
    
    # Get or create source
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    source = SourceRepository.get_source_by_url(rss_url)
    
    if not source:
        logging.warning(f"Source not found for {channel_name}, skipping database save")
        return stats
    
    # Prepare articles data
    articles_data = []
    for video in videos:
        articles_data.append({
            "source_id": source.id,
            "title": video.title,
            "url": video.url,
            "content": video.content or "",
            "published_at": video.published_at,
            "video_id": video.video_id,
            "category": None
        })
    
    # Bulk insert
    if articles_data:
        stats = ArticleRepository.bulk_create_articles(articles_data)
    
    return stats


def save_openai_articles(articles: list) -> dict:
    """Save OpenAI articles to database"""
    stats = {"created": 0, "duplicates": 0, "errors": 0}
    
    # Get source
    source = SourceRepository.get_source_by_url("https://openai.com/news/rss.xml")
    
    if not source:
        logging.warning("OpenAI source not found, skipping database save")
        return stats
    
    # Prepare articles data
    articles_data = []
    for article in articles:
        articles_data.append({
            "source_id": source.id,
            "title": article.title,
            "url": article.url,
            "content": article.summary or "",
            "published_at": article.published_at,
            "video_id": None,
            "category": None
        })
    
    # Bulk insert
    if articles_data:
        stats = ArticleRepository.bulk_create_articles(articles_data)
    
    return stats


def save_anthropic_articles(articles: list) -> dict:
    """Save Anthropic articles to database"""
    stats = {"created": 0, "duplicates": 0, "errors": 0}
    
    # Group articles by category to find correct source
    for article in articles:
        # Determine source URL based on category
        if article.category == "research":
            source_url = "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_research.xml"
        elif article.category == "engineering":
            source_url = "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_engineering.xml"
        elif article.category == "news":
            source_url = "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml"
        else:
            logging.warning(f"Unknown Anthropic category: {article.category}")
            continue
        
        source = SourceRepository.get_source_by_url(source_url)
        
        if not source:
            logging.warning(f"Anthropic {article.category} source not found")
            stats["errors"] += 1
            continue
        
        # Save individual article
        result = ArticleRepository.create_article(
            source_id=source.id,
            title=article.title,
            url=article.url,
            content=article.summary or "",
            published_at=article.published_at,
            video_id=None,
            category=article.category
        )
        
        if result:
            stats["created"] += 1
        else:
            stats["duplicates"] += 1
    
    return stats


def save_google_articles(articles: list) -> dict:
    """Save Google Blog articles to database"""
    stats = {"created": 0, "duplicates": 0, "errors": 0}
    
    # Get source
    source = SourceRepository.get_source_by_url("https://blog.google/rss")
    
    if not source:
        logging.warning("Google Blog source not found, skipping database save")
        return stats
    
    # Prepare articles data
    articles_data = []
    for article in articles:
        articles_data.append({
            "source_id": source.id,
            "title": article.title,
            "url": article.url,
            "content": article.summary or "",
            "published_at": article.published_at,
            "video_id": None,
            "category": "blog"
        })
    
    # Bulk insert
    if articles_data:
        stats = ArticleRepository.bulk_create_articles(articles_data)
    
    return stats


def run_youtube_scraper(hours_back: int, include_transcripts: bool, config_file: Path, save_to_db: bool = True):
    """Run YouTube scraper for all configured channels"""
    results = {"channels": [], "total_videos": 0, "errors": 0, "db_stats": {"created": 0, "duplicates": 0, "errors": 0}}
    
    logging.info("\n📺 YOUTUBE SCRAPER")
    logging.info("-" * 60)
    
    scraper = YouTubeScraper(hours_back=hours_back)
    channels = load_youtube_channels(config_file)
    
    for channel_config in channels:
        try:
            channel_name = channel_config.get('name', 'Unknown')
            channel_id = channel_config.get('channel_id')
            
            if not channel_id:
                logging.warning(f"No channel_id for {channel_name}, skipping")
                continue
            
            logging.info(f"Scraping: {channel_name}")
            videos = scraper.scrape_channel(
                channel_id,
                include_transcripts=include_transcripts,
                filter_by_time=True
            )
            
            # Save to database
            db_stats = {"created": 0, "duplicates": 0, "errors": 0}
            if save_to_db and videos:
                db_stats = save_youtube_videos(channel_name, channel_id, videos)
                logging.info(f"  💾 Saved: {db_stats['created']} new, {db_stats['duplicates']} duplicates")
            
            results["channels"].append({
                "name": channel_name,
                "channel_id": channel_id,
                "videos": videos,
                "count": len(videos)
            })
            results["total_videos"] += len(videos)
            results["db_stats"]["created"] += db_stats["created"]
            results["db_stats"]["duplicates"] += db_stats["duplicates"]
            results["db_stats"]["errors"] += db_stats["errors"]
            
            logging.info(f"  → Found {len(videos)} videos")
            
        except Exception as e:
            logging.error(f"Error scraping YouTube channel {channel_name}: {e}")
            results["errors"] += 1
    
    return results


def run_openai_scraper(hours_back: int, save_to_db: bool = True):
    """Run OpenAI scraper"""
    logging.info("\n🤖 OPENAI SCRAPER")
    logging.info("-" * 60)
    
    try:
        scraper = OpenAIScraper(hours_back=hours_back)
        articles = scraper.scrape_articles(filter_by_time=True)
        
        # Save to database
        db_stats = {"created": 0, "duplicates": 0, "errors": 0}
        if save_to_db and articles:
            db_stats = save_openai_articles(articles)
            logging.info(f"  💾 Saved: {db_stats['created']} new, {db_stats['duplicates']} duplicates")
        
        logging.info(f"  → Found {len(articles)} articles")
        return {"articles": articles, "total": len(articles), "error": None, "db_stats": db_stats}
    except Exception as e:
        logging.error(f"Error scraping OpenAI: {e}")
        return {"articles": [], "total": 0, "error": str(e), "db_stats": {"created": 0, "duplicates": 0, "errors": 0}}


def run_anthropic_scraper(hours_back: int, save_to_db: bool = True):
    """Run Anthropic scraper"""
    logging.info("\n🧠 ANTHROPIC SCRAPER")
    logging.info("-" * 60)
    
    try:
        scraper = AnthropicScraper(hours_back=hours_back)
        articles = scraper.scrape_articles(filter_by_time=True)
        
        # Save to database
        db_stats = {"created": 0, "duplicates": 0, "errors": 0}
        if save_to_db and articles:
            db_stats = save_anthropic_articles(articles)
            logging.info(f"  💾 Saved: {db_stats['created']} new, {db_stats['duplicates']} duplicates")
        
        logging.info(f"  → Found {len(articles)} articles")
        return {"articles": articles, "total": len(articles), "errors": 0, "db_stats": db_stats}
    except Exception as e:
        logging.error(f"Error scraping Anthropic: {e}")
        return {"articles": [], "total": 0, "errors": 1, "db_stats": {"created": 0, "duplicates": 0, "errors": 0}}


def run_google_scraper(hours_back: int, save_to_db: bool = True):
    """Run Google Blog scraper"""
    logging.info("\n🔎 GOOGLE BLOG SCRAPER")
    logging.info("-" * 60)
    
    try:
        scraper = GoogleScraper(hours_back=hours_back)
        articles = scraper.scrape_articles(filter_by_time=True)
        
        # Save to database
        db_stats = {"created": 0, "duplicates": 0, "errors": 0}
        if save_to_db and articles:
            db_stats = save_google_articles(articles)
            logging.info(f"  💾 Saved: {db_stats['created']} new, {db_stats['duplicates']} duplicates")
        
        logging.info(f"  → Found {len(articles)} articles")
        return {"articles": articles, "total": len(articles), "errors": 0, "db_stats": db_stats}
    except Exception as e:
        logging.error(f"Error scraping Google Blog: {e}")
        return {"articles": [], "total": 0, "errors": 1, "db_stats": {"created": 0, "duplicates": 0, "errors": 0}}


def main():
    """Main runner function"""
    parser = argparse.ArgumentParser(
        description='Run all AI news scrapers (YouTube, OpenAI, Anthropic) and save to database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default 24-hour lookback
  python run_scrapers.py
  
  # Run with 7-day lookback
  python run_scrapers.py --hours 168
  
  # Include YouTube transcripts (slower)
  python run_scrapers.py --transcripts
  
  # Don't save to database (dry run)
  python run_scrapers.py --no-save
  
  # Verbose output
  python run_scrapers.py --verbose
        """
    )
    
    parser.add_argument(
        '--hours',
        type=int,
        default=24,
        help='Number of hours to look back for articles (default: 24)'
    )
    
    parser.add_argument(
        '--transcripts',
        action='store_true',
        help='Include YouTube video transcripts (slower)'
    )
    
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Do not save to database (dry run)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    logger = logging.getLogger(__name__)
    save_to_db = not args.no_save
    
    try:
        # Config file path
        config_dir = Path(__file__).parent / "config"
        youtube_config = config_dir / "youtube_channels.json"
        
        logger.info("=" * 60)
        logger.info(f"STARTING SCRAPER RUN (Looking back {args.hours} hours)")
        if save_to_db:
            logger.info("💾 Database saving: ENABLED")
        else:
            logger.info("💾 Database saving: DISABLED (dry run)")
        logger.info("=" * 60)
        
        # Run all scrapers

        youtube_results = run_youtube_scraper(args.hours, args.transcripts, youtube_config, save_to_db)
        openai_results = run_openai_scraper(args.hours, save_to_db)
        anthropic_results = run_anthropic_scraper(args.hours, save_to_db)
        google_results = run_google_scraper(args.hours, save_to_db)
        
        # Calculate summary
        total_items = (
            youtube_results["total_videos"] +
            openai_results["total"] +

            anthropic_results["total"] +
            google_results["total"]
        )
        total_errors = (
            youtube_results["errors"] +
            (1 if openai_results["error"] else 0) +
            anthropic_results["errors"] +
            google_results["errors"]
        )
        
        # Database stats
        total_saved = (
            youtube_results["db_stats"]["created"] +
            openai_results["db_stats"]["created"] +

            anthropic_results["db_stats"]["created"] +
            google_results["db_stats"]["created"]
        )
        total_duplicates = (
            youtube_results["db_stats"]["duplicates"] +
            openai_results["db_stats"]["duplicates"] +
            anthropic_results["db_stats"]["duplicates"] +
            google_results["db_stats"]["duplicates"]
        )
        
        # Display summary
        print("\n" + "=" * 60)
        print("📊 FINAL SUMMARY")
        print("=" * 60)
        print(f"Total items scraped: {total_items}")
        print(f"\nBreakdown:")
        print(f"  📺 YouTube videos: {youtube_results['total_videos']} (from {len(youtube_results['channels'])} channels)")
        print(f"  🤖 OpenAI articles: {openai_results['total']}")

        print(f"  🧠 Anthropic articles: {anthropic_results['total']}")
        print(f"  🔎 Google Blog articles: {google_results['total']}")
        
        if save_to_db:
            print(f"\n💾 Database:")
            print(f"  ✅ Saved: {total_saved} new articles")
            print(f"  ⏭️  Skipped: {total_duplicates} duplicates")
        
        if total_errors > 0:
            print(f"\n⚠️  Errors encountered: {total_errors}")
        
        # Show sample items
        if youtube_results['total_videos'] > 0:
            print("\n📺 Sample YouTube Videos:")
            for channel in youtube_results['channels'][:2]:  # Show first 2 channels
                if channel['videos']:
                    video = channel['videos'][0]
                    print(f"  • [{channel['name']}] {video.title}")
                    print(f"    {video.url}")
        
        if openai_results['total'] > 0:
            print("\n🤖 Sample OpenAI Articles:")
            for article in openai_results['articles'][:2]:
                print(f"  • {article.title}")
                print(f"    {article.url}")
        

        if anthropic_results['total'] > 0:
            print("\n🧠 Sample Anthropic Articles:")
            for article in anthropic_results['articles'][:2]:
                print(f"  • [{article.category}] {article.title}")
                print(f"    {article.url}")

        if google_results['total'] > 0:
            print("\n🔎 Sample Google Articles:")
            for article in google_results['articles'][:2]:
                print(f"  • {article.title}")
                print(f"    {article.url}")
        
        print("\n✅ Scraping complete!")
        return 0
        
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Scraping interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"\n❌ Error running scrapers: {e}", exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())
