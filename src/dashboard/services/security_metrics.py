"""Security metrics service.

This service provides security-specific metrics including redaction statistics
and audit event summaries.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from src.domain.ports import Result, StoragePort
from src.dashboard.models.metrics import (
    SecurityMetrics,
    SecurityRedactions,
    AuditEventSummary,
    RedactionTrendPoint
)
from src.dashboard.services.connection_helper import get_db_connection

logger = logging.getLogger(__name__)


class SecurityMetricsService:
    """Service for security-specific metrics."""
    
    def __init__(self, storage: StoragePort):
        """Initialize security metrics service.
        
        Parameters:
            storage: Storage adapter instance
        """
        self.storage = storage
    
    def _parse_time_range(self, time_range: str, end_time: datetime) -> datetime:
        """Parse time range string to start time."""
        time_range = time_range.lower()
        
        if time_range.endswith('h'):
            hours = int(time_range[:-1])
            return end_time - timedelta(hours=hours)
        elif time_range.endswith('d'):
            days = int(time_range[:-1])
            return end_time - timedelta(days=days)
        else:
            logger.warning(f"Unknown time range format: {time_range}, defaulting to 7d")
            return end_time - timedelta(days=7)
    
    def get_security_metrics(
        self,
        time_range: str = "7d"
    ) -> Result[SecurityMetrics]:
        """Get security metrics for the specified time range.
        
        Parameters:
            time_range: Time range string (1h, 24h, 7d, 30d)
            
        Returns:
            Result[SecurityMetrics]: Security metrics or error
        """
        try:
            end_time = datetime.now(timezone.utc).replace(tzinfo=None)
            start_time = self._parse_time_range(time_range, end_time)
            
            # Get redaction metrics
            redactions = self._get_redaction_metrics(start_time, end_time)
            
            # Get audit event metrics
            audit_events = self._get_audit_event_metrics(start_time, end_time)
            
            metrics = SecurityMetrics(
                time_range=time_range,
                redactions=redactions,
                audit_events=audit_events
            )
            
            return Result.success_result(metrics)
            
        except Exception as e:
            logger.error(f"Failed to get security metrics: {str(e)}", exc_info=True)
            return Result.failure_result(
                e,
                error_type="MetricsError"
            )
    
    def _get_redaction_metrics(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> SecurityRedactions:
        """Get redaction metrics with trend data.
        
        Parameters:
            start_time: Start time
            end_time: End time
            
        Returns:
            SecurityRedactions: Redaction metrics with trend
        """
        try:
            if not hasattr(self.storage, '_get_connection'):
                return SecurityRedactions(total=0)
            
            with get_db_connection(self.storage) as conn:
                if conn is None:
                    return SecurityRedactions(total=0)
                
                # Get total count
                total_query = """
                    SELECT COUNT(*) as total
                    FROM logs
                    WHERE timestamp >= ? AND timestamp <= ?
                """
                total_result = conn.execute(total_query, [start_time, end_time]).fetchone()
                total = total_result[0] if total_result and total_result[0] else 0
                
                # Get by rule
                rule_query = """
                    SELECT rule_triggered, COUNT(*) as count
                    FROM logs
                    WHERE timestamp >= ? AND timestamp <= ?
                    GROUP BY rule_triggered
                """
                rule_results = conn.execute(rule_query, [start_time, end_time]).fetchall()
                by_rule = {row[0]: row[1] for row in rule_results if row[0] and row[1]}
                
                # Get by adapter
                adapter_query = """
                    SELECT source_adapter, COUNT(*) as count
                    FROM logs
                    WHERE timestamp >= ? AND timestamp <= ?
                    GROUP BY source_adapter
                """
                adapter_results = conn.execute(adapter_query, [start_time, end_time]).fetchall()
                by_adapter = {row[0]: row[1] for row in adapter_results if row[0] and row[1]}
                
                # Get trend data (daily counts)
                trend_query = """
                    SELECT 
                        DATE(timestamp) as date,
                        COUNT(*) as count
                    FROM logs
                    WHERE timestamp >= ? AND timestamp <= ?
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                """
                trend_results = conn.execute(trend_query, [start_time, end_time]).fetchall()
                trend = [
                    RedactionTrendPoint(date=str(row[0]), count=row[1])
                    for row in trend_results
                    if row[0] and row[1]
                ]
                
                return SecurityRedactions(
                    total=total,
                    by_rule=by_rule,
                    by_adapter=by_adapter,
                    trend=trend
                )
            
        except Exception as e:
            logger.warning(f"Error getting redaction metrics: {str(e)}")
            return SecurityRedactions(total=0)
    
    def _get_audit_event_metrics(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> AuditEventSummary:
        """Get audit event metrics.
        
        Parameters:
            start_time: Start time
            end_time: End time
            
        Returns:
            AuditEventSummary: Audit event statistics
        """
        try:
            if not hasattr(self.storage, '_get_connection'):
                return AuditEventSummary(total=0)
            
            with get_db_connection(self.storage) as conn:
                if conn is None:
                    return AuditEventSummary(total=0)
                
                # Get total count
                total_query = """
                    SELECT COUNT(*) as total
                    FROM audit_log
                    WHERE event_timestamp >= ? AND event_timestamp <= ?
                """
                total_result = conn.execute(total_query, [start_time, end_time]).fetchone()
                total = total_result[0] if total_result and total_result[0] else 0
                
                # Get by severity
                severity_query = """
                    SELECT severity, COUNT(*) as count
                    FROM audit_log
                    WHERE event_timestamp >= ? AND event_timestamp <= ?
                    GROUP BY severity
                """
                severity_results = conn.execute(severity_query, [start_time, end_time]).fetchall()
                by_severity = {row[0]: row[1] for row in severity_results if row[0] and row[1]}
                
                # Get by event type
                type_query = """
                    SELECT event_type, COUNT(*) as count
                    FROM audit_log
                    WHERE event_timestamp >= ? AND event_timestamp <= ?
                    GROUP BY event_type
                """
                type_results = conn.execute(type_query, [start_time, end_time]).fetchall()
                by_type = {row[0]: row[1] for row in type_results if row[0] and row[1]}
                
                return AuditEventSummary(
                    total=total,
                    by_severity=by_severity,
                    by_type=by_type
                )
            
        except Exception as e:
            logger.warning(f"Error getting audit event metrics: {str(e)}")
            return AuditEventSummary(total=0)

