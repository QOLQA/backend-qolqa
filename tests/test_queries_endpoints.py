"""
Tests de integración para los endpoints de /queries.

Cubre:
- CRUD completo (crear, editar, eliminar, obtener por id y por solución).
- Validación de esquema (payload incompleto → 422).
- Ownership cross-tenant (usuario autenticado no puede tocar queries de otro usuario).
- Relación con solución (GET/DELETE por solution_id).

Los repositorios se mockean a nivel de repository (AsyncMock), nunca a nivel de Motor,
siguiendo las convenciones de testing del proyecto.
"""
from unittest.mock import AsyncMock, patch

import pytest
from bson import ObjectId
from fastapi import status

from domain.entities.QueryEntity import QueryEntity
from domain.entities.SolutionEntity import SolutionEntity
from domain.errors import NotFoundError

QUERY_ID = str(ObjectId())
SOLUTION_ID = str(ObjectId())
OTHER_USER_ID = str(ObjectId())


def make_query(query_id: str = QUERY_ID, solution_id: str = SOLUTION_ID, **kwargs) -> QueryEntity:
    return QueryEntity(
        id=query_id,
        full_query=kwargs.get("full_query", "SELECT * FROM users"),
        collections=kwargs.get("collections", ["users"]),
        highlighted_words=kwargs.get("highlighted_words", []),
        solution_id=solution_id,
    )


def make_solution(solution_id: str = SOLUTION_ID, user_id: str | None = None, **kwargs) -> SolutionEntity:
    return SolutionEntity(
        id=solution_id,
        name=kwargs.get("name", "Test Solution"),
        user_id=user_id or str(ObjectId()),
        versions=[],
    )


