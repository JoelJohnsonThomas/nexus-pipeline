"""
Tests for URL deduplication logic in ArticleRepository.bulk_create_articles().
"""
from datetime import datetime

from app.database.models import Source, SourceType
from app.database.repository import ArticleRepository


def _make_source(db_session) -> int:
    """Insert a test source and return its id."""
    source = Source(
        name="Test Source",
        source_type=SourceType.BLOG,
        url="https://example.com/feed",
        active=True,
        created_at=datetime.utcnow(),
    )
    db_session.add(source)
    db_session.flush()
    return source.id


def _article_data(source_id: int, url: str, title: str = "Test Article") -> dict:
    return {
        "source_id": source_id,
        "title": title,
        "url": url,
        "content": "Some content",
        "published_at": datetime.utcnow(),
    }


def test_no_duplicates_all_created(patch_db_session):
    """Inserting three unique URLs should create all three articles."""
    source_id = _make_source(patch_db_session)
    articles = [
        _article_data(source_id, f"https://example.com/article-{i}", f"Article {i}")
        for i in range(3)
    ]
    stats = ArticleRepository.bulk_create_articles(articles)
    assert stats["created"] == 3
    assert stats["duplicates"] == 0
    assert stats["errors"] == 0


def test_duplicate_url_not_inserted(patch_db_session):
    """Inserting the same URL twice should report one duplicate and create only one row."""
    source_id = _make_source(patch_db_session)
    url = "https://example.com/same-article"
    articles = [
        _article_data(source_id, url, "First"),
        _article_data(source_id, url, "Duplicate"),
    ]
    stats = ArticleRepository.bulk_create_articles(articles)
    assert stats["created"] == 1
    assert stats["duplicates"] == 1
    assert stats["errors"] == 0


def test_mixed_batch_partial_duplicates(patch_db_session):
    """A batch with some new and some duplicate URLs should correctly separate them."""
    source_id = _make_source(patch_db_session)
    # Insert one article first
    first = [_article_data(source_id, "https://example.com/existing")]
    ArticleRepository.bulk_create_articles(first)

    # Now send a batch with the existing URL plus two new ones
    batch = [
        _article_data(source_id, "https://example.com/existing", "Existing again"),
        _article_data(source_id, "https://example.com/new-1"),
        _article_data(source_id, "https://example.com/new-2"),
    ]
    stats = ArticleRepository.bulk_create_articles(batch)
    assert stats["created"] == 2
    assert stats["duplicates"] == 1
    assert stats["errors"] == 0
