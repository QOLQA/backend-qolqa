"""
Composition Root for the presentation layer.

All FastAPI dependency factories live here. Routers import the
``Depends``-annotated aliases (e.g. ``QueryRepoDep``) from this module
and never define their own ``Depends`` defaults, which keeps Ruff rule
B008 satisfied.
"""
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorDatabase

from domain.entities.auth.UserEntity import UserEntity
from domain.repositories.query.repo import IQueryRepository
from domain.repositories.solution.repo import ISolutionRepository
from domain.repositories.user.repo import IUserRepository
from domain.repositories.version.repo import IVersionRepository
from infra.presentation.dependencies.common import get_database

# ---------------------------------------------------------------------------
# OAuth2 scheme — module-level so Depends() is not in a function default
# ---------------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
TokenDep = Annotated[str, Depends(oauth2_scheme)]
OAuth2FormDep = Annotated[OAuth2PasswordRequestForm, Depends()]


# ---------------------------------------------------------------------------
# Database dependency
# ---------------------------------------------------------------------------
DatabaseDep = Annotated[AsyncIOMotorDatabase, Depends(get_database)]


# ---------------------------------------------------------------------------
# Simple factories (no Depends in defaults)
# ---------------------------------------------------------------------------
def get_password_hasher():
    from infra.persistence.security import BcryptHasher

    return BcryptHasher()


PasswordHasherDep = Annotated[object, Depends(get_password_hasher)]


def get_google_auth_service():
    from infra.persistence.services.google_auth import GoogleAuthService

    return GoogleAuthService()


GoogleAuthServiceDep = Annotated[object, Depends(get_google_auth_service)]


# ---------------------------------------------------------------------------
# Repository factories — return domain interfaces
# ---------------------------------------------------------------------------
def get_user_repository(
    database: DatabaseDep,
    hasher: PasswordHasherDep,
) -> IUserRepository:
    from infra.persistence.repositories import UserRepositoryImpl

    return UserRepositoryImpl(database, hasher=hasher)


def get_solution_repository(database: DatabaseDep) -> ISolutionRepository:
    from infra.persistence.repositories import SolutionRepositoryImpl

    return SolutionRepositoryImpl(database)


def get_query_repository(database: DatabaseDep) -> IQueryRepository:
    from infra.persistence.repositories import QueryRepositoryImpl

    return QueryRepositoryImpl(database)


def get_version_repository(database: DatabaseDep) -> IVersionRepository:
    from infra.persistence.repositories import VersionRepositoryImpl

    return VersionRepositoryImpl(database)


# ---------------------------------------------------------------------------
# Repository dependency aliases
# ---------------------------------------------------------------------------
UserRepoDep = Annotated[IUserRepository, Depends(get_user_repository)]
SolutionRepoDep = Annotated[ISolutionRepository, Depends(get_solution_repository)]
QueryRepoDep = Annotated[IQueryRepository, Depends(get_query_repository)]
VersionRepoDep = Annotated[IVersionRepository, Depends(get_version_repository)]


# ---------------------------------------------------------------------------
# Auth dependency factories
# ---------------------------------------------------------------------------
def get_token_data(token: TokenDep) -> dict:
    """Extract and validate data from JWT token.

    Raises HTTP 401 if token is invalid or expired.
    """
    from fastapi import HTTPException, status

    from domain.errors import InvalidToken
    from infra.persistence.jwt import decode_access_token

    try:
        return decode_access_token(token)
    except InvalidToken as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.msg,
            headers={"WWW-Authenticate": "Bearer"},
        )


TokenDataDep = Annotated[dict, Depends(get_token_data)]


async def get_current_user(
    token_data: TokenDataDep,
    repository: UserRepoDep,
) -> UserEntity:
    """Get current authenticated user from JWT token.

    Validates token_version to detect invalidated tokens.
    """
    from fastapi import HTTPException, status

    from application.use_cases.auth.GetUserById import get_user_by_id
    from domain.enums.RoleEnum import RoleEnum  # noqa: F401  (used in require_admin)
    from domain.errors import InvalidToken  # noqa: F401
    from infra.presentation.handle_errors import handle_common_errors

    username: str = token_data.get("sub")
    user_id: str = token_data.get("user_id")

    if username is None or user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        entity = await get_user_by_id(repository, user_id)

        if not entity.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user",
            )

        token_version = token_data.get("token_version")
        if token_version is None or token_version != entity.token_version:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been invalidated. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return entity

    except HTTPException:
        raise
    except Exception as exc:
        await handle_common_errors(exc)


