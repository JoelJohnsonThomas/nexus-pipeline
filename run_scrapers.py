#!/usr/bin/env python3
"""
Simple standalone runner script to execute all scrapers (YouTube, OpenAI, Anthropic).
No database dependencies - just runs the scrapers and displays results.
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


def run_youtube_scraper(hours_back: int, include_transcripts: bool, config_file: Path):
    """Run YouTube scraper for all configured channels"""
    results = {"channels": [], "total_videos": 0, "errors": 0}
    
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
            
            results["channels"].append({
                "name": channel_name,
                "channel_id": channel_id,
                "videos": videos,
                "count": len(videos)
            })
            results["total_videos"] += len(videos)
            
            logging.info(f"  → Found {len(videos)} videos")
            
        except Exception as e:
            logging.error(f"Error scraping YouTube channel {channel_name}: {e}")
            results["errors"] += 1
    
    return results


def run_openai_scraper(hours_back: int):
    """Run OpenAI scraper"""
    logging.info("\n🤖 OPENAI SCRAPER")
    logging.info("-" * 60)
    
    try:
        scraper = OpenAIScraper(hours_back=hours_back)
        articles = scraper.scrape_articles(filter_by_time=True)
        logging.info(f"  → Found {len(articles)} articles")
        return {"articles": articles, "total": len(articles), "error": None}
    except Exception as e:
        logging.error(f"Error scraping OpenAI: {e}")
        return {"articles": [], "total": 0, "error": str(e)}


def run_anthropic_scraper(hours_back: int):
    """Run Anthropic scraper"""
    logging.info("\n🧠 ANTHROPIC SCRAPER")
    logging.info("-" * 60)
    
    try:
        scraper = AnthropicScraper(hours_back=hours_back)
        articles = scraper.scrape_articles(filter_by_time=True)
        logging.info(f"  → Found {len(articles)} articles")
        return {"articles": articles, "total": len(articles), "errors": 0}
    except Exception as e:
        logging.error(f"Error scraping Anthropic: {e}")
        return {"articles": [], "total": 0, "errors": 1}


def main():
    """Main runner function"""
    parser = argparse.ArgumentParser(
        description='Run all AI news scrapers (YouTube, OpenAI, Anthropic)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default 24-hour lookback
  python run_scrapers.py
  
  # Run with 7-day lookback
  python run_scrapers.py --hours 168
  
  # Include YouTube transcripts (slower)
  python run_scrapers.py --transcripts
  
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
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    logger = logging.getLogger(__name__)
    
    try:
        # Config file path
        config_dir = Path(__file__).parent / "config"
        youtube_config = config_dir / "youtube_channels.json"
        
        logger.info("=" * 60)
        logger.info(f"STARTING SCRAPER RUN (Looking back {args.hours} hours)")
        logger.info("=" * 60)
        
        # Run all scrapers
        youtube_results = run_youtube_scraper(args.hours, args.transcripts, youtube_config)
        openai_results = run_openai_scraper(args.hours)
        anthropic_results = run_anthropic_scraper(args.hours)
        
        # Calculate summary
        total_items = (
            youtube_results["total_videos"] +
            openai_results["total"] +
            anthropic_results["total"]
        )
        total_errors = (
            youtube_results["errors"] +
            (1 if openai_results["error"] else 0) +
            anthropic_results["errors"]
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
