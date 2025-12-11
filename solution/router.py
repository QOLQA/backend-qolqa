from fastapi import APIRouter, Depends, status, HTTPException

from models.solution import Solution, SolutionCreate, SolutionPartialUpdate, SolutionBase
from models.version import Version, VersionCreate, VersionPartialUpdate, default_version_descriptions
from models.user import User
from solution import service
from solution.repository_nosql import SolutionRepositoryNoSql
from version.repository_nosql import VersionRepositoryNoSql

from auth.router import get_current_user
from utils.handle_errors import handle_common_errors
from utils.get_database import get_database

router = APIRouter()


@router.get('', response_model=list[Solution])
async def all(
    current_user: User = Depends(get_current_user),
    database = Depends(get_database),
) -> list[Solution]:
    """Get all solutions for the current user"""
    repository = SolutionRepositoryNoSql(database)
    # Get only solutions owned by current user
    all_solutions = await service.get_all(repository)
    user_solutions = [s for s in all_solutions if s.user_id == str(current_user.id)]
    return user_solutions


@router.post('', response_model=Solution, status_code=status.HTTP_201_CREATED)
async def create(
    solution_create: SolutionCreate,
    current_user: User = Depends(get_current_user),
    database = Depends(get_database),
) -> Solution:
    """Create a new solution for the current user"""
    try:
        # Add user_id to solution
        solution_data = solution_create.model_dump()
        solution_data['user_id'] = str(current_user.id)
        solution_with_user = SolutionBase(**solution_data)
        
        # Create solution and initial version
        solution = await service.create(SolutionRepositoryNoSql(database), solution_with_user)

        last_version_saved = ""

        for default_version_description in default_version_descriptions:
            # Create initial version
            version_create = VersionCreate(
                queries=[],
                submodels=[],
                description=default_version_description,
                solution_id=str(solution.id)
            )
            new_version = await service.create_version(VersionRepositoryNoSql(database), version_create)
            last_version_saved = str(new_version.id)

        update_solution = SolutionPartialUpdate(last_version_saved=last_version_saved)
        updated_solution = await service.modify(SolutionRepositoryNoSql(database), solution.id, update_solution)
        
        return updated_solution
    except Exception as exc:
        await handle_common_errors(exc)


@router.get('/{id}', response_model=Solution)
async def get(
    id: int | str,
    current_user: User = Depends(get_current_user),
    database = Depends(get_database),
) -> Solution:
    """Get a solution by ID - only if owned by current user"""
    try:
        solution = await service.get_one(SolutionRepositoryNoSql(database), id)
        
        # Verify ownership
        if solution.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this solution"
            )
        
        # Get associated versions
        versions = await service.get_solution_versions(VersionRepositoryNoSql(database), str(solution.id))
        # Add versions to solution response
        solution.versions = versions
        return solution
    except HTTPException:
        raise
    except Exception as exc:
        await handle_common_errors(exc)


@router.patch('/{id}', response_model=Solution)
async def update(
    id: str | int,
    solution_update: SolutionPartialUpdate,
    current_user: User = Depends(get_current_user),
    database = Depends(get_database),
) -> Solution:
    """Update a solution - only if owned by current user"""
    try:
        # Verify ownership
        solution = await service.get_one(SolutionRepositoryNoSql(database), id)
        if solution.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this solution"
            )
        
        return await service.modify(SolutionRepositoryNoSql(database), id, solution_update)
    except HTTPException:
        raise
    except Exception as exc:
        await handle_common_errors(exc)


@router.patch('/{solution_id}/versions/{version_id}', response_model=Version)
async def update_solution_version(
    solution_id: str | int,
    version_id: str | int,
    version_update: VersionPartialUpdate,
    current_user: User = Depends(get_current_user),
    database = Depends(get_database),
) -> Version:
    """Update a specific version of a solution - only if solution is owned by current user"""
    try:
        # Verify solution exists and ownership
        solution = await service.get_one(SolutionRepositoryNoSql(database), solution_id)
        if solution.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this solution"
            )
        
        # Update the last_version_saved field in the solution
        update_last_version_saved = SolutionPartialUpdate.model_construct(last_version_saved=str(version_id))
        await service.modify(SolutionRepositoryNoSql(database), solution_id, update_last_version_saved)
        
        # Update the version
        return await service.modify_version(VersionRepositoryNoSql(database), version_id, version_update)
    except HTTPException:
        raise
    except Exception as exc:
        await handle_common_errors(exc)


@router.delete('/{id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    id: str | int,
    current_user: User = Depends(get_current_user),
    database = Depends(get_database),
) -> None:
    """Delete a solution and all its associated versions - only if owned by current user"""
    try:
        # Verify ownership
        solution = await service.get_one(SolutionRepositoryNoSql(database), id)
        if solution.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this solution"
            )
        
        # Delete all associated versions
        await service.delete_solution_versions(VersionRepositoryNoSql(database), str(solution.id))
        # Delete the solution
        return await service.delete(SolutionRepositoryNoSql(database), id)
    except HTTPException:
        raise
    except Exception as exc:
        await handle_common_errors(exc)
