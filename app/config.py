"""
Configuration management for AI News Aggregator.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration"""
    
    # Database
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://newsaggregator:newspassword@localhost:5433/newsaggregator"
    )
    
    # 
    # 
    #  Gemini API
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    
    # Email Configuration
    EMAIL_SENDER = os.getenv("EMAIL_SENDER")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT")
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    
    # Digest Configuration
    DIGEST_HOURS_BACK = int(os.getenv("DIGEST_HOURS_BACK", "24"))
    TIMEZONE = os.getenv("TIMEZONE", "America/New_York")
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        errors = []
        
        if not cls.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY is required")
        
        if not cls.EMAIL_SENDER:
            errors.append("EMAIL_SENDER is required")
        
        if not cls.EMAIL_PASSWORD:
            errors.append("EMAIL_PASSWORD is required")
        
        if not cls.EMAIL_RECIPIENT:
            errors.append("EMAIL_RECIPIENT is required")
        
        if errors:
            raise ValueError(
                "Missing required configuration:\n" + "\n".join(f"  - {e}" for e in errors)
            )
        
        return True


# Create config instance
config = Config()
