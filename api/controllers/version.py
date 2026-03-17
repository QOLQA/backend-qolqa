from fastapi import APIRouter, Depends, status, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from application.dtos.version.VersionRequest import VersionCreateRequest, VersionPartialUpdateRequest
from application.dtos.version.VersionResponse import VersionResponse
from application.use_cases.version.GetAllVersions import get_all_versions
from application.use_cases.version.GetVersionById import get_version_by_id
from application.use_cases.version.CreateVersion import create_version
from application.use_cases.version.UpdateVersion import update_version
from application.use_cases.version.DeleteVersion import delete_version
from infrastructure.mappers import VersionMapper
from infrastructure.repositories import VersionRepositoryImpl
from models.user import User
from auth.router import get_current_user
from api.handle_errors import handle_common_errors
from infrastructure.db_factory import get_database
from utils.audit import log_resource_operation

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


def get_version_repository(database=Depends(get_database)) -> VersionRepositoryImpl:
    """Dependency: always returns the MongoDB implementation."""
    return VersionRepositoryImpl(database)


@router.get('', response_model=list[VersionResponse])
@limiter.limit("100/minute")
async def get_all_versions_endpoint(
    request: Request,
    current_user: User = Depends(get_current_user),
    repository: VersionRepositoryImpl = Depends(get_version_repository),
) -> list[VersionResponse]:
    """Get all versions."""
    try:
        entities = await get_all_versions(repository)

        log_resource_operation(
            action="version.list",
            user_id=str(current_user.id),
            resource_type="version",
            resource_id="all",
            status="success",
            ip_address=request.client.host if request.client else None,
        )

        return [VersionMapper.to_response(e) for e in entities]
    except Exception as e:
        await handle_common_errors(e, request)


@router.get('/{version_id}', response_model=VersionResponse)
@limiter.limit("100/minute")
async def get_version_endpoint(
    version_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    repository: VersionRepositoryImpl = Depends(get_version_repository),
) -> VersionResponse:
    """Get a specific version by id."""
    try:
        entity = await get_version_by_id(repository, version_id)

        log_resource_operation(
            action="version.read",
            user_id=str(current_user.id),
            resource_type="version",
            resource_id=version_id,
            status="success",
            ip_address=request.client.host if request.client else None,
        )

        return VersionMapper.to_response(entity)
    except Exception as e:
        await handle_common_errors(e, request)


@router.post('', response_model=VersionResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def create_version_endpoint(
    request: Request,
    version_create: VersionCreateRequest,
    current_user: User = Depends(get_current_user),
    repository: VersionRepositoryImpl = Depends(get_version_repository),
) -> VersionResponse:
    """Create a new version."""
    try:
        entity = await create_version(repository, version_create)

        log_resource_operation(
            action="version.create",
            user_id=str(current_user.id),
            resource_type="version",
            resource_id=entity.id,
            status="success",
            ip_address=request.client.host if request.client else None,
        )

        return VersionMapper.to_response(entity)
    except Exception as e:
        await handle_common_errors(e, request)


@router.patch('/{version_id}', response_model=VersionResponse)
@limiter.limit("30/minute")
async def update_version_endpoint(
    version_id: str,
    request: Request,
    version_update: VersionPartialUpdateRequest,
    current_user: User = Depends(get_current_user),
    repository: VersionRepositoryImpl = Depends(get_version_repository),
) -> VersionResponse:
    """Update an existing version."""
    try:
        entity = await update_version(repository, version_id, version_update)

        log_resource_operation(
            action="version.update",
            user_id=str(current_user.id),
            resource_type="version",
            resource_id=version_id,
            status="success",
            ip_address=request.client.host if request.client else None,
        )

        return VersionMapper.to_response(entity)
    except Exception as e:
        await handle_common_errors(e, request)


@router.delete('/{version_id}', status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("20/minute")
async def delete_version_endpoint(
    version_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    repository: VersionRepositoryImpl = Depends(get_version_repository),
):
    """Delete a version."""
    try:
        await delete_version(repository, version_id)

        log_resource_operation(
            action="version.delete",
            user_id=str(current_user.id),
            resource_type="version",
            resource_id=version_id,
            status="success",
            ip_address=request.client.host if request.client else None,
        )

        return None
    except Exception as e:
        await handle_common_errors(e, request)
