"""
Test script for YouTube scraper with transcript extraction.
"""
import logging
import sys
from datetime import datetime

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path
sys.path.insert(0, 'E:/CSE/External/AI_Projects/AI-NEWS-AGGREGATOR')

from app.scrapers.youtube_scraper import YouTubeScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_youtube_scraper():
    """Test YouTube scraper with multiple channels"""
    
    print("=" * 80)
    print("TESTING YOUTUBE SCRAPER WITH TRANSCRIPTS")
    print("=" * 80)
    
    # Test channels (you can modify these)
    test_channels = [
        {
            "name": "Google DeepMind",
            "id": "UCUBmRTq9gqz0wgYj4bFXRQA"
        },
        {
            "name": "Two Minute Papers",
            "id": "UCbfYPyITQ-7l4upoX8nvctg"
        },
        {
            "name": "AI Explained",
            "id": "UCNJ1Ymd5yFuUPtn21xtRbbw"
        }
    ]
    
    # Initialize scraper (last 24 hours)
    scraper = YouTubeScraper(hours_back=24)
    
    print(f"\nLooking for videos from the last 24 hours")
    print(f"Cutoff time: {datetime.utcnow()}\n")
    
    all_videos = []
    
    for channel in test_channels:
        print("\n" + "=" * 80)
        print(f"Testing Channel: {channel['name']}")
        print(f"Channel ID: {channel['id']}")
        print("=" * 80)
        
        # Scrape channel with transcripts and time filtering
        videos = scraper.scrape_channel(
            url=channel['id'],
            include_transcripts=True,
            filter_by_time=True
        )
        
        if not videos:
            print(f"\nNo videos found in the last 24 hours for {channel['name']}")
            continue
        
        print(f"\nFound {len(videos)} video(s) from last 24 hours:\n")
        
        for i, video in enumerate(videos, 1):
            print(f"\n{i}. {video['title']}")
            print(f"   URL: {video['url']}")
            print(f"   Video ID: {video['video_id']}")
            print(f"   Published: {video['published_at']}")
            print(f"   Description: {video['content'][:100]}...")
            
            if video['transcript']:
                transcript_preview = video['transcript'][:200]
                print(f"   Transcript: {transcript_preview}... ({len(video['transcript'])} chars total)")
            else:
                print(f"   Transcript: Not available")
        
        all_videos.extend(videos)
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total channels tested: {len(test_channels)}")
    print(f"Total videos found (last 24h): {len(all_videos)}")
    print(f"Videos with transcripts: {sum(1 for v in all_videos if v['transcript'])}")
    print(f"Videos without transcripts: {sum(1 for v in all_videos if not v['transcript'])}")
    
    return all_videos


def test_specific_video():
    """Test transcript extraction for a specific video"""
    
    print("\n" + "=" * 80)
    print("TESTING SPECIFIC VIDEO TRANSCRIPT")
    print("=" * 80)
    
    # Example video ID (you can change this)
    video_id = input("\nEnter a YouTube video ID (or press Enter to skip): ").strip()
    
    if not video_id:
        print("Skipped.")
        return
    
    scraper = YouTubeScraper()
    transcript = scraper.get_video_transcript(video_id)
    
    if transcript:
        print(f"\nTranscript retrieved ({len(transcript)} characters)")
        print(f"\nFirst 500 characters:")
        print("-" * 80)
        print(transcript[:500])
        print("-" * 80)
    else:
        print("\nCould not retrieve transcript")


def test_without_time_filter():
    """Test scraper without time filtering to see all recent videos"""
    
    print("\n" + "=" * 80)
    print("TESTING WITHOUT TIME FILTER (All Recent Videos)")
    print("=" * 80)
    
    channel_id = "UCbfYPyITQ-7l4upoX8nvctg"  # Two Minute Papers
    
    scraper = YouTubeScraper()
    videos = scraper.scrape_channel(
        url=channel_id,
        include_transcripts=False,  # Skip transcripts for speed
        filter_by_time=False  # Get all videos from RSS feed
    )
    
    print(f"\nFound {len(videos)} total videos in RSS feed\n")
    
    for i, video in enumerate(videos[:5], 1):  # Show first 5
        print(f"{i}. {video['title']}")
        print(f"   Published: {video['published_at']}")
        print()


if __name__ == "__main__":
    try:
        # Main test
        videos = test_youtube_scraper()
        
        # Test specific video
        test_specific_video()
        
        # Test without filter
        print("\n" + "=" * 80)
        response = input("\nTest without time filter? (y/n): ").strip().lower()
        if response == 'y':
            test_without_time_filter()
        
        print("\nTesting complete!")
    
    except KeyboardInterrupt:
        print("\n\nTesting interrupted")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)
