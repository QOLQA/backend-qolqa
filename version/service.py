from models.version import VersionCreate, Version, VersionPartialUpdate
from domain.repositories.user.repo import Repository

async def get_all(repository: Repository) -> list[Version]:
    """Get all versions from the repository"""
    return await repository.get_all()

async def get_one(repository: Repository, id: str | int) -> Version:
    """Get a specific version by ID"""
    return await repository.get_by_id(id)

async def create(repository: Repository, version: VersionCreate) -> Version:
    """Create a new version"""
    return await repository.add(version)

async def modify(
    repository: Repository,
    id: str | int,
    version_update: VersionPartialUpdate,
) -> Version:
    """Update an existing version"""
    return await repository.update(id, version_update)

async def delete(
    repository: Repository,
    id: str | int,
) -> None:
    """Delete a version by ID"""
    return await repository.delete(id)