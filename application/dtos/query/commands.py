"""
Query Commands - Frozen dataclasses for application use cases.
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class CreateQueryCommand:
    """Command to create a new query."""
    full_query: str
    collections: List[str]
    highlighted_words: List[str]
    solution_id: str
    current_user_id: str


@dataclass(frozen=True)
class UpdateQueryCommand:
    """Command to partially update a query."""
    full_query: Optional[str] = None
    collections: Optional[List[str]] = None
    highlighted_words: Optional[List[str]] = None


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