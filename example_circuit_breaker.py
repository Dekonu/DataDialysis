"""Example: Using CircuitBreaker with JSON Ingestion.

This example demonstrates how to use the CircuitBreaker to monitor
failure rates and abort batches when quality thresholds are exceeded.

Security Impact:
    - Prevents processing of low-quality data sources
    - Reduces log noise from repeated failures
    - Enables early detection of data corruption or attacks
"""

import logging
from src.adapters.ingesters.json_ingester import JSONIngester
from src.domain.guardrails import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerOpenError

# Configure logging to see circuit breaker messages
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def ingest_with_circuit_breaker(file_path: str):
    """Ingest JSON data with CircuitBreaker protection.
    
    This function demonstrates how to use CircuitBreaker to monitor
    failure rates and abort batches when quality thresholds are exceeded.
    
    Parameters:
        file_path: Path to JSON file to ingest
    
    Security Impact:
        - Monitors failure rate in sliding window
        - Aborts batch if failure rate exceeds threshold
        - Prevents processing of corrupted or malicious data
    """
    # Configure CircuitBreaker
    # - Abort if 50% of records fail in a window of 100 records
    # - Check threshold after processing at least 10 records
    config = CircuitBreakerConfig(
        failure_threshold_percent=50.0,
        window_size=100,
        min_records_before_check=10,
        abort_on_open=True  # Raise exception when threshold exceeded
    )
    breaker = CircuitBreaker(config)
    
    # Create ingester
    ingester = JSONIngester()
    
    print(f"--- Starting Ingestion with CircuitBreaker for {file_path} ---")
    print(f"Configuration: {config.failure_threshold_percent}% failure threshold, "
          f"window size: {config.window_size}, "
          f"min records: {config.min_records_before_check}")
    print()
    
    valid_count = 0
    failure_count = 0
    
    try:
        for result in ingester.ingest(file_path):
            # Record result in circuit breaker
            breaker.record_result(result)
            
            # Check if circuit is open (will raise if abort_on_open=True)
            if breaker.is_open():
                stats = breaker.get_statistics()
                logger.error(
                    f"CircuitBreaker opened! Failure rate: {stats['failure_rate']:.1f}% "
                    f"({stats['failures_in_window']}/{stats['window_size']} failures in window)"
                )
                # If abort_on_open=False, we'd continue but log warnings
                # With abort_on_open=True, CircuitBreakerOpenError is raised above
            
            # Process successful results
            if result.is_success():
                valid_count += 1
                record = result.value
                print(f"[OK] Ingested: Patient ID: {record.patient.patient_id} | "
                      f"Encounters: {len(record.encounters)} | "
                      f"Observations: {len(record.observations)}")
            else:
                failure_count += 1
                # Failures are already logged by the adapter
                # CircuitBreaker is monitoring these failures
        
        # Print final statistics
        stats = breaker.get_statistics()
        print()
        print(f"--- Ingestion Complete ---")
        print(f"Valid records: {valid_count}")
        print(f"Failed records: {failure_count}")
        print(f"Total processed: {stats['total_processed']}")
        print(f"Failure rate: {stats['failure_rate']:.1f}%")
        print(f"Circuit breaker status: {'OPEN' if stats['is_open'] else 'CLOSED'}")
        
    except CircuitBreakerOpenError as e:
        logger.error(
            f"Batch aborted by CircuitBreaker: {e.failure_rate:.1f}% failure rate "
            f"exceeds threshold {e.threshold}% "
            f"({e.failures} failures in {e.records_processed} records)"
        )
        print()
        print(f"--- Ingestion Aborted by CircuitBreaker ---")
        print(f"Processed: {e.records_processed} records")
        print(f"Failures: {e.failures}")
        print(f"Failure rate: {e.failure_rate:.1f}%")
        print(f"Threshold: {e.threshold}%")
        raise


if __name__ == "__main__":
    # Example: Ingest with circuit breaker protection
    # This will abort if more than 50% of records fail in a window of 100 records
    try:
        ingest_with_circuit_breaker("test_batch.json")
    except CircuitBreakerOpenError:
        print("\nNote: Batch was aborted due to excessive failures.")
        print("This prevents processing of low-quality or corrupted data sources.")

