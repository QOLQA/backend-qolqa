"""
Authentication router
Handles login, registration, and user profile endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.util import get_remote_address

from auth import service
from auth.repository import UserRepository
from auth.jwt import get_token_data
from models.user import User, UserCreate
from schemas.auth import Token
from infrastructure.db_factory import get_database
from api.handle_errors import handle_common_errors
from utils.audit import log_registration, log_auth_attempt

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Rate limiter se configura en main.py y se accede via request.app.state.limiter


async def get_current_user(
    token_data: dict = Depends(get_token_data),
    database = Depends(get_database)
) -> User:
    """
    Get current authenticated user from JWT token
    
    Args:
        token_data: Decoded JWT token data
        database: Database dependency
        
    Returns:
        Current authenticated user
        
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
        repository = UserRepository(database)
        user = await service.get_user_by_id(repository, user_id)
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user"
            )
        
        return user
    except Exception as exc:
        await handle_common_errors(exc)


@router.post('/register', response_model=User, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/hour")  # 3 registros por hora
async def register(
    request: Request,
    user_create: UserCreate,
    database = Depends(get_database)
) -> User:
    """
    Register a new user
    
    Args:
        user_create: User registration data
        database: Database dependency
        
    Returns:
        Created user information (without password)
    """
    try:
        repository = UserRepository(database)
        user = await service.register_user(repository, user_create)
        
        # Audit log: successful registration
        log_registration(
            user_id=str(user.id),
            username=user.username,
            email=user.email,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        
        return user
    except Exception as exc:
        # Audit log: failed registration
        log_auth_attempt(
            username=user_create.username,
            success=False,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            reason=str(exc)
        )
        await handle_common_errors(exc, request)


@router.post('/login', response_model=Token)
@limiter.limit("5/minute")  # 5 intentos de login por minuto
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    database = Depends(get_database)
) -> Token:
    """
    Login endpoint - OAuth2 compatible
    
    Args:
        form_data: OAuth2 form data (username and password)
        database: Database dependency
        
    Returns:
        JWT access token
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        repository = UserRepository(database)
        user = await service.authenticate_user(
            repository,
            form_data.username,
            form_data.password
        )
        
        if not user:
            # Audit log: failed login attempt
            log_auth_attempt(
                username=form_data.username,
                success=False,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                reason="Invalid credentials"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token = await service.create_user_token(user)
        
        # Audit log: successful login
        log_auth_attempt(
            username=user.username,
            success=True,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
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
                reason=str(http_exc.detail)
            )
        raise
    except Exception as exc:
        # Log unexpected errors
        log_auth_attempt(
            username=form_data.username,
            success=False,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            reason=f"Error: {type(exc).__name__}"
        )
        await handle_common_errors(exc)


@router.get('/me', response_model=User)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current user profile
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User profile information
    """
    return current_user
