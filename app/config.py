"""
Configuration management for AI News Aggregator.
Uses Pydantic BaseSettings for type validation and fast-fail on missing required fields.
"""
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = Field(..., description="PostgreSQL connection URL")

    # Redis
    REDIS_HOST: str = Field("localhost", description="Redis host")
    REDIS_PORT: int = Field(6379, description="Redis port")

    # Gemini API
    GEMINI_API_KEY: str = Field(..., description="Google Gemini API key")
    GEMINI_MODEL: str = Field("gemini-1.5-flash", description="Gemini model name")

    # Email
    EMAIL_SENDER: str = Field(..., description="SMTP sender address")
    EMAIL_PASSWORD: str = Field(..., description="SMTP sender password")
    EMAIL_RECIPIENT: str = Field(..., description="Default digest recipient")
    SMTP_HOST: str = Field("smtp.gmail.com", description="SMTP host")
    SMTP_PORT: int = Field(587, description="SMTP port")

    # Digest / pipeline
    DIGEST_HOURS_BACK: int = Field(24, description="Hours back to include in digest")
    TIMEZONE: str = Field("America/New_York", description="Timezone for scheduling")
    MAX_RETRIES: int = Field(3, description="Max pipeline job retries before dead-lettering")
    JOB_TIMEOUT: int = Field(600, description="RQ job timeout in seconds")
    CACHE_TTL: int = Field(3600, description="Redis cache TTL in seconds")
    EMBEDDING_MODEL: str = Field("all-MiniLM-L6-v2", description="sentence-transformers model")

    model_config = {"env_file": ".env", "populate_by_name": True, "extra": "ignore"}


# Module-level singleton — raises ValidationError at import time if required fields are missing
settings = Settings()

# Legacy alias so existing callers using `from app.config import config` still work
# while we migrate them incrementally.
config = settings
