"""
Simple utility to get YouTube video transcripts.
"""
from youtube_transcript_api import YouTubeTranscriptApi
from typing import Optional


def get_transcript(video_id: str) -> Optional[str]:
    """
    Get transcript for a YouTube video in text format.
    
    Args:
        video_id: YouTube video ID (e.g., 'NBQBw_jaEy8')
    
    Returns:
        Full transcript as text, or None if unavailable
    
    Example:
        >>> transcript = get_transcript('NBQBw_jaEy8')
        >>> if transcript:
        >>>     print(transcript)
    """
    try:
        # Create API instance and fetch transcript
        api = YouTubeTranscriptApi()
        result = api.fetch(video_id)
        
        # Extract text from snippets
        if hasattr(result, 'snippets'):
            full_transcript = " ".join([snippet.text for snippet in result.snippets])
            return full_transcript
        
        # Fallback
        print(f"Unexpected result format: {type(result)}")
        return None
    
    except Exception as e:
        print(f"Error getting transcript: {e}")
        return None


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        video_id = sys.argv[1]
    else:
        video_id = input("Enter YouTube video ID: ").strip()
    
    if not video_id:
        print("No video ID provided")
        sys.exit(1)
    
    print(f"\nFetching transcript for video: {video_id}")
    print("-" * 60)
    
    transcript = get_transcript(video_id)
    
    if transcript:
        print(f"\nTranscript ({len(transcript)} characters):")
        print("=" * 60)
        # Show first 500 chars
        preview = transcript[:500] + "..." if len(transcript) > 500 else transcript
        print(preview)
        print("=" * 60)
        print(f"\nFull transcript length: {len(transcript)} characters")
    else:
        print("\nCould not retrieve transcript")
