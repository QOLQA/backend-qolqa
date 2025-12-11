"""
Authentication router
Handles login, registration, and user profile endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from auth import service
from auth.repository import UserRepository
from auth.jwt import get_token_data
from models.user import User, UserCreate
from schemas.auth import Token
from utils.get_database import get_database
from utils.handle_errors import handle_common_errors

router = APIRouter()


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
async def register(
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
        return user
    except Exception as exc:
        await handle_common_errors(exc)


@router.post('/login', response_model=Token)
async def login(
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
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token = await service.create_user_token(user)
        return token
    except HTTPException:
        raise
    except Exception as exc:
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
