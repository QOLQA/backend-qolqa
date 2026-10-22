# Application DTOs - Frozen dataclasses (Commands/Queries)
# These are agnostic of HTTP/Pydantic and used by use cases.

# Auth
from application.dtos.auth.commands import (
    CreateUserCommand,
    UpdateUserCommand,
    AdminUpdateUserCommand,
    RegisterCommand,
    AuthenticateCommand,
    GoogleLoginCommand,
)

from application.dtos.auth.queries import (
    GetUserQuery,
    GetUserByUsernameQuery,
    GetUserByEmailQuery,
)

# Solution
from application.dtos.solution.commands import (
    CreateSolutionCommand,
    UpdateSolutionCommand,
    DeleteSolutionCommand,
)

from application.dtos.solution.queries import (
    GetSolutionQuery,
    GetAllSolutionsQuery,
    GetSolutionWithVersionsQuery,
)

# Version
from application.dtos.version.commands import (
    CreateVersionCommand,
    UpdateVersionCommand,
    DeleteVersionCommand,
)

from application.dtos.version.queries import (
    GetVersionQuery,
    GetAllVersionsQuery,
    GetVersionsBySolutionQuery,
)

# Query
from application.dtos.query.commands import (
    CreateQueryCommand,
    UpdateQueryCommand,
    DeleteQueryCommand,
    DeleteQueriesBySolutionCommand,
)

from application.dtos.query.queries import (
    GetQueryQuery,
    GetAllQueriesQuery,
    GetQueriesBySolutionQuery,
)

__all__ = [
    # Auth Commands
    "CreateUserCommand",
    "UpdateUserCommand",
    "AdminUpdateUserCommand",
    "RegisterCommand",
    "AuthenticateCommand",
    "GoogleLoginCommand",
    # Auth Queries
    "GetUserQuery",
    "GetUserByUsernameQuery",
    "GetUserByEmailQuery",
    # Solution Commands
    "CreateSolutionCommand",
    "UpdateSolutionCommand",
    "DeleteSolutionCommand",
    # Solution Queries
    "GetSolutionQuery",
    "GetAllSolutionsQuery",
    "GetSolutionWithVersionsQuery",
    # Version Commands
    "CreateVersionCommand",
    "UpdateVersionCommand",
    "DeleteVersionCommand",
    # Version Queries
    "GetVersionQuery",
    "GetAllVersionsQuery",
    "GetVersionsBySolutionQuery",
    # Query Commands
    "CreateQueryCommand",
    "UpdateQueryCommand",
    "DeleteQueryCommand",
    "DeleteQueriesBySolutionCommand",
    # Query Queries
    "GetQueryQuery",
    "GetAllQueriesQuery",
    "GetQueriesBySolutionQuery",
]