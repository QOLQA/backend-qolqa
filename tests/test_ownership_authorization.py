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
from application.dtos.version.VersionRequest import VersionCreateRequest, VersionPartialUpdateRequest
from application.use_cases.query.CreateQuery import create_query
from application.use_cases.query.DeleteQueriesBySolution import delete_queries_by_solution
from application.use_cases.query.DeleteQuery import delete_query
from application.use_cases.query.GetAllQueries import get_all_queries
from application.use_cases.query.GetQueriesBySolution import get_queries_by_solution
from application.use_cases.query.GetQueryById import get_query_by_id
from application.use_cases.query.UpdateQuery import update_query
from application.use_cases.version.CreateVersion import create_version
from application.use_cases.version.DeleteVersion import delete_version
from application.use_cases.version.GetAllVersions import get_all_versions
from application.use_cases.version.GetVersionById import get_version_by_id
from application.use_cases.version.UpdateVersion import update_version
from domain.entities.QueryEntity import QueryEntity
from domain.entities.SolutionEntity import SolutionEntity
from domain.entities.VersionEntity import VersionEntity
from domain.errors import Forbidden


OWNER_ID = "507f1f77bcf86cd799439011"
OTHER_USER_ID = "507f1f77bcf86cd799439099"
SOLUTION_ID = "507f1f77bcf86cd799439022"
QUERY_ID = "507f1f77bcf86cd799439033"
VERSION_ID = "507f1f77bcf86cd799439044"
OTHER_SOLUTION_ID = "507f1f77bcf86cd799439055"


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


