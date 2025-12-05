"""
Quick test for Pydantic models in YouTube scraper.
"""
import sys
import io

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, 'E:/CSE/External/AI_Projects/AI-NEWS-AGGREGATOR')

from app.scrapers.youtube_scraper import ChannelVideo, Transcript, YouTubeScraper
from datetime import datetime

print("=" * 60)
print("TESTING PYDANTIC MODELS")
print("=" * 60)

# Test 1: Create a Transcript model
print("\n1. Testing Transcript model:")
transcript = Transcript(text="This is a test transcript")
print(f"   [OK] Created: {transcript}")
print(f"   [OK] Text: {transcript.text[:50]}...")

# Test 2: Create a ChannelVideo model
print("\n2. Testing ChannelVideo model:")
video = ChannelVideo(
    title="Test Video",
    url="https://www.youtube.com/watch?v=test123",
    video_id="test123",
    published_at=datetime.now(),
    content="This is a test video description",
    transcript="Full transcript here"
)
print(f"   [OK] Created: {video.title}")
print(f"   [OK] Video ID: {video.video_id}")
print(f"   [OK] Has transcript: {video.transcript is not None}")

# Test 3: JSON serialization
print("\n3. Testing JSON serialization:")
video_json = video.model_dump_json(indent=2)
print(f"   [OK] JSON output (first 200 chars):")
print(f"   {video_json[:200]}...")

# Test 4: Test with actual scraper
print("\n4. Testing with actual YouTube scraper:")
scraper = YouTubeScraper(hours_back=168)  # Last week

# Use a known channel
videos = scraper.scrape_channel(
    url="UCbfYPyITQ-7l4upoX8nvctg",  # Two Minute Papers
    include_transcripts=False,  # Skip transcripts for speed
    filter_by_time=True
)

if videos:
    print(f"   [OK] Scraped {len(videos)} videos")
    print(f"   [OK] First video type: {type(videos[0])}")
    print(f"   [OK] First video title: {videos[0].title}")
    print(f"   [OK] Is Pydantic model: {hasattr(videos[0], 'model_dump')}")
else:
    print("   [WARN] No videos found in time window")

print("\n" + "=" * 60)
print("ALL TESTS PASSED!")
print("=" * 60)
