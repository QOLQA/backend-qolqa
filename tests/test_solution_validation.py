"""
Validation tests for Solution model
Tests Pydantic model validation, field requirements, and data types
"""
import pytest
from pydantic import ValidationError
from models.solution import Solution, SolutionCreate, SolutionPartialUpdate
from models.query import Query


@pytest.mark.validation
@pytest.mark.unit
class TestSolutionValidation:
    """Test suite for Solution model validation"""
    
    def test_create_valid_solution(self, mock_solution_data):
        """Test creating a valid solution"""
        solution = SolutionCreate(**mock_solution_data)
        
        assert solution.name == "Test Solution"
        assert solution.last_version_saved == "unknown"
        assert solution.src_img == "http://test.com/image.png"
        assert len(solution.queries) == 1
    
    def test_solution_missing_required_field(self):
        """Test that solution creation fails without required name field"""
        with pytest.raises(ValidationError) as exc_info:
            SolutionCreate(
                last_version_saved="unknown",
                src_img="http://test.com/image.png",
                queries=[]
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('name',) for error in errors)
        # Pydantic v2 usa 'required' en lugar de 'missing'
        assert any('missing' in error['msg'].lower() or 'required' in error['msg'].lower() for error in errors)
    
    def test_solution_with_empty_name(self):
        """Test that solution creation fails with empty name"""
        with pytest.raises(ValidationError):
            SolutionCreate(
                name="",
                queries=[]
            )
    
    def test_solution_default_values(self):
        """Test default values for optional fields"""
        solution = SolutionCreate(name="Test")
        
        assert solution.last_version_saved == "unknown"
        assert solution.src_img == "http://unknown.es"
        assert solution.queries == []
    
    def test_solution_with_multiple_queries(self):
        """Test solution with multiple queries"""
        data = {
            "name": "Multi Query Solution",
            "queries": [
                {
                    "id": "q1",
                    "full_query": "SELECT * FROM users",
                    "collections": ["users"]
                },
                {
                    "id": "q2",
                    "full_query": "SELECT * FROM posts",
                    "collections": ["posts"]
                }
            ]
        }
        solution = SolutionCreate(**data)
        
        assert len(solution.queries) == 2
        assert solution.queries[0].id == "q1"
        assert solution.queries[1].id == "q2"
    
    def test_partial_update_all_fields_optional(self):
        """Test that all fields in partial update are optional"""
        update = SolutionPartialUpdate()
        
        assert update.name is None
        assert update.last_version_saved is None
        assert update.src_img is None
        assert update.queries is None
    
    def test_partial_update_with_single_field(self):
        """Test partial update with only one field"""
        update = SolutionPartialUpdate(name="New Name")
        
        assert update.name == "New Name"
        assert update.last_version_saved is None
    
    def test_partial_update_with_multiple_fields(self):
        """Test partial update with multiple fields"""
        update = SolutionPartialUpdate(
            name="Updated Name",
            last_version_saved="version_123",
            src_img="http://new-image.com/img.png"
        )
        
        assert update.name == "Updated Name"
        assert update.last_version_saved == "version_123"
        assert update.src_img == "http://new-image.com/img.png"


@pytest.mark.validation
@pytest.mark.unit
class TestQueryValidation:
    """Test suite for Query model validation"""
    
    def test_create_valid_query(self):
        """Test creating a valid query"""
        query = Query(
            id="query1",
            full_query="SELECT * FROM users",
            collections=["users"]
        )
        
        assert query.id == "query1"
        assert query.full_query == "SELECT * FROM users"
        assert query.collections == ["users"]
    
    def test_query_default_values(self):
        """Test default values for query fields"""
        query = Query()
        
        assert query.id == ''
        assert query.full_query == ''
        assert query.collections == []
    
    def test_query_with_multiple_collections(self):
        """Test query with multiple collections"""
        query = Query(
            id="q1",
            full_query="SELECT * FROM users JOIN posts",
            collections=["users", "posts"]
        )
        
        assert len(query.collections) == 2
        assert "users" in query.collections
        assert "posts" in query.collections
    
    def test_query_collections_type_validation(self):
        """Test that collections must be a list of strings"""
        with pytest.raises(ValidationError):
            Query(
                id="q1",
                full_query="SELECT * FROM users",
                collections="users"  # Should be a list, not a string
            )


@pytest.mark.validation
@pytest.mark.unit
class TestSolutionFieldTypes:
    """Test suite for Solution field type validation"""
    
    def test_name_must_be_string(self):
        """Test that name must be a string"""
        with pytest.raises(ValidationError):
            SolutionCreate(
                name=123,  # Should be string
                queries=[]
            )
    
    def test_queries_must_be_list(self):
        """Test that queries must be a list"""
        with pytest.raises(ValidationError):
            SolutionCreate(
                name="Test",
                queries="not a list"
            )
    
    def test_last_version_saved_must_be_string(self):
        """Test that last_version_saved must be a string"""
        with pytest.raises(ValidationError):
            SolutionCreate(
                name="Test",
                last_version_saved=123
            )
    
    def test_src_img_must_be_string(self):
        """Test that src_img must be a string"""
        with pytest.raises(ValidationError):
            SolutionCreate(
                name="Test",
                src_img=["http://image.com"]
            )
