"""
Scraper manager to orchestrate all scraping operations.
"""
import logging
from datetime import datetime
from typing import List, Dict
from sqlalchemy.exc import IntegrityError

from app.database import get_db_session
from app.models import Source, Article, SourceType
from app.scrapers.youtube_scraper import YouTubeScraper
from app.scrapers.blog_scraper import BlogScraper

logger = logging.getLogger(__name__)


class ScraperManager:
    """Manages all scraping operations"""
    
    def __init__(self):
        self.youtube_scraper = YouTubeScraper()
        self.blog_scraper = BlogScraper()
    
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
