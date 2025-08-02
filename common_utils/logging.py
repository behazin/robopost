import logging
import os
from pythonjsonlogger import jsonlogger


def configure_logging():
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger = logging.getLogger()
    if logger.handlers:
        return logger

    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter()
    handler.setFormatter(formatter)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger
