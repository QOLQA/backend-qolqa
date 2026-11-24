"""
Query Queries - Frozen dataclasses for application use cases.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class GetQueryQuery:
    """Query to get a query by ID."""
    query_id: str
    current_user_id: str


@dataclass(frozen=True)
class GetAllQueriesQuery:
    """Query to get all queries for a user."""
    user_id: str


@dataclass(frozen=True)
class GetQueriesBySolutionQuery:
    """Query to get all queries for a solution."""
    solution_id: str
    current_user_id: str