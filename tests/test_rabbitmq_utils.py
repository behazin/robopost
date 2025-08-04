import pika
import pytest
from unittest.mock import MagicMock, call

from common_utils.rabbitmq import DEFAULT_BASE_DELAY, get_rabbitmq_connection


def test_get_rabbitmq_connection_backoff(monkeypatch):
    """Connection retries use exponential backoff before succeeding."""
    connection = object()
    attempts = {"count": 0}

    def fake_connection(params):
        if attempts["count"] < 3:
            attempts["count"] += 1
            raise pika.exceptions.AMQPConnectionError()
        return connection

    monkeypatch.setattr("common_utils.rabbitmq.pika.BlockingConnection", fake_connection)

    sleep_mock = MagicMock()
    monkeypatch.setattr("common_utils.rabbitmq.time.sleep", sleep_mock)

    result = get_rabbitmq_connection(max_retries=5)

    assert result is connection
    sleep_mock.assert_has_calls(
        [
            call(DEFAULT_BASE_DELAY),
            call(DEFAULT_BASE_DELAY * 2),
            call(DEFAULT_BASE_DELAY * 4),
        ]
    )


def test_get_rabbitmq_connection_max_retries(monkeypatch):
    """The function raises an error when max_retries is exceeded."""

    def always_fail(params):
        raise pika.exceptions.AMQPConnectionError()

    monkeypatch.setattr("common_utils.rabbitmq.pika.BlockingConnection", always_fail)
    monkeypatch.setattr("common_utils.rabbitmq.time.sleep", lambda s: None)

    with pytest.raises(pika.exceptions.AMQPConnectionError):
        get_rabbitmq_connection(max_retries=3)