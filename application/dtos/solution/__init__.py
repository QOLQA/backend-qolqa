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