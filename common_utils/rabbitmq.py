import os
import pika


def get_rabbitmq_connection():
    user = os.getenv("RABBITMQ_USER", "guest")
    password = os.getenv("RABBITMQ_PASSWORD", "guest")
    host = os.getenv("RABBITMQ_HOST", "localhost")
    port = int(os.getenv("RABBITMQ_PORT", "5672"))

    credentials = pika.PlainCredentials(user, password)
    parameters = pika.ConnectionParameters(host=host, port=port, credentials=credentials)
    return pika.BlockingConnection(parameters)
