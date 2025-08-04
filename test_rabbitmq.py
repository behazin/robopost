import time
from unittest.mock import patch, MagicMock

import pika
import pytest

from common_utils.rabbitmq import get_rabbitmq_connection


@patch("common_utils.rabbitmq.pika.BlockingConnection")
@patch("common_utils.rabbitmq.time.sleep")
def test_get_rabbitmq_connection_retries_on_failure(
    mock_sleep: MagicMock, mock_connection: MagicMock
):
    """
    Tests that get_rabbitmq_connection retries connecting if AMQPConnectionError is raised.
    """
    # Simulate connection error on the first 2 attempts, and success on the 3rd.
    mock_connection.side_effect = [
        pika.exceptions.AMQPConnectionError,
        pika.exceptions.AMQPConnectionError,
        MagicMock(),  # Successful connection
    ]

    # Use the correct keyword argument 'max_retries'
    get_rabbitmq_connection(max_retries=3)

    assert mock_connection.call_count == 3
    assert mock_sleep.call_count == 2