"""
Blog post scraper for AI News Aggregator.
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional
import logging
import feedparser
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class BlogScraper:
    """Scraper for blog posts with full content extraction"""
    
    def __init__(self, timeout: int = 30):
        """
        Initialize blog scraper.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    def scrape_blog(self, url: str, is_rss: bool = False) -> List[Dict]:
        """
        Scrape blog posts from a URL.
        
        Args:
            url: Blog URL or RSS feed URL
            is_rss: Whether the URL is an RSS feed
        
        Returns:
            List of article dictionaries with title, url, published_at, content
        """
        if is_rss or url.endswith(('.xml', '.rss', '/feed', '/rss')):
            return self._scrape_rss_feed(url)
        else:
            return self._scrape_single_page(url)
    
    def _scrape_rss_feed(self, url: str) -> List[Dict]:
        """
        Scrape articles from an RSS feed.
        
        Args:
            url: RSS feed URL
        
        Returns:
            List of article dictionaries
        """
        try:
            logger.info(f"Fetching RSS feed: {url}")
            feed = feedparser.parse(url)
            
            if feed.bozo:
                logger.error(f"Error parsing feed: {feed.bozo_exception}")
                return []
            
            articles = []
            for entry in feed.entries:
                # Get full content by scraping the article page
                article_url = entry.get("link", "")
                full_content = self._extract_full_content(article_url) if article_url else ""
                
                article = {
                    "title": entry.get("title", "No Title"),
                    "url": article_url,
                    "published_at": self._parse_published_date(entry),
                    "content": full_content or entry.get("summary", ""),
                }
                articles.append(article)
            
            logger.info(f"Scraped {len(articles)} articles from RSS feed")
            return articles
        
        except Exception as e:
            logger.error(f"Error scraping RSS feed: {e}")
            return []
    
    def _scrape_single_page(self, url: str) -> List[Dict]:
        """
        Scrape a single blog post page.
        
        Args:
            url: Blog post URL
        
        Returns:
            List with single article dictionary
        """
        try:
            logger.info(f"Scraping blog post: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Extract title
            title = self._extract_title(soup)
            
            # Extract full content
            content = self._extract_content(soup)
            
            # Try to extract published date
            published_at = self._extract_published_date(soup)
            
            article = {
                "title": title,
                "url": url,
                "published_at": published_at,
                "content": content,
            }
            
            logger.info(f"Successfully scraped blog post: {title}")
            return [article]
        
        except Exception as e:
            logger.error(f"Error scraping blog post: {e}")
            return []
    
    def _extract_full_content(self, url: str) -> str:
        """
        Extract full content from a blog post URL.
        
        Args:
            url: Article URL
        
        Returns:
            Full article content as text
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'lxml')
            return self._extract_content(soup)
        except Exception as e:
            logger.warning(f"Could not extract full content from {url}: {e}")
            return ""
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract article title from HTML"""
        # Try common title selectors
        title_selectors = [
            ('h1', {}),
            ('meta', {'property': 'og:title'}),
            ('meta', {'name': 'twitter:title'}),
            ('title', {}),
        ]
        
        for tag, attrs in title_selectors:
            element = soup.find(tag, attrs)
            if element:
                if tag == 'meta':
                    return element.get('content', 'No Title')
                return element.get_text(strip=True)
        
        return "No Title"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """
        Extract full article content from HTML.
        
        Tries common content selectors and cleans the text.
        """
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
            element.decompose()
        
        # Try common content selectors
        content_selectors = [
            ('article', {}),
            ('div', {'class': lambda x: x and any(c in str(x).lower() for c in ['content', 'post', 'article', 'entry'])}),
            ('main', {}),
        ]
        
        for tag, attrs in content_selectors:
            element = soup.find(tag, attrs)
            if element:
                # Get text and clean it
                text = element.get_text(separator='\n', strip=True)
                # Remove excessive newlines
                text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())
                if len(text) > 100:  # Ensure we got substantial content
                    return text
        
        # Fallback: get all paragraph text
        paragraphs = soup.find_all('p')
        if paragraphs:
            text = '\n\n'.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
            return text
        
        # Last resort: get body text
        body = soup.find('body')
        if body:
            return body.get_text(separator='\n', strip=True)
        
        return ""
    
    def _extract_published_date(self, soup: BeautifulSoup) -> Optional[datetime]:
        """Extract published date from HTML"""
        # Try common date selectors
        date_selectors = [
            ('meta', {'property': 'article:published_time'}),
            ('meta', {'name': 'publish_date'}),
            ('time', {'datetime': True}),
        ]
        
        for tag, attrs in date_selectors:
            element = soup.find(tag, attrs)
            if element:
                date_str = element.get('content') or element.get('datetime')
                if date_str:
                    try:
                        # Try parsing ISO format
                        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    except Exception:
                        pass
        
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
