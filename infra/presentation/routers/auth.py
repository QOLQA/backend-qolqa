"""
Authentication router (Clean Architecture)
Handles login, registration, and user profile endpoints.

Error strategy: domain errors propagate to the global exception handlers
registered in ``infra/presentation/exception_handlers.py``. Auth endpoints keep
one narrow, typed catch whose only job is audit logging of failed attempts
before re-raising.
"""
from fastapi import APIRouter, Request, status

from application.dtos.auth.commands import (
    AuthenticateCommand,
    GoogleLoginCommand,
    RegisterCommand,
)
from config.rate_limiter import limiter
from config.settings import settings
from domain.errors import AuthException, Duplicate, Format, GoogleLoginNotConfigured
from infra.persistence.audit import log_auth_attempt, log_registration
from infra.persistence.mappers import UserMapper
from infra.persistence.token_service import create_user_token
from infra.presentation.dependencies import (
    AuthenticateUserUseCaseDep,
    CurrentUserDep,
    GoogleLoginUseCaseDep,
    OAuth2FormDep,
    RegisterUserUseCaseDep,
)
from infra.presentation.dtos.auth.request import GoogleLoginRequest, UserCreateRequest
from infra.presentation.dtos.auth.response import (
    GoogleLoginResponse,
    TokenResponse,
    UserResponse,
)

router = APIRouter()


@router.post('/register', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/hour")
async def register(
    request: Request,
    user_create: UserCreateRequest,
    register_use_case: RegisterUserUseCaseDep,
) -> UserResponse:
    """Register a new user."""
    command = RegisterCommand(
        username=user_create.username,
        email=user_create.email,
        password=user_create.password,
        full_name=user_create.full_name,
    )

    try:
        entity = await register_use_case(command)
    except (AuthException, Duplicate, Format) as exc:
        log_auth_attempt(
            username=user_create.username,
            success=False,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            reason=str(exc),
        )
        raise

    response = UserMapper.to_response(entity)

    log_registration(
        user_id=entity.id,
        username=entity.username,
        email=entity.email,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return response


@router.post('/login', response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    form_data: OAuth2FormDep,
    auth_use_case: AuthenticateUserUseCaseDep,
) -> TokenResponse:
    """Login endpoint — OAuth2 compatible."""
    command = AuthenticateCommand(
        username=form_data.username,
        password=form_data.password,
    )

    try:
        entity = await auth_use_case(command)
    except AuthException as exc:
        log_auth_attempt(
            username=form_data.username,
            success=False,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            reason=exc.msg,
        )
        raise

    token = await create_user_token(entity)

    log_auth_attempt(
        username=entity.username,
        success=True,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return token


@router.get('/me', response_model=UserResponse)
async def get_current_user_profile(
    current_user: CurrentUserDep,
) -> UserResponse:
    """Get current user profile."""
    return UserMapper.to_response(current_user)


@router.post('/google', response_model=GoogleLoginResponse)
@limiter.limit("5/minute")
async def google_login_endpoint(
    request: Request,
    login_request: GoogleLoginRequest,
    google_use_case: GoogleLoginUseCaseDep,
) -> GoogleLoginResponse:
    """Google OAuth login endpoint."""
    command = GoogleLoginCommand(
        credential=login_request.credential,
        client_id=settings.google_client_id,
    )

    try:
        entity = await google_use_case(command=command)
    except (AuthException, Duplicate, GoogleLoginNotConfigured) as exc:
        log_email = getattr(exc, 'email', None) or "google-unknown"
        log_auth_attempt(
            username=log_email,
            success=False,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            reason=exc.msg,
        )
        raise

    token = await create_user_token(entity)
    user_response = UserMapper.to_response(entity)

    log_auth_attempt(
        username=entity.username,
        success=True,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return GoogleLoginResponse(
        access_token=token.access_token,
        token_type=token.token_type,
        user=user_response,
    )
