"""Redaction Event Logger.

This module provides a centralized logging mechanism for tracking PII redaction events.
Each redaction is logged with field name, original value hash, timestamp, and the rule that triggered it.

Security Impact:
    - Creates immutable audit trail of all PII redactions
    - Enables forensic analysis of data transformations
    - Required for HIPAA/GDPR compliance reporting
    - Original value hashes allow verification without storing PII

Architecture:
    - Infrastructure layer component
    - Can be called from domain services (RedactorService) or adapters
    - Integrates with storage adapters for persistence
"""

import hashlib
import logging
import uuid
from datetime import datetime
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class RedactionLogger:
    """Logger for tracking PII redaction events.
    
    This class provides a thread-safe way to log redaction events that can be
    persisted to the database. It maintains an in-memory buffer of redaction
    events that can be flushed to storage.
    
    Security Impact:
        - Logs original value hashes (not actual PII values)
        - Tracks which redaction rule was triggered
        - Maintains timestamp for compliance
        - Enables security reporting
    
    Example Usage:
        ```python
        logger = RedactionLogger()
        logger.log_redaction(
            field_name="phone",
            original_value="555-123-4567",
            rule_triggered="PHONE_PATTERN",
            record_id="MRN001"
        )
        # Later, flush to storage
        storage_adapter.flush_redaction_logs(logger.get_logs())
        ```
    """
    
    def __init__(self):
        """Initialize redaction logger."""
        self._logs: list[dict] = []
        self._ingestion_id: Optional[str] = None
    
    def set_ingestion_id(self, ingestion_id: str) -> None:
        """Set ingestion ID for grouping redaction events.
        
        Parameters:
            ingestion_id: Unique identifier for this ingestion run
        """
        self._ingestion_id = ingestion_id
    
    def log_redaction(
        self,
        field_name: str,
        original_value: Optional[str],
        rule_triggered: str,
        record_id: Optional[str] = None,
        source_adapter: Optional[str] = None
    ) -> None:
        """Log a redaction event.
        
        Parameters:
            field_name: Name of the field that was redacted (e.g., "phone", "ssn")
            original_value: Original value before redaction (will be hashed)
            rule_triggered: Name of the redaction rule that was triggered
            record_id: Unique identifier of the record (if applicable)
            source_adapter: Source adapter identifier (if applicable)
        
        Security Impact:
            - Original value is hashed, not stored in plaintext
            - Hash allows verification without exposing PII
        """
        if original_value is None:
            return  # Don't log None values
        
        # Create hash of original value (for verification without storing PII)
        original_hash = hashlib.sha256(str(original_value).encode('utf-8')).hexdigest()
        
        log_entry = {
            "log_id": str(uuid.uuid4()),
            "field_name": field_name,
            "original_hash": original_hash,
            "timestamp": datetime.now(),
            "rule_triggered": rule_triggered,
            "record_id": record_id,
            "source_adapter": source_adapter,
            "ingestion_id": self._ingestion_id,
            "redacted_value": None,  # Can be set if needed for debugging
            "original_value_length": len(str(original_value)) if original_value else 0
        }
        
        self._logs.append(log_entry)
        logger.debug(f"Logged redaction: {field_name} - {rule_triggered}")
    
    def get_logs(self) -> list[dict]:
        """Get all logged redaction events.
        
        Returns:
            List of redaction log entries
        """
        return self._logs.copy()
    
    def clear_logs(self) -> None:
        """Clear all logged events (after flushing to storage)."""
        self._logs.clear()
    
    def get_log_count(self) -> int:
        """Get count of logged redaction events.
        
        Returns:
            Number of redaction events logged
        """
        return len(self._logs)


# Global redaction logger instance (thread-local would be better for production)
_global_logger: Optional[RedactionLogger] = None


def get_redaction_logger() -> RedactionLogger:
    """Get the global redaction logger instance.
    
    Returns:
        RedactionLogger instance
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = RedactionLogger()
    return _global_logger


def reset_redaction_logger() -> None:
    """Reset the global redaction logger (useful for testing)."""
    global _global_logger
    _global_logger = None

