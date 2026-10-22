"""
Version Commands - Frozen dataclasses for application use cases.
"""
from dataclasses import dataclass
from typing import List, Optional

from domain.entities.VersionEntity import Submodel


@dataclass(frozen=True)
class CreateVersionCommand:
    """Command to create a new version."""
    submodels: List[Submodel]
    description: str
    solution_id: str
    current_user_id: str


@dataclass(frozen=True)
class UpdateVersionCommand:
    """Command to partially update a version."""
    submodels: Optional[List[Submodel]] = None
    description: Optional[str] = None
    solution_id: Optional[str] = None


@dataclass(frozen=True)
class DeleteVersionCommand:
    """Command to delete a version."""
    version_id: str
    current_user_id: str