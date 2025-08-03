import os
import time

import pika


DEFAULT_BASE_DELAY = 5  # seconds


def get_rabbitmq_connection(max_retries: int | None = None) -> pika.BlockingConnection:
    """Get a RabbitMQ connection, retrying with exponential backoff.

    Parameters
    ----------
    max_retries:
        Optional number of attempts before giving up. If ``None`` the function
        will keep retrying indefinitely until a connection is established.
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
            if max_retries is not None and attempt >= max_retries:
                raise
            delay = DEFAULT_BASE_DELAY * (2 ** (attempt - 1))
            time.sleep(delay)

