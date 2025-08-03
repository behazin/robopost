import os
import time

import pika


DEFAULT_MAX_RETRIES = 5
DEFAULT_BASE_DELAY = 1  # seconds


def get_rabbitmq_connection(max_retries: int = DEFAULT_MAX_RETRIES) -> pika.BlockingConnection:
    """Get a RabbitMQ connection, retrying with exponential backoff.

    Parameters
    ----------
    max_retries:
        Number of attempts before giving up.
    """

    user = os.getenv("RABBITMQ_USER", "guest")
    password = os.getenv("RABBITMQ_PASSWORD", "guest")
    host = os.getenv("RABBITMQ_HOST", "localhost")
    port = int(os.getenv("RABBITMQ_PORT", "5672"))

    credentials = pika.PlainCredentials(user, password)
    parameters = pika.ConnectionParameters(host=host, port=port, credentials=credentials)

    attempt = 0
    while True:
        try:
            return pika.BlockingConnection(parameters)
        except pika.exceptions.AMQPConnectionError:
            attempt += 1
            if attempt >= max_retries:
                raise
            delay = DEFAULT_BASE_DELAY * (2 ** (attempt - 1))
            time.sleep(delay)

