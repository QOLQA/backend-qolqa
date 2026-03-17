import logging
import pprint

from fastapi import APIRouter, Depends, status, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from application.dtos.solution.SolutionRequest import SolutionCreateRequest, SolutionPartialUpdateRequest
from application.dtos.solution.SolutionResponse import SolutionResponse
from application.dtos.version.VersionRequest import VersionCreateRequest, VersionPartialUpdateRequest
from application.dtos.version.VersionResponse import VersionResponse
from application.use_cases.solution.GetAllSolutionsForUser import get_all_solutions_for_user
from application.use_cases.solution.GetSolutionById import get_solution_by_id
from application.use_cases.solution.CreateSolution import create_solution
from application.use_cases.solution.UpdateSolution import update_solution
from application.use_cases.solution.DeleteSolution import delete_solution
from application.use_cases.version.CreateVersion import create_version
from application.use_cases.version.UpdateVersion import update_version
from infrastructure.mappers import SolutionMapper, VersionMapper
from infrastructure.repositories import SolutionRepositoryImpl, VersionRepositoryImpl
from infrastructure.repositories.QueryRepoImpl import QueryRepositoryImpl
from models.user import User
from models.version import default_version_descriptions
from auth.router import get_current_user
from api.handle_errors import handle_common_errors
from domain.errors import Forbidden
from infrastructure.db_factory import get_database
from utils.audit import log_resource_operation, log_access_denied

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


def get_solution_repository(database=Depends(get_database)) -> SolutionRepositoryImpl:
    """Dependency: always returns the MongoDB solution implementation."""
    return SolutionRepositoryImpl(database)


def get_version_repository(database=Depends(get_database)) -> VersionRepositoryImpl:
    """Dependency: always returns the MongoDB version implementation."""
    return VersionRepositoryImpl(database)


def get_query_repository(database=Depends(get_database)) -> QueryRepositoryImpl:
    """Dependency: always returns the MongoDB query implementation."""
    return QueryRepositoryImpl(database)


@router.get('', response_model=list[SolutionResponse])
@limiter.limit("100/minute")
async def get_all_solutions_endpoint(
    request: Request,
    current_user: User = Depends(get_current_user),
    solution_repository: SolutionRepositoryImpl = Depends(get_solution_repository),
) -> list[SolutionResponse]:
    """Get all solutions owned by the current user."""
    try:
        entities = await get_all_solutions_for_user(solution_repository, str(current_user.id))

        log_resource_operation(
            action="solution.list",
            user_id=str(current_user.id),
            resource_type="solution",
            resource_id="all",
            status="success",
            ip_address=request.client.host if request.client else None,
        )

        return [SolutionMapper.to_response(e) for e in entities]
    except Exception as exc:
        await handle_common_errors(exc, request)


