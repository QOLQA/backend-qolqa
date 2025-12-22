from datetime import datetime
from models.solution import SolutionCreate, Solution, SolutionPartialUpdate
from models.version import Version, VersionCreate, VersionPartialUpdate
from interfaces.repository import Repository

async def get_all(repository: Repository) -> list[Solution]:
    return await repository.get_all()

async def get_one(repository: Repository, id: str | int):
    return await repository.get_by_id(id)

async def create(repository: Repository, solution: SolutionCreate) -> Solution:
    # Add timestamp when creating
    solution_data = solution.model_dump()
    solution_data['last_updated_at'] = datetime.utcnow()
    return await repository.add(solution_data)

async def modify(
    repository: Repository,
    id: str | int,
    solution_update: SolutionPartialUpdate,
) -> Solution:
    # Always update the timestamp when modifying
    if not solution_update.last_updated_at:
        solution_update.last_updated_at = datetime.utcnow()
    return await repository.update(id, solution_update)

async def delete(
    repository: Repository,
    id: str | int,
) -> None:
    return await repository.delete(id)

async def get_solution_versions(repository: Repository, solution_id: str) -> list[Version]:
    """Get all versions associated with a solution"""
    return await repository.get_by_solution_id(solution_id)

async def create_version(repository: Repository, version: VersionCreate) -> Version:
    """Create a new version"""
    return await repository.add(version)

async def modify_version(
    repository: Repository,
    id: str | int,
    version_update: VersionPartialUpdate,
) -> Version:
    """Update a specific version"""
    return await repository.update(id, version_update)

async def delete_solution_versions(repository: Repository, solution_id: str) -> None:
    """Delete all versions associated with a solution"""
    return await repository.delete_by_solution_id(solution_id)
