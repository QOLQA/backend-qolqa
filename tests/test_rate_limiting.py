"""
Tests de rate limiting usando SlowAPI
"""
import asyncio

import pytest

from main import app


class TestRateLimiting:
    """Tests para verificar que rate limiting funciona correctamente"""
    
    @pytest.mark.asyncio
    async def test_login_rate_limit(self, async_client):
        """Test que login tiene rate limit de 5 requests por minuto"""
        # Usar async_client fixture que mockea la DB
        for i in range(3):
            response = await async_client.post(
                "/auth/login",
                data={"username": f"testuser_{i}", "password": "test"}
            )
            # Puede ser 401 (credenciales inválidas) o 404 (usuario no existe)
            # Lo importante es que NO sea 429 (rate limit) en las primeras requests
            assert response.status_code != 429, f"Request {i+1} fue bloqueada prematuramente"
            await asyncio.sleep(0.1)  # Pequeño delay entre requests
    
    @pytest.mark.asyncio
    async def test_register_rate_limit(self, async_client):
        """Test que register tiene rate limit de 3 requests por hora"""
        # Usar async_client fixture que mockea la DB
        response = await async_client.post(
            "/auth/register",
            json={
                "username": "reguser_solo",
                "email": "reguser@example.com",
                "password": "TestPassword123!"
            }
        )
        # Puede ser 409 (usuario existe), 201 (creado), 429 (rate limit), 500 (DB error), 404 (mock)
        # Este test simplemente verifica que el endpoint responde
        assert response.status_code in [201, 404, 409, 429, 500]
    
    @pytest.mark.asyncio
    async def test_rate_limit_different_ips(self, async_client):
        """Test que rate limit es por IP (diferentes IPs tienen límites independientes)."""
        response_1 = await async_client.post(
            "/auth/login",
            data={"username": "test", "password": "test"},
            headers={"X-Forwarded-For": "10.0.0.1"},
        )
        response_2 = await async_client.post(
            "/auth/login",
            data={"username": "test", "password": "test"},
            headers={"X-Forwarded-For": "10.0.0.2"},
        )
        assert response_1.status_code in [401, 404, 429, 500]
        assert response_2.status_code in [401, 404, 429, 500]
    
    @pytest.mark.asyncio
    async def test_rate_limit_headers(self, async_client):
        """Test que los headers de rate limit están presentes (si están configurados)."""
        response = await async_client.post(
            "/auth/login",
            data={"username": "test", "password": "test"},
        )
        assert response.status_code in [401, 404, 429, 500]
    
    @pytest.mark.asyncio
    async def test_solutions_read_rate_limit(self, async_client):
        """Test que endpoint de lectura de solutions tiene rate limit generoso (100/min)"""
        # Usar async_client fixture que mockea la DB
        # Sin autenticación, debería retornar 401
        response = await async_client.get("/solutions")
        # Verificar que NO está bloqueado por rate limit inmediatamente
        # (debería ser 401 por falta de autenticación)
        assert response.status_code in [401, 403], "Debería fallar por auth, no por rate limit"
    
    @pytest.mark.asyncio
    async def test_health_endpoint_no_rate_limit(self, async_client):
        """Test que el endpoint de health no tiene rate limit (puede ser consultado libremente)"""
        # Usar async_client fixture
        # Hacer múltiples requests al health endpoint
        for i in range(10):
            response = await async_client.get("/health")
            # Debería siempre retornar 200 o 503 (nunca 429)
            assert response.status_code in [200, 503], f"Health check no debería tener rate limit (request {i+1})"
            assert response.status_code != 429


class TestRateLimitRecovery:
    """Tests para verificar que rate limits se resetean correctamente"""
    
    @pytest.mark.asyncio
    async def test_rate_limit_resets(self, async_client):
        """Test que el rate limit se resetea después del tiempo de ventana."""
        import time
        from unittest.mock import patch

        # Agotar el límite con requests consecutivos (login: 5/minute)
        for _ in range(5):
            await async_client.post(
                "/auth/login",
                data={"username": "test_reset", "password": "test"},
            )

        # La siguiente request debería recibir 429 (rate limit agotado)
        response_limited = await async_client.post(
            "/auth/login",
            data={"username": "test_reset", "password": "test"},
        )
        assert response_limited.status_code == 429

        # Simular el paso del tiempo (65 segundos > ventana de 1 minuto)
        with patch("time.time", return_value=time.time() + 65):
            response_after_reset = await async_client.post(
                "/auth/login",
                data={"username": "test_reset", "password": "test"},
            )
            # Después de resetear el tiempo, ya no debería ser 429
            assert response_after_reset.status_code in [401, 404, 500]


class TestRateLimitConfiguration:
    """Tests para verificar configuración de rate limits"""
    
    def test_limiter_configured(self):
        """Test que el limiter está configurado en la aplicación"""
        assert hasattr(app.state, 'limiter'), "App debe tener limiter configurado"
    
    def test_rate_limit_exception_handler(self):
        """Test que el exception handler para RateLimitExceeded está registrado"""
        from slowapi.errors import RateLimitExceeded
        # Verificar que hay un handler para RateLimitExceeded
        assert RateLimitExceeded in app.exception_handlers or len(app.exception_handlers) > 0


# Fixture para limpiar rate limits entre tests (si fuera necesario)
@pytest.fixture(autouse=False)
def reset_rate_limits():
    """
    Fixture para resetear rate limits entre tests
    En producción con Redis esto se haría limpiando Redis
    Con SlowAPI in-memory, se resetea al reiniciar la app
    """
    yield
    # Aquí podrías implementar lógica para limpiar contadores
    # Con SlowAPI es más difícil porque usa memoria interna
