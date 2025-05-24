from fastapi import APIRouter, Depends, status

from models.solution import Solution, SolutionCreate, SolutionPartialUpdate
from models.version import Version, VersionCreate, VersionPartialUpdate
from solution import service
from solution.repository_nosql import SolutionRepositoryNoSql
from version.repository_nosql import VersionRepositoryNoSql

from utils.handle_errors import handle_common_errors
from utils.get_database import get_database

router = APIRouter()


@router.get('', response_model=list[Solution])
async def all(
    database = Depends(get_database),
) -> list[Solution]:
    return await service.get_all(SolutionRepositoryNoSql(database))


@router.post('', response_model=Solution, status_code=status.HTTP_201_CREATED)
async def create(
    solution_create: SolutionCreate,
    database = Depends(get_database),
) -> Solution:
    try:
        # Create solution and initial version
        solution = await service.create(SolutionRepositoryNoSql(database), solution_create)
        
        # Create initial version
        version_create = VersionCreate(
            queries=[],
            submodels=[],
            description="Initial version",
            solution_id=str(solution.id)
        )
        await service.create_version(VersionRepositoryNoSql(database), version_create)
        
        return solution
    except Exception as exc:
        await handle_common_errors(exc)


@router.get('/{id}', response_model=Solution)
async def get(
    id: int | str,
    database = Depends(get_database),
) -> Solution:
    try:
        solution = await service.get_one(SolutionRepositoryNoSql(database), id)
        # Get associated versions
        versions = await service.get_solution_versions(VersionRepositoryNoSql(database), str(solution.id))
        # Add versions to solution response
        solution.versions = versions
        return solution
    except Exception as exc:
        await handle_common_errors(exc)


@router.patch('/{id}', response_model=Solution)
async def update(
    id: str | int,
    solution_update: SolutionPartialUpdate,
    database = Depends(get_database),
) -> Solution:
    try:
        return await service.modify(SolutionRepositoryNoSql(database), id, solution_update)
    except Exception as exc:
        await handle_common_errors(exc)
    

@router.get('/{id}/versions', response_model=list[Version])
async def get_solution_versions(
    id: str | int,
    database = Depends(get_database),
) -> list[Version]:
    """Get all versions for a specific solution"""
    try:
        return await service.get_solution_versions(VersionRepositoryNoSql(database), str(id))
    except Exception as exc:
        await handle_common_errors(exc)


@router.post('/{id}/versions', response_model=Version, status_code=status.HTTP_201_CREATED)
async def create_solution_version(
    id: str | int,
    version_create: VersionCreate,
    database = Depends(get_database),
) -> Version:
    """Create a new version for a specific solution"""
    try:
        # Verify solution exists
        await service.get_one(SolutionRepositoryNoSql(database), id)
        # Ensure the version is associated with the correct solution
        version_create.solution_id = str(id)
        return await service.create_version(VersionRepositoryNoSql(database), version_create)
    except Exception as exc:
        await handle_common_errors(exc)


@router.patch('/{solution_id}/versions/{version_id}', response_model=Version)
async def update_solution_version(
    solution_id: str | int,
    version_id: str | int,
    version_update: VersionPartialUpdate,
    database = Depends(get_database),
) -> Version:
    """Update a specific version of a solution"""
    try:
        # Verify solution exists
        await service.get_one(SolutionRepositoryNoSql(database), solution_id)
        # Update the version
        return await service.modify_version(VersionRepositoryNoSql(database), version_id, version_update)
    except Exception as exc:
        await handle_common_errors(exc)


@router.delete('/{id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    id: str | int,
    database = Depends(get_database),
) -> None:
    """Delete a solution and all its associated versions"""
    try:
        solution = await service.get_one(SolutionRepositoryNoSql(database), id)
        # Delete all associated versions
        await service.delete_solution_versions(VersionRepositoryNoSql(database), str(solution.id))
        # Delete the solution
        return await service.delete(SolutionRepositoryNoSql(database), id)
    except Exception as exc:
        await handle_common_errors(exc)
