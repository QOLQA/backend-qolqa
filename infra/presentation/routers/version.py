from fastapi import APIRouter, Request, status

from application.dtos.version.commands import CreateVersionCommand, UpdateVersionCommand
from application.use_cases.version.CreateVersion import create_version
from application.use_cases.version.DeleteVersion import delete_version
from application.use_cases.version.GetAllVersions import get_all_versions
from application.use_cases.version.GetVersionById import get_version_by_id
from application.use_cases.version.UpdateVersion import update_version
from config.rate_limiter import limiter
from infra.persistence.audit import log_resource_operation
from infra.persistence.mappers import VersionMapper
from infra.presentation.dependencies import (
    CurrentUserDep,
    SolutionRepoDep,
    VersionRepoDep,
)
from infra.presentation.dtos.version.request import (
    VersionCreateRequest,
    VersionPartialUpdateRequest,
)
from infra.presentation.dtos.version.response import VersionResponse

router = APIRouter()


@router.get('', response_model=list[VersionResponse])
@limiter.limit("100/minute")
async def get_all_versions_endpoint(
    request: Request,
    current_user: CurrentUserDep,
    repository: VersionRepoDep,
    solution_repository: SolutionRepoDep,
) -> list[VersionResponse]:
    """Get all versions owned by the current user."""
    entities = await get_all_versions(
        repository, solution_repository, str(current_user.id)
    )

    log_resource_operation(
        action="version.list",
        user_id=str(current_user.id),
        resource_type="version",
        resource_id="all",
        status="success",
        ip_address=request.client.host if request.client else None,
    )

    return [VersionMapper.to_response(e) for e in entities]


@router.get('/{version_id}', response_model=VersionResponse)
@limiter.limit("100/minute")
async def get_version_endpoint(
    version_id: str,
    request: Request,
    current_user: CurrentUserDep,
    repository: VersionRepoDep,
    solution_repository: SolutionRepoDep,
) -> VersionResponse:
    """Get a specific version by id — only if owned by the current user."""
    entity = await get_version_by_id(
        repository, solution_repository, version_id, str(current_user.id)
    )

    log_resource_operation(
        action="version.read",
        user_id=str(current_user.id),
        resource_type="version",
        resource_id=version_id,
        status="success",
        ip_address=request.client.host if request.client else None,
    )

    return VersionMapper.to_response(entity)


@router.post('', response_model=VersionResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def create_version_endpoint(
    request: Request,
    version_create: VersionCreateRequest,
    current_user: CurrentUserDep,
    repository: VersionRepoDep,
    solution_repository: SolutionRepoDep,
) -> VersionResponse:
    """Create a new version on a solution owned by the current user."""
    command = CreateVersionCommand(
        submodels=version_create.submodels,
        description=version_create.description,
        solution_id=version_create.solution_id,
        current_user_id=str(current_user.id),
    )
    entity = await create_version(
        repository, solution_repository, command
    )

    log_resource_operation(
        action="version.create",
        user_id=str(current_user.id),
        resource_type="version",
        resource_id=entity.id,
        status="success",
        ip_address=request.client.host if request.client else None,
    )

    return VersionMapper.to_response(entity)


@router.patch('/{version_id}', response_model=VersionResponse)
@limiter.limit("30/minute")
async def update_version_endpoint(
    version_id: str,
    request: Request,
    version_update: VersionPartialUpdateRequest,
    current_user: CurrentUserDep,
    repository: VersionRepoDep,
    solution_repository: SolutionRepoDep,
) -> VersionResponse:
    """Update an existing version — only if owned by the current user."""
    command = UpdateVersionCommand(
        submodels=version_update.submodels,
        description=version_update.description,
        solution_id=version_update.solution_id,
    )
    entity = await update_version(
        repository, solution_repository, version_id, command, str(current_user.id)
    )

    log_resource_operation(
        action="version.update",
        user_id=str(current_user.id),
        resource_type="version",
        resource_id=version_id,
        status="success",
        ip_address=request.client.host if request.client else None,
    )

    return VersionMapper.to_response(entity)


@router.delete('/{version_id}', status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("20/minute")
async def delete_version_endpoint(
    version_id: str,
    request: Request,
    current_user: CurrentUserDep,
    repository: VersionRepoDep,
    solution_repository: SolutionRepoDep,
):
    """Delete a version — only if owned by the current user."""
    await delete_version(
        repository, solution_repository, version_id, str(current_user.id)
    )

    log_resource_operation(
        action="version.delete",
        user_id=str(current_user.id),
        resource_type="version",
        resource_id=version_id,
        status="success",
        ip_address=request.client.host if request.client else None,
    )

