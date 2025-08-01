import json
import logging
import asyncio
from celery import Celery

from .config import settings
from .db import get_session
from . import crud
from .publishers.manager import publish_to_platform
from .monitoring import setup_monitoring_app

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

celery_app = Celery(
    'publisher_tasks',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['app.main']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
)

@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Start monitoring server in a separate thread/task when the worker starts
    # This is a simple way to expose metrics from a Celery worker
    monitoring_app = setup_monitoring_app()
    # Running FastAPI app in a background task
    loop = asyncio.get_event_loop()
    loop.create_task(monitoring_app.run(host="0.0.0.0", port=settings.METRICS_PORT))

@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3},
    retry_backoff=True,
    retry_backoff_max=600
)
def publish_article_task(self, message_body: str):
    """
    Celery task to publish an article to a specific destination.
    """
    data = json.loads(message_body)
    article_id = data['article_id']
    destination_id = data['destination_id']
    
    db_session = get_session()
    try:
        logging.info(f"Starting publication for article {article_id} to destination {destination_id}")
        
        article = crud.get_article(db_session, article_id)
        destination = crud.get_destination(db_session, destination_id)

        if not article or not destination:
            logging.error(f"Article {article_id} or Destination {destination_id} not found. Aborting task.")
            return

        publish_to_platform(destination, article)

        crud.create_publication_log(db_session, article_id, destination_id, "SUCCESS")
        logging.info(f"Successfully published article {article_id} to {destination.platform.value} (ID: {destination_id})")

    except Exception as e:
        logging.error(f"Failed to publish article {article_id} to {destination_id}. Error: {e}", exc_info=True)
        crud.create_publication_log(db_session, article_id, destination_id, "FAILED", str(e), self.request.retries)
        raise  # Re-raise exception to trigger Celery's retry mechanism
    finally:
        db_session.close()