"""
Shared pytest fixtures for NexusFeed unit tests.

All database tests use an in-memory SQLite engine so no live Postgres
instance is required. The fixtures patch app.database.base.SessionLocal
and app.database.base.get_db_session so the code under test uses the
test session transparently.
"""
import pytest
from contextlib import contextmanager
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
# Import all models so Base.metadata is fully populated before create_all
from app.database import models, models_extended  # noqa: F401


@pytest.fixture
def test_engine():
    """Function-scoped in-memory SQLite engine — each test gets a clean DB."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(test_engine):
    """Per-test database session."""
    TestSession = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)
    session = TestSession()
    yield session
    session.close()


@pytest.fixture
def patch_db_session(db_session):
    """
    Patch get_db_session wherever it's used so code that calls it internally
    (e.g. repository.py) uses the test session instead of the Postgres engine.
    """
    @contextmanager
    def _test_session():
        try:
            yield db_session
            db_session.flush()
        except Exception:
            db_session.rollback()
            raise

    # Patch the name in every module that imports it directly
    with patch("app.database.base.get_db_session", _test_session), \
         patch("app.database.repository.get_db_session", _test_session):
        yield db_session


@pytest.fixture
def patch_worker_session(db_session):
    """
    Patch workers.get_db() to return the test session.
    Use this for worker functions that call get_db() directly.
    """
    with patch("app.orchestrator.workers.get_db", return_value=db_session):
        yield db_session
