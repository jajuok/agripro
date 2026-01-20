"""Cross-database compatible column types.

This module provides column types that work across different database backends,
particularly for PostgreSQL (production) and SQLite (testing).
"""

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import TypeDecorator


class JSONBCompatible(TypeDecorator):
    """A JSON type that uses JSONB on PostgreSQL and JSON on other databases.
    
    This allows using JSONB features in production while maintaining
    compatibility with SQLite for testing.
    """
    
    impl = JSON
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        """Load the appropriate implementation based on dialect."""
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())
