import type {
  OverviewMetrics,
  SecurityMetrics,
  PerformanceMetrics,
  TimeRange,
  AuditLogsResponse,
  RedactionLogsResponse,
  CircuitBreakerStatus,
} from '@/types/api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  version: string;
  database: {
    status: 'connected' | 'disconnected';
    type: string;
    response_time_ms?: number;
  };
}

export async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export const api = {
  health: () => apiRequest<HealthResponse>('/api/health'),
  metrics: {
    overview: (timeRange: TimeRange = '24h') =>
      apiRequest<OverviewMetrics>(`/api/metrics/overview?time_range=${timeRange}`),
    security: (timeRange: TimeRange = '7d') =>
      apiRequest<SecurityMetrics>(`/api/metrics/security?time_range=${timeRange}`),
    performance: (timeRange: TimeRange = '24h') =>
      apiRequest<PerformanceMetrics>(`/api/metrics/performance?time_range=${timeRange}`),
  },
  audit: {
    logs: (params?: {
      limit?: number;
      offset?: number;
      severity?: string;
      event_type?: string;
      start_date?: string;
      end_date?: string;
      source_adapter?: string;
      sort_by?: string;
      sort_order?: 'ASC' | 'DESC';
    }) => {
      const searchParams = new URLSearchParams();
      if (params) {
        Object.entries(params).forEach(([key, value]) => {
          if (value !== undefined && value !== null) {
            searchParams.append(key, String(value));
          }
        });
      }
      const query = searchParams.toString();
      return apiRequest<AuditLogsResponse>(`/api/audit-logs${query ? `?${query}` : ''}`);
    },
    redactionLogs: (params?: {
      field_name?: string;
      time_range?: TimeRange;
      limit?: number;
      offset?: number;
      rule_triggered?: string;
      source_adapter?: string;
      ingestion_id?: string;
      sort_by?: string;
      sort_order?: 'ASC' | 'DESC';
    }) => {
      const searchParams = new URLSearchParams();
      if (params) {
        Object.entries(params).forEach(([key, value]) => {
          if (value !== undefined && value !== null) {
            searchParams.append(key, String(value));
          }
        });
      }
      const query = searchParams.toString();
      return apiRequest<RedactionLogsResponse>(`/api/redaction-logs${query ? `?${query}` : ''}`);
    },
    export: (params: {
      format: 'json' | 'csv';
      severity?: string;
      event_type?: string;
      start_date?: string;
      end_date?: string;
    }) => {
      const searchParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value));
        }
      });
      return fetch(`${API_BASE_URL}/api/audit-logs/export?${searchParams.toString()}`).then(
        (response) => {
          if (!response.ok) {
            throw new Error(`Export failed: ${response.statusText}`);
          }
          return response.blob();
        }
      );
    },
  },
  circuitBreaker: {
    status: () => apiRequest<CircuitBreakerStatus>('/api/circuit-breaker/status'),
  },
};

