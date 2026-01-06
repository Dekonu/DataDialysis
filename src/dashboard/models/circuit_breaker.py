"""Pydantic models for circuit breaker status endpoint."""

from pydantic import BaseModel, Field


class CircuitBreakerStatus(BaseModel):
    """Circuit breaker status information."""
    
    is_open: bool = Field(..., description="Whether the circuit breaker is open")
    failure_rate: float = Field(..., description="Current failure rate percentage")
    threshold: float = Field(..., description="Configured failure threshold percentage")
    total_processed: int = Field(..., description="Total records processed")
    total_failures: int = Field(..., description="Total failures encountered")
    window_size: int = Field(..., description="Sliding window size")
    failures_in_window: int = Field(..., description="Number of failures in current window")
    records_in_window: int = Field(..., description="Number of records in current window")
    min_records_before_check: int = Field(..., description="Minimum records before checking threshold")