@router.post('', response_model=SolutionResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def create_solution_endpoint(
    request: Request,
    solution_create: SolutionCreateRequest,
    current_user: User = Depends(get_current_user),
    solution_repository: SolutionRepositoryImpl = Depends(get_solution_repository),
    version_repository: VersionRepositoryImpl = Depends(get_version_repository),
) -> SolutionResponse:
    """Create a new solution with an initial version for the current user."""
    try:
        # 1. Create the solution (user_id injected by use case via mapper)
        entity = await create_solution(solution_repository, solution_create, str(current_user.id))

        # 2. Create the initial version
        version_request = VersionCreateRequest(
            submodels=[],
            description=default_version_descriptions[0],
            solution_id=entity.id,
        )
        version_entity = await create_version(version_repository, version_request)

        # 3. Update last_version_saved on the solution
        update_request = SolutionPartialUpdateRequest(last_version_saved=version_entity.id)
        updated_entity = await solution_repository.update(entity.id, update_request)

        logger.info("=" * 60)
        logger.info(">>>>>>>>>>>>> SOLUTION CREATED (clean arch):")
        logger.info(pprint.pformat(SolutionMapper.to_response(updated_entity).model_dump(), indent=2, width=100))
        logger.info("=" * 60)

        log_resource_operation(
            action="solution.create",
            user_id=str(current_user.id),
            resource_type="solution",
            resource_id=updated_entity.id,
            resource_name=updated_entity.name,
            status="success",
            ip_address=request.client.host if request.client else None,
        )

        return SolutionMapper.to_response(updated_entity)
    except Exception as exc:
        await handle_common_errors(exc, request)


@router.get('/{id}', response_model=SolutionResponse)
@limiter.limit("100/minute")
async def get_solution_endpoint(
    request: Request,
    id: str,
    current_user: User = Depends(get_current_user),
    solution_repository: SolutionRepositoryImpl = Depends(get_solution_repository),
    version_repository: VersionRepositoryImpl = Depends(get_version_repository),
) -> SolutionResponse:
    """Get a solution by ID — only if owned by the current user."""
    try:
        # Fetch base entity (no versions yet)
        entity = await solution_repository.get_by_id(id)

        # Ownership check — no domain use case needed since this is a read guard
        if entity.user_id != str(current_user.id):
            log_access_denied(
                action="solution.read",
                user_id=str(current_user.id),
                resource_type="solution",
                resource_id=str(id),
                reason="Not owner",
                ip_address=request.client.host if request.client else None,
            )
            raise Forbidden(msg="Not authorized to access this solution")

        # Fetch associated versions from the versions collection
        version_entities = await version_repository.get_by_solution_id(entity.id)
        entity = await get_solution_by_id(solution_repository, id, versions=version_entities)

        log_resource_operation(
            action="solution.read",
            user_id=str(current_user.id),
            resource_type="solution",
            resource_id=str(id),
            resource_name=entity.name,
            status="success",
            ip_address=request.client.host if request.client else None,
        )

        return SolutionMapper.to_response(entity)
    except Exception as exc:
        await handle_common_errors(exc, request)


@router.patch('/{id}', response_model=SolutionResponse)
@limiter.limit("30/minute")
async def update_solution_endpoint(
    request: Request,
    id: str,
    solution_update: SolutionPartialUpdateRequest,
    current_user: User = Depends(get_current_user),
    solution_repository: SolutionRepositoryImpl = Depends(get_solution_repository),
) -> SolutionResponse:
    """Update a solution — only if owned by the current user."""
    try:
        entity = await update_solution(
            solution_repository,
            id,
            solution_update,
            str(current_user.id),
        )

        log_resource_operation(
            action="solution.update",
            user_id=str(current_user.id),
            resource_type="solution",
            resource_id=str(id),
            resource_name=entity.name,
            status="success",
            ip_address=request.client.host if request.client else None,
        )

        return SolutionMapper.to_response(entity)
    except Exception as exc:
        await handle_common_errors(exc, request)


@router.post('/{solution_id}/versions', response_model=VersionResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def create_version_for_solution_endpoint(
    request: Request,
    solution_id: str,
    version_create: VersionCreateRequest,
    current_user: User = Depends(get_current_user),
    solution_repository: SolutionRepositoryImpl = Depends(get_solution_repository),
    version_repository: VersionRepositoryImpl = Depends(get_version_repository),
) -> VersionResponse:
    """Create a new version for a solution — only if the solution is owned by the current user."""
    try:
        # Verify solution ownership (ownership check in use case)
        solution_entity = await solution_repository.get_by_id(solution_id)
        if solution_entity.user_id != str(current_user.id):
            raise Forbidden(msg="Not authorized to create versions for this solution")

        # Ensure solution_id in version_create matches the URL parameter
        version_create.solution_id = solution_id

        # Create the version
        version_entity = await create_version(version_repository, version_create)

        # Update last_version_saved in the solution
        update_request = SolutionPartialUpdateRequest(last_version_saved=version_entity.id)
        await solution_repository.update(solution_id, update_request)

        log_resource_operation(
            action="version.create",
            user_id=str(current_user.id),
            resource_type="version",
            resource_id=version_entity.id,
            resource_name=version_create.description,
            status="success",
            ip_address=request.client.host if request.client else None,
        )

        return VersionMapper.to_response(version_entity)
    except Exception as exc:
        await handle_common_errors(exc, request)


@router.patch('/{solution_id}/versions/{version_id}', response_model=VersionResponse)
@limiter.limit("30/minute")
async def update_solution_version_endpoint(
    request: Request,
    solution_id: str,
    version_id: str,
    version_update: VersionPartialUpdateRequest,
    current_user: User = Depends(get_current_user),
    solution_repository: SolutionRepositoryImpl = Depends(get_solution_repository),
    version_repository: VersionRepositoryImpl = Depends(get_version_repository),
) -> VersionResponse:
    """Update a specific version of a solution — only if the solution is owned by the current user."""
    try:
        # Verify solution ownership
        solution_entity = await solution_repository.get_by_id(solution_id)
        if solution_entity.user_id != str(current_user.id):
            raise Forbidden(msg="Not authorized to modify this solution")

        # Update last_version_saved field in the solution
        update_solution_request = SolutionPartialUpdateRequest(last_version_saved=version_id)
        await solution_repository.update(solution_id, update_solution_request)

        # Update the version
        version_entity = await update_version(version_repository, version_id, version_update)

        log_resource_operation(
            action="version.update",
            user_id=str(current_user.id),
            resource_type="version",
            resource_id=version_id,
            resource_name=version_entity.description,
            status="success",
            ip_address=request.client.host if request.client else None,
        )

        return VersionMapper.to_response(version_entity)
    except Exception as exc:
        await handle_common_errors(exc, request)


@router.delete('/{id}', status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_solution_endpoint(
    request: Request,
    id: str,
    current_user: User = Depends(get_current_user),
    solution_repository: SolutionRepositoryImpl = Depends(get_solution_repository),
    version_repository: VersionRepositoryImpl = Depends(get_version_repository),
    query_repository: QueryRepositoryImpl = Depends(get_query_repository),
) -> None:
    """Delete a solution and all associated versions and queries — only if owned by the current user."""
    try:
        # Fetch solution name for audit log before deletion
        entity = await solution_repository.get_by_id(id)

        await delete_solution(
            solution_repository=solution_repository,
            solution_id=id,
            current_user_id=str(current_user.id),
            version_repository=version_repository,
            query_repository=query_repository,
        )

        log_resource_operation(
            action="solution.delete",
            user_id=str(current_user.id),
            resource_type="solution",
            resource_id=str(id),
            resource_name=entity.name,
            status="success",
            ip_address=request.client.host if request.client else None,
        )

        return None
    except Exception as exc:
        await handle_common_errors(exc, request)
