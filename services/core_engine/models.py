from sqlalchemy import Column, Integer, String, Text, DateTime, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)
    source_url = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    translated_content = Column(Text)
    summary = Column(Text)
    status = Column(String(50), default="PENDING_APPROVAL", nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)