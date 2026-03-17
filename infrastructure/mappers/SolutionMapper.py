from datetime import datetime
from typing import List

from application.dtos.solution.SolutionRequest import SolutionCreateRequest
from application.dtos.solution.SolutionResponse import SolutionResponse
from application.dtos.version.VersionResponse import VersionResponse
from domain.entities.SolutionEntity import SolutionEntity
from domain.entities.VersionEntity import VersionEntity


class SolutionMapper:
    """Stateless mapper between raw MongoDB dicts, SolutionEntity, and DTOs."""

    @staticmethod
    def to_entity(raw: dict, versions: List[VersionEntity] = None) -> SolutionEntity:
        """Convert a raw MongoDB dict to a domain SolutionEntity.

        Used when Motor returns a plain dict (e.g. from find_one / cursor).
        Optionally accepts pre-fetched VersionEntity list (from versions collection).
        """
        return SolutionEntity(
            id=str(raw['_id']),
            name=raw['name'],
            user_id=raw['user_id'],
            last_version_saved=raw.get('last_version_saved', 'unknown'),
            src_img=raw.get('src_img', 'http://unknown.es'),
            last_updated_at=raw.get('last_updated_at'),
            versions=versions or [],
        )

    @staticmethod
    def from_create_request(request: SolutionCreateRequest, user_id: str) -> dict:
        """Convert a SolutionCreateRequest DTO + injected user_id to a MongoDB-insertable dict."""
        return {
            'name': request.name,
            'last_version_saved': request.last_version_saved,
            'src_img': request.src_img,
            'user_id': user_id,
            'last_updated_at': datetime.utcnow(),
        }

    @staticmethod
    def to_response(entity: SolutionEntity) -> SolutionResponse:
        """Convert a domain SolutionEntity to a SolutionResponse DTO."""
        version_responses = [
            VersionResponse(
                id=v.id,
                submodels=v.submodels,
                description=v.description,
                solution_id=v.solution_id,
            )
            for v in entity.versions
        ]
        return SolutionResponse(
            id=entity.id,
            name=entity.name,
            user_id=entity.user_id,
            last_version_saved=entity.last_version_saved,
            src_img=entity.src_img,
            last_updated_at=entity.last_updated_at,
            versions=version_responses,
        )
