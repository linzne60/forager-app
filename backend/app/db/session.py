from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# create async engine with pooling
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,    # logs sql when in dev mode
    pool_pre_ping=True,     # verifies connection health
    pool_recycle=3600,      # recycle connections after 1 hour
)

# async-safe session  factory
async_session_factory = async_sessionmaker(
    engine,
    expire_on_commit=False,  # prevent attribute expiration after commit; needed for asyc patterns
    autoflush=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise