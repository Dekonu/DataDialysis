"""Connection helper for dashboard services.

This module provides a context manager to ensure PostgreSQL connections
are properly returned to the pool, preventing connection leaks.
It also provides a unified interface for both DuckDB and PostgreSQL connections.
"""

from contextlib import contextmanager
from typing import Optional, Any
import logging

from src.domain.ports import StoragePort

logger = logging.getLogger(__name__)


class ConnectionWrapper:
    """Wrapper for database connections that provides a unified execute interface.
    
    This wrapper makes PostgreSQL connections work like DuckDB connections,
    where execute() is called directly on the connection object.
    """
    
    def __init__(self, conn: Any, uses_cursor: bool = False, connection_lock: Optional[Any] = None):
        """Initialize connection wrapper.
        
        Parameters:
            conn: Raw database connection
            uses_cursor: Whether this connection requires cursors
        """
        self._conn = conn
        self._uses_cursor = uses_cursor
        self._current_cursor: Optional[Any] = None
        self._connection_lock = connection_lock
    
    def execute(self, query: str, params: Optional[list] = None):
        """Execute a query and return a result object.
        
        Parameters:
            query: SQL query string
            params: Optional query parameters
            
        Returns:
            Result object with fetchone() and fetchall() methods
        """
        if self._uses_cursor:
            # PostgreSQL: create cursor, execute, return cursor
            # Convert ? placeholders to %s for PostgreSQL compatibility
            pg_query = query.replace('?', '%s')
            
            if self._current_cursor:
                self._current_cursor.close()
            self._current_cursor = self._conn.cursor()
            if params:
                self._current_cursor.execute(pg_query, params)
            else:
                self._current_cursor.execute(pg_query)
            return self._current_cursor
        else:
            # DuckDB: execute directly on connection
            connection_lock = self._connection_lock
            if connection_lock:
                with connection_lock:
                    if params:
                        result = self._conn.execute(query, params)
                    else:
                        result = self._conn.execute(query)
            elif params:
                result = self._conn.execute(query, params)
            else:
                result = self._conn.execute(query)
            return result
    
    def close(self):
        """Close any open cursors."""
        if self._current_cursor:
            try:
                self._current_cursor.close()
            except Exception:
                pass
            self._current_cursor = None


@contextmanager
def get_db_connection(storage: StoragePort):
    """Context manager for database connections.
    
    Ensures connections are properly returned to the pool even if an exception occurs.
    Provides a unified interface for both DuckDB and PostgreSQL.
    
    Parameters:
        storage: Storage adapter instance
        
    Yields:
        ConnectionWrapper: Wrapped database connection with execute() method
        
    Example:
        ```python
        with get_db_connection(storage) as conn:
            result = conn.execute("SELECT 1").fetchone()
        ```
    """
    conn = None
    wrapper = None
    try:
        if hasattr(storage, '_get_connection'):
            base_conn = storage._get_connection()
            conn = base_conn
            
            # Check if this adapter requires DB-API cursors. DuckDB gets a
            # duplicate cursor/connection so concurrent dashboard reads do not
            # share one open result set across threads.
            uses_cursor = hasattr(storage, 'connection_params')
            query_conn = base_conn
            connection_lock = getattr(storage, '_connection_lock', None)
            if not uses_cursor and hasattr(base_conn, 'cursor'):
                query_conn = base_conn.cursor()
                connection_lock = None
            
            wrapper = ConnectionWrapper(query_conn, uses_cursor=uses_cursor, connection_lock=connection_lock)
            yield wrapper
        else:
            # For adapters that don't use connection pools (e.g., DuckDB)
            yield None
    finally:
        if wrapper:
            wrapper.close()
        if conn is not None and hasattr(storage, '_return_connection'):
            try:
                storage._return_connection(conn)
            except Exception as e:
                logger.warning(f"Error returning connection to pool: {str(e)}")

