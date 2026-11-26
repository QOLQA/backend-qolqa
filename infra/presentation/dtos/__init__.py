# Infra Presentation DTOs (Pydantic models for HTTP transport)

# Auth
from infra.presentation.dtos.auth.request import (
    AdminUserUpdateRequest,
    GoogleLoginRequest,
    UserCreateRequest,
    UserLoginRequest,
    UserUpdateRequest,
)
from infra.presentation.dtos.auth.response import (
    GoogleLoginResponse,
    TokenResponse,
    UserResponse,
)

# Query
from infra.presentation.dtos.query.request import (
    QueryCreateRequest,
    QueryPartialUpdateRequest,
)
from infra.presentation.dtos.query.response import (
    QueryResponse,
)

# Solution
from infra.presentation.dtos.solution.request import (
    SolutionCreateRequest,
    SolutionPartialUpdateRequest,
)
from infra.presentation.dtos.solution.response import (
    SolutionResponse,
)

# Version
from infra.presentation.dtos.version.request import (
    VersionCreateRequest,
    VersionPartialUpdateRequest,
    default_version_descriptions,
)
from infra.presentation.dtos.version.response import (
    VersionResponse,
)

__all__ = [
    "AdminUserUpdateRequest",
    "GoogleLoginRequest",
    "GoogleLoginResponse",
    "QueryCreateRequest",
    "QueryPartialUpdateRequest",
    "QueryResponse",
    "SolutionCreateRequest",
    "SolutionPartialUpdateRequest",
    "SolutionResponse",
    "TokenResponse",
    "UserCreateRequest",
    "UserLoginRequest",
    "UserResponse",
    "UserUpdateRequest",
    "VersionCreateRequest",
    "VersionPartialUpdateRequest",
    "VersionResponse",
    "default_version_descriptions",
]