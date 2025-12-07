"""
CRUD repository for database operations.
Provides a clean interface for interacting with the database.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy import desc

from app.database.base import get_db_session
from app.database.models import Source, Article, SourceType

logger = logging.getLogger(__name__)


class ArticleRepository:
    """Repository for Article CRUD operations"""
    
    @staticmethod
    def create_article(
        source_id: int,
        title: str,
        url: str,
        content: Optional[str] = None,
        published_at: Optional[datetime] = None,
        video_id: Optional[str] = None,
        category: Optional[str] = None
    ) -> Optional[Article]:
        """
        Create a new article.
        
        Returns:
            Article object if created, None if duplicate
        """
        try:
            with get_db_session() as session:
                article = Article(
                    source_id=source_id,
                    title=title,
                    url=url,
                    content=content,
                    published_at=published_at,
                    video_id=video_id,
                    category=category,
                    scraped_at=datetime.utcnow()
                )
                session.add(article)
                session.commit()
                session.refresh(article)
                logger.info(f"Created article: {title[:50]}")
                return article
        except IntegrityError:
            logger.debug(f"Article already exists: {url}")
            return None
        except Exception as e:
            logger.error(f"Error creating article: {e}")
            return None
    
    @staticmethod
    def bulk_create_articles(articles_data: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Bulk create articles from scraped data.
        
        Args:
            articles_data: List of dicts with article data
        
        Returns:
            Dict with statistics (created, duplicates, errors)
        """
        stats = {"created": 0, "duplicates": 0, "errors": 0}
        
        with get_db_session() as session:
            for data in articles_data:
                try:
                    # Check if article already exists
                    existing = session.query(Article).filter(
                        Article.url == data["url"]
                    ).first()
                    
                    if existing:
                        stats["duplicates"] += 1
                        continue
                    
                    # Create new article
                    article = Article(
                        source_id=data["source_id"],
                        title=data["title"],
                        url=data["url"],
                        content=data.get("content"),
                        published_at=data.get("published_at"),
                        video_id=data.get("video_id"),
                        category=data.get("category"),
                        scraped_at=datetime.utcnow()
                    )
                    session.add(article)
                    session.commit()
                    stats["created"] += 1
                    
                except IntegrityError:
                    session.rollback()
                    stats["duplicates"] += 1
                except Exception as e:
                    session.rollback()
                    stats["errors"] += 1
                    logger.error(f"Error creating article: {e}")
        
        return stats
    
    @staticmethod
    def get_article_by_url(url: str) -> Optional[Article]:
        """Get article by URL"""
        with get_db_session() as session:
            return session.query(Article).filter(Article.url == url).first()
    
    @staticmethod
    def get_articles_by_source(source_id: int, limit: int = 100) -> List[Article]:
        """Get articles for a specific source"""
        with get_db_session() as session:
            return session.query(Article).filter(
                Article.source_id == source_id
            ).order_by(desc(Article.published_at)).limit(limit).all()
    
    @staticmethod
    def get_recent_articles(hours: int = 24, limit: int = 100) -> List[Article]:
        """Get recent articles within specified hours"""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        with get_db_session() as session:
            return session.query(Article).filter(
                Article.scraped_at >= cutoff
            ).order_by(desc(Article.scraped_at)).limit(limit).all()


class SourceRepository:
    """Repository for Source CRUD operations"""
    
    @staticmethod
    def create_source(
        name: str,
        source_type: SourceType,
        url: str,
        active: bool = True
    ) -> Optional[Source]:
        """
        Create a new source.
        
        Returns:
            Source object if created, None if duplicate
        """
        try:
            with get_db_session() as session:
                source = Source(
                    name=name,
                    source_type=source_type,
                    url=url,
                    active=active
                )
                session.add(source)
                session.commit()
                session.refresh(source)
                logger.info(f"Created source: {name}")
                return source
        except IntegrityError:
            logger.debug(f"Source already exists: {url}")
            return None
        except Exception as e:
            logger.error(f"Error creating source: {e}")
            return None
    
    @staticmethod
    def get_source_by_url(url: str) -> Optional[Source]:
        """Get source by URL"""
        with get_db_session() as session:
            return session.query(Source).filter(Source.url == url).first()
    
    @staticmethod
    def get_source_by_name(name: str) -> Optional[Source]:
        """Get source by name"""
        with get_db_session() as session:
            return session.query(Source).filter(Source.name == name).first()
    
    @staticmethod
    def get_all_sources(active_only: bool = True) -> List[Source]:
        """Get all sources"""
        with get_db_session() as session:
            query = session.query(Source)
            if active_only:
                query = query.filter(Source.active == True)
            return query.all()
    
    @staticmethod
    def get_sources_by_type(source_type: SourceType, active_only: bool = True) -> List[Source]:
        """Get sources by type"""
        with get_db_session() as session:
            query = session.query(Source).filter(Source.source_type == source_type)
            if active_only:
                query = query.filter(Source.active == True)
            return query.all()
    
    @staticmethod
    def update_source_status(source_id: int, active: bool) -> bool:
        """Update source active status"""
        try:
            with get_db_session() as session:
                source = session.query(Source).filter(Source.id == source_id).first()
                if source:
                    source.active = active
                    session.commit()
                    logger.info(f"Updated source {source_id} active status to {active}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Error updating source status: {e}")
            return False
