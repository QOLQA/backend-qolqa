# Application DTOs - Frozen dataclasses (Commands/Queries)
# These are agnostic of HTTP/Pydantic and used by use cases.

# Auth
from application.dtos.auth.commands import (
    AdminUpdateUserCommand,
    AuthenticateCommand,
    CreateUserCommand,
    GoogleLoginCommand,
    RegisterCommand,
    UpdateUserCommand,
)
from application.dtos.auth.queries import (
    GetUserByEmailQuery,
    GetUserByUsernameQuery,
    GetUserQuery,
)

# Query
from application.dtos.query.commands import (
    CreateQueryCommand,
    DeleteQueriesBySolutionCommand,
    DeleteQueryCommand,
    UpdateQueryCommand,
)
from application.dtos.query.queries import (
    GetAllQueriesQuery,
    GetQueriesBySolutionQuery,
    GetQueryQuery,
)

# Solution
from application.dtos.solution.commands import (
    CreateSolutionCommand,
    DeleteSolutionCommand,
    UpdateSolutionCommand,
)
from application.dtos.solution.queries import (
    GetAllSolutionsQuery,
    GetSolutionQuery,
    GetSolutionWithVersionsQuery,
)

# Version
from application.dtos.version.commands import (
    CreateVersionCommand,
    DeleteVersionCommand,
    UpdateVersionCommand,
)
from application.dtos.version.queries import (
    GetAllVersionsQuery,
    GetVersionQuery,
    GetVersionsBySolutionQuery,
)

__all__ = [
    "AdminUpdateUserCommand",
    "AuthenticateCommand",
    "CreateQueryCommand",
    "CreateSolutionCommand",
    "CreateUserCommand",
    "CreateVersionCommand",
    "DeleteQueriesBySolutionCommand",
    "DeleteQueryCommand",
    "DeleteSolutionCommand",
    "DeleteVersionCommand",
    "GetAllQueriesQuery",
    "GetAllSolutionsQuery",
    "GetAllVersionsQuery",
    "GetQueriesBySolutionQuery",
    "GetQueryQuery",
    "GetSolutionQuery",
    "GetSolutionWithVersionsQuery",
    "GetUserByEmailQuery",
    "GetUserByUsernameQuery",
    "GetUserQuery",
    "GetVersionQuery",
    "GetVersionsBySolutionQuery",
    "GoogleLoginCommand",
    "RegisterCommand",
    "UpdateQueryCommand",
    "UpdateSolutionCommand",
    "UpdateUserCommand",
    "UpdateVersionCommand",
]