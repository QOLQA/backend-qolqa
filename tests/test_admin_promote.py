"""
Tests de seguridad para POST /admin/users/{id}/promote.

Verifica que promover un usuario:
1. Agrega RoleEnum.admin a sus roles.
2. Incrementa token_version (invalidando JWTs previos).
3. Es idempotente si el usuario ya es admin.
4. Rechaza acceso a usuarios no-admin (403 vía require_admin real).

La capa de datos se mockea sobrescribiendo get_user_repository para devolver
un UserRepositoryImpl simulado. require_admin y get_current_user se dejan
reales para probar la autorización verdadera con tokens JWT.
"""
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from bson import ObjectId
from fastapi import status

from domain.entities.auth.UserEntity import UserEntity
from domain.enums.RoleEnum import RoleEnum
from infra.persistence.jwt import create_access_token
from infra.presentation.dependencies.auth import get_user_repository
from main import app

ADMIN_ID = str(ObjectId())
TARGET_ID = str(ObjectId())

ADMIN_JWT = create_access_token({
    "sub": "admin",
    "user_id": ADMIN_ID,
    "roles": [RoleEnum.admin.value],
    "token_version": 0,
})

REGULAR_JWT = create_access_token({
    "sub": "regular",
    "user_id": ADMIN_ID,
    "roles": [],
    "token_version": 0,
})


def make_user(user_id: str, username: str, roles: list, token_version: int = 0) -> UserEntity:
    return UserEntity(
        id=user_id,
        username=username,
        email=f"{username}@test.com",
        is_active=True,
        created_at=datetime.now(UTC),
        roles=roles,
        token_version=token_version,
    )


def build_mock_repo(*get_by_id_results):
    """Construye un mock de UserRepositoryImpl con side_effect para get_by_id."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(side_effect=list(get_by_id_results))
    repo.save = AsyncMock()
    repo.collection = AsyncMock()
    repo.collection.update_one = AsyncMock()
    return repo


@pytest.mark.auth
class TestAdminPromote:
    """Tests para el endpoint POST /admin/users/{id}/promote."""

    @pytest.mark.asyncio
    async def test_promote_user_to_admin_changes_token_version(self, async_client):
        """Promover agrega RoleEnum.admin, incrementa token_version y llama a $inc."""
        admin_actor = make_user(ADMIN_ID, "admin", [RoleEnum.admin], token_version=0)
        target_v0 = make_user(TARGET_ID, "target", [], token_version=0)
        target_v1 = make_user(TARGET_ID, "target", [RoleEnum.admin], token_version=1)

        mock_repo = build_mock_repo(admin_actor, target_v0, target_v1)
        mock_repo.save.return_value = target_v1

        app.dependency_overrides[get_user_repository] = lambda: mock_repo
        try:
            response = await async_client.post(
                f"/admin/users/{TARGET_ID}/promote",
                headers={"Authorization": f"Bearer {ADMIN_JWT}"},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert RoleEnum.admin.value in data["roles"]
            # token_version es interno (no está en UserResponse); se verifica vía $inc
            mock_repo.collection.update_one.assert_awaited_once_with(
                {"_id": ObjectId(TARGET_ID)},
                {"$inc": {"token_version": 1}},
            )
        finally:
            app.dependency_overrides.pop(get_user_repository, None)

    @pytest.mark.asyncio
    async def test_promote_already_admin_is_idempotent(self, async_client):
        """Si ya es admin, no hay side effects: ni save ni update_one."""
        admin_actor = make_user(ADMIN_ID, "admin", [RoleEnum.admin], token_version=0)
        target_already_admin = make_user(TARGET_ID, "target", [RoleEnum.admin], token_version=0)

        mock_repo = build_mock_repo(admin_actor, target_already_admin)

        app.dependency_overrides[get_user_repository] = lambda: mock_repo
        try:
            response = await async_client.post(
                f"/admin/users/{TARGET_ID}/promote",
                headers={"Authorization": f"Bearer {ADMIN_JWT}"},
            )

            assert response.status_code == status.HTTP_200_OK
            mock_repo.save.assert_not_awaited()
            mock_repo.collection.update_one.assert_not_awaited()
        finally:
            app.dependency_overrides.pop(get_user_repository, None)

    @pytest.mark.asyncio
    async def test_promote_invalidates_previous_jwt(self, async_client):
        """JWT con token_version anterior es rechazado con 401 tras promover."""
        admin_actor = make_user(ADMIN_ID, "admin", [RoleEnum.admin], token_version=0)
        target_v0 = make_user(TARGET_ID, "target", [], token_version=0)
        target_v1 = make_user(TARGET_ID, "target", [RoleEnum.admin], token_version=1)

        call_count = {"n": 0}

        async def get_by_id_side_effect(user_id):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return admin_actor          # get_current_user del actor admin
            if call_count["n"] == 2:
                return target_v0            # router obtiene target antes de promover
            # call 3+ (promote get_by_id + /auth/me get_user_by_id): devuelve target_v1
            return target_v1

        mock_repo = AsyncMock()
        mock_repo.get_by_id = get_by_id_side_effect
        mock_repo.save = AsyncMock(return_value=target_v1)
        mock_repo.collection = AsyncMock()
        mock_repo.collection.update_one = AsyncMock()

        target_jwt_v0 = create_access_token({
            "sub": "target",
            "user_id": TARGET_ID,
            "roles": [],
            "token_version": 0,
        })

        app.dependency_overrides[get_user_repository] = lambda: mock_repo
        try:
            # 1. Promover al usuario
            promote_response = await async_client.post(
                f"/admin/users/{TARGET_ID}/promote",
                headers={"Authorization": f"Bearer {ADMIN_JWT}"},
            )
            assert promote_response.status_code == status.HTTP_200_OK

            # 2. El JWT viejo (token_version=0) debe ser rechazado en /auth/me
            me_response = await async_client.get(
                "/auth/me",
                headers={"Authorization": f"Bearer {target_jwt_v0}"},
            )
            assert me_response.status_code == status.HTTP_401_UNAUTHORIZED
        finally:
            app.dependency_overrides.pop(get_user_repository, None)

    @pytest.mark.asyncio
    async def test_regular_user_cannot_access_admin_promote(self, async_client):
        """Usuario sin rol admin recibe 403 de require_admin sin tocar la DB."""
        regular_user = make_user(ADMIN_ID, "regular", [], token_version=0)

        mock_repo = build_mock_repo(regular_user)

        app.dependency_overrides[get_user_repository] = lambda: mock_repo
        try:
            response = await async_client.post(
                f"/admin/users/{TARGET_ID}/promote",
                headers={"Authorization": f"Bearer {REGULAR_JWT}"},
            )

            assert response.status_code == status.HTTP_403_FORBIDDEN
            mock_repo.collection.update_one.assert_not_awaited()
        finally:
            app.dependency_overrides.pop(get_user_repository, None)