CurrentUserDep = Annotated[UserEntity, Depends(get_current_user)]


async def require_admin(
    token_data: TokenDataDep,
    current_user: CurrentUserDep,
) -> UserEntity:
    """Dependency that requires the current user to have admin role.

    Reads roles from JWT payload (no extra DB query).
    Raises HTTP 403 if user is not admin.
    """
    from fastapi import HTTPException, status

    from domain.enums.RoleEnum import RoleEnum

    token_roles = token_data.get("roles", [])
    if RoleEnum.admin.value not in token_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


AdminUserDep = Annotated[UserEntity, Depends(require_admin)]


# ---------------------------------------------------------------------------
# Auth use-case factories
# ---------------------------------------------------------------------------
def get_register_user_use_case(repository: UserRepoDep) -> Callable:
    from application.use_cases.auth.RegisterUser import register_user

    return lambda command: register_user(repository, command)


RegisterUserUseCaseDep = Annotated[Callable, Depends(get_register_user_use_case)]


def get_authenticate_user_use_case(repository: UserRepoDep) -> Callable:
    from application.use_cases.auth.AuthenticateUser import authenticate_user

    return lambda command: authenticate_user(repository, command.username, command.password)


AuthenticateUserUseCaseDep = Annotated[Callable, Depends(get_authenticate_user_use_case)]


def get_google_login_use_case(
    repository: UserRepoDep,
    google_auth: GoogleAuthServiceDep,
) -> Callable:
    from application.use_cases.auth.GoogleLogin import google_login

    return lambda command: google_login(repository, google_auth, command.credential, command.client_id)


GoogleLoginUseCaseDep = Annotated[Callable, Depends(get_google_login_use_case)]


def get_get_user_by_id_use_case(repository: UserRepoDep) -> Callable:
    from application.use_cases.auth.GetUserById import get_user_by_id

    return get_user_by_id


GetUserByIdUseCaseDep = Annotated[Callable, Depends(get_get_user_by_id_use_case)]


# ---------------------------------------------------------------------------
# Solution use-case factories
# ---------------------------------------------------------------------------
def get_create_solution_use_case(repository: SolutionRepoDep) -> Callable:
    from application.use_cases.solution.CreateSolution import create_solution

    return create_solution


CreateSolutionUseCaseDep = Annotated[Callable, Depends(get_create_solution_use_case)]


def get_update_solution_use_case(repository: SolutionRepoDep) -> Callable:
    from application.use_cases.solution.UpdateSolution import update_solution

    return update_solution


UpdateSolutionUseCaseDep = Annotated[Callable, Depends(get_update_solution_use_case)]


def get_delete_solution_use_case(
    repository: SolutionRepoDep,
    version_repository: VersionRepoDep,
    query_repository: QueryRepoDep,
    database: DatabaseDep,
) -> Callable:
    from application.use_cases.solution.DeleteSolution import delete_solution

    return lambda solution_id, current_user_id: delete_solution(
        repository,
        solution_id,
        current_user_id,
        version_repository=version_repository,
        query_repository=query_repository,
        database=database,
    )


DeleteSolutionUseCaseDep = Annotated[Callable, Depends(get_delete_solution_use_case)]


def get_get_solution_by_id_use_case(
    repository: SolutionRepoDep,
    version_repository: VersionRepoDep,
) -> Callable:
    from application.use_cases.solution.GetSolutionById import get_solution_by_id

    return lambda solution_id, versions=None: get_solution_by_id(
        repository, solution_id, versions
    )


GetSolutionByIdUseCaseDep = Annotated[Callable, Depends(get_get_solution_by_id_use_case)]


def get_get_all_solutions_for_user_use_case(repository: SolutionRepoDep) -> Callable:
    from application.use_cases.solution.GetAllSolutionsForUser import (
        get_all_solutions_for_user,
    )

    return get_all_solutions_for_user


GetAllSolutionsForUserUseCaseDep = Annotated[
    Callable, Depends(get_get_all_solutions_for_user_use_case)
]


