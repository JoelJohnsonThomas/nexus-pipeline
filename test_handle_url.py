"""
Quick test for YouTube handle URL support.
"""
import logging
import sys

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, 'E:/CSE/External/AI_Projects/AI-NEWS-AGGREGATOR')

from app.scrapers.youtube_scraper import YouTubeScraper

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

def test_handle_urls():
    """Test various YouTube URL formats"""
    
    print("=" * 80)
    print("TESTING YOUTUBE HANDLE URL SUPPORT")
    print("=" * 80)
    
    test_urls = [
        {
            "name": "Google Handle",
            "url": "https://www.youtube.com/@Google",
            "expected": "Starts with UC"
        },
        {
            "name": "Direct Channel ID",
            "url": "UCbfYPyITQ-7l4upoX8nvctg",
            "expected": "UCbfYPyITQ-7l4upoX8nvctg"
        },
        {
            "name": "Channel URL",
            "url": "https://www.youtube.com/channel/UCbfYPyITQ-7l4upoX8nvctg",
            "expected": "UCbfYPyITQ-7l4upoX8nvctg"
        },
        {
            "name": "RSS Feed URL",
            "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCbfYPyITQ-7l4upoX8nvctg",
            "expected": "UCbfYPyITQ-7l4upoX8nvctg"
        }
    ]
    
    scraper = YouTubeScraper()
    
    for test in test_urls:
        print(f"\n{'-' * 80}")
        print(f"Testing: {test['name']}")
        print(f"URL: {test['url']}")
        print(f"Expected: {test['expected']}")
        
        channel_id = scraper.extract_channel_id_from_url(test['url'])
        
        if channel_id:
            print(f"Result: {channel_id}")
            
            if test['expected'] == "Starts with UC":
                if channel_id.startswith("UC"):
                    print("Status: PASS")
                else:
                    print("Status: FAIL - Does not start with UC")
            elif channel_id == test['expected']:
                print("Status: PASS")
            else:
                print(f"Status: FAIL - Expected {test['expected']}")
        else:
            print("Result: None")
            print("Status: FAIL - Could not extract channel ID")
    
    print("\n" + "=" * 80)
    print("Testing complete!")
    print("=" * 80)


def test_scrape_with_handle():
    """Test scraping with a handle URL"""
    
    print("\n" + "=" * 80)
    print("TESTING SCRAPING WITH HANDLE URL")
    print("=" * 80)
    
    scraper = YouTubeScraper(hours_back=168)  # Last week
    
    # Test with @Google handle
    print("\nScraping @Google channel...")
    videos = scraper.scrape_channel(
        url="https://www.youtube.com/@Google",
        include_transcripts=False,  # Skip transcripts for speed
        filter_by_time=True
    )
    
    if videos:
        print(f"\nFound {len(videos)} video(s) from last week:")
        for i, video in enumerate(videos[:3], 1):
            print(f"\n{i}. {video['title']}")
            print(f"   Published: {video['published_at']}")
            print(f"   URL: {video['url']}")
    else:
        print("\nNo videos found in the time window")


if __name__ == "__main__":
    try:
        # Test URL extraction
        test_handle_urls()
        
        # Test actual scraping
        response = input("\nTest scraping with handle URL? (y/n): ").strip().lower()
        if response == 'y':
            test_scrape_with_handle()
        
        print("\nAll tests complete!")
    
    except KeyboardInterrupt:
        print("\n\nTesting interrupted")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
