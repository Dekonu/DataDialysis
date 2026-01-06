import { Suspense } from 'react';
import { api } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { MetricsCard } from '@/components/dashboard/metrics-card';
import { TimeRangeSelector } from '@/components/dashboard/time-range-selector';
import type { TimeRange } from '@/types/api';

async function HealthStatus() {
  let health;
  let healthError: string | null = null;

  try {
    health = await api.health();
  } catch (err) {
    healthError = err instanceof Error ? err.message : 'Failed to fetch health status';
  }

  if (healthError) {
    return (
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle>Connection Error</CardTitle>
          <CardDescription>Unable to connect to the API</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-destructive">{healthError}</p>
          <p className="text-sm text-muted-foreground mt-2">
            Make sure the backend API is running on{' '}
            {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}
          </p>
        </CardContent>
      </Card>
    );
  }

  if (!health) {
    return null;
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <Card>
        <CardHeader>
          <CardTitle>API Status</CardTitle>
          <CardDescription>Backend API health</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Status</span>
            <Badge
              variant={
                health.status === 'healthy'
                  ? 'default'
                  : health.status === 'degraded'
                  ? 'secondary'
                  : 'destructive'
              }
            >
              {health.status}
            </Badge>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Database</CardTitle>
          <CardDescription>Database connection status</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Status</span>
              <Badge
                variant={health.database.status === 'connected' ? 'default' : 'destructive'}
              >
                {health.database.status}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Type</span>
              <span className="text-sm text-muted-foreground">{health.database.type}</span>
            </div>
            {health.database.response_time_ms && (
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Response Time</span>
                <span className="text-sm text-muted-foreground">
                  {health.database.response_time_ms.toFixed(2)}ms
                </span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Version</CardTitle>
          <CardDescription>API version information</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Version</span>
            <span className="text-sm text-muted-foreground">{health.version}</span>
          </div>
          <div className="flex items-center justify-between mt-2">
            <span className="text-sm font-medium">Last Updated</span>
            <span className="text-sm text-muted-foreground">
              {new Date(health.timestamp).toLocaleString()}
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

interface DashboardContentProps {
  timeRange: TimeRange;
}

async function DashboardContent({ timeRange }: DashboardContentProps) {
  let metrics;
  let error: string | null = null;

  try {
    metrics = await api.metrics.overview(timeRange);
  } catch (err) {
    error = err instanceof Error ? err.message : 'Failed to fetch metrics';
  }

  if (error) {
    return (
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle>Error Loading Metrics</CardTitle>
          <CardDescription>Unable to fetch metrics from the API</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-destructive">{error}</p>
          <p className="text-sm text-muted-foreground mt-2">
            Make sure the backend API is running on{' '}
            {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}
          </p>
        </CardContent>
      </Card>
    );
  }

  if (!metrics) {
    return (
      <Card>
        <CardContent className="pt-6">
          <p className="text-muted-foreground">No metrics available</p>
        </CardContent>
      </Card>
    );
  }

  const successRate = metrics.ingestions.success_rate;
  const recordSuccessRate =
    metrics.records.total_processed > 0
      ? metrics.records.total_successful / metrics.records.total_processed
      : 0;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricsCard
          title="Total Ingestions"
          value={metrics.ingestions.total}
          description={`${metrics.ingestions.successful} successful, ${metrics.ingestions.failed} failed`}
          trend={successRate}
          trendLabel="success rate"
          variant={successRate >= 0.95 ? 'success' : successRate >= 0.8 ? 'warning' : 'destructive'}
          formatType="number"
        />

        <MetricsCard
          title="Records Processed"
          value={metrics.records.total_processed}
          description={`${metrics.records.total_successful} successful, ${metrics.records.total_failed} failed`}
          trend={recordSuccessRate}
          trendLabel="success rate"
          variant={
            recordSuccessRate >= 0.95 ? 'success' : recordSuccessRate >= 0.8 ? 'warning' : 'destructive'
          }
          formatType="number"
        />

        <MetricsCard
          title="PII Redactions"
          value={metrics.redactions.total}
          description="Total redactions performed"
          variant="default"
          formatType="number"
        />

        <MetricsCard
          title="Circuit Breaker"
          value={metrics.circuit_breaker?.status || 'N/A'}
          description={
            metrics.circuit_breaker?.failure_rate !== null &&
            metrics.circuit_breaker?.failure_rate !== undefined
              ? `${(metrics.circuit_breaker.failure_rate * 100).toFixed(1)}% failure rate`
              : 'Status unknown'
          }
          variant={
            metrics.circuit_breaker?.status === 'closed'
              ? 'success'
              : metrics.circuit_breaker?.status === 'half_open'
              ? 'warning'
              : 'destructive'
          }
          formatType="plain"
        />
      </div>

      {/* Additional metrics section */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Ingestion Metrics</CardTitle>
            <CardDescription>Detailed ingestion statistics</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Success Rate</span>
                <span className="text-sm font-bold">
                  {(successRate * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Successful</span>
                <span className="text-sm text-muted-foreground">
                  {metrics.ingestions.successful.toLocaleString()}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Failed</span>
                <span className="text-sm text-muted-foreground">
                  {metrics.ingestions.failed.toLocaleString()}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Record Processing</CardTitle>
            <CardDescription>Record processing statistics</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Success Rate</span>
                <span className="text-sm font-bold">
                  {(recordSuccessRate * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Successful</span>
                <span className="text-sm text-muted-foreground">
                  {metrics.records.total_successful.toLocaleString()}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Failed</span>
                <span className="text-sm text-muted-foreground">
                  {metrics.records.total_failed.toLocaleString()}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Redaction Summary</CardTitle>
            <CardDescription>PII redaction statistics</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Total Redactions</span>
                <span className="text-sm font-bold">
                  {metrics.redactions.total.toLocaleString()}
                </span>
              </div>
              {Object.keys(metrics.redactions.by_field).length > 0 && (
                <div className="mt-4">
                  <p className="text-xs font-medium mb-2">By Field:</p>
                  <div className="space-y-1">
                    {Object.entries(metrics.redactions.by_field)
                      .slice(0, 3)
                      .map(([field, count]) => (
                        <div key={field} className="flex items-center justify-between text-xs">
                          <span className="text-muted-foreground">{field}</span>
                          <span>{count.toLocaleString()}</span>
                        </div>
                      ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default async function HomePage({
  searchParams,
}: {
  searchParams: { timeRange?: TimeRange };
}) {
  const timeRange = (searchParams.timeRange as TimeRange) || '24h';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Dashboard Overview</h2>
          <p className="text-muted-foreground">
            Monitor the health and performance of your Data-Dialysis pipeline
          </p>
        </div>
        <Suspense fallback={<div className="w-[180px] h-10 bg-muted animate-pulse rounded-md" />}>
          <TimeRangeSelector defaultValue={timeRange} />
        </Suspense>
      </div>

      {/* Health Status Section */}
      <div>
        <h3 className="text-xl font-semibold mb-4">System Health</h3>
        <Suspense
          fallback={
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {[...Array(3)].map((_, i) => (
                <Card key={i} className="animate-pulse">
                  <CardHeader>
                    <div className="h-4 bg-muted rounded w-24" />
                  </CardHeader>
                  <CardContent>
                    <div className="h-6 bg-muted rounded w-32" />
                  </CardContent>
                </Card>
              ))}
            </div>
          }
        >
          <HealthStatus />
        </Suspense>
      </div>

      {/* Metrics Section */}
      <div>
        <h3 className="text-xl font-semibold mb-4">Metrics</h3>
        <Suspense
          fallback={
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              {[...Array(4)].map((_, i) => (
                <Card key={i} className="animate-pulse">
                  <CardHeader>
                    <div className="h-4 bg-muted rounded w-24" />
                  </CardHeader>
                  <CardContent>
                    <div className="h-8 bg-muted rounded w-32 mb-2" />
                    <div className="h-3 bg-muted rounded w-48" />
                  </CardContent>
                </Card>
              ))}
            </div>
          }
        >
          <DashboardContent timeRange={timeRange} />
        </Suspense>
      </div>
    </div>
  );
}
