"""
Integration tests for Solutions endpoints
Tests API endpoints for CRUD operations on solutions
"""
import pytest
from fastapi import status
from unittest.mock import AsyncMock, patch


@pytest.mark.integration
class TestSolutionsEndpoints:
    """Test suite for Solutions API endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_all_solutions_empty(self, async_client, mock_user, auth_headers):
        """Test getting all solutions when database is empty"""
        from domain.entities.auth.UserEntity import UserEntity

        mock_entity = UserEntity(
            id=str(mock_user.id),
            username=mock_user.username,
            email=mock_user.email,
            is_active=mock_user.is_active,
            created_at=mock_user.created_at,
        )

        with patch('api.controllers.auth.get_user_by_id', new_callable=AsyncMock) as mock_get_user, \
             patch('api.controllers.solution.get_all_solutions_for_user', new_callable=AsyncMock) as mock_get_all:
            
            mock_get_user.return_value = mock_entity
            mock_get_all.return_value = []
            
            response = await async_client.get("/solutions", headers=auth_headers)
            
            assert response.status_code == status.HTTP_200_OK
            assert response.json() == []
    
    @pytest.mark.asyncio
    async def test_get_all_solutions_with_data(self, authenticated_client, mock_user, mock_solution_data, auth_headers):
        """Test getting all solutions with data"""
        from domain.entities.SolutionEntity import SolutionEntity
        from bson import ObjectId
        
        # Create modified solution data for second solution
        solution_data_2 = {**mock_solution_data, "name": "Second Solution"}
        
        mock_solutions = [
            SolutionEntity(id=str(ObjectId()), user_id=str(mock_user.id), name=mock_solution_data["name"], versions=[]),
            SolutionEntity(id=str(ObjectId()), user_id=str(mock_user.id), name=solution_data_2["name"], versions=[])
        ]
        
        with patch('api.controllers.solution.get_all_solutions_for_user', new_callable=AsyncMock) as mock_get_all:
            mock_get_all.return_value = mock_solutions
            
            response = await authenticated_client.get("/solutions", headers=auth_headers)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 2
    
    @pytest.mark.asyncio
    async def test_create_solution_success(self, authenticated_client, mock_user, mock_solution_data, auth_headers):
        """Test successful solution creation"""
        from domain.entities.SolutionEntity import SolutionEntity
        from domain.entities.VersionEntity import VersionEntity
        from bson import ObjectId
        
        solution_id = str(ObjectId())
        version_id = str(ObjectId())
        expected_solution = SolutionEntity(
            id=solution_id,
            name=mock_solution_data["name"],
            user_id=str(mock_user.id),
            versions=[]
        )
        
        mock_version = VersionEntity(
            id=version_id,
            description="Initial version",
            solution_id=solution_id,
            submodels=[]
        )
        
        with patch('api.controllers.solution.create_solution', new_callable=AsyncMock) as mock_create, \
             patch('api.controllers.solution.create_version', new_callable=AsyncMock) as mock_create_version, \
             patch('api.controllers.solution.SolutionRepositoryImpl.update', new_callable=AsyncMock) as mock_modify:
            
            mock_create.return_value = expected_solution
            mock_create_version.return_value = mock_version
            mock_modify.return_value = expected_solution
            
            response = await authenticated_client.post("/solutions", json=mock_solution_data, headers=auth_headers)
            
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["name"] == mock_solution_data["name"]
    
    @pytest.mark.asyncio
    async def test_create_solution_invalid_data(self, authenticated_client, auth_headers):
        """Test solution creation with invalid data"""
        invalid_data = {
            "last_version_saved": "unknown"
            # Missing required 'name' field
        }
        
        response = await authenticated_client.post("/solutions", json=invalid_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_create_solution_empty_name(self, authenticated_client, auth_headers):
        """Test solution creation with empty name"""
        invalid_data = {
            "name": "",
            "queries": []
        }
        
        response = await authenticated_client.post("/solutions", json=invalid_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_get_solution_by_id_success(self, authenticated_client, mock_user, mock_solution_data, auth_headers):
        """Test getting a solution by ID"""
        from domain.entities.SolutionEntity import SolutionEntity
        from bson import ObjectId
        
        solution_id = str(ObjectId())
        expected_solution = SolutionEntity(
            id=solution_id,
            name=mock_solution_data["name"],
            user_id=str(mock_user.id),
            versions=[]
        )
        
        with patch('api.controllers.solution.SolutionRepositoryImpl.get_by_id', new_callable=AsyncMock) as mock_get_one, \
             patch('api.controllers.solution.VersionRepositoryImpl.get_by_solution_id', new_callable=AsyncMock) as mock_get_versions:
            
            mock_get_one.return_value = expected_solution
            mock_get_versions.return_value = []
            
            response = await authenticated_client.get(f"/solutions/{solution_id}", headers=auth_headers)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["name"] == mock_solution_data["name"]
    
    @pytest.mark.asyncio
    async def test_get_solution_not_found(self, authenticated_client, auth_headers):
        """Test getting a non-existent solution"""
        from domain.errors import NotFoundError
        
        with patch('api.controllers.solution.SolutionRepositoryImpl.get_by_id', new_callable=AsyncMock) as mock_get_one:
            mock_get_one.side_effect = NotFoundError("Solution not found")
            
            response = await authenticated_client.get("/solutions/nonexistent", headers=auth_headers)
            
            # The error handling should catch this
            assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_500_INTERNAL_SERVER_ERROR]
    
    @pytest.mark.asyncio
    async def test_update_solution_success(self, authenticated_client, mock_user, mock_partial_update_data, auth_headers):
        """Test successful solution update"""
        from domain.entities.SolutionEntity import SolutionEntity
        from bson import ObjectId
        
        solution_id = str(ObjectId())
        updated_solution = SolutionEntity(
            id=solution_id,
            name=mock_partial_update_data["name"],
            user_id=str(mock_user.id),
            versions=[]
        )
        
        with patch('api.controllers.solution.update_solution', new_callable=AsyncMock) as mock_modify:
            
            mock_modify.return_value = updated_solution
            
            response = await authenticated_client.patch(
                f"/solutions/{solution_id}",
                json=mock_partial_update_data,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["name"] == mock_partial_update_data["name"]
    
    @pytest.mark.asyncio
    async def test_update_solution_partial_fields(self, authenticated_client, mock_user, auth_headers):
        """Test updating only specific fields"""
        from domain.entities.SolutionEntity import SolutionEntity
        from bson import ObjectId
        
        solution_id = str(ObjectId())
        update_data = {"last_version_saved": "version_456"}
        
        updated_solution = SolutionEntity(
            id=solution_id,
            name="Original Name",
            last_version_saved="version_456",
            user_id=str(mock_user.id),
            versions=[]
        )
        
        with patch('api.controllers.solution.update_solution', new_callable=AsyncMock) as mock_modify:
            
            mock_modify.return_value = updated_solution
            
            response = await authenticated_client.patch(
                f"/solutions/{solution_id}",
                json=update_data,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["last_version_saved"] == "version_456"
    
    @pytest.mark.asyncio
    async def test_update_solution_invalid_id(self, authenticated_client, auth_headers):
        """Test updating a solution with invalid ID"""
        from domain.errors import NotFoundError
        
        with patch('api.controllers.solution.update_solution', new_callable=AsyncMock) as mock_get_one:
            mock_get_one.side_effect = NotFoundError("Solution not found")
            
            response = await authenticated_client.patch(
                "/solutions/invalid_id",
                json={"name": "Updated Name"},
                headers=auth_headers
            )
            
            assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_500_INTERNAL_SERVER_ERROR]


@pytest.mark.integration
class TestVersionEndpoints:
    """Test suite for Version endpoints"""
    
    @pytest.mark.asyncio
    async def test_update_solution_version_success(self, authenticated_client, mock_user, auth_headers):
        """Test successful version update"""
        from domain.entities.SolutionEntity import SolutionEntity
        from domain.entities.VersionEntity import VersionEntity
        from bson import ObjectId
        
        solution_id = str(ObjectId())
        version_id = str(ObjectId())
        version_update = {
            "description": "Updated version description"
        }
        
        mock_solution = SolutionEntity(
            id=solution_id,
            name="Test Solution",
            user_id=str(mock_user.id),
            versions=[]
        )
        
        mock_version = VersionEntity(
            id=version_id,
            description="Updated version description",
            solution_id=solution_id,
            submodels=[]
        )
        
        with patch('api.controllers.solution.SolutionRepositoryImpl.get_by_id', new_callable=AsyncMock) as mock_get_one, \
             patch('api.controllers.solution.SolutionRepositoryImpl.update', new_callable=AsyncMock) as mock_modify_solution, \
             patch('api.controllers.solution.update_version', new_callable=AsyncMock) as mock_modify_version:
            
            mock_get_one.return_value = mock_solution
            mock_modify_solution.return_value = mock_solution
            mock_modify_version.return_value = mock_version
            
            response = await authenticated_client.patch(
                f"/solutions/{solution_id}/versions/{version_id}",
                json=version_update,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["description"] == version_update["description"]
    
    @pytest.mark.asyncio
    async def test_update_version_nonexistent_solution(self, authenticated_client, auth_headers):
        """Test updating version for non-existent solution"""
        from domain.errors import NotFoundError
        
        with patch('api.controllers.solution.SolutionRepositoryImpl.get_by_id', new_callable=AsyncMock) as mock_get_one:
            mock_get_one.side_effect = NotFoundError("Solution not found")
            
            response = await authenticated_client.patch(
                "/solutions/invalid/versions/123",
                json={"description": "Update"},
                headers=auth_headers
            )
            
            assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_500_INTERNAL_SERVER_ERROR]


@pytest.mark.integration
class TestSolutionValidationEndpoints:
    """Test suite for validation at endpoint level"""
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requiere MongoDB activo - falla con 500 en lugar de 422 cuando DB no disponible")
    async def test_create_solution_with_invalid_query_structure(self, authenticated_client, auth_headers):
        """Test creating solution with malformed query"""
        invalid_data = {
            "name": "Test Solution",
            "queries": [
                {
                    "id": "q1",
                    # Missing full_query field
                    "collections": ["users"]
                }
            ]
        }
        
        response = await authenticated_client.post("/solutions", json=invalid_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_create_solution_with_wrong_type_queries(self, authenticated_client, auth_headers):
        """Test creating solution with wrong type for queries"""
        invalid_data = {
            "name": "Test Solution",
            "queries": "not a list"  # Should be a list
        }
        
        response = await authenticated_client.post("/solutions", json=invalid_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_update_solution_with_invalid_data_types(self, authenticated_client, auth_headers):
        """Test updating solution with invalid data types"""
        invalid_update = {
            "name": 123,  # Should be string
            "last_version_saved": ["not", "a", "string"]
        }
        
        response = await authenticated_client.patch(
            "/solutions/123",
            json=invalid_update,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_version_update_with_invalid_submodel(self, authenticated_client, auth_headers):
        """Test version update with invalid submodel structure"""
        invalid_update = {
            "submodels": [
                {
                    "nodes": "not a list",  # Should be a list
                    "edges": []
                }
            ]
        }
        
        response = await authenticated_client.patch(
            "/solutions/123/versions/456",
            json=invalid_update,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.integration
class TestEndpointErrorHandling:
    """Test suite for error handling in endpoints"""
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self, authenticated_client, mock_solution_data, auth_headers):
        """Test proper error handling for database errors"""
        with patch('api.controllers.solution.create_solution', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("Database connection error")
            
            response = await authenticated_client.post("/solutions", json=mock_solution_data, headers=auth_headers)
            
            # Should handle the error gracefully
            assert response.status_code in [status.HTTP_500_INTERNAL_SERVER_ERROR, status.HTTP_400_BAD_REQUEST]
    
    @pytest.mark.asyncio
    async def test_malformed_json_request(self, authenticated_client, auth_headers):
        """Test handling of malformed JSON in request"""
        headers = {**auth_headers, "Content-Type": "application/json"}
        response = await authenticated_client.post(
            "/solutions",
            content="not valid json",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
