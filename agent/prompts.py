"""
Prompt templates and utilities for the AI news digest agent.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any

# Get the agent directory path
AGENT_DIR = Path(__file__).parent


def load_system_prompt() -> str:
    """
    Load the system prompt from file.
    
    Returns:
        System prompt text
    """
    prompt_file = AGENT_DIR / "system_prompt.txt"
    with open(prompt_file, 'r', encoding='utf-8') as f:
        return f.read().strip()


def load_agent_config() -> Dict[str, Any]:
    """
    Load the agent configuration from YAML file.
    
    Returns:
        Configuration dictionary
    """
    config_file = AGENT_DIR / "config.yaml"
    with open(config_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_article_summary_prompt(article_title: str, article_content: str) -> str:
    """
    Generate a prompt for summarizing a single article.
    
    Args:
        article_title: Article title
        article_content: Article content
    
    Returns:
        Formatted prompt
    """
    return f"""Summarize the following article in 2-3 concise sentences. Focus on the key points, what's new, and why it matters.

Title: {article_title}

Content:
{article_content[:2000]}  # Limit content length

Summary:"""


def get_digest_generation_prompt(articles_by_source: Dict[str, list]) -> str:
    """
    Generate a prompt for creating the full daily digest.
    
    Args:
        articles_by_source: Dictionary mapping source names to lists of articles
    
    Returns:
        Formatted prompt
    """
    # Build article list
    articles_text = []
    for source_name, articles in articles_by_source.items():
        articles_text.append(f"\n## {source_name}\n")
        for i, article in enumerate(articles, 1):
            articles_text.append(
                f"{i}. **{article['title']}**\n"
                f"   URL: {article['url']}\n"
                f"   Content preview: {article['content'][:300]}...\n"
            )
    
    articles_section = "\n".join(articles_text)
    
    return f"""Create a daily digest email from the following articles. For each article, write a concise 2-3 sentence summary that captures the key points and why it matters.

Format the output as follows:
- Group articles by source
- For each article, provide: a brief summary and the original URL
- Use clear, engaging language
- Maintain a professional tone

{articles_section}

Generate the digest:"""


def get_snippet_format_template() -> str:
    """
    Get the template for formatting individual snippets.
    
    Returns:
        Template string
    """
    return """**{title}**
{summary}
[Read more]({url})
"""
