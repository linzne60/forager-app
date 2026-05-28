import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings
from app.db.session import get_db
from app.main import app
from app.rate_limit import limiter

# NullPool disables connection pooling — each DB call gets a fresh connection
# on the current event loop, so there's no cross-test loop contamination
_test_engine = create_async_engine(settings.database_url, poolclass=NullPool)
_test_session_factory = async_sessionmaker(_test_engine, expire_on_commit=False)


async def _get_test_db():
    async with _test_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest.fixture
async def client():
    app.dependency_overrides[get_db] = _get_test_db
    limiter.enabled = False
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c
    limiter.enabled = True
    app.dependency_overrides.clear()


@pytest.fixture
async def db():
    async with _test_session_factory() as session:
        yield session
