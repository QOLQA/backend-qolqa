from fastapi import APIRouter, Depends, status, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from models.query import Query, QueryCreate, QueryPartialUpdate
from models.user import User
from query import service
from query.repository_sql import QueryRepositorySql
from query.repository_nosql import QueryRepositoryNoSql

from auth.router import get_current_user
from utils.handle_errors import handle_common_errors
from utils.get_database import get_database
from utils.audit import log_resource_operation, log_access_denied
from config.settings import settings, TypeDB

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


def get_query_repository(database=Depends(get_database)):
    """Dependency to get the appropriate repository based on database type"""
    if settings.type_db == TypeDB.sql:
        return QueryRepositorySql(database)
    else:
        return QueryRepositoryNoSql(database)


@router.get('', response_model=list[Query])
@limiter.limit("100/minute")
async def get_all_queries(
    request: Request,
    current_user: User = Depends(get_current_user),
    repository=Depends(get_query_repository),
) -> list[Query]:
    """Get all queries (admin endpoint)"""
    try:
        all_queries = await service.get_all(repository)
        
        log_resource_operation(
            action="query.list",
            user_id=str(current_user.id),
            resource_type="query",
            resource_id="all",
            status="success",
            ip_address=request.client.host if request.client else None
        )
        
        return all_queries
    except Exception as e:
        await handle_common_errors(e, request)


@router.get('/solution/{solution_id}', response_model=list[Query])
@limiter.limit("100/minute")
async def get_queries_by_solution(
    solution_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    repository=Depends(get_query_repository),
) -> list[Query]:
    """Get all queries for a specific solution"""
    try:
        queries = await service.get_by_solution(repository, solution_id)
        
        log_resource_operation(
            action="query.list_by_solution",
            user_id=str(current_user.id),
            resource_type="query",
            resource_id=solution_id,
            status="success",
            ip_address=request.client.host if request.client else None
        )
        
        return queries
    except Exception as e:
        await handle_common_errors(e, request)


@router.get('/{query_id}', response_model=Query)
@limiter.limit("100/minute")
async def get_query(
    query_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    repository=Depends(get_query_repository),
) -> Query:
    """Get a specific query by id"""
    try:
        query = await service.get_one(repository, query_id)
        
        log_resource_operation(
            action="query.read",
            user_id=str(current_user.id),
            resource_type="query",
            resource_id=query_id,
            status="success",
            ip_address=request.client.host if request.client else None
        )
        
        return query
    except Exception as e:
        await handle_common_errors(e, request)


@router.post('', response_model=Query, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def create_query(
    request: Request,
    query_create: QueryCreate,
    current_user: User = Depends(get_current_user),
    repository=Depends(get_query_repository),
) -> Query:
    """Create a new query"""
    try:
        new_query = await service.create(repository, query_create)
        
        log_resource_operation(
            action="query.create",
            user_id=str(current_user.id),
            resource_type="query",
            resource_id=str(new_query.id),
            status="success",
            ip_address=request.client.host if request.client else None
        )
        
        return new_query
    except Exception as e:
        await handle_common_errors(e, request)


@router.patch('/{query_id}', response_model=Query)
@limiter.limit("30/minute")
async def update_query(
    query_id: str,
    request: Request,
    query_update: QueryPartialUpdate,
    current_user: User = Depends(get_current_user),
    repository=Depends(get_query_repository),
) -> Query:
    """Update an existing query"""
    try:
        updated_query = await service.modify(repository, query_id, query_update)
        
        log_resource_operation(
            action="query.update",
            user_id=str(current_user.id),
            resource_type="query",
            resource_id=query_id,
            status="success",
            ip_address=request.client.host if request.client else None
        )
        
        return updated_query
    except Exception as e:
        await handle_common_errors(e, request)


@router.delete('/{query_id}', status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("20/minute")
async def delete_query(
    query_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    repository=Depends(get_query_repository),
):
    """Delete a query"""
    try:
        await service.delete(repository, query_id)
        
        log_resource_operation(
            action="query.delete",
            user_id=str(current_user.id),
            resource_type="query",
            resource_id=query_id,
            status="success",
            ip_address=request.client.host if request.client else None
        )
        
        return None
    except Exception as e:
        await handle_common_errors(e, request)


@router.delete('/solution/{solution_id}', status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_queries_by_solution(
    solution_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    repository=Depends(get_query_repository),
):
    """Delete all queries for a specific solution"""
    try:
        await service.delete_by_solution(repository, solution_id)
        
        log_resource_operation(
            action="query.delete_by_solution",
            user_id=str(current_user.id),
            resource_type="query",
            resource_id=solution_id,
            status="success",
            ip_address=request.client.host if request.client else None
        )
        
        return None
    except Exception as e:
        await handle_common_errors(e, request)
