"""Health check endpoint for dashboard API."""

import logging
import time
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from src.dashboard.api.dependencies import StorageDep
from src.dashboard.models.health import DatabaseHealth, HealthResponse
from src.domain.ports import StoragePort

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["health"])


async def check_database_health(storage: StoragePort) -> DatabaseHealth:
    """Check database connection health.
    
    Parameters:
        storage: Storage adapter instance
        
    Returns:
        DatabaseHealth: Database health status
        
    Security Impact:
        - Only checks connectivity, no sensitive data exposed
    """
    # Determine database type
    db_type = "unknown"
    if hasattr(storage, 'db_config') and storage.db_config:
        db_type = storage.db_config.db_type
    elif hasattr(storage, 'connection_params') and isinstance(getattr(storage, 'connection_params', None), dict):
        # PostgreSQL adapter stores connection_params
        if 'host' in storage.connection_params or 'dsn' in storage.connection_params:
            db_type = "postgresql"
    elif hasattr(storage, 'db_path'):
        # DuckDB adapter
        db_type = "duckdb"
    
    try:
        start_time = time.time()
        
        # For PostgreSQL adapter, test connection pool directly
        if db_type == "postgresql" and hasattr(storage, '_get_connection'):
            try:
                # Try to get a connection from the pool
                conn = storage._get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                
                # Return connection to pool
                if hasattr(storage, '_return_connection'):
                    storage._return_connection(conn)
                
                response_time = (time.time() - start_time) * 1000  # Convert to ms
                logger.debug(f"PostgreSQL health check successful: {response_time:.2f}ms")
                return DatabaseHealth(
                    status="connected",
                    type=db_type,
                    response_time_ms=round(response_time, 2)
                )
            except Exception as e:
                error_msg = str(e)
                logger.warning(
                    f"PostgreSQL connection test failed: {error_msg}",
                    exc_info=True
                )
                return DatabaseHealth(
                    status="disconnected",
                    type=db_type,
                    response_time_ms=None
                )
        
        # For DuckDB adapter, use query method if available
        if hasattr(storage, 'query'):
            result = storage.query("SELECT 1")
            if result.is_success():
                response_time = (time.time() - start_time) * 1000  # Convert to ms
                return DatabaseHealth(
                    status="connected",
                    type=db_type,
                    response_time_ms=round(response_time, 2)
                )
            else:
                logger.warning(f"Database query failed: {result.error}")
                return DatabaseHealth(
                    status="disconnected",
                    type=db_type,
                    response_time_ms=None
                )
        
        # Fallback: check if storage is initialized
        if hasattr(storage, '_initialized') and storage._initialized:
            return DatabaseHealth(
                status="connected",
                type=db_type,
                response_time_ms=None
            )
        
        # Last resort: try to get connection to test
        if hasattr(storage, '_get_connection'):
            try:
                conn = storage._get_connection()
                if conn:
                    if hasattr(storage, '_return_connection'):
                        storage._return_connection(conn)
                    return DatabaseHealth(
                        status="connected",
                        type=db_type,
                        response_time_ms=None
                    )
            except Exception as e:
                logger.warning(f"Connection test failed: {str(e)}")
        
        return DatabaseHealth(
            status="disconnected",
            type=db_type,
            response_time_ms=None
        )
        
    except Exception as e:
        logger.warning(f"Database health check failed: {str(e)}", exc_info=True)
        return DatabaseHealth(
            status="disconnected",
            type=db_type,
            response_time_ms=None
        )


@router.get("/health", response_model=HealthResponse)
async def health_check(storage: StorageDep) -> HealthResponse:
    """Health check endpoint.
    
    This endpoint provides system health status including database connectivity.
    Used by monitoring tools and load balancers.
    
    Parameters:
        storage: Storage adapter (injected via dependency)
        
    Returns:
        HealthResponse: System health status
        
    Security Impact:
        - No sensitive information exposed
        - Safe for public health checks
    """
    try:
        # Check database health
        db_health = await check_database_health(storage)
        
        # Determine overall status
        if db_health.status == "connected":
            overall_status = "healthy"
        elif db_health.status == "disconnected":
            overall_status = "unhealthy"
        else:
            overall_status = "degraded"
        
        return HealthResponse(
            status=overall_status,
            timestamp=datetime.now(timezone.utc),
            version="1.0.0",
            database=db_health
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Health check failed"
        )

