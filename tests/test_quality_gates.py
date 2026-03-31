"""
Tests for pipeline quality gates in workers.py.

These tests verify that each pipeline stage correctly skips articles that
don't meet the minimum content length requirements, rather than passing
empty or stub content through to the LLM or embedding model.

We check return values only — not DB state — because the worker closes its
own session before we can inspect it.
"""
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.database.models import Source, Article, SourceType
from app.database.models_extended import ArticleSummary, ProcessingQueue, ProcessingStatus
from app.orchestrator.workers import extract_content, generate_summary


def _insert_source(db):
    source = Source(
        name="QG Source", source_type=SourceType.BLOG,
        url="https://qg.example.com/feed", active=True, created_at=datetime.utcnow(),
    )
    db.add(source)
    db.flush()
    return source


def _insert_article(db, source_id, full_content=None, content=None, url=None):
    article = Article(
        source_id=source_id, title="QG Article",
        url=url or f"https://qg.example.com/art-{id(object())}",
        content=content, full_content=full_content,
        processing_status="pending", scraped_at=datetime.utcnow(),
    )
    db.add(article)
    db.flush()
    return article


def _insert_pq(db, article_id):
    pq = ProcessingQueue(
        article_id=article_id, status=ProcessingStatus.PENDING,
        retry_count=0, created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
    )
    db.add(pq)
    db.flush()
    return pq


class TestSummarizationQualityGate:
    """generate_summary should reject articles whose content is below the 50-char threshold."""

    def test_short_full_content_is_rejected(self, patch_worker_session):
        db = patch_worker_session
        source = _insert_source(db)
        article = _insert_article(db, source.id, full_content="Too short")
        _insert_pq(db, article.id)

        with patch("app.orchestrator.workers.get_db", return_value=db):
            result = generate_summary(article.id)

        assert result is False

    def test_none_content_is_rejected(self, patch_worker_session):
        db = patch_worker_session
        source = _insert_source(db)
        article = _insert_article(db, source.id, full_content=None, content=None)
        _insert_pq(db, article.id)

        with patch("app.orchestrator.workers.get_db", return_value=db):
            result = generate_summary(article.id)

        assert result is False

    def test_sufficient_content_calls_llm(self, patch_worker_session):
        """An article with 200 chars of full_content should call the LLM."""
        db = patch_worker_session
        source = _insert_source(db)
        article = _insert_article(db, source.id, full_content="A" * 200)
        _insert_pq(db, article.id)

        mock_summarizer = MagicMock()
        mock_summarizer.summarize.return_value = {
            "summary": "Good summary.", "key_points": ["p1"], "model": "test-model",
        }
        mock_queue = MagicMock()

        with patch("app.orchestrator.workers.get_db", return_value=db), \
             patch("app.orchestrator.workers.LLMSummarizer", return_value=mock_summarizer), \
             patch("app.queue.get_message_queue", return_value=mock_queue):
            result = generate_summary(article.id)

        assert result is True
        mock_summarizer.summarize.assert_called_once()


class TestExtractionQualityGate:
    """extract_content should skip re-extraction when full_content already exists."""

    def test_article_with_long_content_skips_extraction(self, patch_worker_session):
        """Articles with > 100 chars of full_content skip the extractor."""
        db = patch_worker_session
        source = _insert_source(db)
        article = _insert_article(db, source.id, full_content="X" * 150)
        _insert_pq(db, article.id)

        mock_extractor = MagicMock()
        mock_queue = MagicMock()

        with patch("app.orchestrator.workers.get_db", return_value=db), \
             patch("app.orchestrator.workers.ContentExtractor", return_value=mock_extractor), \
             patch("app.queue.get_message_queue", return_value=mock_queue):
            result = extract_content(article.id)

        mock_extractor.extract_article_content.assert_not_called()
        mock_extractor.extract_video_transcript.assert_not_called()
        assert result is True

    def test_article_without_content_runs_extractor(self, patch_worker_session):
        """Articles with no full_content should invoke the extractor."""
        db = patch_worker_session
        source = _insert_source(db)
        article = _insert_article(db, source.id, full_content=None)
        _insert_pq(db, article.id)

        mock_extractor = MagicMock()
        mock_extractor.extract_article_content.return_value = {
            "content": "B" * 300, "method": "newspaper3k",
        }
        mock_queue = MagicMock()

        with patch("app.orchestrator.workers.get_db", return_value=db), \
             patch("app.orchestrator.workers.ContentExtractor", return_value=mock_extractor), \
             patch("app.queue.get_message_queue", return_value=mock_queue):
            result = extract_content(article.id)

        mock_extractor.extract_article_content.assert_called_once()
        assert result is True
