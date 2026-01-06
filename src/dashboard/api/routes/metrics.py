"""Metrics endpoints for dashboard API.

This module provides endpoints for overview, security, and performance metrics.
"""

from fastapi import APIRouter, HTTPException, Query

from src.dashboard.api.dependencies import StorageDep
from src.dashboard.services.metrics_aggregator import MetricsAggregator
from src.dashboard.services.security_metrics import SecurityMetricsService
from src.dashboard.services.performance_metrics import PerformanceMetricsService

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/overview")
def get_overview_metrics(
    time_range: str = Query("24h", pattern="^(1h|24h|7d|30d)$", description="Time range for metrics"),
    storage: StorageDep = None
):
    """Get overview metrics.
    
    Returns aggregated metrics including:
    - Ingestion statistics (total, successful, failed, success rate)
    - Record processing statistics
    - PII redaction summary
    - Circuit breaker status
    
    Parameters:
        time_range: Time range for metrics (1h, 24h, 7d, 30d)
        storage: Storage adapter (injected via dependency)
        
    Returns:
        OverviewMetrics: Overview metrics response
    """
    try:
        aggregator = MetricsAggregator(storage)
        result = aggregator.get_overview_metrics(time_range)
        
        if result.is_success():
            return result.value
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get overview metrics: {str(result.error)}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error getting overview metrics: {str(e)}"
        )


@router.get("/security")
def get_security_metrics(
    time_range: str = Query("7d", pattern="^(1h|24h|7d|30d)$", description="Time range for metrics"),
    storage: StorageDep = None
):
    """Get security metrics.
    
    Returns security-specific metrics including:
    - Redaction statistics (by rule, by adapter, trend)
    - Audit event summary (by severity, by type)
    
    Parameters:
        time_range: Time range for metrics (1h, 24h, 7d, 30d)
        storage: Storage adapter (injected via dependency)
        
    Returns:
        SecurityMetrics: Security metrics response
    """
    try:
        service = SecurityMetricsService(storage)
        result = service.get_security_metrics(time_range)
        
        if result.is_success():
            return result.value
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get security metrics: {str(result.error)}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error getting security metrics: {str(e)}"
        )


@router.get("/performance")
def get_performance_metrics(
    time_range: str = Query("24h", pattern="^(1h|24h|7d|30d)$", description="Time range for metrics"),
    storage: StorageDep = None
):
    """Get performance metrics.
    
    Returns performance-specific metrics including:
    - Throughput (records/sec, MB/sec)
    - Latency (avg, p50, p95, p99)
    - File processing statistics
    - Memory usage
    
    Parameters:
        time_range: Time range for metrics (1h, 24h, 7d, 30d)
        storage: Storage adapter (injected via dependency)
        
    Returns:
        PerformanceMetrics: Performance metrics response
    """
    try:
        service = PerformanceMetricsService(storage)
        result = service.get_performance_metrics(time_range)
        
        if result.is_success():
            return result.value
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get performance metrics: {str(result.error)}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error getting performance metrics: {str(e)}"
        )

