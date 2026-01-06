"""Performance metrics service.

This service provides performance-specific metrics including throughput,
latency, file processing, and memory usage.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from src.domain.ports import Result, StoragePort
from src.dashboard.models.metrics import (
    PerformanceMetrics,
    ThroughputMetrics,
    LatencyMetrics,
    FileProcessingMetrics,
    MemoryMetrics
)

logger = logging.getLogger(__name__)


class PerformanceMetricsService:
    """Service for performance-specific metrics."""
    
    def __init__(self, storage: StoragePort):
        """Initialize performance metrics service.
        
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
            logger.warning(f"Unknown time range format: {time_range}, defaulting to 24h")
            return end_time - timedelta(hours=24)
    
    def get_performance_metrics(
        self,
        time_range: str = "24h"
    ) -> Result[PerformanceMetrics]:
        """Get performance metrics for the specified time range.
        
        Parameters:
            time_range: Time range string (1h, 24h, 7d, 30d)
            
        Returns:
            Result[PerformanceMetrics]: Performance metrics or error
        """
        try:
            end_time = datetime.now(timezone.utc).replace(tzinfo=None)
            start_time = self._parse_time_range(time_range, end_time)
            
            # Get throughput metrics
            throughput = self._get_throughput_metrics(start_time, end_time)
            
            # Get latency metrics (placeholder - would need timing data)
            latency = self._get_latency_metrics(start_time, end_time)
            
            # Get file processing metrics
            file_processing = self._get_file_processing_metrics(start_time, end_time)
            
            # Get memory metrics (placeholder - would need memory tracking)
            memory = self._get_memory_metrics(start_time, end_time)
            
            metrics = PerformanceMetrics(
                time_range=time_range,
                throughput=throughput,
                latency=latency,
                file_processing=file_processing,
                memory=memory
            )
            
            return Result.success_result(metrics)
            
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {str(e)}", exc_info=True)
            return Result.failure_result(
                e,
                error_type="MetricsError"
            )
    
    def _get_throughput_metrics(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> ThroughputMetrics:
        """Get throughput metrics.
        
        Parameters:
            start_time: Start time
            end_time: End time
            
        Returns:
            ThroughputMetrics: Throughput statistics
        """
        try:
            if not hasattr(self.storage, '_get_connection'):
                return ThroughputMetrics(records_per_second=0.0)
            
            conn = self.storage._get_connection()
            
            # Count total records processed
            total_records = 0
            for table in ['patients', 'encounters', 'observations']:
                try:
                    query = f"""
                        SELECT COUNT(*) as count
                        FROM {table}
                        WHERE ingestion_timestamp >= ? AND ingestion_timestamp <= ?
                    """
                    result = conn.execute(query, [start_time, end_time]).fetchone()
                    if result and result[0]:
                        total_records += result[0]
                except Exception as e:
                    logger.debug(f"Could not query {table}: {str(e)}")
                    continue
            
            # Calculate time delta in seconds
            time_delta = (end_time - start_time).total_seconds()
            if time_delta > 0:
                records_per_second = total_records / time_delta
            else:
                records_per_second = 0.0
            
            # For now, we don't track file sizes or peak throughput
            # These would need additional tracking
            return ThroughputMetrics(
                records_per_second=round(records_per_second, 2),
                mb_per_second=None,
                peak_records_per_second=None
            )
            
        except Exception as e:
            logger.warning(f"Error getting throughput metrics: {str(e)}")
            return ThroughputMetrics(records_per_second=0.0)
    
    def _get_latency_metrics(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> LatencyMetrics:
        """Get latency metrics.
        
        Note: Latency metrics would require timing data to be stored.
        This is a placeholder implementation.
        
        Parameters:
            start_time: Start time
            end_time: End time
            
        Returns:
            LatencyMetrics: Latency statistics
        """
        # Latency metrics would need to be tracked during ingestion
        # For now, return placeholder values
        return LatencyMetrics(
            avg_processing_time_ms=None,
            p50_ms=None,
            p95_ms=None,
            p99_ms=None
        )
    
    def _get_file_processing_metrics(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> FileProcessingMetrics:
        """Get file processing metrics.
        
        Parameters:
            start_time: Start time
            end_time: End time
            
        Returns:
            FileProcessingMetrics: File processing statistics
        """
        try:
            if not hasattr(self.storage, '_get_connection'):
                return FileProcessingMetrics(total_files=0)
            
            conn = self.storage._get_connection()
            
            # Count unique ingestion IDs as proxy for file count
            query = """
                SELECT COUNT(DISTINCT ingestion_id) as count
                FROM logs
                WHERE timestamp >= ? AND timestamp <= ?
                AND ingestion_id IS NOT NULL
            """
            result = conn.execute(query, [start_time, end_time]).fetchone()
            total_files = result[0] if result and result[0] else 0
            
            # File size metrics would need to be tracked separately
            return FileProcessingMetrics(
                total_files=total_files,
                avg_file_size_mb=None,
                total_data_processed_mb=None
            )
            
        except Exception as e:
            logger.warning(f"Error getting file processing metrics: {str(e)}")
            return FileProcessingMetrics(total_files=0)
    
    def _get_memory_metrics(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> MemoryMetrics:
        """Get memory usage metrics.
        
        Note: Memory metrics would require memory tracking during ingestion.
        This is a placeholder implementation.
        
        Parameters:
            start_time: Start time
            end_time: End time
            
        Returns:
            MemoryMetrics: Memory usage statistics
        """
        # Memory metrics would need to be tracked during ingestion
        # For now, return placeholder values
        return MemoryMetrics(
            avg_peak_memory_mb=None,
            max_peak_memory_mb=None
        )

