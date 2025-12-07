"""
Scraper manager to orchestrate all scraping operations.
"""
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.exc import IntegrityError

from app.database import get_db_session, Source, Article, SourceType
from app.scrapers.youtube_scraper import YouTubeScraper
from app.scrapers.blog_scraper import BlogScraper
from app.scrapers.openai_scraper import OpenAIScraper
from app.scrapers.anthropic_scraper import AnthropicScraper

logger = logging.getLogger(__name__)


class ScraperManager:
    """Manages all scraping operations"""
    
    def __init__(self, hours_back: int = 24):
        """
        Initialize scraper manager with all scrapers.
        
        Args:
            hours_back: Number of hours to look back for articles (default: 24)
        """
        self.hours_back = hours_back
        self.youtube_scraper = YouTubeScraper(hours_back=hours_back)
        self.blog_scraper = BlogScraper()
        self.openai_scraper = OpenAIScraper(hours_back=hours_back)
        self.anthropic_scraper = AnthropicScraper(hours_back=hours_back)
        
        # Path to YouTube channels config
        self.config_dir = Path(__file__).parent.parent.parent / "config"
        self.youtube_channels_file = self.config_dir / "youtube_channels.json"
    
    def load_youtube_channels(self) -> List[Dict]:
        """
        Load YouTube channels from config file.
        
        Returns:
            List of channel configurations
        """
        try:
            if not self.youtube_channels_file.exists():
                logger.warning(f"YouTube channels config not found: {self.youtube_channels_file}")
                return []
            
            with open(self.youtube_channels_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                channels = config.get('channels', [])
                logger.info(f"Loaded {len(channels)} YouTube channels from config")
                return channels
        except Exception as e:
            logger.error(f"Error loading YouTube channels config: {e}")
            return []
    
    def run_all_scrapers(self, include_transcripts: bool = False) -> Dict[str, any]:
        """
        Run all scrapers (YouTube, OpenAI, Anthropic) and return results.
        
        Args:
            include_transcripts: Whether to fetch YouTube video transcripts
        
        Returns:
            Dictionary with results from all scrapers
        """
        results = {
            "youtube": {"channels": [], "total_videos": 0, "errors": 0},
            "openai": {"articles": [], "total": 0, "error": None},
            "anthropic": {"articles": [], "total": 0, "errors": 0},
            "summary": {"total_items": 0, "total_errors": 0}
        }
        
        logger.info("=" * 60)
        logger.info(f"STARTING SCRAPER RUN (Looking back {self.hours_back} hours)")
        logger.info("=" * 60)
        
        # 1. Scrape YouTube channels
        logger.info("\n📺 YOUTUBE SCRAPER")
        logger.info("-" * 60)
        channels = self.load_youtube_channels()
        
        for channel_config in channels:
            try:
                channel_name = channel_config.get('name', 'Unknown')
                channel_id = channel_config.get('channel_id')
                
                if not channel_id:
                    logger.warning(f"No channel_id for {channel_name}, skipping")
                    continue
                
                logger.info(f"Scraping: {channel_name}")
                videos = self.youtube_scraper.scrape_channel(
                    channel_id,
                    include_transcripts=include_transcripts,
                    filter_by_time=True
                )
                
                results["youtube"]["channels"].append({
                    "name": channel_name,
                    "channel_id": channel_id,
                    "videos": videos,
                    "count": len(videos)
                })
                results["youtube"]["total_videos"] += len(videos)
                
                logger.info(f"  → Found {len(videos)} videos")
                
            except Exception as e:
                logger.error(f"Error scraping YouTube channel {channel_name}: {e}")
                results["youtube"]["errors"] += 1
        
        # 2. Scrape OpenAI
        logger.info("\n🤖 OPENAI SCRAPER")
        logger.info("-" * 60)
        try:
            openai_articles = self.openai_scraper.scrape_articles(filter_by_time=True)
            results["openai"]["articles"] = openai_articles
            results["openai"]["total"] = len(openai_articles)
            logger.info(f"  → Found {len(openai_articles)} articles")
        except Exception as e:
            logger.error(f"Error scraping OpenAI: {e}")
            results["openai"]["error"] = str(e)
        
        # 3. Scrape Anthropic
        logger.info("\n🧠 ANTHROPIC SCRAPER")
        logger.info("-" * 60)
        try:
            anthropic_articles = self.anthropic_scraper.scrape_articles(filter_by_time=True)
            results["anthropic"]["articles"] = anthropic_articles
            results["anthropic"]["total"] = len(anthropic_articles)
            logger.info(f"  → Found {len(anthropic_articles)} articles")
        except Exception as e:
            logger.error(f"Error scraping Anthropic: {e}")
            results["anthropic"]["errors"] += 1
        
        # Summary
        results["summary"]["total_items"] = (
            results["youtube"]["total_videos"] +
            results["openai"]["total"] +
            results["anthropic"]["total"]
        )
        results["summary"]["total_errors"] = (
            results["youtube"]["errors"] +
            (1 if results["openai"]["error"] else 0) +
            results["anthropic"]["errors"]
        )
        
        logger.info("\n" + "=" * 60)
        logger.info("SCRAPING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Total items found: {results['summary']['total_items']}")
        logger.info(f"  - YouTube videos: {results['youtube']['total_videos']}")
        logger.info(f"  - OpenAI articles: {results['openai']['total']}")
        logger.info(f"  - Anthropic articles: {results['anthropic']['total']}")
        logger.info(f"Total errors: {results['summary']['total_errors']}")
        
        return results
    
    def scrape_all_sources(self) -> Dict[str, int]:
        """
        Scrape all active sources and save articles to database.
        
        Returns:
            Dictionary with scraping statistics
        """
        stats = {
            "sources_processed": 0,
            "articles_found": 0,
            "articles_new": 0,
            "articles_duplicate": 0,
            "errors": 0,
        }
        
        with get_db_session() as session:
            # Get all active sources
            sources = session.query(Source).filter(Source.active == True).all()
            
            logger.info(f"Found {len(sources)} active sources to scrape")
            
            for source in sources:
                try:
                    logger.info(f"Scraping source: {source.name} ({source.source_type.value})")
                    
                    # Scrape based on source type
                    if source.source_type == SourceType.YOUTUBE:
                        articles_data = self.youtube_scraper.scrape_channel(source.url)
                    elif source.source_type == SourceType.BLOG:
                        articles_data = self.blog_scraper.scrape_blog(source.url)
                    else:
                        logger.warning(f"Unknown source type: {source.source_type}")
                        continue
                    
                    stats["sources_processed"] += 1
                    stats["articles_found"] += len(articles_data)
                    
                    # Save articles to database
                    for article_data in articles_data:
                        try:
                            # Check if article already exists
                            existing = session.query(Article).filter(
                                Article.url == article_data["url"]
                            ).first()
                            
                            if existing:
                                stats["articles_duplicate"] += 1
                                logger.debug(f"Article already exists: {article_data['title']}")
                                continue
                            
                            # Create new article
                            article = Article(
                                source_id=source.id,
                                title=article_data["title"],
                                url=article_data["url"],
                                content=article_data.get("content", ""),
                                published_at=article_data.get("published_at"),
                                scraped_at=datetime.utcnow(),
                            )
                            
                            session.add(article)
                            session.commit()
                            stats["articles_new"] += 1
                            logger.info(f"Saved new article: {article.title}")
                        
                        except IntegrityError:
                            session.rollback()
                            stats["articles_duplicate"] += 1
                            logger.debug(f"Duplicate article (integrity error): {article_data['title']}")
                        
                        except Exception as e:
                            session.rollback()
                            stats["errors"] += 1
                            logger.error(f"Error saving article: {e}")
                
                except Exception as e:
                    stats["errors"] += 1
                    logger.error(f"Error scraping source {source.name}: {e}")
        
        logger.info(f"Scraping complete. Stats: {stats}")
        return stats
    
    def scrape_source_by_id(self, source_id: int) -> Dict[str, int]:
        """
        Scrape a specific source by ID.
        
        Args:
            source_id: Source ID to scrape
        
        Returns:
            Dictionary with scraping statistics
        """
        stats = {
            "articles_found": 0,
            "articles_new": 0,
            "articles_duplicate": 0,
        }
        
        with get_db_session() as session:
            source = session.query(Source).filter(Source.id == source_id).first()
            
            if not source:
                logger.error(f"Source with ID {source_id} not found")
                return stats
            
            logger.info(f"Scraping source: {source.name}")
            
            # Scrape based on source type
            if source.source_type == SourceType.YOUTUBE:
                articles_data = self.youtube_scraper.scrape_channel(source.url)
            elif source.source_type == SourceType.BLOG:
                articles_data = self.blog_scraper.scrape_blog(source.url)
            else:
                logger.warning(f"Unknown source type: {source.source_type}")
                return stats
            
            stats["articles_found"] = len(articles_data)
            
            # Save articles
            for article_data in articles_data:
                try:
                    existing = session.query(Article).filter(
                        Article.url == article_data["url"]
                    ).first()
                    
                    if existing:
                        stats["articles_duplicate"] += 1
                        continue
                    
                    article = Article(
                        source_id=source.id,
                        title=article_data["title"],
                        url=article_data["url"],
                        content=article_data.get("content", ""),
                        published_at=article_data.get("published_at"),
                        scraped_at=datetime.utcnow(),
                    )
                    
                    session.add(article)
                    session.commit()
                    stats["articles_new"] += 1
                
                except IntegrityError:
                    session.rollback()
                    stats["articles_duplicate"] += 1
        
        logger.info(f"Scraping complete for source {source_id}. Stats: {stats}")
        return stats