# ---------------------------------------------------------------------------
# Version use-case factories
# ---------------------------------------------------------------------------
def get_create_version_use_case(
    repository: VersionRepoDep,
    solution_repository: SolutionRepoDep,
) -> Callable:
    from application.use_cases.version.CreateVersion import create_version

    return create_version


CreateVersionUseCaseDep = Annotated[Callable, Depends(get_create_version_use_case)]


def get_update_version_use_case(
    repository: VersionRepoDep,
    solution_repository: SolutionRepoDep,
) -> Callable:
    from application.use_cases.version.UpdateVersion import update_version

    return update_version


UpdateVersionUseCaseDep = Annotated[Callable, Depends(get_update_version_use_case)]


def get_delete_version_use_case(
    repository: VersionRepoDep,
    solution_repository: SolutionRepoDep,
) -> Callable:
    from application.use_cases.version.DeleteVersion import delete_version

    return delete_version


DeleteVersionUseCaseDep = Annotated[Callable, Depends(get_delete_version_use_case)]


def get_get_version_by_id_use_case(
    repository: VersionRepoDep,
    solution_repository: SolutionRepoDep,
) -> Callable:
    from application.use_cases.version.GetVersionById import get_version_by_id

    return get_version_by_id


GetVersionByIdUseCaseDep = Annotated[Callable, Depends(get_get_version_by_id_use_case)]


def get_get_all_versions_use_case(
    repository: VersionRepoDep,
    solution_repository: SolutionRepoDep,
) -> Callable:
    from application.use_cases.version.GetAllVersions import get_all_versions

    return get_all_versions


GetAllVersionsUseCaseDep = Annotated[Callable, Depends(get_get_all_versions_use_case)]


# ---------------------------------------------------------------------------
# Query use-case factories
# ---------------------------------------------------------------------------
def get_create_query_use_case(
    repository: QueryRepoDep,
    solution_repository: SolutionRepoDep,
) -> Callable:
    from application.use_cases.query.CreateQuery import create_query

    return create_query


CreateQueryUseCaseDep = Annotated[Callable, Depends(get_create_query_use_case)]


def get_update_query_use_case(
    repository: QueryRepoDep,
    solution_repository: SolutionRepoDep,
) -> Callable:
    from application.use_cases.query.UpdateQuery import update_query

    return update_query


UpdateQueryUseCaseDep = Annotated[Callable, Depends(get_update_query_use_case)]


def get_delete_query_use_case(
    repository: QueryRepoDep,
    solution_repository: SolutionRepoDep,
) -> Callable:
    from application.use_cases.query.DeleteQuery import delete_query

    return delete_query


DeleteQueryUseCaseDep = Annotated[Callable, Depends(get_delete_query_use_case)]


def get_delete_queries_by_solution_use_case(
    repository: QueryRepoDep,
    solution_repository: SolutionRepoDep,
) -> Callable:
    from application.use_cases.query.DeleteQueriesBySolution import (
        delete_queries_by_solution,
    )

    return delete_queries_by_solution


DeleteQueriesBySolutionUseCaseDep = Annotated[
    Callable, Depends(get_delete_queries_by_solution_use_case)
]


def get_get_all_queries_use_case(
    repository: QueryRepoDep,
    solution_repository: SolutionRepoDep,
) -> Callable:
    from application.use_cases.query.GetAllQueries import get_all_queries

    return get_all_queries


GetAllQueriesUseCaseDep = Annotated[Callable, Depends(get_get_all_queries_use_case)]


def get_get_queries_by_solution_use_case(
    repository: QueryRepoDep,
    solution_repository: SolutionRepoDep,
) -> Callable:
    from application.use_cases.query.GetQueriesBySolution import (
        get_queries_by_solution,
    )

    return get_queries_by_solution


GetQueriesBySolutionUseCaseDep = Annotated[
    Callable, Depends(get_get_queries_by_solution_use_case)
]


def get_get_query_by_id_use_case(
    repository: QueryRepoDep,
    solution_repository: SolutionRepoDep,
) -> Callable:
    from application.use_cases.query.GetQueryById import get_query_by_id

    return get_query_by_id


GetQueryByIdUseCaseDep = Annotated[Callable, Depends(get_get_query_by_id_use_case)]
