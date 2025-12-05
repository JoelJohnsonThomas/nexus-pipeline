"""
Clean and simple OpenAI News RSS scraper.
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

class OpenAIArticle(BaseModel):
    """Model for OpenAI news article"""
    title: str = Field(..., description="Article title")
    url: str = Field(..., description="Article URL")
    published_at: Optional[datetime] = Field(None, description="Publication timestamp")
    summary: str = Field(default="", description="Article summary/description")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Introducing GPT-4",
                "url": "https://openai.com/blog/gpt-4",
                "published_at": "2024-03-14T10:00:00",
                "summary": "We've created GPT-4, the latest milestone..."
            }
        }


# ============================================================================
# OpenAI Scraper Class
# ============================================================================

class OpenAIScraper:
    """Scraper for OpenAI news RSS feed"""
    
    RSS_URL = "https://openai.com/news/rss.xml"
    
    def __init__(self, hours_back: int = 24):
        """
        Initialize OpenAI scraper.
        
        Args:
            hours_back: Number of hours to look back for articles (default: 24)
        """
        self.hours_back = hours_back
    
    def scrape_articles(self, filter_by_time: bool = True) -> List[OpenAIArticle]:
        """
        Scrape articles from OpenAI news RSS feed.
        
        Args:
            filter_by_time: Whether to filter articles by time window
        
        Returns:
            List of OpenAIArticle Pydantic models
        """
        try:
            logger.info(f"📰 Fetching OpenAI RSS feed: {self.RSS_URL}")
            
            # Parse RSS feed with feedparser (handles headers automatically)
            feed = feedparser.parse(self.RSS_URL)
            
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
                
                # Create OpenAIArticle Pydantic model
                article = OpenAIArticle(
                    title=entry.get("title", "No Title"),
                    url=entry.get("link", ""),
                    published_at=published_at,
                    summary=entry.get("summary", ""),
                )
                articles.append(article)
                
                logger.info(f"✅ Scraped: {article.title} (published {published_at})")
            
            logger.info(f"📊 Scraped {len(articles)} articles from OpenAI")
            return articles
        
        except Exception as e:
            logger.error(f"❌ Error scraping OpenAI feed: {e}")
            return []
    
    @staticmethod
    def get_article_content(url: str) -> Optional[str]:
        """
        Extract article content from URL and convert to Markdown.
        Uses requests with proper headers to bypass Cloudflare protection.
        
        Args:
            url: Article URL to extract content from
        
        Returns:
            Article content in Markdown format, or None if extraction fails
        """
        try:
            import requests
            import tempfile
            from pathlib import Path
            from docling.document_converter import DocumentConverter
            
            logger.info(f"📄 Extracting content from: {url}")
            
            # Use requests with proper headers to bypass Cloudflare
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0',
            }
            
            # Download content with proper headers
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as tmp_file:
                tmp_file.write(response.text)
                tmp_path = tmp_file.name
            
            try:
                # Convert the downloaded HTML file with Docling
                converter = DocumentConverter()
                result = converter.convert(tmp_path)
                
                # Export to Markdown
                document = result.document
                markdown_output = document.export_to_markdown()
                
                logger.info(f"✅ Successfully extracted {len(markdown_output)} characters")
                return markdown_output
            
            finally:
                # Clean up temp file
                Path(tmp_path).unlink(missing_ok=True)
        
        except Exception as e:
            logger.error(f"❌ Error extracting content from {url}: {e}")
            return None
    
    @staticmethod
    def _parse_published_date(entry) -> Optional[datetime]:
        """Parse published date from feed entry"""
        try:
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                return datetime(*entry.published_parsed[:6])
            return None
        except Exception:
            return None



# ============================================================================
# Simple Usage Example
# ============================================================================

if __name__ == "__main__":
    import sys
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("OPENAI NEWS SCRAPER")
    print("=" * 60)
    
    # Create scraper (last 7 days)
    scraper = OpenAIScraper(hours_back=168)
    
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
    
    # Test JSON serialization
    if articles:
        print("\n" + "=" * 60)
        print("JSON EXPORT TEST")
        print("=" * 60)
        print(articles[0].model_dump_json(indent=2))
