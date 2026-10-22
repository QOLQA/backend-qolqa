"""
Auth Queries - Frozen dataclasses for application use cases.
These are agnostic of HTTP/Pydantic and used by use cases.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class GetUserQuery:
    """Query to get a user by ID."""
    user_id: str


@dataclass(frozen=True)
class GetUserByUsernameQuery:
    """Query to get a user by username."""
    username: str


@dataclass(frozen=True)
class GetUserByEmailQuery:
    """Query to get a user by email."""
    email: str