"""
Authentication service layer
Business logic for user authentication and management
"""
from typing import Optional
from datetime import timedelta

from fastapi import HTTPException, status

from auth.repository import UserRepository
from auth.password import verify_password
from auth.jwt import create_access_token
from models.user import UserInDB, UserCreate, User
from schemas.auth import Token
from config.settings import settings


async def authenticate_user(repository: UserRepository, username: str, password: str) -> Optional[UserInDB]:
    """
    Authenticate a user by username or email and password
    
    Args:
        repository: User repository instance
        username: Username or email to authenticate
        password: Plain text password
        
    Returns:
        UserInDB if authentication successful, None otherwise
    """
    # Try to get user by username first
    user = await repository.get_by_username(username)
    
    # If not found, try by email
    if not user:
        user = await repository.get_by_email(username)
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    if not user.is_active:
        return None
    
    return user


async def create_user_token(user: UserInDB) -> Token:
    """
    Create access token for user
    
    Args:
        user: User to create token for
        
    Returns:
        Token with access token
    """
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": str(user.id),
            "email": user.email
        },
        expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")


async def register_user(repository: UserRepository, user_create: UserCreate) -> User:
    """
    Register a new user
    
    Args:
        repository: User repository instance
        user_create: User creation data
        
    Returns:
        Created user (without password)
    """
    user_in_db = await repository.create(user_create)
    
    return User(
        id=str(user_in_db.id),
        username=user_in_db.username,
        email=user_in_db.email,
        full_name=user_in_db.full_name,
        is_active=user_in_db.is_active,
        created_at=user_in_db.created_at
    )


async def get_user_by_id(repository: UserRepository, user_id: str) -> User:
    """
    Get user by ID
    
    Args:
        repository: User repository instance
        user_id: User ID
        
    Returns:
        User information
    """
    user_in_db = await repository.get_by_id(user_id)
    
    return User(
        id=str(user_in_db.id),
        username=user_in_db.username,
        email=user_in_db.email,
        full_name=user_in_db.full_name,
        is_active=user_in_db.is_active,
        created_at=user_in_db.created_at
    )
