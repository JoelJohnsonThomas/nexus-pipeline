"""
Subscription management service for email subscriptions.
"""
from typing import List, Optional
from sqlalchemy import and_
from app.database import SessionLocal, EmailSubscription, EmailFrequency
import logging
import re

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Manages email subscriptions"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def __del__(self):
        """Close database session"""
        if hasattr(self, 'db'):
            self.db.close()
    
    def get_active_subscribers(self) -> List[EmailSubscription]:
        """
        Get all active email subscriptions.
        
        Returns:
            List of active EmailSubscription records
        """
        subscribers = (
            self.db.query(EmailSubscription)
            .filter(EmailSubscription.active == True)
            .all()
        )
        
        logger.info(f"Found {len(subscribers)} active subscribers")
        return subscribers
    
    def get_subscriber_by_email(self, email: str) -> Optional[EmailSubscription]:
        """
        Get subscriber by email address.
        
        Args:
            email: Email address to look up
            
        Returns:
            EmailSubscription or None if not found
        """
        return (
            self.db.query(EmailSubscription)
            .filter(EmailSubscription.email == email)
            .first()
        )
    
    def create_subscription(
        self,
        email: str,
        name: Optional[str] = None,
        frequency: EmailFrequency = EmailFrequency.DAILY
    ) -> Optional[EmailSubscription]:
        """
        Create a new email subscription.
        
        Args:
            email: Subscriber email address
            name: Subscriber name (optional)
            frequency: Email frequency (default: daily)
            
        Returns:
            Created EmailSubscription or None if validation fails
        """
        # Validate email
        if not self.validate_email(email):
            logger.error(f"Invalid email address: {email}")
            return None
        
        # Check if already exists
        existing = self.get_subscriber_by_email(email)
        if existing:
            logger.warning(f"Subscription already exists for {email}")
            return existing
        
        # Create new subscription
        try:
            subscription = EmailSubscription(
                email=email,
                name=name,
                frequency=frequency,
                active=True
            )
            self.db.add(subscription)
            self.db.commit()
            self.db.refresh(subscription)
            
            logger.info(f"✅ Created subscription for {email}")
            return subscription
            
        except Exception as e:
            logger.error(f"Failed to create subscription: {e}")
            self.db.rollback()
            return None
    
    def update_frequency(
        self,
        subscriber_id: int,
        frequency: EmailFrequency
    ) -> bool:
        """
        Update subscription frequency.
        
        Args:
            subscriber_id: ID of subscription to update
            frequency: New frequency setting
            
        Returns:
            True if updated successfully
        """
        try:
            subscription = self.db.query(EmailSubscription).get(subscriber_id)
            if not subscription:
                logger.error(f"Subscription {subscriber_id} not found")
                return False
            
            subscription.frequency = frequency
            self.db.commit()
            
            logger.info(f"Updated frequency for subscription {subscriber_id} to {frequency.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update frequency: {e}")
            self.db.rollback()
            return False
    
    def unsubscribe(self, subscriber_id: int) -> bool:
        """
        Mark subscription as inactive (unsubscribe).
        
        Args:
            subscriber_id: ID of subscription to deactivate
            
        Returns:
            True if unsubscribed successfully
        """
        try:
            subscription = self.db.query(EmailSubscription).get(subscriber_id)
            if not subscription:
                logger.error(f"Subscription {subscriber_id} not found")
                return False
            
            subscription.active = False
            self.db.commit()
            
            logger.info(f"Unsubscribed: {subscription.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unsubscribe: {e}")
            self.db.rollback()
            return False
    
    def reactivate(self, subscriber_id: int) -> bool:
        """
        Reactivate an inactive subscription.
        
        Args:
            subscriber_id: ID of subscription to reactivate
            
        Returns:
            True if reactivated successfully
        """
        try:
            subscription = self.db.query(EmailSubscription).get(subscriber_id)
            if not subscription:
                logger.error(f"Subscription {subscriber_id} not found")
                return False
            
            subscription.active = True
            self.db.commit()
            
            logger.info(f"Reactivated subscription: {subscription.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reactivate: {e}")
            self.db.rollback()
            return False
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email address format.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if valid email format
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None


def get_subscription_service() -> SubscriptionService:
    """Factory function to create SubscriptionService"""
    return SubscriptionService()
