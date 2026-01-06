import { Suspense } from 'react';
import { api } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { AlertCircle, CheckCircle2, AlertTriangle } from 'lucide-react';

async function CircuitBreakerContent() {
  let status;
  let error: string | null = null;

  try {
    status = await api.circuitBreaker.status();
  } catch (err) {
    error = err instanceof Error ? err.message : 'Failed to fetch circuit breaker status';
  }

  if (error) {
    return (
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle>Error Loading Circuit Breaker Status</CardTitle>
          <CardDescription>Unable to fetch circuit breaker status from the API</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-destructive">{error}</p>
        </CardContent>
      </Card>
    );
  }

  if (!status) {
    return (
      <Card>
        <CardContent className="pt-6">
          <p className="text-muted-foreground">Circuit breaker status unavailable</p>
        </CardContent>
      </Card>
    );
  }

  const statusColor = status.is_open ? 'destructive' : 'default';
  const statusIcon = status.is_open ? (
    <AlertCircle className="h-5 w-5" />
  ) : (
    <CheckCircle2 className="h-5 w-5" />
  );
  const statusText = status.is_open ? 'OPEN' : 'CLOSED';

  // Calculate percentage for gauge
  const failureRatePercent = status.failure_rate ?? 0;
  const thresholdPercent = status.threshold ?? 100;
  const gaugePercentage = Math.min((failureRatePercent / thresholdPercent) * 100, 100);

  return (
    <div className="space-y-6">
      {/* Status Card */}
      <Card>
        <CardHeader>
          <CardTitle>Circuit Breaker Status</CardTitle>
          <CardDescription>Current circuit breaker state and failure metrics</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <div
              className={`flex items-center gap-2 p-4 rounded-lg border-2 ${
                status.is_open
                  ? 'border-destructive bg-destructive/10'
                  : 'border-green-500 bg-green-500/10'
              }`}
            >
              {statusIcon}
              <div>
                <div className="text-sm font-medium text-muted-foreground">Status</div>
                <div className="text-2xl font-bold">{statusText}</div>
              </div>
            </div>

            <div className="flex-1">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Failure Rate</span>
                <span className="text-sm font-bold">
                  {failureRatePercent.toFixed(2)}% / {thresholdPercent.toFixed(2)}%
                </span>
              </div>
              <div className="w-full bg-muted rounded-full h-4">
                <div
                  className={`h-4 rounded-full transition-all ${
                    gaugePercentage >= 100
                      ? 'bg-destructive'
                      : gaugePercentage >= 80
                      ? 'bg-yellow-500'
                      : 'bg-green-500'
                  }`}
                  style={{ width: `${gaugePercentage}%` }}
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Statistics Table */}
      <Card>
        <CardHeader>
          <CardTitle>Statistics</CardTitle>
          <CardDescription>Circuit breaker operational metrics</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableBody>
              <TableRow>
                <TableHead className="w-[200px]">Total Processed</TableHead>
                <TableCell>{status.total_processed.toLocaleString()}</TableCell>
              </TableRow>
              <TableRow>
                <TableHead>Total Failures</TableHead>
                <TableCell>
                  <span className={status.total_failures > 0 ? 'text-destructive' : ''}>
                    {status.total_failures.toLocaleString()}
                  </span>
                </TableCell>
              </TableRow>
              <TableRow>
                <TableHead>Failure Rate</TableHead>
                <TableCell>
                  <Badge
                    variant={
                      failureRatePercent >= thresholdPercent
                        ? 'destructive'
                        : failureRatePercent >= thresholdPercent * 0.8
                        ? 'secondary'
                        : 'default'
                    }
                  >
                    {failureRatePercent.toFixed(2)}%
                  </Badge>
                </TableCell>
              </TableRow>
              <TableRow>
                <TableHead>Threshold</TableHead>
                <TableCell>{thresholdPercent.toFixed(2)}%</TableCell>
              </TableRow>
              <TableRow>
                <TableHead>Window Size</TableHead>
                <TableCell>{status.window_size.toLocaleString()}</TableCell>
              </TableRow>
              <TableRow>
                <TableHead>Records in Window</TableHead>
                <TableCell>{status.records_in_window.toLocaleString()}</TableCell>
              </TableRow>
              <TableRow>
                <TableHead>Failures in Window</TableHead>
                <TableCell>
                  <span
                    className={status.failures_in_window > 0 ? 'text-destructive font-medium' : ''}
                  >
                    {status.failures_in_window.toLocaleString()}
                  </span>
                </TableCell>
              </TableRow>
              <TableRow>
                <TableHead>Min Records Before Check</TableHead>
                <TableCell>{status.min_records_before_check.toLocaleString()}</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Status Explanation */}
      <Card>
        <CardHeader>
          <CardTitle>Status Explanation</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <p>
              <strong>CLOSED:</strong> Circuit breaker is allowing requests. System is operating
              normally.
            </p>
            <p>
              <strong>OPEN:</strong> Circuit breaker has opened due to high failure rate. Requests
              are being blocked to prevent further failures.
            </p>
            <p className="text-muted-foreground mt-4">
              The circuit breaker monitors the failure rate over a sliding window of{' '}
              {status.window_size} records. When the failure rate exceeds{' '}
              {thresholdPercent.toFixed(2)}%, the circuit opens to protect the system.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default async function CircuitBreakerPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Circuit Breaker</h2>
        <p className="text-muted-foreground">
          Monitor circuit breaker status and failure metrics
        </p>
      </div>

      <Suspense
        fallback={
          <Card>
            <CardContent className="pt-6">
              <div className="animate-pulse space-y-4">
                <div className="h-4 bg-muted rounded w-3/4" />
                <div className="h-4 bg-muted rounded w-1/2" />
                <div className="h-4 bg-muted rounded w-2/3" />
              </div>
            </CardContent>
          </Card>
        }
      >
        <CircuitBreakerContent />
      </Suspense>
    </div>
  );
}

