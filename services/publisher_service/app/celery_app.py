import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

celery = Celery(
    'robopost_publisher',
    broker=os.getenv('CELERY_BROKER_URL'),
    backend=os.getenv('CELERY_RESULT_BACKEND'),
    include=['app.tasks']
)

celery.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)

if __name__ == '__main__':
    celery.start()