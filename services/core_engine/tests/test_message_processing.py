import sys
import types
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from common_utils import configure_logging


def test_message_callback_processes_and_acks(monkeypatch):
    import services.core_engine.app as core_app
    from services.core_engine.models import Article

    translator = types.SimpleNamespace(translate=lambda text, target_language: {"translatedText": "translated"})
    summarizer = types.SimpleNamespace(predict=lambda text: types.SimpleNamespace(text="summary"))
    trafilatura_stub = types.SimpleNamespace(fetch_url=lambda url: "html", extract=lambda html: "content")
    monkeypatch.setitem(sys.modules, "trafilatura", trafilatura_stub)
    monkeypatch.setattr(core_app, "trafilatura", trafilatura_stub)
    monkeypatch.setattr(core_app, "summarizer", summarizer)
    monkeypatch.setattr(core_app, "translate", types.SimpleNamespace(Client=lambda: translator))

    engine = create_engine("sqlite:///:memory:")
    core_app.init_db(engine)
    monkeypatch.setattr(core_app, "init_db", lambda: None)
    Session = sessionmaker(bind=engine)

    @contextmanager
    def fake_session_scope():
        session = Session()
        try:
            yield session
            session.commit()
        finally:
            session.close()

    monkeypatch.setattr(core_app, "session_scope", fake_session_scope)

    calls = []
    real_process_url = core_app.process_url

    def spy_process_url(url, translator_, summarizer_, logger_):
        calls.append(url)
        return real_process_url(url, translator_, summarizer_, logger_)

    monkeypatch.setattr(core_app, "process_url", spy_process_url)

    class DummyChannel:
        def queue_declare(self, queue, durable):
            pass

        def basic_consume(self, queue, on_message_callback):
            self.callback = on_message_callback

        def start_consuming(self):
            body = b"http://example.com"
            method = types.SimpleNamespace(delivery_tag=1)
            self.callback(self, method, None, body)

        def basic_ack(self, delivery_tag):
            with Session() as session:
                assert session.query(Article).count() == 1
            self.ack_called = True

        def close(self):
            pass

    channel = DummyChannel()

    class DummyConnection:
        def channel(self):
            return channel

        def close(self):
            pass

    monkeypatch.setattr(core_app, "get_rabbitmq_connection", lambda: DummyConnection())

    logger = configure_logging()
    monkeypatch.setattr(core_app, "configure_logging", lambda: logger)

    core_app.main()

    assert calls == ["http://example.com"]
    assert getattr(channel, "ack_called", False)


def test_process_url_logs_warning_when_fetch_none(monkeypatch):
    trafilatura_stub = types.SimpleNamespace(fetch_url=lambda url: None, extract=lambda html: "content")
    monkeypatch.setitem(sys.modules, "trafilatura", trafilatura_stub)
    import services.core_engine.app as core_app
    monkeypatch.setattr(core_app, "trafilatura", trafilatura_stub)

    translator = types.SimpleNamespace(translate=lambda text, target_language: {"translatedText": "translated"})
    summarizer = types.SimpleNamespace(predict=lambda text: types.SimpleNamespace(text="summary"))

    warnings = []
    logger = types.SimpleNamespace(warning=lambda msg, extra=None: warnings.append((msg, extra)))

    @contextmanager
    def dummy_session_scope():
        yield None

    monkeypatch.setattr(core_app, "session_scope", dummy_session_scope)

    core_app.process_url("http://example.com", translator, summarizer, logger)

    assert warnings and warnings[0][0] == "Failed to download URL"
