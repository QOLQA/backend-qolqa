from fastapi import Depends

from interfaces.repository import Repository
from models.settings import settings, TypeDB

# if settings.type_db == TypeDB.mongo:
#     from solution.repository_nosql import SolutionRepositoryNoSql as SolutionRepository
#     from config.mongo import get_database
# else:
#     from solution.repository_sql import SolutionRepositorySql as SolutionRepository
#     from config.sql import get_async_session as get_database

from solution.repository_sql import SolutionRepositorySql as SolutionRepository
from config.sql import get_async_session as get_database

async def get_repository(
    database = Depends(get_database),
) -> Repository:
    return SolutionRepository(database)
