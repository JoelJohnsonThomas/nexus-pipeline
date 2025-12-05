"""
SQLAlchemy models for AI News Aggregator.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class SourceType(enum.Enum):
    """Enum for source types"""
    YOUTUBE = "youtube"
    BLOG = "blog"


class Source(Base):
    """
    Model for news sources (YouTube channels or blogs).
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
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)
    title = Column(String(512), nullable=False)
    url = Column(String(512), nullable=False, unique=True)
    content = Column(Text, nullable=True)  # Full content for blogs, description for YouTube
    published_at = Column(DateTime, nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    included_in_digest = Column(Boolean, default=False, nullable=False)
    
    # Relationship to source
    source = relationship("Source", back_populates="articles")

    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title[:50]}...', source_id={self.source_id})>"
