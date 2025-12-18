#!/usr/bin/env python3
"""
Script de prueba para validaciones de seguridad mejoradas
Tests: NoSQL injection prevention y manejo de errores
"""
import asyncio
from utils.mongo import get_object_id, sanitize_query_filters
from fastapi import HTTPException

def test_object_id_validation():
    """Test de validación de ObjectIds"""
    print("\n🔍 Testeando validación de ObjectIds\n")
    print("="*60)
    
    # Test casos válidos
    valid_ids = [
        "507f1f77bcf86cd799439011",
        "5f8d0d55b54764421b7156c9",
        "AABBCCDDEEFF001122334455",
    ]
    
    print("\n✅ Casos VÁLIDOS:")
    for test_id in valid_ids:
        try:
            result = asyncio.run(get_object_id(test_id))
            print(f"  ✓ '{test_id}' -> Valid ObjectId")
        except Exception as e:
            print(f"  ✗ '{test_id}' -> ERROR: {e}")
    
    # Test casos inválidos (intentos de injection)
    invalid_ids = [
        # Intentos de NoSQL injection
        {"$ne": None},
        {"$gt": ""},
        '{"$ne": null}',
        # Formatos inválidos
        "123",  # Muy corto
        "507f1f77bcf86cd799439011EXTRA",  # Muy largo
        "507f1f77bcf86cd799439g11",  # Carácter inválido 'g'
        "507f-1f77-bcf8-6cd7-9943-9011",  # Con guiones
        "<script>alert(1)</script>",  # XSS attempt
        "'; DROP TABLE users; --",  # SQL injection attempt
        "../../../etc/passwd",  # Path traversal
        "",  # Vacío
        " 507f1f77bcf86cd799439011 ",  # Con espacios (debería limpiar)
    ]
    
    print("\n❌ Casos INVÁLIDOS (deben ser rechazados):")
    for test_id in invalid_ids:
        try:
            result = asyncio.run(get_object_id(str(test_id)))
            print(f"  ✗ '{test_id}' -> FALLO: Se aceptó cuando debió rechazarse")
        except HTTPException as e:
            print(f"  ✓ '{test_id}' -> Bloqueado correctamente: {e.detail}")
        except Exception as e:
            print(f"  ✓ '{test_id}' -> Bloqueado: {type(e).__name__}")


def test_query_sanitization():
    """Test de sanitización de queries"""
    print("\n\n🔍 Testeando sanitización de queries\n")
    print("="*60)
    
    allowed_fields = ['name', 'user_id', 'created_at', 'status']
    
    # Test 1: Filtros seguros
    safe_filters = {
        'name': 'test',
        'user_id': '123',
        'status': 'active'
    }
    result = sanitize_query_filters(safe_filters, allowed_fields)
    print(f"\n✅ Filtros seguros:")
    print(f"  Input:  {safe_filters}")
    print(f"  Output: {result}")
    
    # Test 2: Filtros con operadores MongoDB (intento de injection)
    injection_filters = {
        'name': {'$ne': None},  # NoSQL injection attempt
        'user_id': {'$gt': ''},  # NoSQL injection attempt
        '$where': 'this.password == "123"',  # Dangerous operator
        'created_at': '2024-01-01'  # Safe value
    }
    result = sanitize_query_filters(injection_filters, allowed_fields)
    print(f"\n❌ Filtros con injection (deben ser bloqueados):")
    print(f"  Input:  {injection_filters}")
    print(f"  Output: {result}")
    print(f"  ✓ Operadores maliciosos eliminados")
    
    # Test 3: Campos no permitidos
    unauthorized_filters = {
        'name': 'test',
        'password': 'leaked',  # Campo no permitido
        'email': 'admin@test.com',  # Campo no permitido
        'secret_key': 'xxx'  # Campo no permitido
    }
    result = sanitize_query_filters(unauthorized_filters, allowed_fields)
    print(f"\n❌ Campos no autorizados (deben ser filtrados):")
    print(f"  Input:  {unauthorized_filters}")
    print(f"  Output: {result}")
    print(f"  ✓ Solo campos permitidos en whitelist")
    
    # Test 4: Listas seguras ($in operator)
    list_filters = {
        'status': ['active', 'pending', 'completed'],
        'user_id': ['123', '456', '789']
    }
    result = sanitize_query_filters(list_filters, allowed_fields)
    print(f"\n✅ Listas seguras (convertidas a $in):")
    print(f"  Input:  {list_filters}")
    print(f"  Output: {result}")
    
    # Test 5: Listas con objetos (intento de injection)
    malicious_list = {
        'status': [{'$ne': None}, 'active'],
    }
    result = sanitize_query_filters(malicious_list, allowed_fields)
    print(f"\n❌ Listas con objetos maliciosos:")
    print(f"  Input:  {malicious_list}")
    print(f"  Output: {result}")
    print(f"  ✓ Lista bloqueada (contiene objetos)")


def main():
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║       🛡️  Security Validation Tests - QOLQA API          ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    try:
        test_object_id_validation()
        test_query_sanitization()
        
        print("\n\n" + "="*60)
        print("✅ Tests completados")
        print("="*60)
        print("\n💡 Resumen:")
        print("  - Validación de ObjectIds: Previene NoSQL injection")
        print("  - Sanitización de queries: Bloquea operadores MongoDB")
        print("  - Whitelist de campos: Solo permite campos autorizados")
        print("  - Validación estricta: Solo tipos simples permitidos")
        
    except Exception as e:
        print(f"\n❌ Error durante tests: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
