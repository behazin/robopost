import time
from typing import Optional

from sqlalchemy.engine import Engine

from common_utils import get_engine
from .models import Base


def _get_engine_with_retry(
    retries: int = 5, delay: float = 1.0, backoff: float = 2.0
) -> Engine:
    """Return a database engine, retrying with exponential backoff."""
    current_delay = delay
    for attempt in range(retries):
        try:
            engine = get_engine()
            # Attempt to establish a real connection to ensure MySQL is ready
            with engine.connect():
                pass
            return engine
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(current_delay)
            current_delay *= backoff


def init_db(
    engine: Optional[Engine] = None,
    retries: int = 5,
    delay: float = 1.0,
    backoff: float = 2.0,
) -> None:
    """Create database tables.

    Retries obtaining a database engine a few times to tolerate transient
    connection failures during service start-up.
    """
    if engine is None:
        engine = _get_engine_with_retry(retries=retries, delay=delay, backoff=backoff)
    Base.metadata.create_all(bind=engine)