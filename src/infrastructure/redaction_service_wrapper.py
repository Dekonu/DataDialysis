"""Redaction Service Wrapper with Logging.

This module provides a wrapper around RedactorService that logs all redaction events
to the redaction logger for persistence and reporting.

Security Impact:
    - Every redaction is logged with field name, hash, timestamp, and rule
    - Enables comprehensive security reporting
    - Maintains audit trail for compliance
"""

import hashlib
from typing import Optional, Union, Callable
import pandas as pd

from src.domain.services import RedactorService
from src.infrastructure.redaction_logger import get_redaction_logger


class LoggingRedactorService:
    """Wrapper around RedactorService that logs all redaction events.
    
    This wrapper maintains the same interface as RedactorService but adds
    logging functionality to track every redaction event.
    
    Security Impact:
        - All redactions are logged before being applied
        - Original values are hashed (not stored in plaintext)
        - Enables security reporting and compliance auditing
    """
    
    def __init__(self, record_id: Optional[str] = None, source_adapter: Optional[str] = None):
        """Initialize logging redactor service.
        
        Parameters:
            record_id: Optional record identifier for logging context
            source_adapter: Optional source adapter identifier
        """
        self.record_id = record_id
        self.source_adapter = source_adapter
        self.logger = get_redaction_logger()
    
    def _log_redaction(
        self,
        field_name: str,
        original_value: Optional[str],
        rule_triggered: str
    ) -> None:
        """Log a redaction event.
        
        Parameters:
            field_name: Name of the field being redacted
            original_value: Original value (will be hashed)
            rule_triggered: Name of the redaction rule
        """
        if original_value is None or (isinstance(original_value, str) and not original_value.strip()):
            return
        
        self.logger.log_redaction(
            field_name=field_name,
            original_value=original_value,
            rule_triggered=rule_triggered,
            record_id=self.record_id,
            source_adapter=self.source_adapter
        )
    
    def redact_ssn(self, value: Union[Optional[str], 'pd.Series']) -> Union[Optional[str], 'pd.Series']:
        """Redact SSN with logging."""
        if isinstance(value, pd.Series):
            # For Series, log each non-null value that gets redacted
            result = RedactorService.redact_ssn(value)
            # Log redactions (where result is different from input and matches mask)
            mask = (result == RedactorService.SSN_MASK) & (value.notna())
            for idx in value[mask].index:
                self._log_redaction("ssn", str(value.iloc[idx]), "SSN_PATTERN")
            return result
        else:
            # For scalar, log if redaction occurred
            original = value
            result = RedactorService.redact_ssn(value)
            if result != original and result == RedactorService.SSN_MASK:
                self._log_redaction("ssn", str(original), "SSN_PATTERN")
            return result
    
    def redact_phone(self, value: Union[Optional[str], 'pd.Series']) -> Union[Optional[str], 'pd.Series']:
        """Redact phone with logging."""
        if isinstance(value, pd.Series):
            result = RedactorService.redact_phone(value)
            mask = (result == RedactorService.PHONE_MASK) & (value.notna())
            for idx in value[mask].index:
                self._log_redaction("phone", str(value.iloc[idx]), "PHONE_PATTERN")
            return result
        else:
            original = value
            result = RedactorService.redact_phone(value)
            if result != original and result == RedactorService.PHONE_MASK:
                self._log_redaction("phone", str(original), "PHONE_PATTERN")
            return result
    
    def redact_email(self, value: Union[Optional[str], 'pd.Series']) -> Union[Optional[str], 'pd.Series']:
        """Redact email with logging."""
        if isinstance(value, pd.Series):
            result = RedactorService.redact_email(value)
            mask = (result == RedactorService.EMAIL_MASK) & (value.notna())
            for idx in value[mask].index:
                self._log_redaction("email", str(value.iloc[idx]), "EMAIL_PATTERN")
            return result
        else:
            original = value
            result = RedactorService.redact_email(value)
            if result != original and result == RedactorService.EMAIL_MASK:
                self._log_redaction("email", str(original), "EMAIL_PATTERN")
            return result
    
    def redact_name(self, value: Optional[str]) -> Optional[str]:
        """Redact name with logging."""
        original = value
        result = RedactorService.redact_name(value)
        if result != original and result == RedactorService.NAME_MASK:
            self._log_redaction("name", str(original), "NAME_PATTERN")
        return result
    
    def redact_address(self, value: Optional[str]) -> Optional[str]:
        """Redact address with logging."""
        original = value
        result = RedactorService.redact_address(value)
        if result != original and result == RedactorService.ADDRESS_MASK:
            self._log_redaction("address", str(original), "ADDRESS_PATTERN")
        return result
    
    def redact_date_of_birth(self, value: Optional['date']) -> Optional['date']:
        """Redact date of birth with logging."""
        original = value
        result = RedactorService.redact_date_of_birth(value)
        if result != original:
            self._log_redaction("date_of_birth", str(original) if original else None, "DATE_REDACTION")
        return result
    
    def redact_zip_code(self, value: Optional[str]) -> Optional[str]:
        """Redact ZIP code with logging."""
        original = value
        result = RedactorService.redact_zip_code(value)
        if result != original:
            self._log_redaction("postal_code", str(original), "ZIP_CODE_PARTIAL_REDACTION")
        return result
    
    def redact_unstructured_text(self, value: Optional[str]) -> Optional[str]:
        """Redact unstructured text with logging."""
        original = value
        result = RedactorService.redact_unstructured_text(value)
        if result != original and original:
            # Log if any PII was found and redacted
            self._log_redaction("unstructured_text", str(original)[:100], "UNSTRUCTURED_TEXT_PII_DETECTION")
        return result
    
    def redact_observation_notes(self, value: Optional[str]) -> Optional[str]:
        """Redact observation notes with logging."""
        original = value
        result = RedactorService.redact_observation_notes(value)
        if result != original and original:
            self._log_redaction("observation_notes", str(original)[:100], "OBSERVATION_NOTES_PII_DETECTION")
        return result

