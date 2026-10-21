"""
Cross-tenant authorization tests for queries and versions.

Before this change set, any authenticated user could read and mutate any
other user's queries and versions. These tests pin the ownership rules:

- listings only return the resources attached to the caller's own solutions
- reading / updating / deleting someone else's resource raises Forbidden
- creating a resource against someone else's solution raises Forbidden

Repositories are mocked at the repository level (AsyncMock), never at the
Motor level, per the project testing conventions.
"""
import pytest
from unittest.mock import AsyncMock, patch

from application.dtos.query.QueryRequest import QueryCreateRequest, QueryPartialUpdateRequest
from application.use_cases.query.CreateQuery import create_query
from application.use_cases.query.DeleteQueriesBySolution import delete_queries_by_solution
from application.use_cases.query.DeleteQuery import delete_query
from application.use_cases.query.GetAllQueries import get_all_queries
from application.use_cases.query.GetQueriesBySolution import get_queries_by_solution
from application.use_cases.query.GetQueryById import get_query_by_id
from application.use_cases.query.UpdateQuery import update_query
from domain.entities.QueryEntity import QueryEntity
from domain.entities.SolutionEntity import SolutionEntity
from domain.errors import Forbidden


OWNER_ID = "507f1f77bcf86cd799439011"
OTHER_USER_ID = "507f1f77bcf86cd799439099"
SOLUTION_ID = "507f1f77bcf86cd799439022"
QUERY_ID = "507f1f77bcf86cd799439033"


def make_solution(user_id: str, solution_id: str = SOLUTION_ID) -> SolutionEntity:
    """Build a solution owned by user_id."""
    return SolutionEntity(
        id=solution_id,
        name="Test Solution",
        user_id=user_id,
        versions=[],
    )


def make_query(solution_id: str = SOLUTION_ID, query_id: str = QUERY_ID) -> QueryEntity:
    """Build a query attached to solution_id."""
    return QueryEntity(
        id=query_id,
        full_query="SELECT * FROM users",
        collections=["users"],
        highlighted_words=[],
        solution_id=solution_id,
    )


@pytest.mark.unit
class TestGetAllQueriesOwnership:
    """GET /queries must only expose the caller's own queries."""

    @pytest.mark.asyncio
    async def test_returns_only_queries_of_own_solutions(self):
        query_repository = AsyncMock()
        solution_repository = AsyncMock()

        solution_repository.get_all_for_user = AsyncMock(return_value=[make_solution(OWNER_ID)])
        query_repository.get_by_solution_ids = AsyncMock(return_value=[make_query()])

        result = await get_all_queries(query_repository, solution_repository, OWNER_ID)

        assert [q.id for q in result] == [QUERY_ID]
        solution_repository.get_all_for_user.assert_awaited_once_with(OWNER_ID)
        query_repository.get_by_solution_ids.assert_awaited_once_with([SOLUTION_ID])

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_user_has_no_solutions(self):
        query_repository = AsyncMock()
        solution_repository = AsyncMock()

        solution_repository.get_all_for_user = AsyncMock(return_value=[])
        query_repository.get_by_solution_ids = AsyncMock(return_value=[])

        result = await get_all_queries(query_repository, solution_repository, OWNER_ID)

        assert result == []
        query_repository.get_by_solution_ids.assert_not_awaited()


