"""
LLM-powered digest generation using Google Gemini API.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import google.generativeai as genai

from app.database import get_db_session, Article, Source
from app.config import config
from agent.prompts import (
    load_system_prompt,
    load_agent_config,
    get_article_summary_prompt,
)

logger = logging.getLogger(__name__)


class DigestGenerator:
    """Generates daily digests using Google Gemini API"""
    
    def __init__(self):
        """Initialize the digest generator with Gemini API"""
        # Configure Gemini API
        genai.configure(api_key=config.GEMINI_API_KEY)
        
        # Load agent configuration
        self.agent_config = load_agent_config()
        self.system_prompt = load_system_prompt()
        
        # Initialize model
        model_config = self.agent_config.get('model', {})
        self.model = genai.GenerativeModel(
            model_name=config.GEMINI_MODEL,
            generation_config={
                'temperature': model_config.get('temperature', 0.3),
                'max_output_tokens': model_config.get('max_tokens_total', 2000),
            }
        )
        
        logger.info(f"Initialized DigestGenerator with model: {config.GEMINI_MODEL}")
    
    def generate_digest(self, hours_back: Optional[int] = None) -> Dict[str, any]:
        """
        Generate a daily digest from recent articles.
        
        Args:
            hours_back: Number of hours to look back for articles (default from config)
        
        Returns:
            Dictionary with digest content and metadata
        """
        if hours_back is None:
            hours_back = config.DIGEST_HOURS_BACK
        
        logger.info(f"Generating digest for articles from last {hours_back} hours")
        
        # Fetch recent articles
        articles_by_source = self._fetch_recent_articles(hours_back)
        
        if not articles_by_source:
            logger.warning("No articles found for digest generation")
            return {
                "success": False,
                "message": "No new articles found",
                "html_content": "",
                "text_content": "",
            }
        
        # Generate summaries for each article
        digest_sections = []
        total_articles = 0
        
        for source_name, articles in articles_by_source.items():
            logger.info(f"Processing {len(articles)} articles from {source_name}")
            
            article_summaries = []
            max_articles = self.agent_config.get('formatting', {}).get('max_articles_per_source', 5)
            
            for article in articles[:max_articles]:
                summary = self._generate_article_summary(article)
                if summary:
                    article_summaries.append({
                        'title': article.title,
                        'url': article.url,
                        'summary': summary,
                        'published_at': article.published_at,
                    })
                    total_articles += 1
            
            if article_summaries:
                digest_sections.append({
                    'source_name': source_name,
                    'articles': article_summaries,
                })
        
        # Format digest
        html_content = self._format_digest_html(digest_sections)
        text_content = self._format_digest_text(digest_sections)
        
        logger.info(f"Digest generated successfully with {total_articles} articles from {len(digest_sections)} sources")
        
        return {
            "success": True,
            "total_articles": total_articles,
            "total_sources": len(digest_sections),
            "html_content": html_content,
            "text_content": text_content,
            "generated_at": datetime.utcnow(),
        }
    
    def _fetch_recent_articles(self, hours_back: int) -> Dict[str, List[Article]]:
        """
        Fetch recent articles grouped by source.
        
        Args:
            hours_back: Number of hours to look back
        
        Returns:
            Dictionary mapping source names to lists of articles
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        articles_by_source = {}
        
        with get_db_session() as session:
            # Query articles scraped within the time window
            articles = session.query(Article).join(Source).filter(
                Article.scraped_at >= cutoff_time
            ).order_by(Article.published_at.desc()).all()
            
            # Group by source
            for article in articles:
                source_name = article.source.name
                if source_name not in articles_by_source:
                    articles_by_source[source_name] = []
                articles_by_source[source_name].append(article)
        
        return articles_by_source
    
    def _generate_article_summary(self, article: Article) -> Optional[str]:
        """
        Generate a summary for a single article using Gemini.
        
        Args:
            article: Article object
        
        Returns:
            Summary text or None if generation fails
        """
        try:
            # Prepare content (limit length)
            content = article.content[:2000] if article.content else article.title
            
            # Create prompt
            prompt = f"""{self.system_prompt}

Now, summarize this article in 2-3 concise sentences:

Title: {article.title}
Content: {content}

Summary:"""
            
            # Generate summary
            response = self.model.generate_content(prompt)
            summary = response.text.strip()
            
            logger.debug(f"Generated summary for: {article.title}")
            return summary
        
        except Exception as e:
            logger.error(f"Error generating summary for article {article.id}: {e}")
            return None
    
    def _format_digest_html(self, digest_sections: List[Dict]) -> str:
        """
        Format digest as HTML for email.
        
        Args:
            digest_sections: List of digest sections with source and articles
        
        Returns:
            HTML formatted digest
        """
        html_parts = []
        
        # Header
        html_parts.append(f"""
        <h1 style="color: #2c3e50; font-family: Arial, sans-serif;">🤖 AI News Daily Digest</h1>
        <p style="color: #7f8c8d; font-family: Arial, sans-serif;">
            {datetime.utcnow().strftime('%B %d, %Y')}
        </p>
        <hr style="border: 1px solid #ecf0f1;">
        """)
        
        # Sections by source
        for section in digest_sections:
            html_parts.append(f"""
            <h2 style="color: #3498db; font-family: Arial, sans-serif; margin-top: 30px;">
                📰 {section['source_name']}
            </h2>
            """)
            
            for article in section['articles']:
                published_date = ""
                if article.get('published_at'):
                    published_date = f"<small style='color: #95a5a6;'>{article['published_at'].strftime('%b %d, %Y')}</small>"
                
                html_parts.append(f"""
                <div style="margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-left: 4px solid #3498db;">
                    <h3 style="margin: 0 0 10px 0; font-family: Arial, sans-serif;">
                        <a href="{article['url']}" style="color: #2c3e50; text-decoration: none;">
                            {article['title']}
                        </a>
                    </h3>
                    {published_date}
                    <p style="color: #34495e; font-family: Arial, sans-serif; line-height: 1.6; margin: 10px 0;">
                        {article['summary']}
                    </p>
                    <a href="{article['url']}" style="color: #3498db; text-decoration: none; font-weight: bold;">
                        Read more →
                    </a>
                </div>
                """)
        
        # Footer
        html_parts.append("""
        <hr style="border: 1px solid #ecf0f1; margin-top: 40px;">
        <p style="color: #95a5a6; font-size: 12px; font-family: Arial, sans-serif; text-align: center;">
            This digest was automatically generated by AI News Aggregator
        </p>
        """)
        
        return "".join(html_parts)
    
    def _format_digest_text(self, digest_sections: List[Dict]) -> str:
        """
        Format digest as plain text.
        
        Args:
            digest_sections: List of digest sections
        
        Returns:
            Plain text formatted digest
        """
        text_parts = []
        
        # Header
        text_parts.append("=" * 60)
        text_parts.append("AI NEWS DAILY DIGEST")
        text_parts.append(datetime.utcnow().strftime('%B %d, %Y'))
        text_parts.append("=" * 60)
        text_parts.append("")
        
        # Sections
        for section in digest_sections:
            text_parts.append(f"\n📰 {section['source_name'].upper()}")
            text_parts.append("-" * 60)
            
            for article in section['articles']:
                text_parts.append(f"\n• {article['title']}")
                if article.get('published_at'):
                    text_parts.append(f"  {article['published_at'].strftime('%b %d, %Y')}")
                text_parts.append(f"\n  {article['summary']}")
                text_parts.append(f"  Read more: {article['url']}\n")
        
        # Footer
        text_parts.append("\n" + "=" * 60)
        text_parts.append("Generated by AI News Aggregator")
        text_parts.append("=" * 60)
        
        return "\n".join(text_parts)
