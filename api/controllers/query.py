from fastapi import APIRouter, Depends, status, Request

from application.dtos.query.QueryRequest import QueryCreateRequest, QueryPartialUpdateRequest
from application.dtos.query.QueryResponse import QueryResponse
from application.use_cases.query.GetAllQueries import get_all_queries
from application.use_cases.query.GetQueryById import get_query_by_id
from application.use_cases.query.GetQueriesBySolution import get_queries_by_solution
from application.use_cases.query.CreateQuery import create_query
from application.use_cases.query.UpdateQuery import update_query
from application.use_cases.query.DeleteQuery import delete_query
from application.use_cases.query.DeleteQueriesBySolution import delete_queries_by_solution
from infrastructure.mappers import QueryMapper
from infrastructure.repositories import QueryRepositoryImpl, SolutionRepositoryImpl
from domain.entities.auth.UserEntity import UserEntity as User
from api.controllers.auth import get_current_user
from api.handle_errors import handle_common_errors
from infrastructure.db_factory import get_database
from infrastructure.audit import log_resource_operation
from config.rate_limiter import limiter

router = APIRouter()


def get_query_repository(database=Depends(get_database)) -> QueryRepositoryImpl:
    """Dependency: always returns the MongoDB implementation."""
    return QueryRepositoryImpl(database)


def get_solution_repository(database=Depends(get_database)) -> SolutionRepositoryImpl:
    """Dependency: always returns the MongoDB solution implementation."""
    return SolutionRepositoryImpl(database)


@router.get('', response_model=list[QueryResponse])
@limiter.limit("100/minute")
async def get_all_queries_endpoint(
    request: Request,
    current_user: User = Depends(get_current_user),
    repository: QueryRepositoryImpl = Depends(get_query_repository),
    solution_repository: SolutionRepositoryImpl = Depends(get_solution_repository),
) -> list[QueryResponse]:
    """Get all queries owned by the current user."""
    try:
        entities = await get_all_queries(repository, solution_repository, str(current_user.id))

        log_resource_operation(
            action="query.list",
            user_id=str(current_user.id),
            resource_type="query",
            resource_id="all",
            status="success",
            ip_address=request.client.host if request.client else None,
        )

        return [QueryMapper.to_response(e) for e in entities]
    except Exception as e:
        await handle_common_errors(e, request)


@router.get('/solution/{solution_id}', response_model=list[QueryResponse])
@limiter.limit("100/minute")
async def get_queries_by_solution_endpoint(
    solution_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    repository: QueryRepositoryImpl = Depends(get_query_repository),
    solution_repository: SolutionRepositoryImpl = Depends(get_solution_repository),
) -> list[QueryResponse]:
    """Get all queries for a specific solution owned by the current user."""
    try:
        entities = await get_queries_by_solution(
            repository, solution_repository, solution_id, str(current_user.id)
        )

        log_resource_operation(
            action="query.list_by_solution",
            user_id=str(current_user.id),
            resource_type="query",
            resource_id=solution_id,
            status="success",
            ip_address=request.client.host if request.client else None,
        )

        return [QueryMapper.to_response(e) for e in entities]
    except Exception as e:
        await handle_common_errors(e, request)


@router.get('/{query_id}', response_model=QueryResponse)
@limiter.limit("100/minute")
async def get_query_endpoint(
    query_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    repository: QueryRepositoryImpl = Depends(get_query_repository),
    solution_repository: SolutionRepositoryImpl = Depends(get_solution_repository),
) -> QueryResponse:
    """Get a specific query by id — only if owned by the current user."""
    try:
        entity = await get_query_by_id(
            repository, solution_repository, query_id, str(current_user.id)
        )

        log_resource_operation(
            action="query.read",
            user_id=str(current_user.id),
            resource_type="query",
            resource_id=query_id,
            status="success",
            ip_address=request.client.host if request.client else None,
        )

        return QueryMapper.to_response(entity)
    except Exception as e:
        await handle_common_errors(e, request)


@router.post('', response_model=QueryResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def create_query_endpoint(
    request: Request,
    query_create: QueryCreateRequest,
    current_user: User = Depends(get_current_user),
    repository: QueryRepositoryImpl = Depends(get_query_repository),
    solution_repository: SolutionRepositoryImpl = Depends(get_solution_repository),
) -> QueryResponse:
    """Create a new query on a solution owned by the current user."""
    try:
        entity = await create_query(
            repository, solution_repository, query_create, str(current_user.id)
        )

        log_resource_operation(
            action="query.create",
            user_id=str(current_user.id),
            resource_type="query",
            resource_id=entity.id,
            status="success",
            ip_address=request.client.host if request.client else None,
        )

        return QueryMapper.to_response(entity)
    except Exception as e:
        await handle_common_errors(e, request)


@router.patch('/{query_id}', response_model=QueryResponse)
@limiter.limit("30/minute")
async def update_query_endpoint(
    query_id: str,
    request: Request,
    query_update: QueryPartialUpdateRequest,
    current_user: User = Depends(get_current_user),
    repository: QueryRepositoryImpl = Depends(get_query_repository),
    solution_repository: SolutionRepositoryImpl = Depends(get_solution_repository),
) -> QueryResponse:
    """Update an existing query — only if owned by the current user."""
    try:
        entity = await update_query(
            repository, solution_repository, query_id, query_update, str(current_user.id)
        )

        log_resource_operation(
            action="query.update",
            user_id=str(current_user.id),
            resource_type="query",
            resource_id=query_id,
            status="success",
            ip_address=request.client.host if request.client else None,
        )

        return QueryMapper.to_response(entity)
    except Exception as e:
        await handle_common_errors(e, request)


@router.delete('/{query_id}', status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("20/minute")
async def delete_query_endpoint(
    query_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    repository: QueryRepositoryImpl = Depends(get_query_repository),
    solution_repository: SolutionRepositoryImpl = Depends(get_solution_repository),
):
    """Delete a query — only if owned by the current user."""
    try:
        await delete_query(
            repository, solution_repository, query_id, str(current_user.id)
        )

        log_resource_operation(
            action="query.delete",
            user_id=str(current_user.id),
            resource_type="query",
            resource_id=query_id,
            status="success",
            ip_address=request.client.host if request.client else None,
        )

        return None
    except Exception as e:
        await handle_common_errors(e, request)


@router.delete('/solution/{solution_id}', status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_queries_by_solution_endpoint(
    solution_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    repository: QueryRepositoryImpl = Depends(get_query_repository),
    solution_repository: SolutionRepositoryImpl = Depends(get_solution_repository),
):
    """Delete all queries for a specific solution owned by the current user."""
    try:
        await delete_queries_by_solution(
            repository, solution_repository, solution_id, str(current_user.id)
        )

        log_resource_operation(
            action="query.delete_by_solution",
            user_id=str(current_user.id),
            resource_type="query",
            resource_id=solution_id,
            status="success",
            ip_address=request.client.host if request.client else None,
        )

        return None
    except Exception as e:
        await handle_common_errors(e, request)
