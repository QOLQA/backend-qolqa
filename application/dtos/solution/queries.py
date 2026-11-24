"""
Solution Queries - Frozen dataclasses for application use cases.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class GetSolutionQuery:
    """Query to get a solution by ID."""
    solution_id: str
    current_user_id: str


@dataclass(frozen=True)
class GetAllSolutionsQuery:
    """Query to get all solutions for a user."""
    user_id: str


@dataclass(frozen=True)
class GetSolutionWithVersionsQuery:
    """Query to get a solution with its versions."""
    solution_id: str
    current_user_id: str