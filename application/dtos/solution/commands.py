"""
Solution Commands - Frozen dataclasses for application use cases.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CreateSolutionCommand:
    """Command to create a new solution."""
    name: str
    last_version_saved: str = "unknown"
    src_img: str = "http://unknown.es"
    user_id: str = ""  # Injected from auth context


@dataclass(frozen=True)
class UpdateSolutionCommand:
    """Command to partially update a solution."""
    name: Optional[str] = None
    last_version_saved: Optional[str] = None
    src_img: Optional[str] = None


@dataclass(frozen=True)
class DeleteSolutionCommand:
    """Command to delete a solution."""
    solution_id: str
    current_user_id: str