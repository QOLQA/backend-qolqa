"""
Solution, Version, Query use cases and repository dependencies.
"""
from fastapi import Depends

from infra.presentation.dependencies.common import get_database


# Repository dependencies
def get_solution_repository(database=Depends(get_database)):
    from infra.persistence.repositories import SolutionRepositoryImpl
    return SolutionRepositoryImpl(database)


def get_version_repository(database=Depends(get_database)):
    from infra.persistence.repositories import VersionRepositoryImpl
    return VersionRepositoryImpl(database)


def get_query_repository(database=Depends(get_database)):
    from infra.persistence.repositories import QueryRepositoryImpl
    return QueryRepositoryImpl(database)


def get_google_auth_service():
    from infra.persistence.services.google_auth import GoogleAuthService
    return GoogleAuthService()


# Solution use cases
def get_create_solution_use_case(
    repository=Depends(get_solution_repository),
):
    from application.use_cases.solution.CreateSolution import create_solution
    return create_solution


def get_update_solution_use_case(
    repository=Depends(get_solution_repository),
):
    from application.use_cases.solution.UpdateSolution import update_solution
    return update_solution


def get_delete_solution_use_case(
    repository=Depends(get_solution_repository),
    version_repository=Depends(get_version_repository),
    query_repository=Depends(get_query_repository),
    database=Depends(get_database),
):
    from application.use_cases.solution.DeleteSolution import delete_solution
    return lambda solution_id, current_user_id: delete_solution(
        repository, solution_id, current_user_id,
        version_repository=version_repository,
        query_repository=query_repository,
        database=database,
    )


def get_get_solution_by_id_use_case(
    repository=Depends(get_solution_repository),
    version_repository=Depends(get_version_repository),
):
    from application.use_cases.solution.GetSolutionById import get_solution_by_id
    return lambda solution_id, versions=None: get_solution_by_id(repository, solution_id, versions)


def get_get_all_solutions_for_user_use_case(
    repository=Depends(get_solution_repository),
):
    from application.use_cases.solution.GetAllSolutionsForUser import (
        get_all_solutions_for_user,
    )
    return get_all_solutions_for_user


# Version use cases
def get_create_version_use_case(
    repository=Depends(get_version_repository),
    solution_repository=Depends(get_solution_repository),
):
    from application.use_cases.version.CreateVersion import create_version
    return create_version


def get_update_version_use_case(
    repository=Depends(get_version_repository),
    solution_repository=Depends(get_solution_repository),
):
    from application.use_cases.version.UpdateVersion import update_version
    return update_version


def get_delete_version_use_case(
    repository=Depends(get_version_repository),
    solution_repository=Depends(get_solution_repository),
):
    from application.use_cases.version.DeleteVersion import delete_version
    return delete_version


def get_get_version_by_id_use_case(
    repository=Depends(get_version_repository),
    solution_repository=Depends(get_solution_repository),
):
    from application.use_cases.version.GetVersionById import get_version_by_id
    return get_version_by_id


def get_get_all_versions_use_case(
    repository=Depends(get_version_repository),
    solution_repository=Depends(get_solution_repository),
):
    from application.use_cases.version.GetAllVersions import get_all_versions
    return get_all_versions


# Query use cases
def get_create_query_use_case(
    repository=Depends(get_query_repository),
    solution_repository=Depends(get_solution_repository),
):
    from application.use_cases.query.CreateQuery import create_query
    return create_query


def get_update_query_use_case(
    repository=Depends(get_query_repository),
    solution_repository=Depends(get_solution_repository),
):
    from application.use_cases.query.UpdateQuery import update_query
    return update_query


def get_delete_query_use_case(
    repository=Depends(get_query_repository),
    solution_repository=Depends(get_solution_repository),
):
    from application.use_cases.query.DeleteQuery import delete_query
    return delete_query


def get_delete_queries_by_solution_use_case(
    repository=Depends(get_query_repository),
    solution_repository=Depends(get_solution_repository),
):
    from application.use_cases.query.DeleteQueriesBySolution import (
        delete_queries_by_solution,
    )
    return delete_queries_by_solution


def get_get_all_queries_use_case(
    repository=Depends(get_query_repository),
    solution_repository=Depends(get_solution_repository),
):
    from application.use_cases.query.GetAllQueries import get_all_queries
    return get_all_queries


def get_get_queries_by_solution_use_case(
    repository=Depends(get_query_repository),
    solution_repository=Depends(get_solution_repository),
):
    from application.use_cases.query.GetQueriesBySolution import get_queries_by_solution
    return get_queries_by_solution


def get_get_query_by_id_use_case(
    repository=Depends(get_query_repository),
    solution_repository=Depends(get_solution_repository),
):
    from application.use_cases.query.GetQueryById import get_query_by_id
    return get_query_by_id