@pytest.mark.unit
class TestQueryUseCaseOwnership:
    """Single-resource use cases must refuse non-owners."""

    @pytest.mark.asyncio
    async def test_get_query_by_id_raises_forbidden_for_non_owner(self):
        query_repository = AsyncMock()
        solution_repository = AsyncMock()

        query_repository.get_by_id = AsyncMock(return_value=make_query())
        solution_repository.get_by_id = AsyncMock(return_value=make_solution(OTHER_USER_ID))

        with pytest.raises(Forbidden):
            await get_query_by_id(query_repository, solution_repository, QUERY_ID, OWNER_ID)

    @pytest.mark.asyncio
    async def test_get_query_by_id_returns_query_for_owner(self):
        query_repository = AsyncMock()
        solution_repository = AsyncMock()

        query_repository.get_by_id = AsyncMock(return_value=make_query())
        solution_repository.get_by_id = AsyncMock(return_value=make_solution(OWNER_ID))

        result = await get_query_by_id(query_repository, solution_repository, QUERY_ID, OWNER_ID)

        assert result.id == QUERY_ID

    @pytest.mark.asyncio
    async def test_update_query_raises_forbidden_for_non_owner(self):
        query_repository = AsyncMock()
        solution_repository = AsyncMock()

        query_repository.get_by_id = AsyncMock(return_value=make_query())
        solution_repository.get_by_id = AsyncMock(return_value=make_solution(OTHER_USER_ID))

        with pytest.raises(Forbidden):
            await update_query(
                query_repository,
                solution_repository,
                QUERY_ID,
                QueryPartialUpdateRequest(full_query="DROP TABLE users"),
                OWNER_ID,
            )

        query_repository.update.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_update_query_updates_for_owner(self):
        query_repository = AsyncMock()
        solution_repository = AsyncMock()

        query_repository.get_by_id = AsyncMock(return_value=make_query())
        query_repository.update = AsyncMock(return_value=make_query())
        solution_repository.get_by_id = AsyncMock(return_value=make_solution(OWNER_ID))

        result = await update_query(
            query_repository,
            solution_repository,
            QUERY_ID,
            QueryPartialUpdateRequest(full_query="SELECT 1"),
            OWNER_ID,
        )

        assert result.id == QUERY_ID
        query_repository.update.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_query_raises_forbidden_for_non_owner(self):
        query_repository = AsyncMock()
        solution_repository = AsyncMock()

        query_repository.get_by_id = AsyncMock(return_value=make_query())
        solution_repository.get_by_id = AsyncMock(return_value=make_solution(OTHER_USER_ID))

        with pytest.raises(Forbidden):
            await delete_query(query_repository, solution_repository, QUERY_ID, OWNER_ID)

        query_repository.delete.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_delete_query_deletes_for_owner(self):
        query_repository = AsyncMock()
        solution_repository = AsyncMock()

        query_repository.get_by_id = AsyncMock(return_value=make_query())
        query_repository.delete = AsyncMock()
        solution_repository.get_by_id = AsyncMock(return_value=make_solution(OWNER_ID))

        await delete_query(query_repository, solution_repository, QUERY_ID, OWNER_ID)

        query_repository.delete.assert_awaited_once_with(QUERY_ID)


@pytest.mark.unit
class TestQuerySolutionScopeOwnership:
    """Solution-scoped query operations must refuse non-owners."""

    @pytest.mark.asyncio
    async def test_create_query_raises_forbidden_for_non_owner(self):
        query_repository = AsyncMock()
        solution_repository = AsyncMock()

        solution_repository.get_by_id = AsyncMock(return_value=make_solution(OTHER_USER_ID))

        with pytest.raises(Forbidden):
            await create_query(
                query_repository,
                solution_repository,
                QueryCreateRequest(
                    full_query="SELECT * FROM users",
                    collections=["users"],
                    highlighted_words=[],
                    solution_id=SOLUTION_ID,
                ),
                OWNER_ID,
            )

        query_repository.add.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_create_query_creates_for_owner(self):
        query_repository = AsyncMock()
        solution_repository = AsyncMock()

        solution_repository.get_by_id = AsyncMock(return_value=make_solution(OWNER_ID))
        query_repository.add = AsyncMock(return_value=make_query())

        result = await create_query(
            query_repository,
            solution_repository,
            QueryCreateRequest(
                full_query="SELECT * FROM users",
                collections=["users"],
                highlighted_words=[],
                solution_id=SOLUTION_ID,
            ),
            OWNER_ID,
        )

        assert result.id == QUERY_ID
        query_repository.add.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_queries_by_solution_raises_forbidden_for_non_owner(self):
        query_repository = AsyncMock()
        solution_repository = AsyncMock()

        solution_repository.get_by_id = AsyncMock(return_value=make_solution(OTHER_USER_ID))

        with pytest.raises(Forbidden):
            await get_queries_by_solution(
                query_repository, solution_repository, SOLUTION_ID, OWNER_ID
            )

        query_repository.get_by_solution_id.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_delete_queries_by_solution_raises_forbidden_for_non_owner(self):
        query_repository = AsyncMock()
        solution_repository = AsyncMock()

        solution_repository.get_by_id = AsyncMock(return_value=make_solution(OTHER_USER_ID))

        with pytest.raises(Forbidden):
            await delete_queries_by_solution(
                query_repository, solution_repository, SOLUTION_ID, OWNER_ID
            )

        query_repository.delete_by_solution_id.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_delete_queries_by_solution_deletes_for_owner(self):
        query_repository = AsyncMock()
        solution_repository = AsyncMock()

        solution_repository.get_by_id = AsyncMock(return_value=make_solution(OWNER_ID))
        query_repository.delete_by_solution_id = AsyncMock()

        await delete_queries_by_solution(
            query_repository, solution_repository, SOLUTION_ID, OWNER_ID
        )

        query_repository.delete_by_solution_id.assert_awaited_once_with(SOLUTION_ID)


