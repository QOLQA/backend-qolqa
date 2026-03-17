from bson import ObjectId

from application.dtos.query.QueryRequest import QueryCreateRequest
from application.dtos.query.QueryResponse import QueryResponse
from domain.entities.QueryEntity import QueryEntity
from infrastructure.documents.QueryDocument import QueryDocument


class QueryMapper:
    """Stateless mapper between QueryDocument, QueryEntity, and DTOs."""

    @staticmethod
    def to_entity(doc: QueryDocument) -> QueryEntity:
        """Convert a QueryDocument (MongoDB shape) to a domain QueryEntity."""
        return QueryEntity(
            id=str(doc.id),
            full_query=doc.full_query,
            collections=doc.collections,
            highlighted_words=doc.highlighted_words,
            solution_id=str(doc.solution_id),
        )

    @staticmethod
    def to_entity_from_dict(raw: dict) -> QueryEntity:
        """Convert a raw MongoDB dict to a domain QueryEntity.

        Used when Motor returns a plain dict (e.g. from find_one / cursor).
        """
        return QueryEntity(
            id=str(raw['_id']),
            full_query=raw['full_query'],
            collections=raw.get('collections', []),
            highlighted_words=raw.get('highlighted_words', []),
            solution_id=str(raw['solution_id']),
        )

    @staticmethod
    def to_document(entity: QueryEntity) -> dict:
        """Convert a QueryEntity to a MongoDB-insertable dict.

        Converts string ids back to ObjectId for storage.
        """
        return {
            'full_query': entity.full_query,
            'collections': entity.collections,
            'highlighted_words': entity.highlighted_words,
            'solution_id': ObjectId(entity.solution_id),
        }

    @staticmethod
    def from_create_request(request: QueryCreateRequest) -> dict:
        """Convert a QueryCreateRequest DTO to a MongoDB-insertable dict."""
        return {
            'full_query': request.full_query,
            'collections': request.collections,
            'highlighted_words': request.highlighted_words,
            'solution_id': ObjectId(request.solution_id),
        }

    @staticmethod
    def to_response(entity: QueryEntity) -> QueryResponse:
        """Convert a domain QueryEntity to a QueryResponse DTO."""
        return QueryResponse(
            id=entity.id,
            full_query=entity.full_query,
            collections=entity.collections,
            highlighted_words=entity.highlighted_words,
            solution_id=entity.solution_id,
        )
