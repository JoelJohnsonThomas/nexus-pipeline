"""
Digest generator - fetches and formats articles for email digest.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy import and_
from app.database import SessionLocal, Article, ArticleSummary, Source
import logging

logger = logging.getLogger(__name__)


class DigestGenerator:
    """Generates email digests from recent articles"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def __del__(self):
        """Close database session"""
        if hasattr(self, 'db'):
            self.db.close()
    
    def generate_digest(self, hours_back: int = 24) -> List[Dict]:
        """
        Generate digest from articles in the last N hours.
        
        Args:
            hours_back: How many hours back to look for articles
            
        Returns:
            List of formatted article dicts ready for email template
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        
        # Fetch articles with summaries from the time period
        articles_with_summaries = (
            self.db.query(Article, ArticleSummary, Source)
            .join(ArticleSummary, Article.id == ArticleSummary.article_id)
            .join(Source, Article.source_id == Source.id)
            .filter(Article.published_at >= cutoff_time)
            .order_by(Article.published_at.desc())
            .all()
        )
        
        logger.info(f"Found {len(articles_with_summaries)} articles with summaries from last {hours_back} hours")
        
        # Format for email template
        formatted_articles = []
        for article, summary, source in articles_with_summaries:
            formatted_articles.append({
                'title': article.title,
                'url': article.url,
                'published_date': article.published_at.strftime('%B %d, %Y') if article.published_at else 'Unknown',
                'source_name': source.name,
                'summary': summary.summary,
                'key_points': summary.key_points if summary.key_points else []
            })
        
        return formatted_articles
    
    def fetch_recent_articles(self, since_datetime: datetime) -> List[Article]:
        """
        Fetch articles published after a specific datetime.
        
        Args:
            since_datetime: Only return articles after this time
            
        Returns:
            List of Article model instances
        """
        articles = (
            self.db.query(Article)
            .filter(Article.published_at >= since_datetime)
            .order_by(Article.published_at.desc())
            .all()
        )
        
        logger.info(f"Fetched {len(articles)} articles since {since_datetime}")
        return articles
    
    def get_articles_by_source(self, source_name: str, hours_back: int = 24) -> List[Dict]:
        """
        Get articles from a specific source.
        
        Args:
            source_name: Name of the source to filter by
            hours_back: Hours to look back
            
        Returns:
            List of formatted article dicts
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        
        articles_with_summaries = (
            self.db.query(Article, ArticleSummary, Source)
            .join(ArticleSummary, Article.id == ArticleSummary.article_id)
            .join(Source, Article.source_id == Source.id)
            .filter(
                and_(
                    Article.published_at >= cutoff_time,
                    Source.name == source_name
                )
            )
            .order_by(Article.published_at.desc())
            .all()
        )
        
        formatted_articles = []
        for article, summary, source in articles_with_summaries:
            formatted_articles.append({
                'title': article.title,
                'url': article.url,
                'published_date': article.published_at.strftime('%B %d, %Y') if article.published_at else 'Unknown',
                'source_name': source.name,
                'summary': summary.summary,
                'key_points': summary.key_points if summary.key_points else []
            })
        
        return formatted_articles


def get_digest_generator() -> DigestGenerator:
    """Factory function to create DigestGenerator"""
    return DigestGenerator()
