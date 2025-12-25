"""
Seed initial email subscription for testing.
"""
import sys
import os
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.email.subscription_service import get_subscription_service
from app.database import EmailFrequency
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_subscription(email: str, name: str = None, frequency: str = 'daily'):
    """
    Create an email subscription.
    
    Args:
        email: Email address
        name: Subscriber name (optional)
        frequency: Email frequency (daily, weekly)
    """
    logger.info("🌱 Seeding email subscription...")
    
    # Map string to enum
    freq_map = {
        'daily': EmailFrequency.DAILY,
        'weekly': EmailFrequency.WEEKLY
    }
    freq_enum = freq_map.get(frequency.lower(), EmailFrequency.DAILY)
    
    service = get_subscription_service()
    subscription = service.create_subscription(
        email=email,
        name=name,
        frequency=freq_enum
    )
    
    if subscription:
        logger.info(f"✅ Subscription created:")
        logger.info(f"   Email: {subscription.email}")
        logger.info(f"   Name: {subscription.name or 'Not provided'}")
        logger.info(f"   Frequency: {subscription.frequency.value}")
        logger.info(f"   Active: {subscription.active}")
        logger.info(f"   ID: {subscription.id}")
    else:
        logger.error("❌ Failed to create subscription")


def main():
    print("=" * 60)
    print("🌱 AI NEWS AGGREGATOR - SEED SUBSCRIPTION")
    print("=" * 60)
    
    # Get email from environment or prompt
    default_email = os.getenv('EMAIL_RECIPIENT')
    
    if default_email:
        logger.info(f"Using email from .env: {default_email}")
        email = default_email
        name = input("Enter your name (optional, press Enter to skip): ").strip() or None
    else:
        email = input("Enter email address: ").strip()
        if not email:
            logger.error("Email address is required")
            return
        name = input("Enter name (optional, press Enter to skip): ").strip() or None
    
    frequency = input("Enter frequency (daily/weekly, default: daily): ").strip() or 'daily'
    
    print("")
    seed_subscription(email, name, frequency)
    
    print("")
    print("=" * 60)
    print("✅ Subscription seeding complete!")
    print("=" * 60)
    print("")
    print("Next steps:")
    print("1. Test email sending:")
    print(f"   python scripts/send_digest_now.py --email {email}")
    print("")
    print("2. Or run full email test:")
    print(f"   python scripts/test_email.py --full-test --recipient {email}")


if __name__ == "__main__":
    main()
