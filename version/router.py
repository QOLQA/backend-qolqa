from fastapi import APIRouter, Depends, status

from models.version import Version, VersionCreate, VersionPartialUpdate
from version import service
from version.repository_nosql import VersionRepositoryNoSql

from api.handle_errors import handle_common_errors
from infrastructure.db_factory import get_database

router = APIRouter()


@router.get('', response_model=list[Version])
async def all(
    database = Depends(get_database),
) -> list[Version]:
    """Get all versions"""
    return await service.get_all(VersionRepositoryNoSql(database))


@router.post('', response_model=Version, status_code=status.HTTP_201_CREATED)
async def create(
    version_create: VersionCreate,
    database = Depends(get_database),
) -> Version:
    """Create a new version"""
    try:
        return await service.create(VersionRepositoryNoSql(database), version_create)
    except Exception as exc:
        await handle_common_errors(exc)


@router.get('/{id}', response_model=Version)
async def get(
    id: int | str,
    database = Depends(get_database),
) -> Version:
    """Get a specific version by ID"""
    try:
        return await service.get_one(VersionRepositoryNoSql(database), id)
    except Exception as exc:
        await handle_common_errors(exc)


@router.patch('/{id}', response_model=Version)
async def update(
    id: str | int,
    version_update: VersionPartialUpdate,
    database = Depends(get_database),
) -> Version:
    """Update a specific version"""
    try:
        return await service.modify(VersionRepositoryNoSql(database), id, version_update)
    except Exception as exc:
        await handle_common_errors(exc)
    

@router.delete('/{id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    id: str | int,
    database = Depends(get_database),
) -> None:
    """Delete a specific version"""
    try:
        return await service.delete(VersionRepositoryNoSql(database), id)
    except Exception as exc:
        await handle_common_errors(exc)