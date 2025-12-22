"""
Database package for AI News Aggregator.
Provides SQLAlchemy models, database configuration, and CRUD operations.
"""
from app.database.base import Base, engine, SessionLocal, get_db_session, init_db, drop_all_tables
from app.database.models import Source, Article, SourceType, OpenAIArticle, AnthropicArticle, YouTubeVideo
from app.database.models_extended import (
    ArticleSummary, ArticleEmbedding, EmailSubscription, EmailDelivery,
    ProcessingQueue, ProcessingStatus, EmailFrequency, DeliveryStatus
)

__all__ = [
    "Base",
    "engine", 
    "SessionLocal",
    "get_db_session",
    "init_db",
    "drop_all_tables",
    "Source",
    "Article",
    "SourceType",
    "OpenAIArticle",
    "AnthropicArticle",
    "YouTubeVideo",
    # Extended models
    "ArticleSummary",
    "ArticleEmbedding",
    "EmailSubscription",
    "EmailDelivery",
    "ProcessingQueue",
    "ProcessingStatus",
    "EmailFrequency",
    "DeliveryStatus",
]
