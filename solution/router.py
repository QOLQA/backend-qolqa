from fastapi import APIRouter, Depends, status, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging
import pprint

from models.solution import Solution, SolutionCreate, SolutionPartialUpdate, SolutionBase
from models.version import Version, VersionCreate, VersionPartialUpdate, default_version_descriptions
from models.user import User
from models.query import Query
from solution import service
from solution.repository_nosql import SolutionRepositoryNoSql
from version.repository_nosql import VersionRepositoryNoSql
from query.repository_nosql import QueryRepositoryNoSql

from auth.router import get_current_user
from api.handle_errors import handle_common_errors
from infrastructure.db_factory import get_database
from utils.audit import log_resource_operation, log_access_denied


logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get('', response_model=list[Solution])
@limiter.limit("100/minute")  # 100 consultas por minuto
async def all(
    request: Request,
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
@limiter.limit("20/minute")  # 20 creaciones por minuto
async def create(
    request: Request,
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

        # Create only one initial version
        version_create = VersionCreate(
            submodels=[],
            description=default_version_descriptions[0],  # "Primera version"
            solution_id=str(solution.id)
        )
        new_version = await service.create_version(VersionRepositoryNoSql(database), version_create)
        last_version_saved = str(new_version.id)



        update_solution = SolutionPartialUpdate(last_version_saved=last_version_saved)
        updated_solution = await service.modify(SolutionRepositoryNoSql(database), solution.id, update_solution)
        
        # Usar logger en lugar de print - esto SÍ aparecerá
        logger.info("=" * 60)
        logger.info(">>>>>>>>>>>>> SOLUTION_WITH_USER:")
        logger.info(pprint.pformat(updated_solution.model_dump(), indent=2, width=100))
        logger.info("=" * 60)

        # Audit log: solution created
        log_resource_operation(
            action="solution.create",
            user_id=str(current_user.id),
            resource_type="solution",
            resource_id=str(updated_solution.id),
            resource_name=updated_solution.name,
            status="success",
            ip_address=request.client.host if request.client else None,
        )
        
        return updated_solution
    except Exception as exc:
        await handle_common_errors(exc, request)


@router.get('/{id}', response_model=Solution)
@limiter.limit("100/minute")  # 100 consultas por minuto
async def get(
    request: Request,
    id: int | str,
    current_user: User = Depends(get_current_user),
    database = Depends(get_database),
) -> Solution:
    """Get a solution by ID - only if owned by current user"""
    try:
        solution = await service.get_one(SolutionRepositoryNoSql(database), id)
        
        # Verify ownership
        if solution.user_id != str(current_user.id):
            # Audit log: access denied
            log_access_denied(
                action="solution.read",
                user_id=str(current_user.id),
                resource_type="solution",
                resource_id=str(id),
                reason="Not owner",
                ip_address=request.client.host if request.client else None,
            )
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
@limiter.limit("30/minute")  # 30 actualizaciones por minuto
async def update(
    request: Request,
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
            # Audit log: access denied
            log_access_denied(
                action="solution.update",
                user_id=str(current_user.id),
                resource_type="solution",
                resource_id=str(id),
                reason="Not owner",
                ip_address=request.client.host if request.client else None,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this solution"
            )
        
        updated_solution = await service.modify(SolutionRepositoryNoSql(database), id, solution_update)
        
        # Audit log: solution updated
        log_resource_operation(
            action="solution.update",
            user_id=str(current_user.id),
            resource_type="solution",
            resource_id=str(id),
            resource_name=updated_solution.name,
            status="success",
            ip_address=request.client.host if request.client else None,
        )
        
        return updated_solution
    except HTTPException:
        raise
    except Exception as exc:
        await handle_common_errors(exc)


@router.post('/{solution_id}/versions', response_model=Version, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")  # 20 creaciones por minuto
async def create_version_for_solution(
    request: Request,
    solution_id: str | int,
    version_create: VersionCreate,
    current_user: User = Depends(get_current_user),
    database = Depends(get_database),
) -> Version:
    """Create a new version for a solution - only if solution is owned by current user"""
    try:
        # Verify solution exists and ownership
        solution = await service.get_one(SolutionRepositoryNoSql(database), solution_id)
        if solution.user_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create versions for this solution"
            )
        
        # Ensure solution_id in version_create matches the URL parameter
        version_create.solution_id = str(solution_id)
        
        # Create the version
        new_version = await service.create_version(VersionRepositoryNoSql(database), version_create)
        
        # Update last_version_saved in the solution
        update_solution = SolutionPartialUpdate(last_version_saved=str(new_version.id))
        await service.modify(SolutionRepositoryNoSql(database), solution_id, update_solution)
        
        # Audit log: version created
        log_resource_operation(
            action="version.create",
            user_id=str(current_user.id),
            resource_type="version",
            resource_id=str(new_version.id),
            resource_name=version_create.description,
            status="success",
            ip_address=request.client.host if request.client else None,
        )
        
        return new_version
    except HTTPException:
        raise
    except Exception as exc:
        await handle_common_errors(exc, request)


@router.patch('/{solution_id}/versions/{version_id}', response_model=Version)
@limiter.limit("30/minute")  # 30 actualizaciones por minuto
async def update_solution_version(
    request: Request,
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
@limiter.limit("10/minute")  # 10 eliminaciones por minuto
async def delete(
    request: Request,
    id: str | int,
    current_user: User = Depends(get_current_user),
    database = Depends(get_database),
) -> None:
    """Delete a solution and all its associated versions - only if owned by current user"""
    try:
        # Verify ownership
        solution = await service.get_one(SolutionRepositoryNoSql(database), id)
        if solution.user_id != str(current_user.id):
            # Audit log: access denied
            log_access_denied(
                action="solution.delete",
                user_id=str(current_user.id),
                resource_type="solution",
                resource_id=str(id),
                reason="Not owner",
                ip_address=request.client.host if request.client else None,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this solution"
            )
        
        # Audit log: solution deleted
        log_resource_operation(
            action="solution.delete",
            user_id=str(current_user.id),
            resource_type="solution",
            resource_id=str(id),
            resource_name=solution.name,
            status="success",
            ip_address=request.client.host if request.client else None,
        )
        
        # Delete all associated queries
        query_repository = QueryRepositoryNoSql(database)
        await query_repository.delete_by_solution_id(str(solution.id))
        
        # Delete all associated versions
        await service.delete_solution_versions(VersionRepositoryNoSql(database), str(solution.id))
        # Delete the solution
        return await service.delete(SolutionRepositoryNoSql(database), id)
    except HTTPException:
        raise
    except Exception as exc:
        await handle_common_errors(exc)
