"""
Validation tests for Version model
Tests Pydantic model validation for versions, submodels, nodes, and edges
"""
import pytest
from pydantic import ValidationError
from models.version import (
    Version, VersionCreate, VersionPartialUpdate,
    Submodel, Node, Edge, Column, NestedNode, Position
)


@pytest.mark.validation
@pytest.mark.unit
class TestVersionValidation:
    """Test suite for Version model validation"""
    
    def test_create_valid_version(self, mock_version_data):
        """Test creating a valid version"""
        version = VersionCreate(**mock_version_data)
        
        assert version.description == "Test version"
        assert version.solution_id == "test_solution_id"
        assert len(version.submodels) == 1
    
    def test_version_missing_required_fields(self):
        """Test that version creation fails without required fields"""
        with pytest.raises(ValidationError) as exc_info:
            VersionCreate(
                submodels=[],
                description="Test"
                # Missing solution_id
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('solution_id',) for error in errors)
    
    def test_version_with_empty_description(self):
        """Test version with empty description"""
        version = VersionCreate(
            submodels=[],
            description="",
            solution_id="123"
        )
        
        assert version.description == ""
    
    def test_version_with_multiple_submodels(self):
        """Test version with multiple submodels"""
        data = {
            "submodels": [
                {
                    "nodes": [],
                    "edges": []
                },
                {
                    "nodes": [],
                    "edges": []
                }
            ],
            "description": "Multiple submodels",
            "solution_id": "123"
        }
        version = VersionCreate(**data)
        
        assert len(version.submodels) == 2
    
    def test_partial_update_all_fields_optional(self):
        """Test that all fields in partial update are optional"""
        update = VersionPartialUpdate()
        
        assert update.submodels is None
        assert update.description is None
        assert update.solution_id is None
    
    def test_partial_update_with_description_only(self):
        """Test partial update with only description"""
        update = VersionPartialUpdate(description="Updated description")
        
        assert update.description == "Updated description"
        assert update.submodels is None


@pytest.mark.validation
@pytest.mark.unit
class TestSubmodelValidation:
    """Test suite for Submodel validation"""
    
    def test_create_valid_submodel(self):
        """Test creating a valid submodel"""
        submodel = Submodel(
            nodes=[],
            edges=[]
        )
        
        assert submodel.nodes == []
        assert submodel.edges == []
    
    def test_submodel_missing_nodes(self):
        """Test that submodel requires nodes field"""
        with pytest.raises(ValidationError) as exc_info:
            Submodel(edges=[])
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('nodes',) for error in errors)
    
    def test_submodel_missing_edges(self):
        """Test that submodel requires edges field"""
        with pytest.raises(ValidationError) as exc_info:
            Submodel(nodes=[])
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('edges',) for error in errors)


@pytest.mark.validation
@pytest.mark.unit
class TestNodeValidation:
    """Test suite for Node validation"""
    
    def test_create_valid_node(self):
        """Test creating a valid node"""
        node = Node(
            id="node1",
            name="User",
            type="entity",
            position={"x": 100, "y": 200},
            cols=[
                {"id": "col1", "name": "id", "type": "int"}
            ],
            nested_nodes=None
        )
        
        assert node.id == "node1"
        assert node.name == "User"
        assert node.type == "entity"
        assert node.position.x == 100
        assert node.position.y == 200
        assert len(node.cols) == 1
    
    def test_node_missing_required_fields(self):
        """Test that node requires all mandatory fields"""
        with pytest.raises(ValidationError):
            Node(
                id="node1",
                name="User"
                # Missing type, position, cols
            )
    
    def test_node_with_nested_nodes(self):
        """Test node with nested nodes"""
        node = Node(
            id="node1",
            name="User",
            type="entity",
            position={"x": 100, "y": 200},
            cols=[],
            nested_nodes=[
                {
                    "id": "nested1",
                    "name": "Address",
                    "cols": [],
                    "nested_nodes": None
                }
            ]
        )
        
        assert len(node.nested_nodes) == 1
        assert node.nested_nodes[0].id == "nested1"
    
    def test_node_with_multiple_columns(self):
        """Test node with multiple columns"""
        node = Node(
            id="node1",
            name="User",
            type="entity",
            position={"x": 0, "y": 0},
            cols=[
                {"id": "col1", "name": "id", "type": "int"},
                {"id": "col2", "name": "name", "type": "string"},
                {"id": "col3", "name": "email", "type": "string"}
            ]
        )
        
        assert len(node.cols) == 3


