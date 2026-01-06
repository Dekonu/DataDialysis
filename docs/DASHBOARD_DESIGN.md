# Data-Dialysis Health Dashboard - Design Document

## Executive Summary

This document proposes a comprehensive, production-ready health monitoring dashboard for the Data-Dialysis pipeline. The dashboard will provide real-time visibility into pipeline health, security metrics, performance indicators, and compliance reporting.

## Repository Structure Decision

### Recommendation: **Same Repository (Monorepo)**

**Rationale:**
1. **Architectural Consistency**: Maintains Hexagonal Architecture principles - dashboard is an adapter (presentation layer)
2. **Shared Domain Logic**: Dashboard can reuse domain services, ports, and adapters
3. **Simplified Deployment**: Single codebase, shared dependencies, unified CI/CD
4. **Security Boundary**: Dashboard accesses data through existing storage adapters (no new attack surface)
5. **Code Reuse**: Leverage existing security report generation, audit logging, and data access patterns

**Structure:**
```
DataDialysis/
├── src/
│   ├── domain/          # Shared domain logic (unchanged)
│   ├── adapters/        # Existing adapters (unchanged)
│   ├── infrastructure/   # Shared infrastructure (unchanged)
│   └── dashboard/       # NEW: Dashboard module
│       ├── api/         # FastAPI backend
│       ├── models/      # Pydantic response models
│       └── services/    # Dashboard-specific services
├── dashboard-frontend/  # NEW: Next.js frontend
│   ├── app/            # Next.js App Router
│   ├── components/     # React components
│   ├── lib/            # Utilities
│   └── types/          # TypeScript types
└── tests/
    └── dashboard/      # Dashboard tests
```

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Dashboard Frontend                        │
│  (Next.js 14+ App Router, TypeScript, Shadcn UI, Tailwind) │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Overview   │  │   Security   │  │ Performance  │     │
│  │   Dashboard   │  │   Metrics    │  │   Metrics    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Audit Log  │  │   Circuit     │  │   Data       │     │
│  │   Explorer    │  │   Breaker    │  │   Volume     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ↕ REST API + WebSocket
┌─────────────────────────────────────────────────────────────┐
│                    Dashboard Backend                         │
│  (FastAPI, Pydantic V2, Async, Dependency Injection)        │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              API Routes (FastAPI)                     │  │
│  │  - GET  /api/health                                   │  │
│  │  - GET  /api/metrics/overview                         │  │
│  │  - GET  /api/metrics/security                          │  │
│  │  - GET  /api/metrics/performance                       │  │
│  │  - GET  /api/audit-logs                                │  │
│  │  - GET  /api/redaction-logs                           │  │
│  │  - GET  /api/circuit-breaker/status                   │  │
│  │  - GET  /api/ingestions                               │  │
│  │  - WS   /ws/realtime                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                        ↕ Ports                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Dashboard Services (Domain Layer)             │  │
│  │  - MetricsAggregator                                   │  │
│  │  - SecurityMetricsService                             │  │
│  │  - PerformanceMetricsService                          │  │
│  │  - AuditLogService                                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                        ↕ Adapters                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Storage Adapters (Existing)                   │  │
│  │  - DuckDBAdapter                                       │  │
│  │  - PostgreSQLAdapter                                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                    Data Sources                              │
│  - logs table (redaction events)                            │
│  - audit_log table (audit trail)                             │
│  - patients/encounters/observations tables                   │
│  - Security report JSON files                                │
│  - Circuit breaker state                                     │
└─────────────────────────────────────────────────────────────┘
```

## Backend Design (FastAPI)

### Technology Stack

- **Framework**: FastAPI 0.104+ (async, automatic OpenAPI docs)
- **Validation**: Pydantic V2 (type-safe, fast)
- **Database**: Existing storage adapters (DuckDB/PostgreSQL)
- **Real-time**: WebSocket support for live updates
- **Authentication**: JWT tokens (optional, for production)
- **CORS**: Configured for frontend origin

### API Structure

```
src/dashboard/
├── __init__.py
├── api/
│   ├── __init__.py
│   ├── main.py              # FastAPI app instance
│   ├── dependencies.py      # Dependency injection
│   ├── middleware.py        # CORS, logging, error handling
│   └── routes/
│       ├── __init__.py
│       ├── health.py        # Health check endpoint
│       ├── metrics.py        # Metrics endpoints
│       ├── security.py       # Security metrics
│       ├── audit.py          # Audit log endpoints
│       ├── circuit_breaker.py # Circuit breaker status
│       └── websocket.py      # WebSocket for real-time updates
├── models/
│   ├── __init__.py
│   ├── health.py            # Health check models
│   ├── metrics.py           # Metrics response models
│   ├── security.py           # Security metrics models
│   └── audit.py             # Audit log models
└── services/
    ├── __init__.py
    ├── metrics_aggregator.py    # Aggregate metrics from multiple sources
    ├── security_metrics.py      # Security-specific metrics
    ├── performance_metrics.py   # Performance metrics
    └── audit_service.py         # Audit log queries
