from typing import Optional

from sqlalchemy.engine import Engine

from common_utils import get_engine
from .models import Base


def init_db(engine: Optional[Engine] = None) -> None:
    """Create database tables."""
    if engine is None:
        engine = get_engine()
    Base.metadata.create_all(bind=engine)