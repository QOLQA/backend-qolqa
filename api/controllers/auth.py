"""
Authentication controller (Clean Architecture)
Handles login, registration, and user profile endpoints.
"""
from fastapi import APIRouter, Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.util import get_remote_address

from application.dtos.auth.AuthRequest import UserCreateRequest
from application.dtos.auth.AuthResponse import UserResponse, TokenResponse
from application.use_cases.auth.AuthenticateUser import authenticate_user
from application.use_cases.auth.RegisterUser import register_user
from infrastructure.token_service import create_user_token
from infrastructure.mappers import UserMapper
from infrastructure.repositories.UserRepoImpl import UserRepositoryImpl
from domain.entities.auth.UserEntity import UserEntity as User
from api.handle_errors import handle_common_errors
from api.dependencies.auth import get_current_user, get_user_repository
from infrastructure.audit import log_registration, log_auth_attempt

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post('/register', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/hour")
async def register(
    request: Request,
    user_create: UserCreateRequest,
    repository: UserRepositoryImpl = Depends(get_user_repository),
) -> UserResponse:
    """
    Register a new user.

    Args:
        request: FastAPI Request (for audit logging)
        user_create: UserCreateRequest DTO
        repository: UserRepositoryImpl dependency

    Returns:
        UserResponse with the created user data (no password fields)
    """
    try:
        entity = await register_user(repository, user_create)

        response = UserMapper.to_response(entity)

        # Audit log: successful registration
        log_registration(
            user_id=entity.id,
            username=entity.username,
            email=entity.email,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        return response
    except Exception as exc:
        # Audit log: failed registration
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
    repository: UserRepositoryImpl = Depends(get_user_repository),
) -> TokenResponse:
    """
    Login endpoint — OAuth2 compatible.

    Args:
        request: FastAPI Request (for audit logging and rate limiting)
        form_data: OAuth2 form data (username and password)
        repository: UserRepositoryImpl dependency

    Returns:
        TokenResponse with JWT access token

    Raises:
        HTTPException: If authentication fails
    """
    try:
        entity = await authenticate_user(
            repository,
            form_data.username,
            form_data.password,
        )

        token = await create_user_token(entity)

        # Audit log: successful login
        log_auth_attempt(
            username=entity.username,
            success=True,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        return token
    except Exception as exc:
        # Log failed or unexpected errors before delegating to error handler
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
    """
    Get current user profile.

    Args:
        current_user: Current authenticated user

    Returns:
        UserResponse with user profile information
    """
    return UserMapper.to_response(current_user)
