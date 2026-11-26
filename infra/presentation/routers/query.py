from fastapi import APIRouter, Request, status

from application.dtos.query.commands import CreateQueryCommand, UpdateQueryCommand
from application.use_cases.query.CreateQuery import create_query
from application.use_cases.query.DeleteQueriesBySolution import (
    delete_queries_by_solution,
)
from application.use_cases.query.DeleteQuery import delete_query
from application.use_cases.query.GetAllQueries import get_all_queries
from application.use_cases.query.GetQueriesBySolution import get_queries_by_solution
from application.use_cases.query.GetQueryById import get_query_by_id
from application.use_cases.query.UpdateQuery import update_query
from config.rate_limiter import limiter
from infra.persistence.audit import log_resource_operation
from infra.persistence.mappers import QueryMapper
from infra.presentation.dependencies import (
    CurrentUserDep,
    QueryRepoDep,
    SolutionRepoDep,
)
from infra.presentation.dtos.query.request import (
    QueryCreateRequest,
    QueryPartialUpdateRequest,
)
from infra.presentation.dtos.query.response import QueryResponse

router = APIRouter()


@router.get('', response_model=list[QueryResponse])
@limiter.limit("100/minute")
async def get_all_queries_endpoint(
    request: Request,
    current_user: CurrentUserDep,
    repository: QueryRepoDep,
    solution_repository: SolutionRepoDep,
) -> list[QueryResponse]:
    """Get all queries owned by the current user."""
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


@router.get('/solution/{solution_id}', response_model=list[QueryResponse])
@limiter.limit("100/minute")
async def get_queries_by_solution_endpoint(
    solution_id: str,
    request: Request,
    current_user: CurrentUserDep,
    repository: QueryRepoDep,
    solution_repository: SolutionRepoDep,
) -> list[QueryResponse]:
    """Get all queries for a specific solution owned by the current user."""
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


@router.get('/{query_id}', response_model=QueryResponse)
@limiter.limit("100/minute")
async def get_query_endpoint(
    query_id: str,
    request: Request,
    current_user: CurrentUserDep,
    repository: QueryRepoDep,
    solution_repository: SolutionRepoDep,
) -> QueryResponse:
    """Get a specific query by id — only if owned by the current user."""
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


@router.post('', response_model=QueryResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def create_query_endpoint(
    request: Request,
    query_create: QueryCreateRequest,
    current_user: CurrentUserDep,
    repository: QueryRepoDep,
    solution_repository: SolutionRepoDep,
) -> QueryResponse:
    """Create a new query on a solution owned by the current user."""
    command = CreateQueryCommand(
        full_query=query_create.full_query,
        collections=query_create.collections,
        highlighted_words=query_create.highlighted_words,
        solution_id=query_create.solution_id,
        current_user_id=str(current_user.id),
    )
    entity = await create_query(
        repository, solution_repository, command
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


@router.patch('/{query_id}', response_model=QueryResponse)
@limiter.limit("30/minute")
async def update_query_endpoint(
    query_id: str,
    request: Request,
    query_update: QueryPartialUpdateRequest,
    current_user: CurrentUserDep,
    repository: QueryRepoDep,
    solution_repository: SolutionRepoDep,
) -> QueryResponse:
    """Update an existing query — only if owned by the current user."""
    command = UpdateQueryCommand(
        full_query=query_update.full_query,
        collections=query_update.collections,
        highlighted_words=query_update.highlighted_words,
    )
    entity = await update_query(
        repository, solution_repository, query_id, command, str(current_user.id)
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


@router.delete('/{query_id}', status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("20/minute")
async def delete_query_endpoint(
    query_id: str,
    request: Request,
    current_user: CurrentUserDep,
    repository: QueryRepoDep,
    solution_repository: SolutionRepoDep,
):
    """Delete a query — only if owned by the current user."""
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


@router.delete('/solution/{solution_id}', status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_queries_by_solution_endpoint(
    solution_id: str,
    request: Request,
    current_user: CurrentUserDep,
    repository: QueryRepoDep,
    solution_repository: SolutionRepoDep,
):
    """Delete all queries for a specific solution owned by the current user."""
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

