"""
Clean and simple Anthropic RSS scraper.
Combines Research, Engineering, and News feeds.
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

class AnthropicArticle(BaseModel):
    """Model for Anthropic article"""
    title: str = Field(..., description="Article title")
    url: str = Field(..., description="Article URL")
    published_at: Optional[datetime] = Field(None, description="Publication timestamp")
    summary: str = Field(default="", description="Article summary/description")
    category: str = Field(..., description="Article category: research, engineering, or news")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Introducing Claude 3",
                "url": "https://www.anthropic.com/news/claude-3",
                "published_at": "2024-03-04T10:00:00",
                "summary": "Today we're announcing Claude 3...",
                "category": "news"
            }
        }


# ============================================================================
# Anthropic Scraper Class
# ============================================================================

class AnthropicScraper:
    """Scraper for Anthropic RSS feeds (Research, Engineering, News)"""
    
    # All three Anthropic RSS feeds
    FEEDS = {
        "research": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_research.xml",
        "engineering": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_engineering.xml",
        "news": "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml"
    }
    
    def __init__(self, hours_back: int = 24):
        """
        Initialize Anthropic scraper.
        
        Args:
            hours_back: Number of hours to look back for articles (default: 24)
        """
        self.hours_back = hours_back
    
    def scrape_articles(self, filter_by_time: bool = True) -> List[AnthropicArticle]:
        """
        Scrape articles from all Anthropic RSS feeds.
        
        Args:
            filter_by_time: Whether to filter articles by time window
        
        Returns:
            List of AnthropicArticle Pydantic models from all feeds
        """
        all_articles = []
        
        # Calculate cutoff time if filtering
        cutoff_time = None
        if filter_by_time:
            cutoff_time = datetime.utcnow() - timedelta(hours=self.hours_back)
            logger.info(f"⏰ Filtering articles published after: {cutoff_time}")
        
        # Scrape each feed
        for category, feed_url in self.FEEDS.items():
            logger.info(f"📰 Fetching Anthropic {category.upper()} feed")
            articles = self._scrape_feed(feed_url, category, cutoff_time, filter_by_time)
            all_articles.extend(articles)
        
        logger.info(f"📊 Total scraped: {len(all_articles)} articles from Anthropic")
        return all_articles
    
    def _scrape_feed(
        self,
        feed_url: str,
        category: str,
        cutoff_time: Optional[datetime],
        filter_by_time: bool
    ) -> List[AnthropicArticle]:
        """
        Scrape a single RSS feed.
        
        Args:
            feed_url: RSS feed URL
            category: Category name (research, engineering, news)
            cutoff_time: Cutoff datetime for filtering
            filter_by_time: Whether to filter by time
        
        Returns:
            List of AnthropicArticle models
        """
        try:
            import requests
            
            # For GitHub raw URLs, fetch content first then parse
            # This avoids the "text/plain" content-type issue
            response = requests.get(feed_url, timeout=10)
            response.raise_for_status()
            
            # Parse the fetched content as XML
            feed = feedparser.parse(response.content)
            
            if feed.bozo:
                logger.error(f"❌ Error parsing {category} feed: {feed.bozo_exception}")
                return []
            
            articles = []
            for entry in feed.entries:
                published_at = self._parse_published_date(entry)
                
                # Filter by time if enabled
                if filter_by_time and published_at and cutoff_time:
                    if published_at < cutoff_time:
                        logger.debug(f"⏭️  Skipping old article: {entry.get('title')}")
                        continue
                
                # Create AnthropicArticle Pydantic model
                article = AnthropicArticle(
                    title=entry.get("title", "No Title"),
                    url=entry.get("link", ""),
                    published_at=published_at,
                    summary=entry.get("summary", ""),
                    category=category,
                )
                articles.append(article)
                
                logger.info(f"✅ [{category.upper()}] {article.title} ({published_at})")
            
            logger.info(f"   → {len(articles)} articles from {category}")
            return articles
        
        except Exception as e:
            logger.error(f"❌ Error scraping {category} feed: {e}")
            return []
    
    @staticmethod
    def _parse_published_date(entry) -> Optional[datetime]:
        """Parse published date from feed entry"""
        try:
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                return datetime(*entry.published_parsed[:6])
            return None
        except Exception:
            return None
    
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
            # Note: requests library automatically handles gzip/deflate decompression
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0',
            }
            
            # Download content with proper headers
            # requests automatically decompresses gzip/deflate responses
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Ensure we have the text content properly decoded
            response.encoding = response.apparent_encoding or 'utf-8'
            html_content = response.text
            
            # Save to temporary file with explicit UTF-8 encoding
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8', errors='replace') as tmp_file:
                tmp_file.write(html_content)
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



# ============================================================================
# Simple Usage Example
# ============================================================================

if __name__ == "__main__":
    import sys
    import io
    
    # Fix Windows encoding
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("ANTHROPIC SCRAPER (Research + Engineering + News)")
    print("=" * 60)
    
    # Create scraper (last 7 days)
    scraper = AnthropicScraper(hours_back=168)
    
    # Scrape all feeds
    articles = scraper.scrape_articles(filter_by_time=True)
    
    if articles:
        print(f"\n✅ Found {len(articles)} total articles from last 7 days\n")
        
        # Group by category
        by_category = {}
        for article in articles:
            if article.category not in by_category:
                by_category[article.category] = []
            by_category[article.category].append(article)
        
        # Display by category
        for category, cat_articles in by_category.items():
            print(f"\n{category.upper()} ({len(cat_articles)} articles):")
            print("-" * 60)
            for i, article in enumerate(cat_articles[:3], 1):  # Show first 3
                print(f"{i}. {article.title}")
                print(f"   URL: {article.url}")
                print(f"   Published: {article.published_at}")
                print()
    else:
        print("\nNo articles found in the time window")
    
    # Test JSON serialization
    if articles:
        print("\n" + "=" * 60)
        print("JSON EXPORT TEST")
        print("=" * 60)
        print(articles[0].model_dump_json(indent=2))
        
        # Test content extraction
        print("\n" + "=" * 60)
        print("CONTENT EXTRACTION TEST")
        print("=" * 60)
        if len(articles) > 1:
            test_article = articles[1]
            print(f"\nExtracting content from: {test_article.title}")
            print(f"URL: {test_article.url}\n")
            
            markdown = AnthropicScraper.get_article_content(test_article.url)
            if markdown:
                print(f"Successfully extracted {len(markdown)} characters")
                print(f"First 300 characters:\n{markdown[:300]}...")
            else:
                print("Failed to extract content")
