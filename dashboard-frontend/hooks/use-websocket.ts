'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import {
  WebSocketClient,
  type WebSocketMessage,
  type WebSocketClientOptions,
} from '@/lib/websocket';
import type {
  OverviewMetrics,
  SecurityMetrics,
  PerformanceMetrics,
  CircuitBreakerStatus,
} from '@/types/api';

export interface UseWebSocketReturn {
  isConnected: boolean;
  overviewMetrics: OverviewMetrics | null;
  securityMetrics: SecurityMetrics | null;
  performanceMetrics: PerformanceMetrics | null;
  circuitBreakerStatus: CircuitBreakerStatus | null;
  error: Error | null;
  connect: () => void;
  disconnect: () => void;
}

export function useWebSocket(
  timeRange: string = '24h',
  options?: Omit<WebSocketClientOptions, 'timeRange' | 'onMessage'>
): UseWebSocketReturn {
  const clientRef = useRef<WebSocketClient | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [overviewMetrics, setOverviewMetrics] = useState<OverviewMetrics | null>(null);
  const [securityMetrics, setSecurityMetrics] = useState<SecurityMetrics | null>(null);
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetrics | null>(null);
  const [circuitBreakerStatus, setCircuitBreakerStatus] = useState<CircuitBreakerStatus | null>(null);
  const [error, setError] = useState<Error | null>(null);

  const handleMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'connection':
        setIsConnected(true);
        setError(null);
        break;
      
      case 'metrics_update':
        if (message.data) {
          setOverviewMetrics(message.data as OverviewMetrics);
        }
        break;
      
      case 'security_metrics_update':
        if (message.data) {
          setSecurityMetrics(message.data as SecurityMetrics);
        }
        break;
      
      case 'performance_metrics_update':
        if (message.data) {
          setPerformanceMetrics(message.data as PerformanceMetrics);
        }
        break;
      
      case 'circuit_breaker_update':
        if (message.data) {
          setCircuitBreakerStatus(message.data as CircuitBreakerStatus);
        }
        break;
      
      case 'error':
        setError(new Error(message.error || 'Unknown error'));
        break;
      
      default:
        // Ignore heartbeat and other messages
        break;
    }
  }, []);

  const connect = useCallback(() => {
    if (clientRef.current?.isConnected) {
      return;
    }

    const client = new WebSocketClient({
      timeRange,
      ...options,
      onConnect: () => {
        setIsConnected(true);
        setError(null);
        options?.onConnect?.();
      },
      onDisconnect: () => {
        setIsConnected(false);
        options?.onDisconnect?.();
      },
      onError: (err) => {
        setError(err);
        options?.onError?.(err);
      },
      onMessage: handleMessage,
    });

    clientRef.current = client;
    client.connect();
  }, [timeRange, handleMessage, options]);

  const disconnect = useCallback(() => {
    if (clientRef.current) {
      clientRef.current.disconnect();
      clientRef.current = null;
      setIsConnected(false);
    }
  }, []);

  useEffect(() => {
    // Auto-connect on mount
    connect();

    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    overviewMetrics,
    securityMetrics,
    performanceMetrics,
    circuitBreakerStatus,
    error,
    connect,
    disconnect,
  };
}