```

### Key API Endpoints

#### 1. Health Check
```python
GET /api/health
Response: {
    "status": "healthy" | "degraded" | "unhealthy",
    "timestamp": "2025-01-15T10:30:00Z",
    "version": "1.0.0",
    "database": {
        "status": "connected",
        "type": "duckdb" | "postgresql"
    }
}
```

#### 2. Overview Metrics
```python
GET /api/metrics/overview?time_range=24h
Response: {
    "time_range": "24h",
    "ingestions": {
        "total": 150,
        "successful": 145,
        "failed": 5,
        "success_rate": 0.967
    },
    "records": {
        "total_processed": 125000,
        "total_successful": 123500,
        "total_failed": 1500
    },
    "redactions": {
        "total": 3500,
        "by_field": {
            "ssn": 1200,
            "phone": 1500,
            "email": 800
        }
    },
    "circuit_breaker": {
        "status": "closed" | "open" | "half_open",
        "failure_rate": 0.012
    }
}
```

#### 3. Security Metrics
```python
GET /api/metrics/security?time_range=7d
Response: {
    "time_range": "7d",
    "redactions": {
        "total": 12500,
        "by_rule": {
            "SSN_PATTERN": 4500,
            "PHONE_PATTERN": 5200,
            "EMAIL_PATTERN": 2800
        },
        "by_adapter": {
            "csv_ingester": 8000,
            "json_ingester": 3500,
            "xml_ingester": 1000
        },
        "trend": [
            {"date": "2025-01-08", "count": 1500},
            {"date": "2025-01-09", "count": 1800},
            ...
        ]
    },
    "audit_events": {
        "total": 2500,
        "by_severity": {
            "CRITICAL": 1200,
            "WARNING": 800,
            "INFO": 500
        },
        "by_type": {
            "REDACTION": 1200,
            "VALIDATION_ERROR": 800,
            "PERSISTENCE": 500
        }
    }
}
```

#### 4. Performance Metrics
```python
GET /api/metrics/performance?time_range=24h
Response: {
    "time_range": "24h",
    "throughput": {
        "records_per_second": 1450.5,
        "mb_per_second": 12.3,
        "peak_records_per_second": 2100.0
    },
    "latency": {
        "avg_processing_time_ms": 45.2,
        "p50_ms": 38.0,
        "p95_ms": 120.0,
        "p99_ms": 250.0
    },
    "file_processing": {
        "total_files": 25,
        "avg_file_size_mb": 15.5,
        "total_data_processed_mb": 387.5
    },
    "memory": {
        "avg_peak_memory_mb": 85.3,
        "max_peak_memory_mb": 120.0
    }
}
```

#### 5. Audit Logs
```python
GET /api/audit-logs?limit=100&offset=0&severity=CRITICAL&start_date=2025-01-01
Response: {
    "total": 1250,
    "limit": 100,
    "offset": 0,
    "logs": [
        {
            "audit_id": "uuid",
            "event_type": "REDACTION",
            "event_timestamp": "2025-01-15T10:30:00Z",
            "severity": "CRITICAL",
            "record_id": "MRN001",
            "source_adapter": "csv_ingester",
            "details": {...}
        },
        ...
    ]
}
```

#### 6. Redaction Logs
```python
GET /api/redaction-logs?field_name=ssn&time_range=24h
Response: {
    "total": 1200,
    "logs": [
        {
            "log_id": "uuid",
            "field_name": "ssn",
            "timestamp": "2025-01-15T10:30:00Z",
            "rule_triggered": "SSN_PATTERN",
            "record_id": "MRN001",
            "source_adapter": "csv_ingester",
            "ingestion_id": "uuid",
            "original_hash": "sha256-hash",
            "redacted_value": "***-**-****"
        },
        ...
    ]
}
```

#### 7. Circuit Breaker Status
```python
GET /api/circuit-breaker/status
Response: {
    "status": "closed" | "open" | "half_open",
    "failure_rate": 0.012,
    "threshold": 0.10,
    "total_requests": 125000,
    "total_failures": 1500,
    "last_state_change": "2025-01-15T09:00:00Z",
    "statistics": {
        "window_start": "2025-01-15T10:00:00Z",
        "window_end": "2025-01-15T11:00:00Z",
        "requests_in_window": 5000,
        "failures_in_window": 60
    }
}
```

#### 8. Real-time Updates (WebSocket)
```python
WS /ws/realtime
Messages: {
    "type": "metrics_update",
    "data": {
        "ingestions": {...},
        "redactions": {...},
        "circuit_breaker": {...}
    }
}
```

### Service Layer Design

Following Hexagonal Architecture, services are pure domain logic:

```python
# src/dashboard/services/metrics_aggregator.py
class MetricsAggregator:
    """Aggregates metrics from multiple data sources."""
    
    def __init__(self, storage: StoragePort):
        self.storage = storage
    
    async def get_overview_metrics(
        self, 
        time_range: str
    ) -> OverviewMetrics:
        """Aggregate overview metrics from all sources."""
        # Query logs, audit_log, and calculate aggregations
        pass
    
    async def get_security_metrics(
        self,
        time_range: str
    ) -> SecurityMetrics:
        """Get security-specific metrics."""
        pass
