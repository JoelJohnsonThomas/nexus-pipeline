"""
Scraper for Google Blog News RSS feed.
"""
import feedparser
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Models
# ============================================================================

class GoogleArticle(BaseModel):
    """Model for Google Blog news article"""
    title: str = Field(..., description="Article title")
    url: str = Field(..., description="Article URL")
    published_at: Optional[datetime] = Field(None, description="Publication timestamp")
    summary: str = Field(default="", description="Article summary/description")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "A new way to search",
                "url": "https://blog.google/products/search/generative-ai-search/",
                "published_at": "2024-05-14T10:00:00",
                "summary": "We're introducing a new way to search with generative AI..."
            }
        }


# ============================================================================
# Google Scraper Class
# ============================================================================

class GoogleScraper:
    """Scraper for Google Blog news RSS feed"""
    
    RSS_URL = "https://blog.google/rss"
    
    def __init__(self, hours_back: int = 24):
        """
        Initialize Google scraper.
        
        Args:
            hours_back: Number of hours to look back for articles (default: 24)
        """
        self.hours_back = hours_back
    
    def scrape_articles(self, filter_by_time: bool = True) -> List[GoogleArticle]:
        """
        Scrape articles from Google Blog RSS feed.
        
        Args:
            filter_by_time: Whether to filter articles by time window
        
        Returns:
            List of GoogleArticle Pydantic models
        """
        try:
            logger.info(f"📰 Fetching Google Blog RSS feed: {self.RSS_URL}")
            
            # Use requests with generic user-agent to avoid blocking
            import requests
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(self.RSS_URL, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse RSS feed content
            feed = feedparser.parse(response.content)
            
            if feed.bozo:
                logger.error(f"❌ Error parsing feed: {feed.bozo_exception}")
                return []
            
            # Calculate cutoff time if filtering
            cutoff_time = None
            if filter_by_time:
                cutoff_time = datetime.utcnow() - timedelta(hours=self.hours_back)
                logger.info(f"⏰ Filtering articles published after: {cutoff_time}")
            
            articles = []
            for entry in feed.entries:
                published_at = self._parse_published_date(entry)
                
                # Filter by time if enabled
                if filter_by_time and published_at and cutoff_time:
                    if published_at < cutoff_time:
                        logger.debug(f"⏭️  Skipping old article: {entry.get('title')}")
                        continue
                
                # Create GoogleArticle Pydantic model
                article = GoogleArticle(
                    title=entry.get("title", "No Title"),
                    url=entry.get("link", ""),
                    published_at=published_at,
                    summary=entry.get("summary", ""),
                )
                articles.append(article)
                
                logger.info(f"✅ Scraped: {article.title} (published {published_at})")
            
            logger.info(f"📊 Scraped {len(articles)} articles from Google Blog")
            return articles
        
        except Exception as e:
            logger.error(f"❌ Error scraping Google Blog feed: {e}")
            return []
            
    @staticmethod
    def _parse_published_date(entry) -> Optional[datetime]:
        """Parse published date from feed entry"""
        try:
            # Google often uses published_parsed or updated_parsed
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                return datetime(*entry.published_parsed[:6])
            if hasattr(entry, "updated_parsed") and entry.updated_parsed:
                return datetime(*entry.updated_parsed[:6])
            return None
        except Exception:
            return None

if __name__ == "__main__":
    import sys
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("GOOGLE BLOG SCRAPER")
    print("=" * 60)
    
    # Create scraper (last 7 days to ensure we get something)
    scraper = GoogleScraper(hours_back=168)
    
    # Scrape articles
    articles = scraper.scrape_articles(filter_by_time=True)
    
    if articles:
        print(f"\n✅ Found {len(articles)} articles from last 7 days:\n")
        
        for i, article in enumerate(articles, 1):
            print(f"{i}. {article.title}")
            print(f"   URL: {article.url}")
            print(f"   Published: {article.published_at}")
            print(f"   Summary: {article.summary[:100]}...")
            print()
    else:
        print("\n⚠️  No articles found in the time window")
