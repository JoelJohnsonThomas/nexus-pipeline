"""
Content extraction for articles and videos.
Extracts full content from web articles using newspaper3k and transcripts from YouTube.
"""
import os
import logging
from typing import Optional, Dict
from newspaper import Article as NewspaperArticle
from youtube_transcript_api import YouTubeTranscriptApi
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ContentExtractor:
    """Extract full content from articles and videos"""
    
    def __init__(self):
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    
    def extract_article_content(self, url: str) -> Optional[Dict[str, str]]:
        """
        Extract full text from web articles using newspaper3k.
        
        Args:
            url: Article URL
        
        Returns:
            Dict with 'content', 'title', 'authors', 'publish_date' or None if failed
        """
        try:
            article = NewspaperArticle(url)
            article.download()
            article.parse()
            
            return {
                'content': article.text,
                'title': article.title,
                'authors': article.authors,
                'publish_date': article.publish_date,
                'top_image': article.top_image,
                'method': 'newspaper3k'
            }
        except Exception as e:
            logger.error(f"Newspaper3k extraction failed for {url}: {e}")
            # Fallback to BeautifulSoup
            return self._extract_with_beautifulsoup(url)
    
    def _extract_with_beautifulsoup(self, url: str) -> Optional[Dict[str, str]]:
        """Fallback content extraction using BeautifulSoup"""
        try:
            headers = {'User-Agent': self.user_agent}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return {
                'content': text,
                'title': soup.title.string if soup.title else '',
                'authors': [],
                'publish_date': None,
                'top_image': None,
                'method': 'beautifulsoup'
            }
        except Exception as e:
            logger.error(f"BeautifulSoup extraction failed for {url}: {e}")
            return None
    
    def extract_video_transcript(self, video_id: str, language: str = 'en') -> Optional[Dict[str, str]]:
        """
        Extract transcript from YouTube videos.
        
        Args:
            video_id: YouTube video ID
            language: Preferred language code (default: 'en')
        
        Returns:
            Dict with 'transcript' and 'method' or None if failed
        """
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
            
            # Combine all transcript segments
            full_transcript = ' '.join([item['text'] for item in transcript_list])
            
            return {
                'content': full_transcript,
                'method': 'youtube_transcript_api',
                'language': language
            }
        except Exception as e:
            logger.error(f"YouTube transcript extraction failed for {video_id}: {e}")
            # Try without language specification
            try:
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                full_transcript = ' '.join([item['text'] for item in transcript_list])
                
                return {
                    'content': full_transcript,
                    'method': 'youtube_transcript_api',
                    'language': 'auto'
                }
            except Exception as e2:
                logger.error(f"YouTube transcript extraction failed (no lang): {e2}")
                return None
    
    def extract_rss_content(self, content: str) -> Dict[str, str]:
        """
        Extract and clean content from RSS feed entries.
        
        Args:
            content: Raw RSS content
        
        Returns:
            Dict with cleaned 'content' and 'method'
        """
        try:
            # Parse HTML content from RSS
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove unwanted tags
            for tag in soup(['script', 'style', 'img', 'video']):
                tag.decompose()
            
            # Get clean text
            clean_text = soup.get_text(separator=' ', strip=True)
            
            return {
                'content': clean_text,
                'method': 'rss_parse'
            }
        except Exception as e:
            logger.error(f"RSS content parsing failed: {e}")
            return {
                'content': content,
                'method': 'raw'
            }
    
    def extract(self, url: str, content_type: str = 'article', video_id: str = None) -> Optional[Dict[str, str]]:
        """
        Universal extraction method that routes to appropriate extractor.
        
        Args:
            url: Content URL
            content_type: 'article' or 'video'
            video_id: YouTube video ID (required for videos)
        
        Returns:
            Dict with extracted content or None
        """
        if content_type == 'video' and video_id:
            return self.extract_video_transcript(video_id)
        elif content_type == 'article':
            return self.extract_article_content(url)
        else:
            logger.error(f"Invalid content type or missing video_id: {content_type}")
            return None
