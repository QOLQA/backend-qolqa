from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from domain.entities.VersionEntity import VersionEntity
from domain.errors import Forbidden


@dataclass
class SolutionEntity:
    """Pure domain entity for a Solution. No infrastructure dependencies."""

    id: str
    name: str
    user_id: str
    last_version_saved: str = "unknown"
    src_img: str = "http://unknown.es"
    last_updated_at: Optional[datetime] = None
    versions: List[VersionEntity] = field(default_factory=list)

    # ------------------------------------------------------------------ #
    # Factory Methods
    # ------------------------------------------------------------------ #

    @classmethod
    def create(
        cls,
        id: str,
        name: str,
        user_id: str,
        last_version_saved: str = "unknown",
        src_img: str = "http://unknown.es",
    ) -> "SolutionEntity":
        """Create a new solution."""
        if not name or not name.strip():
            raise ValueError("Solution name cannot be empty")
        if len(name) > 200:
            raise ValueError("Solution name cannot exceed 200 characters")
        if not user_id:
            raise ValueError("User ID is required")
        if not id:
            raise ValueError("Solution ID is required")

        return cls(
            id=id,
            name=name.strip(),
            user_id=user_id,
            last_version_saved=last_version_saved[:100],
            src_img=src_img[:500],
            last_updated_at=datetime.utcnow(),
            versions=[],
        )

    # ------------------------------------------------------------------ #
    # Business Mutation Methods
    # ------------------------------------------------------------------ #

    def update_name(self, name: str) -> None:
        """Update solution name."""
        if not name or not name.strip():
            raise ValueError("Solution name cannot be empty")
        if len(name) > 200:
            raise ValueError("Solution name cannot exceed 200 characters")
        self.name = name.strip()
        self.last_updated_at = datetime.utcnow()

    def update_image(self, src_img: str) -> None:
        """Update solution image URL."""
        if not src_img:
            raise ValueError("Image URL cannot be empty")
        if len(src_img) > 500:
            raise ValueError("Image URL cannot exceed 500 characters")
        self.src_img = src_img
        self.last_updated_at = datetime.utcnow()

    def update_last_version(self, version_name: str) -> None:
        """Update the last saved version name."""
        if not version_name:
            raise ValueError("Version name cannot be empty")
        self.last_version_saved = version_name[:100]
        self.last_updated_at = datetime.utcnow()

    def add_version(self, version: VersionEntity) -> None:
        """Add a version to this solution."""
        if not version:
            raise ValueError("Version cannot be None")
        if version.solution_id != self.id:
            raise ValueError("Version solution_id must match this solution's ID")
        self.versions.append(version)
        self.last_updated_at = datetime.utcnow()

    def remove_version(self, version_id: str) -> bool:
        """Remove a version by ID. Returns True if removed."""
        for i, v in enumerate(self.versions):
            if v.id == version_id:
                self.versions.pop(i)
                self.last_updated_at = datetime.utcnow()
                return True
        return False

    # ------------------------------------------------------------------ #
    # Authorization
    # ------------------------------------------------------------------ #

    def assert_owned_by(self, user_id: str) -> None:
        """Raise Forbidden when this solution is not owned by user_id."""
        if self.user_id != user_id:
            raise Forbidden(msg=f'User {user_id} is not authorized to access solution {self.id}.')