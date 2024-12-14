from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from schemas.solution import Base

from models.settings import settings

DATABASE_URL = f'postgresql+asyncpg://roswell:pando@localhost:5434/qolqa'


engine = create_async_engine(DATABASE_URL)


async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def create_all_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)