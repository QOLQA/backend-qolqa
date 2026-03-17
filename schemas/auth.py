"""
Authentication schemas for requests and responses
"""
from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data extracted from JWT token"""
    username: Optional[str] = None
    user_id: Optional[str] = None


class UserLogin(BaseModel):
    """Login request schema"""
    username: str
    password: str

