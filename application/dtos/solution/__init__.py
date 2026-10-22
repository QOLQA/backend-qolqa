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

__all__ = [
    # Commands
    "CreateSolutionCommand",
    "UpdateSolutionCommand",
    "DeleteSolutionCommand",
    # Queries
    "GetSolutionQuery",
    "GetAllSolutionsQuery",
    "GetSolutionWithVersionsQuery",
]