"""Processing package for AI News Aggregator pipeline."""
from app.processing.content_extractor import ContentExtractor
from app.processing.llm_summarizer import LLMSummarizer
from app.processing.embeddings import EmbeddingGenerator

__all__ = ["ContentExtractor", "LLMSummarizer", "EmbeddingGenerator"]