```

## Frontend Design (Next.js)

### Technology Stack

- **Framework**: Next.js 14+ (App Router, React Server Components)
- **Language**: TypeScript (strict mode)
- **UI Components**: Shadcn UI + Radix UI primitives
- **Styling**: Tailwind CSS (mobile-first, responsive)
- **State Management**: React Server Components + `nuqs` for URL state
- **Charts**: Recharts or Chart.js (beautiful, accessible)
- **Real-time**: WebSocket client for live updates
- **Forms**: React Hook Form + Zod validation

### Project Structure

```
dashboard-frontend/
├── app/
│   ├── layout.tsx              # Root layout
│   ├── page.tsx                # Overview dashboard (home)
│   ├── (dashboard)/
│   │   ├── security/
│   │   │   └── page.tsx       # Security metrics page
│   │   ├── performance/
│   │   │   └── page.tsx       # Performance metrics page
│   │   ├── audit/
│   │   │   └── page.tsx       # Audit log explorer
│   │   └── circuit-breaker/
│   │       └── page.tsx       # Circuit breaker status
│   ├── api/
│   │   └── health/
│   │       └── route.ts       # Health check proxy (optional)
│   └── globals.css              # Global styles
├── components/
│   ├── ui/                     # Shadcn UI components
│   ├── dashboard/
│   │   ├── overview-card.tsx
│   │   ├── metrics-card.tsx
│   │   ├── chart-card.tsx
│   │   └── real-time-indicator.tsx
│   ├── security/
│   │   ├── redaction-chart.tsx
│   │   ├── audit-log-table.tsx
│   │   └── security-summary.tsx
│   ├── performance/
│   │   ├── throughput-chart.tsx
│   │   ├── latency-chart.tsx
│   │   └── memory-chart.tsx
│   └── circuit-breaker/
│       └── circuit-breaker-status.tsx
├── lib/
│   ├── api.ts                  # API client (typed)
│   ├── websocket.ts            # WebSocket client
│   └── utils.ts                # Utilities
├── types/
│   ├── api.ts                  # API response types
│   └── metrics.ts              # Metrics types
└── public/
    └── ...                     # Static assets
