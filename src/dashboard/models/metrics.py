"""Metrics response models for dashboard API."""

from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


class IngestionMetrics(BaseModel):
    """Ingestion metrics model."""
    total: int = Field(description="Total number of ingestions")
    successful: int = Field(description="Number of successful ingestions")
    failed: int = Field(description="Number of failed ingestions")
    success_rate: float = Field(description="Success rate (0.0 to 1.0)")


class RecordMetrics(BaseModel):
    """Record processing metrics model."""
    total_processed: int = Field(description="Total records processed")
    total_successful: int = Field(description="Total records successfully processed")
    total_failed: int = Field(description="Total records that failed processing")


class RedactionSummary(BaseModel):
    """Redaction summary model."""
    total: int = Field(description="Total number of redactions")
    by_field: dict[str, int] = Field(default_factory=dict, description="Redactions grouped by field name")
    by_rule: Optional[dict[str, int]] = Field(None, description="Redactions grouped by rule triggered")
    by_adapter: Optional[dict[str, int]] = Field(None, description="Redactions grouped by source adapter")


class CircuitBreakerStatus(BaseModel):
    """Circuit breaker status model."""
    status: Literal["closed", "open", "half_open"] = Field(description="Circuit breaker state")
    failure_rate: Optional[float] = Field(None, description="Current failure rate (0.0 to 1.0)")


class OverviewMetrics(BaseModel):
    """Overview metrics response model."""
    time_range: str = Field(description="Time range for metrics (e.g., '24h', '7d')")
    ingestions: IngestionMetrics = Field(description="Ingestion statistics")
    records: RecordMetrics = Field(description="Record processing statistics")
    redactions: RedactionSummary = Field(description="PII redaction statistics")
    circuit_breaker: Optional[CircuitBreakerStatus] = Field(None, description="Circuit breaker status")


class RedactionTrendPoint(BaseModel):
    """Single point in redaction trend."""
    date: str = Field(description="Date in YYYY-MM-DD format")
    count: int = Field(description="Number of redactions on this date")


class SecurityRedactions(BaseModel):
    """Security redaction metrics."""
    total: int = Field(description="Total redactions")
    by_rule: dict[str, int] = Field(default_factory=dict, description="Redactions by rule")
    by_adapter: dict[str, int] = Field(default_factory=dict, description="Redactions by adapter")
    trend: list[RedactionTrendPoint] = Field(default_factory=list, description="Time-series trend data")


class AuditEventSummary(BaseModel):
    """Audit event summary."""
    total: int = Field(description="Total audit events")
    by_severity: dict[str, int] = Field(default_factory=dict, description="Events grouped by severity")
    by_type: dict[str, int] = Field(default_factory=dict, description="Events grouped by event type")


class SecurityMetrics(BaseModel):
    """Security metrics response model."""
    time_range: str = Field(description="Time range for metrics")
    redactions: SecurityRedactions = Field(description="Redaction statistics")
    audit_events: AuditEventSummary = Field(description="Audit event statistics")


class ThroughputMetrics(BaseModel):
    """Throughput metrics model."""
    records_per_second: float = Field(description="Average records processed per second")
    mb_per_second: Optional[float] = Field(None, description="Average megabytes processed per second")
    peak_records_per_second: Optional[float] = Field(None, description="Peak records per second")


class LatencyMetrics(BaseModel):
    """Latency metrics model."""
    avg_processing_time_ms: Optional[float] = Field(None, description="Average processing time in milliseconds")
    p50_ms: Optional[float] = Field(None, description="50th percentile latency")
    p95_ms: Optional[float] = Field(None, description="95th percentile latency")
    p99_ms: Optional[float] = Field(None, description="99th percentile latency")


class FileProcessingMetrics(BaseModel):
    """File processing metrics model."""
    total_files: int = Field(description="Total number of files processed")
    avg_file_size_mb: Optional[float] = Field(None, description="Average file size in MB")
    total_data_processed_mb: Optional[float] = Field(None, description="Total data processed in MB")


class MemoryMetrics(BaseModel):
    """Memory usage metrics model."""
    avg_peak_memory_mb: Optional[float] = Field(None, description="Average peak memory usage in MB")
    max_peak_memory_mb: Optional[float] = Field(None, description="Maximum peak memory usage in MB")


class PerformanceMetrics(BaseModel):
    """Performance metrics response model."""
    time_range: str = Field(description="Time range for metrics")
    throughput: ThroughputMetrics = Field(description="Throughput statistics")
    latency: LatencyMetrics = Field(description="Latency statistics")
    file_processing: FileProcessingMetrics = Field(description="File processing statistics")
    memory: MemoryMetrics = Field(description="Memory usage statistics")

