import logging

from common_utils import configure_logging


def test_configure_logging_does_not_add_duplicate_handlers():
    logger = logging.getLogger()
    original_handlers = logger.handlers.copy()
    for handler in original_handlers:
        logger.removeHandler(handler)

    try:
        logger = configure_logging()
        assert len(logger.handlers) == 1

        logger = configure_logging()
        assert len(logger.handlers) == 1
    finally:
        for handler in logger.handlers:
            logger.removeHandler(handler)
        for handler in original_handlers:
            logger.addHandler(handler)