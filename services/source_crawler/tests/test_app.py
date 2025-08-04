import logging
import types

import pytest
from common_utils import configure_logging
import services.source_crawler.app as app
from services.source_crawler.app import fetch_and_publish


class DummyChannel:
    def __init__(self):
        self.messages = []

    def queue_declare(self, queue, durable):
        pass

    def basic_publish(self, exchange, routing_key, body, properties=None):
        self.messages.append((routing_key, body))

    def close(self):
        pass


class DummyConnection:
    def __init__(self, channel):
        self._channel = channel

    def channel(self):
        return self._channel


def test_fetch_and_publish_emits_new_items(monkeypatch):
    logger = configure_logging()
    feeds = ["http://example.com/feed"]
    seen = set()
    channel = DummyChannel()
    conn = DummyConnection(channel)

    def first_parse(url):
        return types.SimpleNamespace(entries=[{"link": "http://example.com/a"}])

    monkeypatch.setattr("services.source_crawler.app.feedparser.parse", first_parse)
    fetch_and_publish(conn, feeds, seen, logger)

    assert channel.messages == [("url.new", b"http://example.com/a")]

    def second_parse(url):
        return types.SimpleNamespace(entries=[{"link": "http://example.com/a"}, {"link": "http://example.com/b"}])

    monkeypatch.setattr("services.source_crawler.app.feedparser.parse", second_parse)
    fetch_and_publish(conn, feeds, seen, logger)

    assert channel.messages == [
        ("url.new", b"http://example.com/a"),
        ("url.new", b"http://example.com/b"),
    ]


def test_fetch_and_publish_logs_and_skips_on_parse_error(monkeypatch, caplog):
    logger = configure_logging()
    feeds = ["http://example.com/feed"]
    seen = set()
    channel = DummyChannel()
    conn = DummyConnection(channel)

    def bad_parse(url):
        raise ValueError("boom")

    monkeypatch.setattr("services.source_crawler.app.feedparser.parse", bad_parse)

    with caplog.at_level(logging.ERROR):
        fetch_and_publish(conn, feeds, seen, logger)

    assert channel.messages == []
    assert any("Error parsing feed" in r.getMessage() for r in caplog.records)


def test_main_initial_run(monkeypatch):
    monkeypatch.setenv(app.FEEDS_ENV_VAR, "http://example.com/feed")
    monkeypatch.setenv(app.INTERVAL_ENV_VAR, "1")

    dummy_conn = DummyConnection(DummyChannel())
    monkeypatch.setattr(app, "get_rabbitmq_connection", lambda: dummy_conn)
    monkeypatch.setattr(app, "configure_logging", lambda: logging.getLogger("test"))

    fetch_called = {"count": 0}

    def fake_fetch(conn, feeds, seen, logger):
        fetch_called["count"] += 1
        assert feeds == ["http://example.com/feed"]

    monkeypatch.setattr(app, "fetch_and_publish", fake_fetch)

    run_called = {"count": 0}

    def fake_run_pending():
        run_called["count"] += 1
        raise RuntimeError("stop")

    monkeypatch.setattr(app.schedule, "run_pending", fake_run_pending)

    with pytest.raises(RuntimeError):
        app.main()

    assert fetch_called["count"] == 1
    assert run_called["count"] == 1
