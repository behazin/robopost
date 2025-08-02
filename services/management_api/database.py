from typing import Generator

from sqlalchemy.orm import declarative_base

from common_utils import get_engine, get_session

Base = declarative_base()


def init_db() -> None:
    """Create database tables."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator:
    """Yield a new database session."""
    db = get_session()
    try:
        yield db
    finally:
        db.close()
