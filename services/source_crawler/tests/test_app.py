import types

from common_utils import configure_logging
from services.source_crawler.app import fetch_and_publish


class DummyChannel:
    def __init__(self):
        self.messages = []

    def queue_declare(self, queue, durable):
        pass

    def basic_publish(self, exchange, routing_key, body):
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

    assert channel.messages == [("url.new", "http://example.com/a")]

    def second_parse(url):
        return types.SimpleNamespace(entries=[{"link": "http://example.com/a"}, {"link": "http://example.com/b"}])

    monkeypatch.setattr("services.source_crawler.app.feedparser.parse", second_parse)
    fetch_and_publish(conn, feeds, seen, logger)

    assert channel.messages == [
        ("url.new", "http://example.com/a"),
        ("url.new", "http://example.com/b"),
    ]