def make_version(solution_id: str = SOLUTION_ID, version_id: str = VERSION_ID) -> VersionEntity:
    """Build a version attached to solution_id."""
    return VersionEntity(
        id=version_id,
        submodels=[],
        description="Test version",
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


@pytest.mark.unit
class TestGetAllVersionsOwnership:
    """GET /versions must only expose the caller's own versions."""

    @pytest.mark.asyncio
    async def test_returns_only_versions_of_own_solutions(self):
        version_repository = AsyncMock()
        solution_repository = AsyncMock()

        solution_repository.get_all_for_user = AsyncMock(return_value=[make_solution(OWNER_ID)])
        version_repository.get_by_solution_ids = AsyncMock(return_value=[make_version()])

        result = await get_all_versions(version_repository, solution_repository, OWNER_ID)

        assert [v.id for v in result] == [VERSION_ID]
        solution_repository.get_all_for_user.assert_awaited_once_with(OWNER_ID)
        version_repository.get_by_solution_ids.assert_awaited_once_with([SOLUTION_ID])

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_user_has_no_solutions(self):
        version_repository = AsyncMock()
        solution_repository = AsyncMock()

        solution_repository.get_all_for_user = AsyncMock(return_value=[])
        version_repository.get_by_solution_ids = AsyncMock(return_value=[])

        result = await get_all_versions(version_repository, solution_repository, OWNER_ID)

        assert result == []
        version_repository.get_by_solution_ids.assert_not_awaited()


@pytest.mark.unit
class TestVersionUseCaseOwnership:
    """Single-version use cases must refuse non-owners."""

    @pytest.mark.asyncio
    async def test_get_version_by_id_raises_forbidden_for_non_owner(self):
        version_repository = AsyncMock()
        solution_repository = AsyncMock()

        version_repository.get_by_id = AsyncMock(return_value=make_version())
        solution_repository.get_by_id = AsyncMock(return_value=make_solution(OTHER_USER_ID))

        with pytest.raises(Forbidden):
            await get_version_by_id(
                version_repository, solution_repository, VERSION_ID, OWNER_ID
            )

    @pytest.mark.asyncio
    async def test_get_version_by_id_returns_version_for_owner(self):
        version_repository = AsyncMock()
        solution_repository = AsyncMock()

        version_repository.get_by_id = AsyncMock(return_value=make_version())
        solution_repository.get_by_id = AsyncMock(return_value=make_solution(OWNER_ID))

        result = await get_version_by_id(
            version_repository, solution_repository, VERSION_ID, OWNER_ID
        )

        assert result.id == VERSION_ID

    @pytest.mark.asyncio
    async def test_update_version_raises_forbidden_for_non_owner(self):
        version_repository = AsyncMock()
        solution_repository = AsyncMock()

        version_repository.get_by_id = AsyncMock(return_value=make_version())
        solution_repository.get_by_id = AsyncMock(return_value=make_solution(OTHER_USER_ID))

        with pytest.raises(Forbidden):
            await update_version(
                version_repository,
                solution_repository,
                VERSION_ID,
                VersionPartialUpdateRequest(description="Updated version"),
                OWNER_ID,
            )

        version_repository.update.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_update_version_updates_for_owner(self):
        version_repository = AsyncMock()
        solution_repository = AsyncMock()

        version_repository.get_by_id = AsyncMock(return_value=make_version())
        version_repository.update = AsyncMock(return_value=make_version())
        solution_repository.get_by_id = AsyncMock(return_value=make_solution(OWNER_ID))

        result = await update_version(
            version_repository,
            solution_repository,
            VERSION_ID,
            VersionPartialUpdateRequest(description="Updated version"),
            OWNER_ID,
        )

        assert result.id == VERSION_ID
        version_repository.update.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_version_cannot_be_reparented_to_foreign_solution(self):
        """Moving a version to another user's solution must be rejected."""
        version_repository = AsyncMock()
        solution_repository = AsyncMock()

        version_repository.get_by_id = AsyncMock(return_value=make_version())
        solution_repository.get_by_id = AsyncMock(
            side_effect=[
                make_solution(OWNER_ID),
                make_solution(OTHER_USER_ID, OTHER_SOLUTION_ID),
            ]
        )

        with pytest.raises(Forbidden):
            await update_version(
                version_repository,
                solution_repository,
                VERSION_ID,
                VersionPartialUpdateRequest(solution_id=OTHER_SOLUTION_ID),
                OWNER_ID,
            )

        version_repository.update.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_delete_version_raises_forbidden_for_non_owner(self):
        version_repository = AsyncMock()
        solution_repository = AsyncMock()

        version_repository.get_by_id = AsyncMock(return_value=make_version())
        solution_repository.get_by_id = AsyncMock(return_value=make_solution(OTHER_USER_ID))

        with pytest.raises(Forbidden):
            await delete_version(
                version_repository, solution_repository, VERSION_ID, OWNER_ID
            )

        version_repository.delete.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_delete_version_deletes_for_owner(self):
        version_repository = AsyncMock()
        solution_repository = AsyncMock()

        version_repository.get_by_id = AsyncMock(return_value=make_version())
        version_repository.delete = AsyncMock()
        solution_repository.get_by_id = AsyncMock(return_value=make_solution(OWNER_ID))

        await delete_version(
            version_repository, solution_repository, VERSION_ID, OWNER_ID
        )

        version_repository.delete.assert_awaited_once_with(VERSION_ID)


@pytest.mark.unit
class TestVersionSolutionScopeOwnership:
    """Solution-scoped version operations must refuse non-owners."""

    @pytest.mark.asyncio
    async def test_create_version_raises_forbidden_for_non_owner(self):
        version_repository = AsyncMock()
        solution_repository = AsyncMock()

        solution_repository.get_by_id = AsyncMock(return_value=make_solution(OTHER_USER_ID))

        with pytest.raises(Forbidden):
            await create_version(
                version_repository,
                solution_repository,
                VersionCreateRequest(
                    submodels=[],
                    description="Test version",
                    solution_id=SOLUTION_ID,
                ),
                OWNER_ID,
            )

        version_repository.add.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_create_version_creates_for_owner(self):
        version_repository = AsyncMock()
        solution_repository = AsyncMock()

        solution_repository.get_by_id = AsyncMock(return_value=make_solution(OWNER_ID))
        version_repository.add = AsyncMock(return_value=make_version())

        result = await create_version(
            version_repository,
            solution_repository,
            VersionCreateRequest(
                submodels=[],
                description="Test version",
                solution_id=SOLUTION_ID,
            ),
            OWNER_ID,
        )

        assert result.id == VERSION_ID
        version_repository.add.assert_awaited_once()


@pytest.mark.unit
class TestForbiddenErrorMapping:
    """The shared error translator must map Forbidden to HTTP 403."""

    @pytest.mark.asyncio
    async def test_handle_common_errors_maps_forbidden_to_403(self):
        from fastapi import HTTPException

        from api.handle_errors import handle_common_errors

        with pytest.raises(HTTPException) as exc_info:
            await handle_common_errors(Forbidden(msg='Not authorized'), None)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == 'Not authorized'


@pytest.mark.integration
class TestVersionEndpointOwnership:
    """HTTP surface: non-owners get 403, owners get 200/201/204."""

    @pytest.mark.asyncio
    async def test_get_version_returns_403_for_non_owner(self, authenticated_client, mock_user):
        with patch('api.controllers.version.VersionRepositoryImpl.get_by_id', new_callable=AsyncMock) as mock_get_version, \
             patch('api.controllers.version.SolutionRepositoryImpl.get_by_id', new_callable=AsyncMock) as mock_get_solution:
            mock_get_version.return_value = make_version()
            mock_get_solution.return_value = make_solution(OTHER_USER_ID)

            response = await authenticated_client.get(f"/versions/{VERSION_ID}")

            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_version_returns_200_for_owner(self, authenticated_client, mock_user):
        with patch('api.controllers.version.VersionRepositoryImpl.get_by_id', new_callable=AsyncMock) as mock_get_version, \
             patch('api.controllers.version.SolutionRepositoryImpl.get_by_id', new_callable=AsyncMock) as mock_get_solution:
            mock_get_version.return_value = make_version()
            mock_get_solution.return_value = make_solution(str(mock_user.id))

            response = await authenticated_client.get(f"/versions/{VERSION_ID}")

            assert response.status_code == 200
            assert response.json()["_id"] == VERSION_ID

    @pytest.mark.asyncio
    async def test_get_all_versions_returns_only_own_versions(self, authenticated_client, mock_user):
        with patch('api.controllers.version.SolutionRepositoryImpl.get_all_for_user', new_callable=AsyncMock) as mock_solutions, \
             patch('api.controllers.version.VersionRepositoryImpl.get_by_solution_ids', new_callable=AsyncMock) as mock_versions:
            mock_solutions.return_value = [make_solution(str(mock_user.id))]
            mock_versions.return_value = [make_version()]

            response = await authenticated_client.get("/versions")

            assert response.status_code == 200
            assert [v["_id"] for v in response.json()] == [VERSION_ID]
            mock_solutions.assert_awaited_once_with(str(mock_user.id))
            mock_versions.assert_awaited_once_with([SOLUTION_ID])

    @pytest.mark.asyncio
    async def test_delete_version_returns_403_for_non_owner(self, authenticated_client, mock_user):
        with patch('api.controllers.version.VersionRepositoryImpl.get_by_id', new_callable=AsyncMock) as mock_get_version, \
             patch('api.controllers.version.SolutionRepositoryImpl.get_by_id', new_callable=AsyncMock) as mock_get_solution:
            mock_get_version.return_value = make_version()
            mock_get_solution.return_value = make_solution(OTHER_USER_ID)

            response = await authenticated_client.delete(f"/versions/{VERSION_ID}")

            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_version_returns_204_for_owner(self, authenticated_client, mock_user):
        with patch('api.controllers.version.VersionRepositoryImpl.get_by_id', new_callable=AsyncMock) as mock_get_version, \
             patch('api.controllers.version.SolutionRepositoryImpl.get_by_id', new_callable=AsyncMock) as mock_get_solution, \
             patch('api.controllers.version.VersionRepositoryImpl.delete', new_callable=AsyncMock) as mock_delete:
            mock_get_version.return_value = make_version()
            mock_get_solution.return_value = make_solution(str(mock_user.id))

            response = await authenticated_client.delete(f"/versions/{VERSION_ID}")

            assert response.status_code == 204
            mock_delete.assert_awaited_once_with(VERSION_ID)

    @pytest.mark.asyncio
    async def test_create_version_returns_403_for_non_owner_solution(self, authenticated_client, mock_user):
        with patch('api.controllers.version.SolutionRepositoryImpl.get_by_id', new_callable=AsyncMock) as mock_get_solution:
            mock_get_solution.return_value = make_solution(OTHER_USER_ID)

            response = await authenticated_client.post(
                "/versions",
                json={
                    "submodels": [],
                    "description": "Test version",
                    "solution_id": SOLUTION_ID,
                },
            )

            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_version_returns_201_for_owner(self, authenticated_client, mock_user):
        with patch('api.controllers.version.SolutionRepositoryImpl.get_by_id', new_callable=AsyncMock) as mock_get_solution, \
             patch('api.controllers.version.VersionRepositoryImpl.add', new_callable=AsyncMock) as mock_add:
            mock_get_solution.return_value = make_solution(str(mock_user.id))
            mock_add.return_value = make_version()

            response = await authenticated_client.post(
                "/versions",
                json={
                    "submodels": [],
                    "description": "Test version",
                    "solution_id": SOLUTION_ID,
                },
            )

            assert response.status_code == 201
            assert response.json()["_id"] == VERSION_ID

    @pytest.mark.asyncio
    async def test_update_version_returns_403_for_non_owner(self, authenticated_client, mock_user):
        with patch('api.controllers.version.VersionRepositoryImpl.get_by_id', new_callable=AsyncMock) as mock_get_version, \
             patch('api.controllers.version.SolutionRepositoryImpl.get_by_id', new_callable=AsyncMock) as mock_get_solution:
            mock_get_version.return_value = make_version()
            mock_get_solution.return_value = make_solution(OTHER_USER_ID)

            response = await authenticated_client.patch(
                f"/versions/{VERSION_ID}",
                json={"description": "Updated version"},
            )

            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_version_returns_200_for_owner(self, authenticated_client, mock_user):
        with patch('api.controllers.version.VersionRepositoryImpl.get_by_id', new_callable=AsyncMock) as mock_get_version, \
             patch('api.controllers.version.SolutionRepositoryImpl.get_by_id', new_callable=AsyncMock) as mock_get_solution, \
             patch('api.controllers.version.VersionRepositoryImpl.update', new_callable=AsyncMock) as mock_update:
            mock_get_version.return_value = make_version()
            mock_get_solution.return_value = make_solution(str(mock_user.id))
            mock_update.return_value = make_version()

            response = await authenticated_client.patch(
                f"/versions/{VERSION_ID}",
                json={"description": "Updated version"},
            )

            assert response.status_code == 200
            assert response.json()["_id"] == VERSION_ID
