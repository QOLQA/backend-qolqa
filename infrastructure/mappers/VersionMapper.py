from application.dtos.version.VersionRequest import VersionCreateRequest
from application.dtos.version.VersionResponse import VersionResponse
from domain.entities.VersionEntity import VersionEntity, Submodel


class VersionMapper:
    """Stateless mapper between raw MongoDB dicts, VersionEntity, and DTOs."""

    @staticmethod
    def to_entity(raw: dict) -> VersionEntity:
        """Convert a raw MongoDB dict to a domain VersionEntity.

        Used when Motor returns a plain dict (e.g. from find_one / cursor).
        """
        submodels = [
            Submodel(**s) if isinstance(s, dict) else s
            for s in raw.get('submodels', [])
        ]
        return VersionEntity(
            id=str(raw['_id']),
            submodels=submodels,
            description=raw['description'],
            solution_id=str(raw['solution_id']),
        )

    @staticmethod
    def from_create_request(request: VersionCreateRequest) -> dict:
        """Convert a VersionCreateRequest DTO to a MongoDB-insertable dict."""
        return {
            'submodels': [s.model_dump() for s in request.submodels],
            'description': request.description,
            'solution_id': request.solution_id,
        }

    @staticmethod
    def to_response(entity: VersionEntity) -> VersionResponse:
        """Convert a domain VersionEntity to a VersionResponse DTO."""
        return VersionResponse(
            id=entity.id,
            submodels=entity.submodels,
            description=entity.description,
            solution_id=entity.solution_id,
        )
