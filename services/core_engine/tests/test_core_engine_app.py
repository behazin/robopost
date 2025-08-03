import sys
import types
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from common_utils import configure_logging


def test_process_url_persists_article(monkeypatch):
    translate_stub = types.SimpleNamespace(
        Client=lambda: types.SimpleNamespace(
            translate=lambda text, target_language: {"translatedText": "translated"}
        )
    )
    summarizer_model = types.SimpleNamespace(
        predict=lambda text: types.SimpleNamespace(text="summary")
    )
    aiplatform_stub = types.SimpleNamespace(
        init=lambda: None,
        TextGenerationModel=types.SimpleNamespace(
            from_pretrained=lambda name: summarizer_model
        ),
    )
    fake_google_cloud = types.SimpleNamespace(
        translate_v2=translate_stub, aiplatform=aiplatform_stub
    )
    monkeypatch.setitem(sys.modules, "google", types.SimpleNamespace(cloud=fake_google_cloud))
    monkeypatch.setitem(sys.modules, "google.cloud", fake_google_cloud)
    monkeypatch.setitem(sys.modules, "google.cloud.translate_v2", translate_stub)
    monkeypatch.setitem(sys.modules, "google.cloud.aiplatform", aiplatform_stub)

    trafilatura_stub = types.SimpleNamespace(
        fetch_url=lambda url: "html",
        extract=lambda html: "content",
    )
    monkeypatch.setitem(sys.modules, "trafilatura", trafilatura_stub)

    import services.core_engine.app as core_app
    from services.core_engine.models import Article

    engine = create_engine("sqlite:///:memory:")
    core_app.init_db(engine)
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

    translator = translate_stub.Client()
    summarizer = aiplatform_stub.TextGenerationModel.from_pretrained("text-bison")
    logger = configure_logging()

    core_app.process_url("http://example.com", translator, summarizer, logger)

    with fake_session_scope() as session:
        articles = session.query(Article).all()
        assert len(articles) == 1
        article = articles[0]
        assert article.source_url == "http://example.com"
        assert article.content == "content"
        assert article.translated_content == "translated"
        assert article.summary == "summary"
        assert article.status == "PENDING_APPROVAL"