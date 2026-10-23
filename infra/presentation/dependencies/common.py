"""
Common dependencies for presentation layer.
"""
from fastapi import Depends
from config.settings import settings, TypeDB
from infra.dependencies.common import get_database as _get_database

# Re-export the database dependency
get_database = _get_database