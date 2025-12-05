"""
YouTube RSS feed scraper for AI News Aggregator with transcript extraction.
"""
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import re
import requests
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable
)
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Models
# ============================================================================

class Transcript(BaseModel):
    """Model for YouTube video transcript"""
    text: str = Field(..., description="Full transcript text")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "This is the full transcript of the video..."
            }
        }


class ChannelVideo(BaseModel):
    """Model for YouTube channel video metadata"""
    title: str = Field(..., description="Video title")
    url: str = Field(..., description="Full YouTube video URL")
    video_id: Optional[str] = Field(None, description="YouTube video ID (11 characters)")
    published_at: Optional[datetime] = Field(None, description="Video publication timestamp")
    content: str = Field(default="", description="Video description/summary")
    transcript: Optional[str] = Field(None, description="Full video transcript if available")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Introduction to Machine Learning",
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "video_id": "dQw4w9WgXcQ",
                "published_at": "2024-01-15T10:30:00",
                "content": "Learn the basics of machine learning...",
                "transcript": "Welcome to this tutorial on machine learning..."
            }
        }


# ============================================================================
# YouTube Scraper Class
# ============================================================================



class YouTubeScraper:
    """Scraper for YouTube channel RSS feeds with transcript extraction"""
    
    def __init__(self, hours_back: int = 24):
        """
        Initialize YouTube scraper.
        
        Args:
            hours_back: Number of hours to look back for videos (default: 24)
        """
        self.hours_back = hours_back
    
    @staticmethod
    def get_channel_rss_url(channel_id: str) -> str:
        """
        Convert YouTube channel ID to RSS feed URL.
        
        Args:
            channel_id: YouTube channel ID (e.g., 'UC_x5XG1OV2P6uZZ5FSM9Ttw')
        
        Returns:
            RSS feed URL
        """
        return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    
    @staticmethod
    def extract_channel_id_from_url(url: str) -> Optional[str]:
        """
        Extract channel ID from various YouTube URL formats.
        
        Supports:
        - https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID
        - https://www.youtube.com/channel/CHANNEL_ID
        - https://www.youtube.com/@username (handle)
        - https://www.youtube.com/c/channelname
        - https://www.youtube.com/user/username
        - Direct channel ID (starts with UC)
        
        Args:
            url: YouTube URL or channel ID
        
        Returns:
            Channel ID or None if not found
        """
        import requests
        from bs4 import BeautifulSoup
        
        # Direct RSS feed URL
        if "channel_id=" in url:
            return url.split("channel_id=")[1].split("&")[0]
        
        # Direct channel URL
        elif "/channel/" in url:
            return url.split("/channel/")[1].split("/")[0].split("?")[0]
        
        # Direct channel ID
        elif url.startswith("UC"):
            return url
        
        # Handle URL (@username), /c/, or /user/ - need to scrape page
        elif "youtube.com/@" in url or "youtube.com/c/" in url or "youtube.com/user/" in url:
            try:
                logger.info(f"Fetching channel page to extract channel ID: {url}")
                
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                
                # Look for channel ID in page source
                # Method 1: Look for channelId in meta tags or scripts
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try meta tag
                meta_tag = soup.find('meta', {'itemprop': 'channelId'})
                if meta_tag and meta_tag.get('content'):
                    channel_id = meta_tag['content']
                    logger.info(f"✅ Found channel ID: {channel_id}")
                    return channel_id
                
                # Method 2: Look in page source for channel ID pattern
                import re
                # Look for "channelId":"UC..." pattern
                match = re.search(r'"channelId":"(UC[\w-]+)"', response.text)
                if match:
                    channel_id = match.group(1)
                    logger.info(f"✅ Found channel ID: {channel_id}")
                    return channel_id
                
                # Method 3: Look for externalId pattern
                match = re.search(r'"externalId":"(UC[\w-]+)"', response.text)
                if match:
                    channel_id = match.group(1)
                    logger.info(f"✅ Found channel ID: {channel_id}")
                    return channel_id
                
                logger.error(f"❌ Could not extract channel ID from {url}")
                return None
            
            except Exception as e:
                logger.error(f"❌ Error extracting channel ID from {url}: {e}")
                return None
        
        return None
    
    @staticmethod
    def extract_video_id_from_url(url: str) -> Optional[str]:
        """
        Extract video ID from YouTube URL.
        
        Args:
            url: YouTube video URL
        
        Returns:
            Video ID or None if not found
        """
        # Pattern for various YouTube URL formats
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/)([0-9A-Za-z_-]{11})',
            r'(?:watch\?v=)([0-9A-Za-z_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def get_video_transcript(self, video_id: str) -> Optional[str]:
        """
        Get transcript for a YouTube video.
        
        Args:
            video_id: YouTube video ID
        
        Returns:
            Full transcript text or None if unavailable
        """
        try:
            # Try to get transcript (prefers English)
            transcript_list = YouTubeTranscriptApi.get_transcript(
                video_id,
                languages=['en', 'en-US', 'en-GB']
            )
            
            # Combine all transcript segments into full text
            full_transcript = " ".join([segment['text'] for segment in transcript_list])
            
            logger.info(f"✅ Retrieved transcript for video {video_id} ({len(full_transcript)} chars)")
            return full_transcript
        
        except TranscriptsDisabled:
            logger.warning(f"⚠️  Transcripts disabled for video {video_id}")
            return None
        
        except NoTranscriptFound:
            logger.warning(f"⚠️  No transcript found for video {video_id}")
            return None
        
        except VideoUnavailable:
            logger.error(f"❌ Video {video_id} is unavailable")
            return None
        
        except Exception as e:
            logger.error(f"❌ Error getting transcript for {video_id}: {e}")
            return None
    
    def scrape_channel(
        self,
        url: str,
        include_transcripts: bool = True,
        filter_by_time: bool = True
    ) -> List[ChannelVideo]:
        """
        Scrape videos from a YouTube channel RSS feed.
        
        Args:
            url: YouTube channel URL or RSS feed URL
            include_transcripts: Whether to fetch video transcripts
            filter_by_time: Whether to filter videos by time window
        
        Returns:
            List of ChannelVideo Pydantic models with video metadata
        """
        try:
            # Extract channel ID and build RSS URL
            channel_id = self.extract_channel_id_from_url(url)
            if not channel_id:
                # Assume it's already an RSS feed URL
                rss_url = url
            else:
                rss_url = self.get_channel_rss_url(channel_id)
            
            logger.info(f"📺 Fetching YouTube RSS feed: {rss_url}")
            
            # Parse RSS feed
            feed = feedparser.parse(rss_url)
            
            if feed.bozo:
                logger.error(f"❌ Error parsing feed: {feed.bozo_exception}")
                return []
            
            # Calculate cutoff time if filtering
            cutoff_time = None
            if filter_by_time:
                cutoff_time = datetime.utcnow() - timedelta(hours=self.hours_back)
                logger.info(f"⏰ Filtering videos published after: {cutoff_time}")
            
            videos = []
            for entry in feed.entries:
                published_at = self._parse_published_date(entry)
                
                # Filter by time if enabled
                if filter_by_time and published_at and cutoff_time:
                    if published_at < cutoff_time:
                        logger.debug(f"⏭️  Skipping old video: {entry.get('title')} (published {published_at})")
                        continue
                
                video_url = entry.get("link", "")
                video_id = self.extract_video_id_from_url(video_url)
                
                # Get transcript if requested
                transcript = None
                if include_transcripts and video_id:
                    transcript = self.get_video_transcript(video_id)
                
                # Create ChannelVideo Pydantic model
                video = ChannelVideo(
                    title=entry.get("title", "No Title"),
                    url=video_url,
                    video_id=video_id,
                    published_at=published_at,
                    content=entry.get("summary", ""),  # Video description
                    transcript=transcript,
                )
                videos.append(video)
                
                logger.info(f"✅ Scraped: {video.title} (published {published_at})")
            
            logger.info(f"📊 Scraped {len(videos)} videos from YouTube channel")
            return videos
        
        except Exception as e:
            logger.error(f"❌ Error scraping YouTube channel: {e}")
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

if __name__ == "__main__":
    scraper = YouTubeScraper(hours_back=24)
    videos = scraper.scrape_channel("https://www.youtube.com/@Google", include_transcripts=True, filter_by_time=True)
    for video in videos:
        print(video)

