import pytest
from unittest.mock import MagicMock

from sqlalchemy import text

from common_utils import db


@pytest.fixture(autouse=True)
def use_sqlite(monkeypatch):
    """Configure db module to use an in-memory SQLite engine for each test."""
    monkeypatch.setattr(db, "_engine", None)
    monkeypatch.setattr(db, "_SessionLocal", None)
    monkeypatch.setattr(db, "_get_db_url", lambda: "sqlite:///:memory:")


def test_get_engine_and_session():
    engine = db.get_engine()
    assert engine.dialect.name == "sqlite"

    session = db.get_session()
    assert session.bind is engine
    assert session.execute(text("SELECT 1")).scalar() == 1
    session.close()


def test_session_scope_commits_and_closes(monkeypatch):
    session = db.get_session()

    commit_mock = MagicMock(wraps=session.commit)
    rollback_mock = MagicMock(wraps=session.rollback)
    close_mock = MagicMock(wraps=session.close)

    monkeypatch.setattr(session, "commit", commit_mock)
    monkeypatch.setattr(session, "rollback", rollback_mock)
    monkeypatch.setattr(session, "close", close_mock)
    monkeypatch.setattr(db, "get_session", lambda: session)

    with db.session_scope() as s:
        s.execute(text("SELECT 1"))

    commit_mock.assert_called_once()
    rollback_mock.assert_not_called()
    close_mock.assert_called_once()


def test_session_scope_rollback_on_exception(monkeypatch):
    session = db.get_session()

    commit_mock = MagicMock(wraps=session.commit)
    rollback_mock = MagicMock(wraps=session.rollback)
    close_mock = MagicMock(wraps=session.close)

    monkeypatch.setattr(session, "commit", commit_mock)
    monkeypatch.setattr(session, "rollback", rollback_mock)
    monkeypatch.setattr(session, "close", close_mock)
    monkeypatch.setattr(db, "get_session", lambda: session)

    with pytest.raises(RuntimeError):
        with db.session_scope() as s:
            raise RuntimeError("boom")

    rollback_mock.assert_called_once()
    commit_mock.assert_not_called()
    close_mock.assert_called_once()