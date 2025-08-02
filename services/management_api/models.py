from sqlalchemy import JSON, Column, DateTime, Integer, String, func

from .database import Base


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now())


class Destination(Base):
    __tablename__ = "destinations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    credentials = Column(JSON, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
