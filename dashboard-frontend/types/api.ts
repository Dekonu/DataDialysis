/**
 * TypeScript types for API responses.
 * These types match the Pydantic models in the backend.
 */

export interface IngestionMetrics {
  total: number;
  successful: number;
  failed: number;
  success_rate: number;
}

export interface RecordMetrics {
  total_processed: number;
  total_successful: number;
  total_failed: number;
}

export interface RedactionSummary {
  total: number;
  by_field: Record<string, number>;
  by_rule?: Record<string, number> | null;
  by_adapter?: Record<string, number> | null;
}

export interface CircuitBreakerStatus {
  status: 'closed' | 'open' | 'half_open';
  failure_rate?: number | null;
}

export interface OverviewMetrics {
  time_range: string;
  ingestions: IngestionMetrics;
  records: RecordMetrics;
  redactions: RedactionSummary;
  circuit_breaker?: CircuitBreakerStatus | null;
}

export interface RedactionTrendPoint {
  date: string;
  count: number;
}

export interface SecurityRedactions {
  total: number;
  by_rule: Record<string, number>;
  by_adapter: Record<string, number>;
  trend: RedactionTrendPoint[];
}

export interface AuditEventSummary {
  total: number;
  by_severity: Record<string, number>;
  by_type: Record<string, number>;
}

export interface SecurityMetrics {
  time_range: string;
  redactions: SecurityRedactions;
  audit_events: AuditEventSummary;
}

export interface ThroughputMetrics {
  records_per_second: number;
  mb_per_second?: number | null;
  peak_records_per_second?: number | null;
}

export interface LatencyMetrics {
  avg_processing_time_ms?: number | null;
  p50_ms?: number | null;
  p95_ms?: number | null;
  p99_ms?: number | null;
}

export interface FileProcessingMetrics {
  total_files: number;
  avg_file_size_mb?: number | null;
  total_data_processed_mb?: number | null;
}

export interface MemoryMetrics {
  avg_peak_memory_mb?: number | null;
  max_peak_memory_mb?: number | null;
}

export interface PerformanceMetrics {
  time_range: string;
  throughput: ThroughputMetrics;
  latency: LatencyMetrics;
  file_processing: FileProcessingMetrics;
  memory: MemoryMetrics;
}

export type TimeRange = '1h' | '24h' | '7d' | '30d';

