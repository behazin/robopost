"""Simplified database layer for the kata tests.

The real project uses SQLAlchemy with an async engine; however installing
all dependencies (like database drivers) is unnecessary for these unit
tests.  Instead we provide lightweight stand-ins that satisfy the
interface expected by the CRUD functions and FastAPI dependencies.
"""

from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession


class DummyResult:
    """Minimal result object mimicking SQLAlchemy's execution result."""

    rowcount = 0

    def scalar_one_or_none(self):
        return None


class DummyAsyncSession:
    def add(self, *args, **kwargs):
        pass

    async def commit(self):
        pass

    async def execute(self, *args, **kwargs):
        return DummyResult()

    async def refresh(self, *args, **kwargs):
        pass


@asynccontextmanager
async def get_db() -> AsyncSession:  # type: ignore[misc]
    """Dependency that yields a dummy async session."""
    yield DummyAsyncSession()


async def init_db():
    """No-op database initialisation for tests."""
    return