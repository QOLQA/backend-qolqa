from config.settings import settings, TypeDB

if settings.type_db == TypeDB.mongo:
    from solution.repository_nosql import SolutionRepositoryNoSql as SolutionRepository
    from config.mongo import get_database
else:
    from solution.repository_sql import SolutionRepositorySql as SolutionRepository
    from config.sql import get_async_session as get_database
    
