"""
LLM-based summarization service using Google Gemini.
Generates concise summaries and key points from article content.
"""
import os
import logging
from typing import Dict, List, Optional
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential
import json

logger = logging.getLogger(__name__)


class LLMSummarizer:
    """Generate summaries using LLM APIs (Gemini)"""
    
    SYSTEM_PROMPT = """You are an AI news summarizer specializing in technology and AI news.
Your task is to create concise, informative summaries of articles.

Guidelines:
1. Create a 2-3 sentence summary that captures the main points
2. Extract 3-5 key points as bullet points
3. Focus on technical details, innovations, and implications
4. Be objective and factual
5. Use clear, professional language

Return your response as JSON with this exact structure:
{
    "summary": "2-3 sentence summary here",
    "key_points": ["point 1", "point 2", "point 3"]
}"""
    
    def __init__(self, provider: str = 'gemini', model: str = None):
        """
        Initialize LLM summarizer.
        
        Args:
            provider: LLM provider ('gemini' or 'claude')
            model: Specific model to use (default from env)
        """
        self.provider = provider
        self.model_name = model or os.getenv('GEMINI_MODEL', 'models/gemini-2.5-flash')
        
        if provider == 'gemini':
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found in environment variables")
            
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(
                self.model_name,
                generation_config={
                    "temperature": 0.3,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 1024,
                }
            )
            logger.info(f"Initialized Gemini LLM with model: {self.model_name}")
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API with retry logic"""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise
    
    def summarize(self, content: str, title: str = None) -> Optional[Dict[str, any]]:
        """
        Generate summary and key points from content.
        
        Args:
            content: Article content to summarize
            title: Optional article title for context
        
        Returns:
            Dict with 'summary', 'key_points', and 'model' or None if failed
        """
        try:
            # Truncate content if too long (Gemini has token limits)
            max_chars = 25000  # ~6000 tokens
            if len(content) > max_chars:
                content = content[:max_chars] + "..."
                logger.warning(f"Content truncated to {max_chars} characters")
            
            # Build prompt
            user_prompt = f"""Analyze and summarize the following article:

Title: {title if title else 'N/A'}

Content:
{content}

Provide a JSON response with the summary and key points."""
            
            # Combine system and user prompts
            full_prompt = f"{self.SYSTEM_PROMPT}\n\n{user_prompt}"
            
            # Call API with retry
            response_text = self._call_gemini(full_prompt)
            
            # Parse JSON response
            try:
                # Try to extract JSON from response
                # Sometimes the model wraps JSON in markdown code blocks
                if '```json' in response_text:
                    json_start = response_text.find('{')
                    json_end = response_text.rfind('}') + 1
                    json_str = response_text[json_start:json_end]
                    result = json.loads(json_str)
                elif '{' in response_text:
                    json_start = response_text.find('{')
                    json_end = response_text.rfind('}') + 1
                    json_str = response_text[json_start:json_end]
                    result = json.loads(json_str)
                else:
                    # Fallback: treat entire response as summary
                    result = {
                        'summary': response_text.strip(),
                        'key_points': []
                    }
                
                # Validate structure
                if 'summary' not in result:
                    result['summary'] = response_text.strip()
                if 'key_points' not in result:
                    result['key_points'] = []
                
                result['model'] = self.model_name
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                # Return response as plain summary
                return {
                    'summary': response_text.strip(),
                    'key_points': [],
                    'model': self.model_name
                }
        
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return None
    
    def summarize_batch(self, articles: List[Dict[str, str]]) -> List[Optional[Dict[str, any]]]:
        """
        Summarize multiple articles.
        
        Args:
            articles: List of dicts with 'content' and optional 'title'
        
        Returns:
            List of summary dicts (same order as input)
        """
        results = []
        for article in articles:
            content = article.get('content', '')
            title = article.get('title')
            summary = self.summarize(content, title)
            results.append(summary)
        
        return results
    
    def get_rate_limit_status(self) -> Dict[str, any]:
        """Get current rate limit status (if supported by provider)"""
        # Gemini doesn't provide rate limit info via API
        # This is a placeholder for potential future implementation
        return {
            'provider': self.provider,
            'model': self.model_name,
            'rate_limit_available': False
        }
