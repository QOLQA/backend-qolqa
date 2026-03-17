"""
Lazy database factory
The get_database dependency function decides at CALL TIME which backend to use,
based on settings.type_db. No import-time branching.
"""
from typing import AsyncGenerator

from config.settings import settings, TypeDB


async def get_database():
    """
    FastAPI dependency: yields (SQL) or returns (MongoDB) the database session/connection.
    The DB type decision happens at call time, not at import time.
    """
    if settings.type_db == TypeDB.mongo:
        from config.mongo import get_database as _get_mongo_db
        yield _get_mongo_db()
    else:
        from config.sql import get_async_session
        async for session in get_async_session():
            yield session