@pytest.mark.validation
@pytest.mark.unit
class TestPositionValidation:
    """Test suite for Position validation"""
    
    def test_create_valid_position(self):
        """Test creating a valid position"""
        position = Position(x=100.5, y=200.75)
        
        assert position.x == 100.5
        assert position.y == 200.75
    
    def test_position_with_integers(self):
        """Test position with integer values"""
        position = Position(x=100, y=200)
        
        assert position.x == 100
        assert position.y == 200
    
    def test_position_missing_x(self):
        """Test that position requires x coordinate"""
        with pytest.raises(ValidationError) as exc_info:
            Position(y=100)
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('x',) for error in errors)
    
    def test_position_missing_y(self):
        """Test that position requires y coordinate"""
        with pytest.raises(ValidationError) as exc_info:
            Position(x=100)
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('y',) for error in errors)
    
    def test_position_negative_values(self):
        """Test position with negative values"""
        position = Position(x=-100, y=-200)
        
        assert position.x == -100
        assert position.y == -200


@pytest.mark.validation
@pytest.mark.unit
class TestColumnValidation:
    """Test suite for Column validation"""
    
    def test_create_valid_column(self):
        """Test creating a valid column"""
        column = Column(
            id="col1",
            name="user_id",
            type="integer"
        )
        
        assert column.id == "col1"
        assert column.name == "user_id"
        assert column.type == "integer"
    
    def test_column_missing_required_fields(self):
        """Test that column requires all fields"""
        with pytest.raises(ValidationError):
            Column(id="col1")


@pytest.mark.validation
@pytest.mark.unit
class TestEdgeValidation:
    """Test suite for Edge validation"""
    
    def test_create_valid_edge(self):
        """Test creating a valid edge"""
        edge = Edge(
            id="edge1",
            source="node1",
            target="node2"
        )
        
        assert edge.id == "edge1"
        assert edge.source == "node1"
        assert edge.target == "node2"
    
    def test_edge_missing_source(self):
        """Test that edge requires source"""
        with pytest.raises(ValidationError) as exc_info:
            Edge(
                id="edge1",
                target="node2"
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('source',) for error in errors)
    
    def test_edge_missing_target(self):
        """Test that edge requires target"""
        with pytest.raises(ValidationError) as exc_info:
            Edge(
                id="edge1",
                source="node1"
            )
        
        errors = exc_info.value.errors()
        assert any(error['loc'] == ('target',) for error in errors)


@pytest.mark.validation
@pytest.mark.unit
class TestNestedNodeValidation:
    """Test suite for NestedNode validation"""
    
    def test_create_valid_nested_node(self):
        """Test creating a valid nested node"""
        nested = NestedNode(
            id="nested1",
            name="Address",
            cols=[
                {"id": "col1", "name": "street", "type": "string"}
            ],
            nested_nodes=None
        )
        
        assert nested.id == "nested1"
        assert nested.name == "Address"
        assert len(nested.cols) == 1
    
    def test_nested_node_with_children(self):
        """Test nested node with child nested nodes"""
        nested = NestedNode(
            id="nested1",
            name="Address",
            cols=[],
            nested_nodes=[
                {
                    "id": "nested2",
                    "name": "Location",
                    "cols": [],
                    "nested_nodes": None
                }
            ]
        )
        
        assert len(nested.nested_nodes) == 1
        assert nested.nested_nodes[0].id == "nested2"
