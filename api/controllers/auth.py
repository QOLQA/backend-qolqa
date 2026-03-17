"""
Authentication controller (Clean Architecture)
Handles login, registration, and user profile endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.util import get_remote_address

from application.dtos.auth.AuthRequest import UserCreateRequest
from application.dtos.auth.AuthResponse import UserResponse, TokenResponse
from application.use_cases.auth.AuthenticateUser import authenticate_user
from application.use_cases.auth.RegisterUser import register_user
from application.use_cases.auth.GetUserById import get_user_by_id
from application.use_cases.auth.CreateUserToken import create_user_token
from infrastructure.mappers import UserMapper
from infrastructure.repositories.UserRepoImpl import UserRepositoryImpl
from auth.jwt import get_token_data
from models.user import User
from api.handle_errors import handle_common_errors
from infrastructure.db_factory import get_database
from utils.audit import log_registration, log_auth_attempt

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


def get_user_repository(database=Depends(get_database)) -> UserRepositoryImpl:
    """Dependency: always returns the MongoDB UserRepositoryImpl."""
    return UserRepositoryImpl(database)


async def get_current_user(
    token_data: dict = Depends(get_token_data),
    repository: UserRepositoryImpl = Depends(get_user_repository),
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        token_data: Decoded JWT token data
        repository: UserRepositoryImpl dependency

    Returns:
        Current authenticated user as models.user.User

    Raises:
        HTTPException: If user not found or inactive
    """
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

        # Return as models.user.User for backward compatibility with other controllers
        return User(
            id=entity.id,
            username=entity.username,
            email=entity.email,
            full_name=entity.full_name,
            is_active=entity.is_active,
            created_at=entity.created_at,
        )
    except HTTPException:
        raise
    except Exception as exc:
        await handle_common_errors(exc)


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

        if not entity:
            # Audit log: failed login attempt
            log_auth_attempt(
                username=form_data.username,
                success=False,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                reason="Invalid credentials",
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
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
    except HTTPException as http_exc:
        # If it's a 401, log failed attempt (in case it wasn't logged above)
        if http_exc.status_code == status.HTTP_401_UNAUTHORIZED:
            log_auth_attempt(
                username=form_data.username,
                success=False,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                reason=str(http_exc.detail),
            )
        raise
    except Exception as exc:
        # Log unexpected errors
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
    return UserResponse(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )
