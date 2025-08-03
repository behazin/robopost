from common_utils import (
    configure_logging,
    get_rabbitmq_connection,
    session_scope,
)
from services.core_engine.database import init_db
from services.core_engine.models import Article

import os
import trafilatura
from google.cloud import translate_v2 as translate
from vertexai import init
from vertexai.preview.language_models import TextGenerationModel


def process_url(url, translator, summarizer, logger):
    """Fetch, translate, summarize and persist an article."""
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        logger.warning("Failed to download URL", extra={"url": url})
        return
    content = trafilatura.extract(downloaded)
    if not content:
        logger.warning("No content extracted", extra={"url": url})
        return
    translated = translator.translate(content, target_language="en")["translatedText"]
    summary_obj = summarizer.predict(translated)
    summary_text = getattr(summary_obj, "text", str(summary_obj))
    with session_scope() as db:
        article = Article(
            source_url=url,
            content=content,
            translated_content=translated,
            summary=summary_text,
        )
        db.add(article)
    logger.info("Processed article", extra={"url": url})


def main():
    logger = configure_logging()
    logger.info("Core engine starting")
    init_db()
    translator = translate.Client()
    init(
        project=os.getenv("GOOGLE_PROJECT_ID"),
        location=os.getenv("GOOGLE_LOCATION", "us-central1"),
    )
    summarizer = TextGenerationModel.from_pretrained("text-bison")
    conn = get_rabbitmq_connection()
    channel = conn.channel()
    channel.queue_declare(queue="url.new", durable=True)

    def callback(ch, method, properties, body):
        url = body.decode()
        process_url(url, translator, summarizer, logger)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue="url.new", on_message_callback=callback)
    try:
        channel.start_consuming()
    finally:
        channel.close()
        conn.close()


if __name__ == "__main__":
    main()