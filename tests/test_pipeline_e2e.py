import os
import sys
import threading
import time
import types
import feedparser
import pytest

from common_utils import session_scope, get_engine, get_rabbitmq_connection
from services.core_engine.models import Article


def wait_for(condition, timeout=10, interval=0.1):
    end = time.time() + timeout
    while time.time() < end:
        if condition():
            return True
        time.sleep(interval)
    return False


def test_pipeline_e2e(monkeypatch):
    # Stub external dependencies before importing core_engine
    fake_feed = types.SimpleNamespace(
        entries=[types.SimpleNamespace(link="https://example.com/article")]
    )
    monkeypatch.setattr(feedparser, "parse", lambda url: fake_feed)
    translate_stub = types.SimpleNamespace(
        Client=lambda: types.SimpleNamespace(
            translate=lambda text, target_language: {"translatedText": text}
        )
    )
    summarizer_model = types.SimpleNamespace(
        predict=lambda text: types.SimpleNamespace(text="summary")
    )

    preview_module = types.ModuleType("preview")
    preview_module.language_models = language_models_module
    vertexai_module = types.ModuleType("vertexai")
    vertexai_module.init = lambda project=None, location=None: None
    vertexai_module.preview = preview_module

    fake_google_cloud = types.SimpleNamespace(translate_v2=translate_stub)
    monkeypatch.setitem(sys.modules, "google", types.SimpleNamespace(cloud=fake_google_cloud))
    monkeypatch.setitem(sys.modules, "google.cloud", fake_google_cloud)
    monkeypatch.setitem(sys.modules, "google.cloud.translate_v2", translate_stub)
    monkeypatch.setitem(sys.modules, "vertexai", vertexai_module)
    monkeypatch.setitem(sys.modules, "vertexai.preview", preview_module)
    monkeypatch.setitem(
        sys.modules, "vertexai.preview.language_models", language_models_module
    )

    trafilatura_stub = types.SimpleNamespace(
        fetch_url=lambda url: "html",
        extract=lambda html: "content",
    )
    monkeypatch.setitem(sys.modules, "trafilatura", trafilatura_stub)

    import services.core_engine.app as core_app
    from services.source_crawler import app as crawler_app

    # Ensure DB and RabbitMQ are reachable
    for _ in range(30):
        try:
            conn = get_rabbitmq_connection()
            conn.close()
            break
        except Exception:
            time.sleep(1)
    else:
        pytest.fail("RabbitMQ not available")

    for _ in range(30):
        try:
            engine = get_engine()
            with engine.connect() as conn:
                pass
            break
        except Exception:
            time.sleep(1)
    else:
        pytest.fail("Database not available")

    core_app.init_db()

    # Start core engine in background
    core_thread = threading.Thread(target=core_app.main, daemon=True)
    core_thread.start()
    time.sleep(1)  # allow consumer to start

    expected_link = fake_feed.entries[0].link

    os.environ[crawler_app.FEEDS_ENV_VAR] = "https://example.com/feed"
    os.environ[crawler_app.INTERVAL_ENV_VAR] = "1"

    crawler_thread = threading.Thread(target=crawler_app.main, daemon=True)
    crawler_thread.start()

    def article_exists():
        with session_scope() as session:
            return (
                session.query(Article)
                .filter_by(source_url=expected_link)
                .first()
                is not None
            )

    assert wait_for(article_exists, timeout=15), "Article was not processed"

    with session_scope() as session:
        article = (
            session.query(Article)
            .filter_by(source_url=expected_link)
            .one()
        )
        assert article.status == "PENDING_APPROVAL"
        