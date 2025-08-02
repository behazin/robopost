import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_engine = None
_SessionLocal = None


def _get_db_url() -> str:
    user = os.getenv("MYSQL_USER", "root")
    password = os.getenv("MYSQL_PASSWORD", "")
    host = os.getenv("MYSQL_HOST", "localhost")
    port = os.getenv("MYSQL_PORT", "3306")
    db = os.getenv("MYSQL_DB", "app")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}"


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(_get_db_url(), pool_pre_ping=True)
    return _engine


def get_session():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autocommit=False, autoflush=False)
    return _SessionLocal()