@pytest.mark.integration
class TestQueriesEndpoints:
    """Test suite para los endpoints de Query."""

    @pytest.mark.asyncio
    async def test_create_query_success(self, authenticated_client, mock_user, auth_headers):
        """POST /queries crea una query y retorna 201 con sus datos."""
        solution = make_solution(user_id=str(mock_user.id))
        created_query = make_query()

        with patch(
            "infra.persistence.repositories.SolutionRepositoryImpl.get_by_id",
            new_callable=AsyncMock,
        ) as mock_get_solution, patch(
            "infra.persistence.repositories.QueryRepositoryImpl.save",
            new_callable=AsyncMock,
        ) as mock_save:

            mock_get_solution.return_value = solution
            mock_save.return_value = created_query

            response = await authenticated_client.post(
                "/queries",
                json={
                    "full_query": "SELECT * FROM users",
                    "collections": ["users"],
                    "highlighted_words": [],
                    "solution_id": SOLUTION_ID,
                },
                headers=auth_headers,
            )

            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["_id"] == QUERY_ID
            assert data["full_query"] == "SELECT * FROM users"
            assert data["collections"] == ["users"]
            assert data["solution_id"] == SOLUTION_ID

    @pytest.mark.asyncio
    async def test_create_query_validation_error(self, authenticated_client, auth_headers):
        """POST /queries con payload incompleto retorna 422."""
        response = await authenticated_client.post(
            "/queries",
            json={
                # Falta full_query (requerido)
                "collections": ["users"],
                "solution_id": SOLUTION_ID,
            },
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_create_query_nonexistent_solution(self, authenticated_client, mock_user, auth_headers):
        """POST /queries con solution_id inexistente retorna 404."""
        with patch(
            "infra.persistence.repositories.SolutionRepositoryImpl.get_by_id",
            new_callable=AsyncMock,
        ) as mock_get_solution:
            mock_get_solution.side_effect = NotFoundError("Solution not found")

            response = await authenticated_client.post(
                "/queries",
                json={
                    "full_query": "SELECT * FROM users",
                    "collections": ["users"],
                    "highlighted_words": [],
                    "solution_id": SOLUTION_ID,
                },
                headers=auth_headers,
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_queries_by_solution(self, authenticated_client, mock_user, auth_headers):
        """GET /queries/solution/{id} retorna las queries de esa solución."""
        solution = make_solution(user_id=str(mock_user.id))
        queries = [make_query(), make_query(query_id=str(ObjectId()))]

        with patch(
            "infra.persistence.repositories.SolutionRepositoryImpl.get_by_id",
            new_callable=AsyncMock,
        ) as mock_get_solution, patch(
            "infra.persistence.repositories.QueryRepositoryImpl.get_by_solution_id",
            new_callable=AsyncMock,
        ) as mock_get_queries:

            mock_get_solution.return_value = solution
            mock_get_queries.return_value = queries

            response = await authenticated_client.get(
                f"/queries/solution/{SOLUTION_ID}",
                headers=auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 2
            assert data[0]["_id"] == QUERY_ID

    @pytest.mark.asyncio
    async def test_get_query_by_id_success(self, authenticated_client, mock_user, auth_headers):
        """GET /queries/{id} retorna 200 si la query pertenece al usuario."""
        query = make_query()
        solution = make_solution(user_id=str(mock_user.id))

        with patch(
            "infra.persistence.repositories.QueryRepositoryImpl.get_by_id",
            new_callable=AsyncMock,
        ) as mock_get_query, patch(
            "infra.persistence.repositories.SolutionRepositoryImpl.get_by_id",
            new_callable=AsyncMock,
        ) as mock_get_solution:

            mock_get_query.return_value = query
            mock_get_solution.return_value = solution

            response = await authenticated_client.get(
                f"/queries/{QUERY_ID}",
                headers=auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["_id"] == QUERY_ID

    @pytest.mark.asyncio
    async def test_get_query_by_id_not_found(self, authenticated_client, auth_headers):
        """GET /queries/{id} con id inexistente retorna 404."""
        with patch(
            "infra.persistence.repositories.QueryRepositoryImpl.get_by_id",
            new_callable=AsyncMock,
        ) as mock_get_query:
            mock_get_query.side_effect = NotFoundError("Query not found")

            response = await authenticated_client.get(
                f"/queries/{QUERY_ID}",
                headers=auth_headers,
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_update_query_success(self, authenticated_client, mock_user, auth_headers):
        """PATCH /queries/{id} actualiza full_query y retorna 200."""
        query = make_query()
        updated_query = make_query(full_query="SELECT * FROM orders")
        solution = make_solution(user_id=str(mock_user.id))

        with patch(
            "infra.persistence.repositories.QueryRepositoryImpl.get_by_id",
            new_callable=AsyncMock,
        ) as mock_get_query, patch(
            "infra.persistence.repositories.SolutionRepositoryImpl.get_by_id",
            new_callable=AsyncMock,
        ) as mock_get_solution, patch(
            "infra.persistence.repositories.QueryRepositoryImpl.save",
            new_callable=AsyncMock,
        ) as mock_save:

            mock_get_query.return_value = query
            mock_get_solution.return_value = solution
            mock_save.return_value = updated_query

            response = await authenticated_client.patch(
                f"/queries/{QUERY_ID}",
                json={"full_query": "SELECT * FROM orders"},
                headers=auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["full_query"] == "SELECT * FROM orders"

    @pytest.mark.asyncio
    async def test_delete_query_success(self, authenticated_client, mock_user, auth_headers):
        """DELETE /queries/{id} retorna 204 y GET posterior retorna 404."""
        query = make_query()
        solution = make_solution(user_id=str(mock_user.id))

        # Un solo mock de get_by_id con side_effect: primero devuelve la query (para el DELETE),
        # luego lanza NotFoundError (para el GET posterior).
        with patch(
            "infra.persistence.repositories.QueryRepositoryImpl.get_by_id",
            new_callable=AsyncMock,
        ) as mock_get_query, patch(
            "infra.persistence.repositories.SolutionRepositoryImpl.get_by_id",
            new_callable=AsyncMock,
        ) as mock_get_solution, patch(
            "infra.persistence.repositories.QueryRepositoryImpl.delete",
            new_callable=AsyncMock,
        ) as mock_delete:

            mock_get_query.side_effect = [query, NotFoundError("Query not found")]
            mock_get_solution.return_value = solution
            mock_delete.return_value = None

            # DELETE
            response = await authenticated_client.delete(
                f"/queries/{QUERY_ID}",
                headers=auth_headers,
            )
            assert response.status_code == status.HTTP_204_NO_CONTENT
            mock_delete.assert_awaited_once_with(QUERY_ID)

            # GET posterior debe fallar
            response_get = await authenticated_client.get(
                f"/queries/{QUERY_ID}",
                headers=auth_headers,
            )
            assert response_get.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_delete_queries_by_solution(self, authenticated_client, mock_user, auth_headers):
        """DELETE /queries/solution/{id} retorna 204 y llama al borrado masivo."""
        solution = make_solution(user_id=str(mock_user.id))

        with patch(
            "infra.persistence.repositories.SolutionRepositoryImpl.get_by_id",
            new_callable=AsyncMock,
        ) as mock_get_solution, patch(
            "infra.persistence.repositories.QueryRepositoryImpl.delete_by_solution_id",
            new_callable=AsyncMock,
        ) as mock_delete_by_solution:

            mock_get_solution.return_value = solution
            mock_delete_by_solution.return_value = None

            response = await authenticated_client.delete(
                f"/queries/solution/{SOLUTION_ID}",
                headers=auth_headers,
            )

            assert response.status_code == status.HTTP_204_NO_CONTENT
            mock_delete_by_solution.assert_awaited_once_with(SOLUTION_ID)

    @pytest.mark.asyncio
    async def test_cross_tenant_query_forbidden(self, authenticated_client, mock_user, auth_headers):
        """Usuario autenticado no puede leer query de solución de otro usuario → 403."""
        query = make_query()
        solution_other = make_solution(user_id=OTHER_USER_ID)

        with patch(
            "infra.persistence.repositories.QueryRepositoryImpl.get_by_id",
            new_callable=AsyncMock,
        ) as mock_get_query, patch(
            "infra.persistence.repositories.SolutionRepositoryImpl.get_by_id",
            new_callable=AsyncMock,
        ) as mock_get_solution:

            mock_get_query.return_value = query
            mock_get_solution.return_value = solution_other

            response = await authenticated_client.get(
                f"/queries/{QUERY_ID}",
                headers=auth_headers,
            )

            assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_cross_tenant_update_forbidden(self, authenticated_client, mock_user, auth_headers):
        """Usuario autenticado no puede actualizar query de solución de otro usuario → 403."""
        query = make_query()
        solution_other = make_solution(user_id=OTHER_USER_ID)

        with patch(
            "infra.persistence.repositories.QueryRepositoryImpl.get_by_id",
            new_callable=AsyncMock,
        ) as mock_get_query, patch(
            "infra.persistence.repositories.SolutionRepositoryImpl.get_by_id",
            new_callable=AsyncMock,
        ) as mock_get_solution:

            mock_get_query.return_value = query
            mock_get_solution.return_value = solution_other

            response = await authenticated_client.patch(
                f"/queries/{QUERY_ID}",
                json={"full_query": "SELECT * FROM hacked"},
                headers=auth_headers,
            )

            assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_cross_tenant_delete_forbidden(self, authenticated_client, mock_user, auth_headers):
        """Usuario autenticado no puede eliminar query de solución de otro usuario → 403."""
        query = make_query()
        solution_other = make_solution(user_id=OTHER_USER_ID)

        with patch(
            "infra.persistence.repositories.QueryRepositoryImpl.get_by_id",
            new_callable=AsyncMock,
        ) as mock_get_query, patch(
            "infra.persistence.repositories.SolutionRepositoryImpl.get_by_id",
            new_callable=AsyncMock,
        ) as mock_get_solution:

            mock_get_query.return_value = query
            mock_get_solution.return_value = solution_other

            response = await authenticated_client.delete(
                f"/queries/{QUERY_ID}",
                headers=auth_headers,
            )

            assert response.status_code == status.HTTP_403_FORBIDDEN
