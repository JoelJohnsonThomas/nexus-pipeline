"""
SQLAlchemy models for AI News Aggregator.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from app.database.base import Base


class SourceType(enum.Enum):
    """Enum for source types"""
    YOUTUBE = "youtube"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    BLOG = "blog"


class Source(Base):
    """
    Model for news sources (YouTube channels, OpenAI, Anthropic, or blogs).
    """
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    source_type = Column(Enum(SourceType), nullable=False)
    url = Column(String(512), nullable=False, unique=True)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship to articles
    articles = relationship("Article", back_populates="source", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Source(id={self.id}, name='{self.name}', type={self.source_type.value})>"


class Article(Base):
    """
    Model for scraped articles/videos.
    """
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False, index=True)
    title = Column(String(512), nullable=False)
    url = Column(String(512), nullable=False, unique=True, index=True)
    content = Column(Text, nullable=True)  # Full content/description/transcript
    published_at = Column(DateTime, nullable=True, index=True)
    scraped_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Additional metadata
    video_id = Column(String(128), nullable=True)  # For YouTube videos
    category = Column(String(128), nullable=True)  # For Anthropic (research/engineering/news)
    
    # Relationship to source
    source = relationship("Source", back_populates="articles")

    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title[:50]}...', source_id={self.source_id})>"


class OpenAIArticle(Base):
    """
    Model for OpenAI articles.
    """
    __tablename__ = "openai_articles"

    guid = Column(String(512), primary_key=True, index=True)
    title = Column(String(512), nullable=False)
    url = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    published_at = Column(DateTime, nullable=True)
    category = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<OpenAIArticle(guid='{self.guid}', title='{self.title[:50]}...')>"


class AnthropicArticle(Base):
    """
    Model for Anthropic articles.
    """
    __tablename__ = "anthropic_articles"

    guid = Column(String(512), primary_key=True, index=True)
    title = Column(String(512), nullable=False)
    url = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    published_at = Column(DateTime, nullable=True)
    category = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<AnthropicArticle(guid='{self.guid}', title='{self.title[:50]}...')>"


class YouTubeVideo(Base):
    """
    Model for YouTube videos.
    """
    __tablename__ = "youtube_videos"

    guid = Column(String(512), primary_key=True, index=True)
    title = Column(String(512), nullable=False)
    url = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    published_at = Column(DateTime, nullable=True)
    category = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<YouTubeVideo(guid='{self.guid}', title='{self.title[:50]}...')>"
