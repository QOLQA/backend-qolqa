"""
Validation tests for Solution model
Tests Pydantic model validation, field requirements, and data types
"""
import pytest
from pydantic import ValidationError
from application.dtos.solution.SolutionRequest import SolutionCreateRequest as SolutionCreate, SolutionPartialUpdateRequest as SolutionPartialUpdate


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
    
    def test_solution_missing_required_field(self):
        """Test that solution creation fails without required name field"""
        with pytest.raises(ValidationError) as exc_info:
            SolutionCreate(
                last_version_saved="unknown",
                src_img="http://test.com/image.png"
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('name',) for error in errors)
        # Pydantic v2 usa 'required' en lugar de 'missing'
        assert any('missing' in error['msg'].lower() or 'required' in error['msg'].lower() for error in errors)
    
    def test_solution_with_empty_name(self):
        """Test that solution creation fails with empty name"""
        with pytest.raises(ValidationError):
            SolutionCreate(
                name=""
            )
    
    def test_solution_default_values(self):
        """Test default values for optional fields"""
        solution = SolutionCreate(name="Test")
        
        assert solution.last_version_saved == "unknown"
        assert solution.src_img == "http://unknown.es"
    
    @pytest.mark.skip(reason="user_id removed from SolutionCreate — injected by endpoint from current_user")
    def test_solution_with_user_id(self):
        """Test solution with user_id"""
        data = {
            "name": "User Solution",
            "user_id": "user123"
        }
        solution = SolutionCreate(**data)
        
        assert solution.name == "User Solution"
        assert solution.user_id == "user123"
    
    def test_partial_update_all_fields_optional(self):
        """Test that all fields in partial update are optional"""
        update = SolutionPartialUpdate()
        
        assert update.name is None
        assert update.last_version_saved is None
        assert update.src_img is None
    
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
class TestSolutionFieldTypes:
    """Test suite for Solution field type validation"""
    
    def test_name_must_be_string(self):
        """Test that name must be a string"""
        with pytest.raises(ValidationError):
            SolutionCreate(
                name=123  # Should be string
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
