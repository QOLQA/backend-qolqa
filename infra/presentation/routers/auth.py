"""
Authentication router (Clean Architecture)
Handles login, registration, and user profile endpoints.
"""
from fastapi import APIRouter, Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm

from infra.presentation.dtos.auth.request import UserCreateRequest, GoogleLoginRequest
from infra.presentation.dtos.auth.response import UserResponse, TokenResponse, GoogleLoginResponse
from application.dtos.auth.commands import RegisterCommand, AuthenticateCommand, GoogleLoginCommand
from infra.presentation.dependencies import (
    get_register_user_use_case,
    get_authenticate_user_use_case,
    get_google_login_use_case,
    get_get_user_by_id_use_case,
    get_current_user,
    get_google_auth_service,
)
from infra.persistence.token_service import create_user_token
from infra.persistence.mappers import UserMapper
from domain.entities.auth.UserEntity import UserEntity as User
from infra.presentation.handle_errors import handle_common_errors
from infra.persistence.audit import log_registration, log_auth_attempt
from config.settings import settings
from config.rate_limiter import limiter

router = APIRouter()


@router.post('/register', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/hour")
async def register(
    request: Request,
    user_create: UserCreateRequest,
    register_use_case=Depends(get_register_user_use_case),
) -> UserResponse:
    """Register a new user."""
    try:
        command = RegisterCommand(
            username=user_create.username,
            email=user_create.email,
            password=user_create.password,
            full_name=user_create.full_name,
        )
        entity = await register_use_case(command)

        response = UserMapper.to_response(entity)

        log_registration(
            user_id=entity.id,
            username=entity.username,
            email=entity.email,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        return response
    except Exception as exc:
        log_auth_attempt(
            username=user_create.username,
            success=False,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            reason=str(exc),
        )
        await handle_common_errors(exc, request)


@router.post('/login', response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_use_case=Depends(get_authenticate_user_use_case),
) -> TokenResponse:
    """Login endpoint — OAuth2 compatible."""
    try:
        command = AuthenticateCommand(
            username=form_data.username,
            password=form_data.password,
        )
        entity = await auth_use_case(command)

        token = await create_user_token(entity)

        log_auth_attempt(
            username=entity.username,
            success=True,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        return token
    except Exception as exc:
        log_auth_attempt(
            username=form_data.username,
            success=False,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            reason=f"Error: {type(exc).__name__}",
        )
        await handle_common_errors(exc)


@router.get('/me', response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Get current user profile."""
    return UserMapper.to_response(current_user)


@router.post('/google', response_model=GoogleLoginResponse)
@limiter.limit("5/minute")
async def google_login_endpoint(
    request: Request,
    login_request: GoogleLoginRequest,
    google_use_case=Depends(get_google_login_use_case),
) -> GoogleLoginResponse:
    """Google OAuth login endpoint."""
    try:
        command = GoogleLoginCommand(
            credential=login_request.credential,
            client_id=settings.google_client_id,
        )
        entity = await google_use_case(repository=None, command=command)

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
    except Exception as exc:
        log_email = getattr(exc, 'email', None) or "google-unknown"
        log_auth_attempt(
            username=log_email,
            success=False,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            reason=f"Error: {type(exc).__name__}",
        )
        await handle_common_errors(exc, request)
