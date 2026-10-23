"""
FastAPI dependency injection providers for auth use cases.
Auth use cases are resolved here with their repository dependencies.
Other use cases are in infra/presentation/dependencies/use_cases.py
"""
from fastapi import Depends

from infra.presentation.dependencies.auth import get_user_repository, get_current_user, require_admin
from infra.presentation.dependencies.common import get_database

# Auth use cases
def get_register_user_use_case(
    repository=Depends(get_user_repository),
):
    from application.use_cases.auth.RegisterUser import register_user
    return register_user


def get_authenticate_user_use_case(
    repository=Depends(get_user_repository),
):
    from application.use_cases.auth.AuthenticateUser import authenticate_user
    return authenticate_user


def get_google_login_use_case(
    repository=Depends(get_user_repository),
    google_auth=Depends(get_google_auth_service),
):
    from application.use_cases.auth.GoogleLogin import google_login
    return lambda command: google_login(repository, google_auth, command.credential, command.client_id)


def get_get_user_by_id_use_case(
    repository=Depends(get_user_repository),
):
    from application.use_cases.auth.GetUserById import get_user_by_id
    return get_user_by_id