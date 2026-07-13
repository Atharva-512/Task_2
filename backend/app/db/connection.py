"""DuckDB connection management.

Provides a singleton, read-oriented connection to the existing DuckDB
warehouse produced by the Task 1 ELT pipeline. This module never creates
databases, tables, or views — it only connects to and queries an
already-existing warehouse file.
"""

import logging
import os
import threading
from typing import Optional

import duckdb
import pandas as pd

from app.core.config import get_settings

logger = logging.getLogger("restaurant_pos_api.db")

_connection: Optional[duckdb.DuckDBPyConnection] = None
_connection_lock = threading.Lock()


class DatabaseConnectionError(Exception):
    """Raised when a DuckDB connection cannot be established."""


class QueryExecutionError(Exception):
    """Raised when a query against the warehouse fails."""


def _resolve_database_path() -> str:
    """Return the configured DuckDB warehouse path, validating it exists.

    Raises:
        FileNotFoundError: If DATABASE_PATH does not point to an existing file.
    """
    settings = get_settings()
    database_path = settings.database_path

    if not database_path:
        raise FileNotFoundError(
            "DATABASE_PATH is not configured. Set it in your environment or .env file."
        )

    if not os.path.isfile(database_path):
        raise FileNotFoundError(
            f"DuckDB warehouse file not found at path: {database_path}"
        )

    return database_path


def get_connection() -> duckdb.DuckDBPyConnection:
    """Return the singleton DuckDB connection, creating it if necessary.

    The connection is opened read-only against the existing warehouse file.
    Thread-safe: concurrent callers will not create duplicate connections.

    Raises:
        FileNotFoundError: If the configured DATABASE_PATH does not exist.
        DatabaseConnectionError: If DuckDB fails to open the connection.
    """
    global _connection

    if _connection is not None:
        return _connection

    with _connection_lock:
        if _connection is not None:
            return _connection

        database_path = _resolve_database_path()

        try:
            logger.info("Connecting to DuckDB warehouse at '%s'", database_path)
            _connection = duckdb.connect(database=database_path, read_only=True)
            logger.info("DuckDB connection established successfully.")
        except duckdb.Error as exc:
            logger.exception("Failed to connect to DuckDB warehouse.")
            raise DatabaseConnectionError(
                f"Could not connect to DuckDB warehouse at '{database_path}': {exc}"
            ) from exc

        return _connection


def execute_query(sql: str, params: Optional[tuple] = None) -> pd.DataFrame:
    """Execute a parameterized SQL query against the warehouse.

    Args:
        sql: SQL query text, using '?' placeholders for parameters.
        params: Optional tuple of parameter values to bind to the query.

    Returns:
        A pandas DataFrame containing the query results.

    Raises:
        DatabaseConnectionError: If the connection cannot be established.
        QueryExecutionError: If the query fails to execute.
    """
    connection = get_connection()

    try:
        if params is not None:
            result = connection.execute(sql, params)
        else:
            result = connection.execute(sql)
        return result.fetchdf()
    except duckdb.Error as exc:
        logger.error("Query execution failed. SQL: %s | Params: %s | Error: %s", sql, params, exc)
        raise QueryExecutionError(f"Query execution failed: {exc}") from exc


def close_connection() -> None:
    """Close the singleton DuckDB connection, if open."""
    global _connection

    with _connection_lock:
        if _connection is None:
            logger.info("No active DuckDB connection to close.")
            return

        try:
            _connection.close()
            logger.info("DuckDB connection closed successfully.")
        except duckdb.Error as exc:
            logger.exception("Error while closing DuckDB connection.")
            raise DatabaseConnectionError(f"Failed to close DuckDB connection: {exc}") from exc
        finally:
            _connection = None
