import time
from typing import Optional

from sqlalchemy.engine import Engine

from common_utils import get_engine
from .models import Base


def init_db(engine: Optional[Engine] = None, retries: int = 5, delay: float = 1.0) -> None:
    """Create database tables.

    Retries obtaining a database engine a few times to tolerate transient
    connection failures during service start-up.
    """
    if engine is None:
        for attempt in range(retries):
            try:
                engine = get_engine()
                break
            except Exception:
                if attempt == retries - 1:
                    raise
                time.sleep(delay)
    Base.metadata.create_all(bind=engine)