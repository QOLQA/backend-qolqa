"""
Presentation layer dependencies - Use case providers and auth dependencies.
"""
from infra.presentation.dependencies.auth import (
    get_authenticate_user_use_case,
    get_current_user,
    get_get_user_by_id_use_case,
    get_google_auth_service,
    get_google_login_use_case,
    get_password_hasher,
    get_register_user_use_case,
    get_token_data,
    get_user_repository,
    require_admin,
)
from infra.presentation.dependencies.common import get_database

# Solution, Version, Query use cases
# Repositories and services
from infra.presentation.dependencies.use_cases import (
    get_create_query_use_case,
    get_create_solution_use_case,
    get_create_version_use_case,
    get_delete_queries_by_solution_use_case,
    get_delete_query_use_case,
    get_delete_solution_use_case,
    get_delete_version_use_case,
    get_get_all_queries_use_case,
    get_get_all_solutions_for_user_use_case,
    get_get_all_versions_use_case,
    get_get_queries_by_solution_use_case,
    get_get_query_by_id_use_case,
    get_get_solution_by_id_use_case,
    get_get_version_by_id_use_case,
    get_google_auth_service,
    get_query_repository,
    get_solution_repository,
    get_update_query_use_case,
    get_update_solution_use_case,
    get_update_version_use_case,
    get_version_repository,
)

__all__ = [
    # Auth
    "get_token_data",
    "get_password_hasher",
    "get_google_auth_service",
    "get_user_repository",
    "get_current_user",
    "require_admin",
    # Common
    "get_database",
    # Auth use cases
    "get_register_user_use_case",
    "get_authenticate_user_use_case",
    "get_google_login_use_case",
    "get_get_user_by_id_use_case",
    # Solution use cases
    "get_create_solution_use_case",
    "get_update_solution_use_case",
    "get_delete_solution_use_case",
    "get_get_solution_by_id_use_case",
    "get_get_all_solutions_for_user_use_case",
    # Version use cases
    "get_create_version_use_case",
    "get_update_version_use_case",
    "get_delete_version_use_case",
    "get_get_version_by_id_use_case",
    "get_get_all_versions_use_case",
    # Query use cases
    "get_create_query_use_case",
    "get_update_query_use_case",
    "get_delete_query_use_case",
    "get_delete_queries_by_solution_use_case",
    "get_get_all_queries_use_case",
    "get_get_queries_by_solution_use_case",
    "get_get_query_by_id_use_case",
    # Repositories
    "get_solution_repository",
    "get_version_repository",
    "get_query_repository",
    # Services
    "get_google_auth_service",
]