import types
import services.publisher_service.app as app

class DummyBot:
    def __init__(self):
        self.messages = []

    def send_message(self, chat_id, text):
        self.messages.append((chat_id, text))


def make_session(article):
    class DummySession:
        def get(self, model, id):
            return article
    class CM:
        def __enter__(self_inner):
            return DummySession()
        def __exit__(self_inner, exc_type, exc, tb):
            pass
    return CM()


def test_publish_article_sends_translated(monkeypatch):
    article = types.SimpleNamespace(
        id=1,
        translated_content="translated",
        content="content",
        source_url="http://example.com",
    )
    bot = DummyBot()
    monkeypatch.setattr(app, "session_scope", lambda: make_session(article))
    logger = app.configure_logging()
    app.publish_article(1, bot, "chat", logger)
    assert bot.messages == [("chat", "translated")]


def test_publish_article_uses_url_when_text_long(monkeypatch):
    long_text = "x" * 5001
    article = types.SimpleNamespace(
        id=2,
        translated_content=long_text,
        content=long_text,
        source_url="http://example.com",
    )
    bot = DummyBot()
    monkeypatch.setattr(app, "session_scope", lambda: make_session(article))
    logger = app.configure_logging()
    app.publish_article(2, bot, "chat", logger)
    assert bot.messages == [("chat", "http://example.com")]