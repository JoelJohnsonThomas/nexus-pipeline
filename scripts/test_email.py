"""
Test email functionality - verify SMTP connection and template rendering.
"""
import sys
import os
from pathlib import Path
import argparse
import logging

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.email.email_sender import EmailSender
from app.email.renderer import get_email_renderer
from app.email.digest_generator import get_digest_generator
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_smtp_connection(recipient: str):
    """Test SMTP connection by sending a test email"""
    logger.info("🧪 Testing SMTP connection...")
    
    sender = EmailSender()
    success = sender.send_test_email(recipient)
    
    if success:
        logger.info("✅ SMTP test passed! Check your inbox.")
        return True
    else:
        logger.error("❌ SMTP test failed. Check your configuration.")
        return False


def test_template_rendering():
    """Test template rendering with sample data"""
    logger.info("🧪 Testing template rendering...")
    
    # Sample article data
    sample_articles = [
        {
            'title': 'Gemini 2.0: Our most capable AI model yet',
            'url': 'https://blog.google/technology/ai/google-gemini-ai-update-december-2024/',
            'published_date': 'December 11, 2024',
            'source_name': 'Google Blog',
            'summary': 'Google has announced Gemini 2.0, their most capable AI model to date. The new model features improved reasoning capabilities, multimodal understanding, and enhanced performance across various tasks.',
            'key_points': [
                'Significantly improved reasoning and problem-solving abilities',
                'Native multimodal capabilities (text, images, audio, video)',
                'Enhanced code generation and debugging features',
                'Better multilingual support'
            ]
        },
        {
            'title': 'Claude 3.5 Sonnet: Enhanced for coding and analysis',
            'url': 'https://www.anthropic.com/news/claude-3-5-sonnet',
            'published_date': 'December 10, 2024',
            'source_name': 'Anthropic',
            'summary': 'Anthropic has released Claude 3.5 Sonnet with major improvements in coding tasks and data analysis. The model shows significant gains in benchmark performance while maintaining safety and reliability.',
            'key_points': [
                '40% improvement on coding benchmarks',
                'Enhanced reasoning for complex analysis tasks',
                'Improved context window handling',
                'Better instruction following'
            ]
        }
    ]
    
    renderer = get_email_renderer()
    html, text = renderer.render_digest(
        articles=sample_articles,
        subscriber_name="Test User",
        subscriber_email="test@example.com"
    )
    
    # Save to files for inspection
    output_dir = Path(__file__).parent.parent / 'temp'
    output_dir.mkdir(exist_ok=True)
    
    html_file = output_dir / 'test_digest.html'
    text_file = output_dir / 'test_digest.txt'
    
    html_file.write_text(html, encoding='utf-8')
    text_file.write_text(text, encoding='utf-8')
    
    logger.info(f"✅ Templates rendered successfully!")
    logger.info(f"   HTML: {html_file}")
    logger.info(f"   Text: {text_file}")
    logger.info(f"   Open the HTML file in a browser to preview")
    
    return True


def test_digest_generation():
    """Test digest generation from database"""
    logger.info("🧪 Testing digest generation from database...")
    
    try:
        generator = get_digest_generator()
        articles = generator.generate_digest(hours_back=168)  # Last week
        
        logger.info(f"✅ Found {len(articles)} articles with summaries")
        
        if articles:
            logger.info(f"   Sample article: {articles[0]['title']}")
        else:
            logger.warning("   No articles found. Run the scraper first!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Digest generation failed: {e}")
        return False


def test_full_email(recipient: str):
    """Send a full test digest email"""
    logger.info(f"🧪 Sending full test digest to {recipient}...")
    
    try:
        # Generate digest
        generator = get_digest_generator()
        articles = generator.generate_digest(hours_back=168)  # Last week
        
        if not articles:
            logger.warning("No articles found, using sample data instead")
            # Use sample data from template test
            articles = [
                {
                    'title': 'Test Article: AI News Update',
                    'url': 'https://example.com',
                    'published_date': datetime.now().strftime('%B %d, %Y'),
                    'source_name': 'Test Source',
                    'summary': 'This is a test article to verify email delivery is working correctly.',
                    'key_points': ['Test point 1', 'Test point 2', 'Test point 3']
                }
            ]
        
        # Render templates
        renderer = get_email_renderer()
        html, text = renderer.render_digest(
            articles=articles,
            subscriber_name="Test Recipient",
            subscriber_email=recipient
        )
        
        # Send email
        sender = EmailSender()
        success = sender.send_digest(recipient, html, text)
        
        if success:
            logger.info(f"✅ Test digest sent successfully to {recipient}")
            logger.info(f"   Included {len(articles)} articles")
        else:
            logger.error("❌ Failed to send test digest")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Full test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description='Test email functionality')
    parser.add_argument('--smtp-test', action='store_true', help='Test SMTP connection')
    parser.add_argument('--template-test', action='store_true', help='Test template rendering')
    parser.add_argument('--digest-test', action='store_true', help='Test digest generation')
    parser.add_argument('--full-test', action='store_true', help='Send full test email')
    parser.add_argument('--recipient', type=str, help='Recipient email for tests')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    
    args = parser.parse_args()
    
    # Default recipient from env
    recipient = args.recipient or os.getenv('EMAIL_RECIPIENT', 'test@example.com')
    
    print("=" * 60)
    print("🧪 AI NEWS AGGREGATOR - EMAIL TESTING")
    print("=" * 60)
    
    results = []
    
    if args.all or args.template_test:
        results.append(("Template Rendering", test_template_rendering()))
    
    if args.all or args.digest_test:
        results.append(("Digest Generation", test_digest_generation()))
    
    if args.all or args.smtp_test:
        results.append(("SMTP Connection", test_smtp_connection(recipient)))
    
    if args.full_test:
        results.append(("Full Email Test", test_full_email(recipient)))
    
    if not any([args.all, args.smtp_test, args.template_test, args.digest_test, args.full_test]):
        # Default: run all tests except full email
        results.append(("Template Rendering", test_template_rendering()))
        results.append(("Digest Generation", test_digest_generation()))
        #results.append(("SMTP Connection", test_smtp_connection(recipient)))
    
    # Print results
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:30s} {status}")
    
    all_passed = all(result[1] for result in results)
    print("=" * 60)
    if all_passed:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the logs above.")
    
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
