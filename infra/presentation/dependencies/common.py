"""
Database dependency factory — re-exports from infra.persistence.db_factory
to keep a single get_database function object for dependency_overrides.
"""
from infra.persistence.db_factory import get_database

__all__ = ["get_database"]
