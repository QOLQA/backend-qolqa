"""
Query Commands - Frozen dataclasses for application use cases.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class CreateQueryCommand:
    """Command to create a new query."""
    full_query: str
    collections: list[str]
    highlighted_words: list[str]
    solution_id: str
    current_user_id: str


@dataclass(frozen=True)
class UpdateQueryCommand:
    """Command to partially update a query."""
    full_query: str | None = None
    collections: list[str] | None = None
    highlighted_words: list[str] | None = None


@dataclass(frozen=True)
class DeleteQueryCommand:
    """Command to delete a query."""
    query_id: str
    current_user_id: str


@dataclass(frozen=True)
class DeleteQueriesBySolutionCommand:
    """Command to delete all queries for a solution."""
    solution_id: str
    current_user_id: str