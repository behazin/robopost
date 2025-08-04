import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import ArgumentError

from services.core_engine.database import init_db
from common_utils import db


def test_init_db_creates_articles_table():
    """init_db should create the articles table on the provided engine."""
    engine = create_engine("sqlite:///:memory:")
    init_db(engine=engine)

    inspector = inspect(engine)
    assert inspector.has_table("articles")


def test_init_db_invalid_db_url(monkeypatch):
    """init_db should raise a helpful error when the DB URL is invalid."""
    # Reset any cached engine and provide an invalid URL.
    monkeypatch.setattr(db, "_engine", None)
    monkeypatch.setattr(db, "_get_db_url", lambda: "invalid-url")

    with pytest.raises(ArgumentError, match="Could not parse SQLAlchemy URL"):
        init_db(retries=1)
