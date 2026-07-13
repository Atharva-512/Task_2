"""Database access layer for the DuckDB warehouse."""

from app.db.connection import (
    DatabaseConnectionError,
    QueryExecutionError,
    close_connection,
    execute_query,
    get_connection,
)

__all__ = [
    "get_connection",
    "execute_query",
    "close_connection",
    "DatabaseConnectionError",
    "QueryExecutionError",
]
