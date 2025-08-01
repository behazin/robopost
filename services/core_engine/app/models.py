import enum
from sqlalchemy import (Column, Integer, String, JSON, Enum, ForeignKey, 
                        Boolean, DateTime, Text)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()

class ArticleStatus(enum.Enum):
    PROCESSING = "PROCESSING"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PUBLISHING = "PUBLISHING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"

class Platform(enum.Enum):
    TELEGRAM = "TELEGRAM"
    WORDPRESS = "WORDPRESS"
    INSTAGRAM = "INSTAGRAM"
    TWITTER = "TWITTER"
    
class PublicationStatus(enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Source(Base):
    __tablename__ = 'sources'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    url = Column(String(2048), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    articles = relationship("Article", back_populates="source")
    destinations = relationship("Destination", secondary="source_destination_map", back_populates="sources")

class Destination(Base):
    __tablename__ = 'destinations'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    platform = Column(Enum(Platform), nullable=False)
    credentials = Column(JSON, nullable=False)
    rate_limit_per_minute = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sources = relationship("Source", secondary="source_destination_map", back_populates="destinations")
    admins = relationship("Admin", secondary="admin_destination_map", back_populates="destinations")

class SourceDestinationMap(Base):
    __tablename__ = 'source_destination_map'
    source_id = Column(Integer, ForeignKey('sources.id'), primary_key=True)
    destination_id = Column(Integer, ForeignKey('destinations.id'), primary_key=True)
    enabled = Column(Boolean, default=True, nullable=False)

class Admin(Base):
    __tablename__ = 'admins'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String(255), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    destinations = relationship("Destination", secondary="admin_destination_map", back_populates="admins")

class AdminDestinationMap(Base):
    __tablename__ = 'admin_destination_map'
    admin_id = Column(Integer, ForeignKey('admins.id'), primary_key=True)
    destination_id = Column(Integer, ForeignKey('destinations.id'), primary_key=True)

class Article(Base):
    __tablename__ = 'articles'
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey('sources.id'), nullable=False)
    original_url = Column(String(2048), nullable=False, unique=True)
    status = Column(Enum(ArticleStatus), nullable=False, default=ArticleStatus.PROCESSING)
    assigned_destinations = Column(JSON, nullable=True) # [{"platform": "TELEGRAM", "destination_id": 12}, ...]
    processed_title = Column(Text, nullable=True)
    processed_content = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    source = relationship("Source", back_populates="articles")

class PublicationLog(Base):
    __tablename__ = 'publication_logs'
    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('articles.id'), nullable=False)
    destination_id = Column(Integer, ForeignKey('destinations.id'), nullable=False)
    platform = Column(Enum(Platform), nullable=False)
    status = Column(Enum(PublicationStatus), nullable=False)
    published_at = Column(DateTime(timezone=True), server_default=func.now())
    log_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    last_error_reason = Column(Text, nullable=True)