@pytest.mark.integration
class TestQueryEndpointOwnership:
    """HTTP surface: non-owners get 403, owners get 200/204."""

    @pytest.mark.asyncio
    async def test_get_query_returns_403_for_non_owner(self, authenticated_client, mock_user):
        with patch('api.controllers.query.QueryRepositoryImpl.get_by_id', new_callable=AsyncMock) as mock_get_query, \
             patch('api.controllers.query.SolutionRepositoryImpl.get_by_id', new_callable=AsyncMock) as mock_get_solution:
            mock_get_query.return_value = make_query()
            mock_get_solution.return_value = make_solution(OTHER_USER_ID)

            response = await authenticated_client.get(f"/queries/{QUERY_ID}")

            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_query_returns_200_for_owner(self, authenticated_client, mock_user):
        with patch('api.controllers.query.QueryRepositoryImpl.get_by_id', new_callable=AsyncMock) as mock_get_query, \
             patch('api.controllers.query.SolutionRepositoryImpl.get_by_id', new_callable=AsyncMock) as mock_get_solution:
            mock_get_query.return_value = make_query()
            mock_get_solution.return_value = make_solution(str(mock_user.id))

            response = await authenticated_client.get(f"/queries/{QUERY_ID}")

            assert response.status_code == 200
            assert response.json()["_id"] == QUERY_ID

    @pytest.mark.asyncio
    async def test_delete_query_returns_403_for_non_owner(self, authenticated_client, mock_user):
        with patch('api.controllers.query.QueryRepositoryImpl.get_by_id', new_callable=AsyncMock) as mock_get_query, \
             patch('api.controllers.query.SolutionRepositoryImpl.get_by_id', new_callable=AsyncMock) as mock_get_solution:
            mock_get_query.return_value = make_query()
            mock_get_solution.return_value = make_solution(OTHER_USER_ID)

            response = await authenticated_client.delete(f"/queries/{QUERY_ID}")

            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_query_returns_204_for_owner(self, authenticated_client, mock_user):
        with patch('api.controllers.query.QueryRepositoryImpl.get_by_id', new_callable=AsyncMock) as mock_get_query, \
             patch('api.controllers.query.SolutionRepositoryImpl.get_by_id', new_callable=AsyncMock) as mock_get_solution, \
             patch('api.controllers.query.QueryRepositoryImpl.delete', new_callable=AsyncMock) as mock_delete:
            mock_get_query.return_value = make_query()
            mock_get_solution.return_value = make_solution(str(mock_user.id))

            response = await authenticated_client.delete(f"/queries/{QUERY_ID}")

            assert response.status_code == 204
            mock_delete.assert_awaited_once_with(QUERY_ID)

    @pytest.mark.asyncio
    async def test_create_query_returns_403_for_non_owner_solution(self, authenticated_client, mock_user):
        with patch('api.controllers.query.SolutionRepositoryImpl.get_by_id', new_callable=AsyncMock) as mock_get_solution:
            mock_get_solution.return_value = make_solution(OTHER_USER_ID)

            response = await authenticated_client.post(
                "/queries",
                json={
                    "full_query": "SELECT * FROM users",
                    "collections": ["users"],
                    "highlighted_words": [],
                    "solution_id": SOLUTION_ID,
                },
            )

            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_queries_by_solution_returns_403_for_non_owner(self, authenticated_client, mock_user):
        with patch('api.controllers.query.SolutionRepositoryImpl.get_by_id', new_callable=AsyncMock) as mock_get_solution:
            mock_get_solution.return_value = make_solution(OTHER_USER_ID)

            response = await authenticated_client.get(f"/queries/solution/{SOLUTION_ID}")

            assert response.status_code == 403
