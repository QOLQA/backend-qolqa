"""
Authentication and authorization dependencies - re-exported from Composition Root.
"""
from infra.presentation.container import (
    AdminUserDep,
    AuthenticateUserUseCaseDep,
    CurrentUserDep,
    GetUserByIdUseCaseDep,
    GoogleAuthServiceDep,
    GoogleLoginUseCaseDep,
    OAuth2FormDep,
    PasswordHasherDep,
    RegisterUserUseCaseDep,
    TokenDataDep,
    TokenDep,
    UserRepoDep,
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

# Backward-compatible alias
get_require_admin = require_admin

__all__ = [
    "AdminUserDep",
    "AuthenticateUserUseCaseDep",
    "CurrentUserDep",
    "GetUserByIdUseCaseDep",
    "GoogleAuthServiceDep",
    "GoogleLoginUseCaseDep",
    "OAuth2FormDep",
    "PasswordHasherDep",
    "RegisterUserUseCaseDep",
    "TokenDataDep",
    "TokenDep",
    "UserRepoDep",
    "get_authenticate_user_use_case",
    "get_current_user",
    "get_get_user_by_id_use_case",
    "get_google_auth_service",
    "get_google_login_use_case",
    "get_password_hasher",
    "get_register_user_use_case",
    "get_token_data",
    "get_user_repository",
    "require_admin",
]
