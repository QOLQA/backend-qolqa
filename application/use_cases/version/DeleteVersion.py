from domain.repositories.version.repo import IVersionRepository


async def delete_version(
    repository: IVersionRepository,
    version_id: str,
) -> None:
    """Delete a version by its id."""
    await repository.delete(version_id)
