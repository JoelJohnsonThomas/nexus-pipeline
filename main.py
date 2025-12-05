"""
Main orchestration script for AI News Aggregator.
"""
import logging
import sys
from datetime import datetime
import argparse

from app.config import config
from app.database import init_db
from app.scrapers.scraper_manager import ScraperManager
from app.llm.digest_generator import DigestGenerator
from app.email.email_sender import EmailSender

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('news_aggregator.log')
    ]
)

logger = logging.getLogger(__name__)


def run_daily_digest():
    """
    Main function to run the complete daily digest workflow:
    1. Scrape all sources
    2. Generate digest with LLM
    3. Send email
    """
    logger.info("=" * 60)
    logger.info("🚀 Starting AI News Aggregator Daily Digest")
    logger.info("=" * 60)
    
    try:
        # Validate configuration
        logger.info("Validating configuration...")
        config.validate()
        logger.info("✅ Configuration valid")
        
        # Step 1: Scrape all sources
        logger.info("\n📡 Step 1: Scraping news sources...")
        scraper = ScraperManager()
        scrape_stats = scraper.scrape_all_sources()
        
        logger.info(f"""
        Scraping Results:
        - Sources processed: {scrape_stats['sources_processed']}
        - Articles found: {scrape_stats['articles_found']}
        - New articles: {scrape_stats['articles_new']}
        - Duplicates skipped: {scrape_stats['articles_duplicate']}
        - Errors: {scrape_stats['errors']}
        """)
        
        if scrape_stats['articles_new'] == 0:
            logger.warning("⚠️  No new articles found. Skipping digest generation.")
            return
        
        # Step 2: Generate digest
        logger.info("\n🤖 Step 2: Generating digest with LLM...")
        digest_gen = DigestGenerator()
        digest_result = digest_gen.generate_digest()
        
        if not digest_result['success']:
            logger.error(f"❌ Digest generation failed: {digest_result.get('message')}")
            return
        
        logger.info(f"""
        Digest Generated:
        - Total articles: {digest_result['total_articles']}
        - Total sources: {digest_result['total_sources']}
        """)
        
        # Step 3: Send email
        logger.info("\n📧 Step 3: Sending digest email...")
        email_sender = EmailSender()
        
        success = email_sender.send_digest(
            recipient=config.EMAIL_RECIPIENT,
            html_content=digest_result['html_content'],
            text_content=digest_result['text_content']
        )
        
        if success:
            logger.info("✅ Daily digest completed successfully!")
        else:
            logger.error("❌ Failed to send digest email")
        
        logger.info("=" * 60)
        logger.info(f"🏁 Workflow completed at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        logger.info("=" * 60)
    
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        logger.error("Please check your .env file")
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}", exc_info=True)
        sys.exit(1)


def test_scraping():
    """Test scraping functionality"""
    logger.info("🧪 Testing scraping functionality...")
    scraper = ScraperManager()
    stats = scraper.scrape_all_sources()
    logger.info(f"Scraping test complete: {stats}")


def test_digest():
    """Test digest generation"""
    logger.info("🧪 Testing digest generation...")
    digest_gen = DigestGenerator()
    result = digest_gen.generate_digest()
    
    if result['success']:
        logger.info("✅ Digest generated successfully")
        logger.info(f"Total articles: {result['total_articles']}")
        print("\n" + "=" * 60)
        print("TEXT PREVIEW:")
        print("=" * 60)
        print(result['text_content'][:500] + "...")
    else:
        logger.error(f"❌ Digest generation failed: {result.get('message')}")


def test_email():
    """Test email sending"""
    logger.info("🧪 Testing email configuration...")
    config.validate()
    
    email_sender = EmailSender()
    success = email_sender.send_test_email(config.EMAIL_RECIPIENT)
    
    if success:
        logger.info("✅ Test email sent successfully!")
    else:
        logger.error("❌ Failed to send test email")


def main():
    """Main entry point with CLI"""
    parser = argparse.ArgumentParser(description="AI News Aggregator")
    parser.add_argument(
        '--mode',
        choices=['run', 'test-scrape', 'test-digest', 'test-email', 'init-db'],
        default='run',
        help='Operation mode'
    )
    
    args = parser.parse_args()
    
    if args.mode == 'run':
        run_daily_digest()
    elif args.mode == 'test-scrape':
        test_scraping()
    elif args.mode == 'test-digest':
        test_digest()
    elif args.mode == 'test-email':
        test_email()
    elif args.mode == 'init-db':
        logger.info("Initializing database...")
        init_db()


if __name__ == "__main__":
    main()
