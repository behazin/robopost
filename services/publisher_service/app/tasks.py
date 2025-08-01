import logging
from .celery_app import celery
from .db import SessionLocal
from .models import Article, Destination, PublicationLog, PublicationStatus, Platform
from .publishers.base import get_publisher

@celery.task(bind=True, max_retries=3, default_retry_delay=60) # Exponential backoff
def publish_article_task(self, article_id: int, destination_id: int):
    logging.info(f"Starting publication task for article {article_id} to destination {destination_id}")
    db_session = SessionLocal()
    try:
        # Idempotency Check
        log_exists = db_session.query(PublicationLog).filter_by(
            article_id=article_id, 
            destination_id=destination_id, 
            status=PublicationStatus.SUCCESS
        ).first()

        if log_exists:
            logging.warning(f"Article {article_id} already successfully published to {destination_id}. Skipping.")
            return {"status": "skipped", "reason": "already published"}

        destination = db_session.query(Destination).get(destination_id)
        article = db_session.query(Article).get(article_id)

        if not destination or not article:
            raise ValueError("Article or Destination not found.")

        publisher = get_publisher(destination.platform)
        if not publisher:
            raise NotImplementedError(f"No publisher available for platform {destination.platform.value}")

        # Rate limiting check would be implemented here
        # ...

        publisher.publish(article=article, credentials=destination.credentials)
        
        # Log success
        log = PublicationLog(
            article_id=article_id,
            destination_id=destination_id,
            platform=destination.platform,
            status=PublicationStatus.SUCCESS,
            log_message="Published successfully."
        )
        db_session.add(log)
        db_session.commit()
        logging.info(f"Successfully published article {article_id} to {destination_id}")
        return {"status": "success"}

    except Exception as exc:
        logging.error(f"Failed to publish article {article_id} to {destination_id}. Error: {exc}", exc_info=True)
        # Log failure
        log = PublicationLog(
            article_id=article_id,
            destination_id=destination_id,
            platform=destination.platform,
            status=PublicationStatus.FAILED,
            log_message=str(exc),
            retry_count=self.request.retries,
            last_error_reason=str(exc)
        )
        db_session.merge(log) # Use merge to update if a failed log already exists
        db_session.commit()
        raise self.retry(exc=exc)
    finally:
        db_session.close()

# A RabbitMQ consumer is needed in this service to listen for 'rk.publication_approved'
# and then call `publish_article_task.delay(article_id, destination_id)`