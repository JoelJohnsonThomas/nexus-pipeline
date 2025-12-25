"""
Send digest email now (manual trigger for testing or one-off sends).
"""
import sys
import os
from pathlib import Path
import argparse
import logging

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.email.digest_generator import get_digest_generator
from app.email.renderer import get_email_renderer
from app.email.email_sender import EmailSender
from app.email.subscription_service import get_subscription_service

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def send_digest_to_subscriber(subscriber, hours_back=24):
    """Send digest to a single subscriber"""
    try:
        logger.info(f"Generating digest for {subscriber.email}...")
        
        # Generate digest
        generator = get_digest_generator()
        articles = generator.generate_digest(hours_back=hours_back)
        
        if not articles:
            logger.warning(f"No articles found in last {hours_back} hours. Skipping {subscriber.email}")
            return False
        
        logger.info(f"Found {len(articles)} articles for digest")
        
        # Render email
        renderer = get_email_renderer()
        html, text = renderer.render_digest(
            articles=articles,
            subscriber_name=subscriber.name,
            subscriber_email=subscriber.email
        )
        
        # Send email
        sender = EmailSender()
        success = sender.send_digest(subscriber.email, html, text)
        
        if success:
            logger.info(f"✅ Digest sent to {subscriber.email} ({len(articles)} articles)")
        else:
            logger.error(f"❌ Failed to send digest to {subscriber.email}")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Error sending to {subscriber.email}: {e}")
        import traceback
        traceback.print_exc()
        return False


def send_digest_to_all(hours_back=24):
    """Send digest to all active subscribers"""
    logger.info("📧 Sending digest to all active subscribers...")
    
    # Get all active subscribers
    sub_service = get_subscription_service()
    subscribers = sub_service.get_active_subscribers()
    
    if not subscribers:
        logger.warning("No active subscribers found")
        return
    
    logger.info(f"Found {len(subscribers)} active subscriber(s)")
    
    # Send to each subscriber
    sent_count = 0
    failed_count = 0
    
    for subscriber in subscribers:
        success = send_digest_to_subscriber(subscriber, hours_back)
        if success:
            sent_count += 1
        else:
            failed_count += 1
    
    # Print summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("📊 DIGEST SEND SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total subscribers: {len(subscribers)}")
    logger.info(f"✅ Sent successfully: {sent_count}")
    logger.info(f"❌ Failed: {failed_count}")
    logger.info("=" * 60)


def send_digest_to_email(email: str, hours_back=24):
    """Send digest to a specific email address"""
    logger.info(f"📧 Sending digest to {email}...")
    
    # Check if subscriber exists
    sub_service = get_subscription_service()
    subscriber = sub_service.get_subscriber_by_email(email)
    
    if not subscriber:
        logger.warning(f"Email {email} not found in subscriptions")
        logger.info("Creating temporary subscription for testing...")
        
        # Create mock subscriber object for testing
        class MockSubscriber:
            def __init__(self, email):
                self.email = email
                self.name = email.split('@')[0].capitalize()
        
        subscriber = MockSubscriber(email)
    
    success = send_digest_to_subscriber(subscriber, hours_back)
    
    if success:
        logger.info(f"🎉 Digest sent successfully to {email}")
    else:
        logger.error(f"❌ Failed to send digest to {email}")


def main():
    parser = argparse.ArgumentParser(description='Send digest emails now')
    parser.add_argument('--all', action='store_true', help='Send to all active subscribers')
    parser.add_argument('--email', type=str, help='Send to specific email address')
    parser.add_argument('--hours', type=int, default=24, help='Hours to look back for articles (default: 24)')
    parser.add_argument('--test', action='store_true', help='Send test using EMAIL_RECIPIENT from .env')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("📧 AI NEWS AGGREGATOR - SEND DIGEST")
    print("=" * 60)
    print(f"Looking back: {args.hours} hours")
    print("=" * 60)
    print("")
    
    if args.all:
        send_digest_to_all(args.hours)
    elif args.email:
        send_digest_to_email(args.email, args.hours)
    elif args.test:
        # Use EMAIL_RECIPIENT from environment
        test_email = os.getenv('EMAIL_RECIPIENT')
        if not test_email:
            logger.error("EMAIL_RECIPIENT not set in .env file")
            sys.exit(1)
        send_digest_to_email(test_email, args.hours)
    else:
        logger.error("Please specify --all, --email, or --test")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
