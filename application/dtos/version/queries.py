"""
Version Queries - Frozen dataclasses for application use cases.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class GetVersionQuery:
    """Query to get a version by ID."""
    version_id: str
    current_user_id: str


@dataclass(frozen=True)
class GetAllVersionsQuery:
    """Query to get all versions for a user."""
    user_id: str


@dataclass(frozen=True)
class GetVersionsBySolutionQuery:
    """Query to get all versions for a solution."""
    solution_id: str
    current_user_id: str