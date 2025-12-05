"""
Email sending functionality using Gmail SMTP.
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional

from app.config import config

logger = logging.getLogger(__name__)


class EmailSender:
    """Sends emails via Gmail SMTP"""
    
    def __init__(self):
        """Initialize email sender with Gmail SMTP configuration"""
        self.smtp_host = config.SMTP_HOST
        self.smtp_port = config.SMTP_PORT
        self.sender_email = config.EMAIL_SENDER
        self.sender_password = config.EMAIL_PASSWORD
        
        logger.info(f"Initialized EmailSender with SMTP: {self.smtp_host}:{self.smtp_port}")
    
    def send_digest(
        self,
        recipient: str,
        html_content: str,
        text_content: str,
        subject: Optional[str] = None
    ) -> bool:
        """
        Send daily digest email.
        
        Args:
            recipient: Recipient email address
            html_content: HTML formatted digest
            text_content: Plain text formatted digest
            subject: Email subject (default: generated from date)
        
        Returns:
            True if sent successfully, False otherwise
        """
        if subject is None:
            subject = f"🤖 AI News Daily Digest - {datetime.utcnow().strftime('%B %d, %Y')}"
        
        try:
            logger.info(f"Sending digest email to {recipient}")
            
            # Create message
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = self.sender_email
            message['To'] = recipient
            
            # Attach both plain text and HTML versions
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            html_part = MIMEText(html_content, 'html', 'utf-8')
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()  # Upgrade to secure connection
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)
            
            logger.info(f"✅ Digest email sent successfully to {recipient}")
            return True
        
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ SMTP Authentication failed: {e}")
            logger.error("Please check your EMAIL_SENDER and EMAIL_PASSWORD in .env")
            logger.error("For Gmail, you need to use an App Password, not your regular password")
            logger.error("Generate one at: https://myaccount.google.com/apppasswords")
            return False
        
        except smtplib.SMTPException as e:
            logger.error(f"❌ SMTP error occurred: {e}")
            return False
        
        except Exception as e:
            logger.error(f"❌ Error sending email: {e}")
            return False
    
    def send_test_email(self, recipient: str) -> bool:
        """
        Send a test email to verify configuration.
        
        Args:
            recipient: Recipient email address
        
        Returns:
            True if sent successfully, False otherwise
        """
        subject = "🧪 AI News Aggregator - Test Email"
        
        html_content = """
        <h1 style="color: #2c3e50;">✅ Email Configuration Test</h1>
        <p style="color: #34495e; font-family: Arial, sans-serif;">
            Congratulations! Your AI News Aggregator email configuration is working correctly.
        </p>
        <p style="color: #7f8c8d; font-family: Arial, sans-serif;">
            You will receive your daily AI news digest at this email address.
        </p>
        """
        
        text_content = """
        ✅ EMAIL CONFIGURATION TEST
        
        Congratulations! Your AI News Aggregator email configuration is working correctly.
        
        You will receive your daily AI news digest at this email address.
        """
        
        return self.send_digest(recipient, html_content, text_content, subject)
