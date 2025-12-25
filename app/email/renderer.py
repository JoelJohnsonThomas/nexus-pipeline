"""
Email template renderer using Jinja2.
Renders HTML and text versions of email templates with article data.
"""
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape
import logging

logger = logging.getLogger(__name__)


class EmailRenderer:
    """Renders email templates using Jinja2"""
    
    def __init__(self):
        """Initialize Jinja2 environment"""
        template_dir = Path(__file__).parent / 'templates'
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )
        logger.info(f"Initialized EmailRenderer with template dir: {template_dir}")
    
    def render_digest(
        self,
        articles: List[Dict],
        subscriber_name: Optional[str] = None,
        subscriber_email: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Render daily digest email in both HTML and text formats.
        
        Args:
            articles: List of article dicts with summary and key_points
            subscriber_name: Name of subscriber for personalization
            subscriber_email: Email for unsubscribe link
            
        Returns:
            Tuple of (html_content, text_content)
        """
        # Prepare template context
        context = {
            'current_date': datetime.now().strftime('%B %d, %Y'),
            'article_count': len(articles),
            'articles': articles,
            'subscriber_name': subscriber_name or 'Reader',
            'unsubscribe_url': self._get_unsubscribe_url(subscriber_email),
            'preferences_url': self._get_preferences_url(subscriber_email),
        }
        
        # Render HTML version
        html_template = self.env.get_template('digest.html')
        html_content = html_template.render(**context)
        
        # Render text version
        text_template = self.env.get_template('digest.txt')
        text_content = text_template.render(**context)
        
        logger.info(f"Rendered digest with {len(articles)} articles")
        return html_content, text_content
    
    def render_template(
        self,
        template_name: str,
        **context
    ) -> str:
        """
        Render any template with given context.
        
        Args:
            template_name: Name of template file (e.g., 'welcome.html')
            **context: Template variables
            
        Returns:
            Rendered template string
        """
        template = self.env.get_template(template_name)
        return template.render(**context)
    
    def _get_unsubscribe_url(self, email: Optional[str]) -> str:
        """Generate unsubscribe URL (placeholder for now)"""
        # TODO: Implement proper unsubscribe URL with token
        return f"http://localhost:8000/unsubscribe?email={email}" if email else "#"
    
    def _get_preferences_url(self, email: Optional[str]) -> str:
        """Generate preferences URL (placeholder for now)"""
        # TODO: Implement proper preferences URL with token
        return f"http://localhost:8000/preferences?email={email}" if email else "#"


# Singleton instance
_renderer = None

def get_email_renderer() -> EmailRenderer:
    """Get or create EmailRenderer singleton"""
    global _renderer
    if _renderer is None:
        _renderer = EmailRenderer()
    return _renderer