```

### Key UI Components

#### 1. Overview Dashboard
- **Hero Metrics Cards**: Total ingestions, success rate, total records, redactions
- **Real-time Activity Feed**: Latest ingestion events, circuit breaker status
- **Quick Stats Grid**: Success rate trend, redaction trend, throughput trend
- **Time Range Selector**: 1h, 24h, 7d, 30d, custom range

#### 2. Security Metrics Page
- **Redaction Summary**: Total redactions, breakdown by field/rule/adapter
- **Redaction Trend Chart**: Time-series chart of redactions over time
- **Redaction Distribution**: Pie/bar charts by field, rule, adapter
- **Audit Log Table**: Filterable, sortable table with pagination
- **Security Alerts**: Critical events, anomalies

#### 3. Performance Metrics Page
- **Throughput Chart**: Records/sec, MB/sec over time
- **Latency Distribution**: P50, P95, P99 latency metrics
- **File Processing Stats**: Total files, avg size, total data processed
- **Memory Usage**: Peak memory over time
- **Performance Alerts**: Slow processing, high memory usage

#### 4. Circuit Breaker Status
- **Status Indicator**: Visual indicator (green/yellow/red)
- **Failure Rate Gauge**: Current failure rate vs threshold
- **Statistics Table**: Total requests, failures, window stats
- **State History**: Timeline of state changes

#### 5. Audit Log Explorer
- **Advanced Filters**: Severity, event type, date range, record ID
- **Search**: Full-text search across audit logs
- **Export**: CSV/JSON export functionality
- **Detail View**: Expandable rows with full event details

### Design Principles

1. **Mobile-First**: Responsive design, works on all screen sizes
2. **Accessibility**: WCAG 2.1 AA compliant, keyboard navigation, screen reader support
3. **Performance**: Server Components where possible, minimal client-side JS
4. **Real-time Updates**: WebSocket for live metrics (optional, can fallback to polling)
5. **Error Handling**: Graceful error states, retry mechanisms
6. **Loading States**: Skeleton loaders, progressive enhancement

## Security Considerations

### Authentication & Authorization

- **JWT Tokens**: Optional authentication for production
- **Role-Based Access**: Admin, viewer roles (future enhancement)
- **API Keys**: For programmatic access (optional)

### Data Security

- **No PII in Responses**: Dashboard never exposes original PII values
- **Hashed Values Only**: Only show hashes for audit trail verification
- **Rate Limiting**: Prevent API abuse
- **Input Validation**: All inputs validated with Pydantic
- **SQL Injection Prevention**: Use existing parameterized queries

### Audit Trail

- **Dashboard Access Logging**: Log all dashboard API access
- **User Actions**: Log user interactions (filter changes, exports)
- **Compliance**: Maintain HIPAA/GDPR compliance

## Implementation Plan

### Phase 1: Foundation (Week 1-2)

1. **Backend Setup**
   - [ ] Create `src/dashboard/` directory structure
   - [ ] Set up FastAPI app with CORS, middleware
   - [ ] Create Pydantic models for all API responses
   - [ ] Implement health check endpoint
   - [ ] Set up dependency injection for storage adapters

2. **Frontend Setup**
   - [ ] Initialize Next.js 14+ project with TypeScript
   - [ ] Install and configure Shadcn UI
   - [ ] Set up Tailwind CSS
   - [ ] Create basic layout and routing structure
   - [ ] Set up API client with TypeScript types

### Phase 2: Core Metrics (Week 3-4)

1. **Backend Services**
   - [ ] Implement `MetricsAggregator` service
   - [ ] Implement `SecurityMetricsService`
   - [ ] Implement `PerformanceMetricsService`
   - [ ] Create SQL queries for metrics aggregation
   - [ ] Add caching layer (Redis or in-memory) for performance

2. **API Endpoints**
   - [ ] Implement `/api/metrics/overview`
   - [ ] Implement `/api/metrics/security`
   - [ ] Implement `/api/metrics/performance`
   - [ ] Add error handling and validation
   - [ ] Write API tests

3. **Frontend Components**
   - [ ] Create overview dashboard page
   - [ ] Build metrics cards components
   - [ ] Implement time range selector
   - [ ] Add loading and error states

### Phase 3: Advanced Features (Week 5-6)

1. **Audit & Logging**
   - [ ] Implement `/api/audit-logs` endpoint
   - [ ] Implement `/api/redaction-logs` endpoint
   - [ ] Add filtering, pagination, sorting
   - [ ] Create audit log explorer UI
   - [ ] Add export functionality

2. **Circuit Breaker**
   - [ ] Implement `/api/circuit-breaker/status` endpoint
   - [ ] Create circuit breaker status UI
   - [ ] Add real-time status updates

3. **Charts & Visualizations**
   - [ ] Integrate charting library (Recharts)
   - [ ] Create time-series charts for trends
   - [ ] Create distribution charts (pie, bar)
   - [ ] Add interactive tooltips and legends

### Phase 4: Real-time & Polish (Week 7-8)

1. **Real-time Updates**
   - [ ] Implement WebSocket endpoint
   - [ ] Create WebSocket client in frontend
   - [ ] Add real-time metrics updates
   - [ ] Implement connection management (reconnect, fallback)

2. **UI/UX Polish**
   - [ ] Add dark mode support
   - [ ] Improve responsive design
   - [ ] Add animations and transitions
   - [ ] Optimize performance (lazy loading, code splitting)
   - [ ] Add accessibility features

3. **Testing & Documentation**
   - [ ] Write comprehensive tests (backend + frontend)
   - [ ] Add API documentation (OpenAPI/Swagger)
   - [ ] Create user documentation
   - [ ] Performance testing and optimization

### Phase 5: Production Readiness (Week 9-10)

1. **Security Hardening**
   - [ ] Implement authentication (if needed)
   - [ ] Add rate limiting
   - [ ] Security audit
   - [ ] Penetration testing

2. **Deployment**
   - [ ] Docker containerization
   - [ ] Docker Compose for local development
   - [ ] CI/CD pipeline setup
   - [ ] Production deployment guide

3. **Monitoring & Observability**
   - [ ] Add application logging
   - [ ] Error tracking (Sentry or similar)
   - [ ] Performance monitoring
   - [ ] Health check endpoints for monitoring tools

## Technical Decisions

### Why FastAPI?
- **Async Support**: Handle concurrent requests efficiently
- **Type Safety**: Pydantic V2 provides runtime validation
- **Auto Documentation**: OpenAPI/Swagger docs generated automatically
- **Performance**: One of the fastest Python frameworks
- **Ecosystem**: Large community, many plugins

### Why Next.js 14+ App Router?
- **Server Components**: Reduce client-side JavaScript
- **TypeScript**: Type safety across the stack
- **Performance**: Built-in optimizations (image, font, etc.)
- **Developer Experience**: Excellent tooling, hot reload
- **SEO**: Server-side rendering (if needed for public pages)

### Why Shadcn UI?
- **Accessibility**: Built on Radix UI primitives (accessible by default)
- **Customizable**: Copy components into project, full control
- **Modern**: Beautiful, modern design system
- **TypeScript**: Fully typed components

### Why WebSocket for Real-time?
- **Low Latency**: Push updates immediately
- **Efficient**: No polling overhead
- **Scalable**: Can handle many concurrent connections
- **Fallback**: Can fallback to polling if WebSocket unavailable

## Success Metrics

1. **Performance**
   - API response time < 200ms (p95)
   - Dashboard load time < 2s
   - Real-time update latency < 500ms

2. **Reliability**
   - 99.9% uptime
   - Graceful error handling
   - No data loss

3. **Usability**
   - Intuitive navigation
   - Responsive on all devices
   - Accessible (WCAG 2.1 AA)

4. **Security**
   - No PII exposure
   - Secure authentication (if implemented)
   - Audit trail for all actions

## Future Enhancements

1. **Advanced Analytics**
   - Machine learning for anomaly detection
   - Predictive metrics
   - Custom report builder

2. **Multi-tenant Support**
   - Tenant isolation
   - Per-tenant dashboards
   - Role-based access control

3. **Alerting**
   - Email/Slack notifications
   - Custom alert rules
   - Alert history

4. **Export & Reporting**
   - Scheduled reports
   - PDF generation
   - Custom report templates

5. **Integration**
   - Grafana integration
   - Prometheus metrics
   - External monitoring tools

---

**Last Updated**: January 2025

**Status**: Design Document - Ready for Implementation

