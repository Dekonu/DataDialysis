# Data-Dialysis Dashboard - Quick Start Guide

## Overview

This guide provides a quick overview of the dashboard project and how to get started.

## Repository Structure Decision

**✅ Recommendation: Same Repository (Monorepo)**

The dashboard will be built in the same repository as the main Data-Dialysis pipeline, following Hexagonal Architecture principles where the dashboard acts as a presentation layer adapter.

## Architecture Summary

### Backend (FastAPI)
- **Location:** `src/dashboard/`
- **Framework:** FastAPI with async support
- **Validation:** Pydantic V2
- **Database:** Uses existing storage adapters (DuckDB/PostgreSQL)

### Frontend (Next.js)
- **Location:** `dashboard-frontend/`
- **Framework:** Next.js 14+ App Router
- **Language:** TypeScript
- **UI:** Shadcn UI + Tailwind CSS
- **Charts:** Recharts

## Key Features

1. **Overview Dashboard**
   - Total ingestions, success rate, records processed
   - Real-time activity feed
   - Quick stats and trends

2. **Security Metrics**
   - Redaction summary and trends
   - Audit log explorer
   - Security alerts

3. **Performance Metrics**
   - Throughput and latency charts
   - File processing stats
   - Memory usage

4. **Circuit Breaker Status**
   - Visual status indicator
   - Failure rate gauge
   - Statistics and history

5. **Real-time Updates**
   - WebSocket for live metrics
   - Automatic refresh
   - Fallback to polling

## Quick Start

### Prerequisites
```bash
# Python 3.11+
python --version

# Node.js 18+
node --version

# Existing Data-Dialysis setup
# Database configured (DuckDB or PostgreSQL)
```

### Backend Setup
```bash
# Activate virtual environment
.\Scripts\Activate.ps1  # Windows
# or
source venv/bin/activate  # Linux/Mac

# Install additional dependencies (if needed)
pip install fastapi uvicorn websockets

# Run backend
cd src/dashboard
uvicorn api.main:app --reload --port 8000
```

### Frontend Setup
```bash
# Navigate to frontend directory
cd dashboard-frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### Access Dashboard
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/api/docs

## API Endpoints

### Core Endpoints
- `GET /api/health` - Health check
- `GET /api/metrics/overview` - Overview metrics
- `GET /api/metrics/security` - Security metrics
- `GET /api/metrics/performance` - Performance metrics
- `GET /api/audit-logs` - Audit log explorer
- `GET /api/redaction-logs` - Redaction log explorer
- `GET /api/circuit-breaker/status` - Circuit breaker status
- `WS /ws/realtime` - WebSocket for real-time updates

## Implementation Phases

1. **Phase 1 (Week 1-2):** Foundation
   - Backend and frontend setup
   - Basic health check
   - Project structure

2. **Phase 2 (Week 3-4):** Core Metrics
   - Metrics aggregation services
   - API endpoints
   - Overview dashboard

3. **Phase 3 (Week 5-6):** Advanced Features
   - Audit log explorer
   - Circuit breaker UI
   - Charts and visualizations

4. **Phase 4 (Week 7-8):** Real-time & Polish
   - WebSocket implementation
   - UI/UX improvements
   - Performance optimization

5. **Phase 5 (Week 9-10):** Production Readiness
   - Security hardening
   - Deployment setup
   - Monitoring and observability

## Documentation

- **[DASHBOARD_DESIGN.md](DASHBOARD_DESIGN.md)** - Comprehensive design document
- **[DASHBOARD_IMPLEMENTATION_PLAN.md](DASHBOARD_IMPLEMENTATION_PLAN.md)** - Detailed implementation plan
- **[DASHBOARD_QUICK_START.md](DASHBOARD_QUICK_START.md)** - This file

## Next Steps

1. Review the [Design Document](DASHBOARD_DESIGN.md)
2. Review the [Implementation Plan](DASHBOARD_IMPLEMENTATION_PLAN.md)
3. Start with Phase 1 tasks
4. Follow the plan step-by-step

## Support

For questions or issues:
1. Check the documentation
2. Review existing codebase patterns
3. Follow Hexagonal Architecture principles
4. Maintain security-first approach

---

**Status:** Ready to Begin Implementation

