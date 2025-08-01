from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from .config import settings
from .models import Base

engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)

AsyncSessionFactory = sessionmaker(
    engine,
    autocommit=False,
    autoflush=False,
    class_=AsyncSession,
    expire_on_commit=False
)

def get_session_factory():
    return AsyncSessionFactory

async def init_db():
    """Initializes the database and creates tables if they don't exist."""
    async with engine.begin() as conn:
        # This is for development only. For production, use Alembic migrations.
        await conn.run_sync(Base.metadata.create_all)