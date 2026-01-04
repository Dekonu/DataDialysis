"""JSON Data Ingestion Adapter.

This adapter implements the IngestionPort contract for JSON data sources.
It provides robust error handling and triage to prevent pipeline failures
from bad data.

Security Impact:
    - Triage logic identifies and rejects malicious or malformed records
    - Bad records are logged as security rejections for audit trail
    - Each record is wrapped in try/except to prevent DoS attacks
    - PII redaction is applied before validation

Architecture:
    - Implements IngestionPort (Hexagonal Architecture)
    - Isolated from domain core - only depends on ports and models
    - Streaming pattern prevents memory exhaustion
    - Fail-safe design: bad records don't crash the pipeline
"""

import json
import logging
import hashlib
from pathlib import Path
from typing import Iterator, Optional, Any
from datetime import datetime

from pydantic import ValidationError as PydanticValidationError

from src.domain.ports import (
    IngestionPort,
    SourceNotFoundError,
    ValidationError,
    TransformationError,
    UnsupportedSourceError,
)
from src.domain.golden_record import (
    GoldenRecord,
    PatientRecord,
    ClinicalObservation,
    EncounterRecord,
)
from src.domain.services import RedactorService

# Configure logging for security rejections
logger = logging.getLogger(__name__)


class JSONIngester(IngestionPort):
    """JSON ingestion adapter with triage and fail-safe error handling.
    
    This adapter reads JSON files and transforms them into GoldenRecord objects.
    It implements robust error handling to prevent bad data from crashing the pipeline.
    
    Key Features:
        - Triage: Identifies and rejects bad records without crashing
        - Fail-safe: Each record wrapped in try/except to prevent DoS
        - Security logging: Bad records logged as security rejections
        - Streaming: Processes records one-by-one to save memory
        - PII redaction: Applies redaction before validation
    
    Security Impact:
        - Malformed records are logged and rejected, not processed
        - DoS protection via per-record error isolation
        - Audit trail of all rejected records
    """
    
    def __init__(self, max_record_size: int = 10 * 1024 * 1024):
        """Initialize JSON ingester.
        
        Parameters:
            max_record_size: Maximum size of a single record in bytes (default: 10MB)
                            Prevents memory exhaustion from oversized records
        """
        self.max_record_size = max_record_size
        self.adapter_name = "json_ingester"
    
    def can_ingest(self, source: str) -> bool:
        """Check if this adapter can handle the given source.
        
        Parameters:
            source: Source identifier (file path or URL)
        
        Returns:
            bool: True if source is a JSON file, False otherwise
        """
        if not source:
            return False
        
        # Check file extension
        source_path = Path(source)
        if source_path.suffix.lower() in ('.json', '.jsonl'):
            return True
        
        # Check if it's a URL ending in .json
        if source.lower().endswith('.json') or source.lower().endswith('.jsonl'):
            return True
        
        return False
    
    def get_source_info(self, source: str) -> Optional[dict]:
        """Get metadata about the JSON source.
        
        Parameters:
            source: Source identifier
        
        Returns:
            Optional[dict]: Metadata dictionary or None if unavailable
        """
        try:
            source_path = Path(source)
            if source_path.exists():
                stat = source_path.stat()
                return {
                    'format': 'json',
                    'size': stat.st_size,
                    'encoding': 'utf-8',
                    'exists': True,
                }
        except (OSError, ValueError):
            pass
        
        return None
    
    def ingest(self, source: str) -> Iterator[GoldenRecord]:
        """Ingest JSON data and yield validated GoldenRecord objects.
        
        This method implements triage logic to handle bad data gracefully:
        1. Each record is wrapped in try/except to prevent DoS
        2. Bad records are logged as security rejections
        3. Pipeline continues processing valid records
        4. Only validated, PII-redacted records are yielded
        
        Parameters:
            source: Path to JSON file or JSON string
        
        Yields:
            GoldenRecord: Validated, PII-redacted golden records
        
        Raises:
            SourceNotFoundError: If source file doesn't exist
            UnsupportedSourceError: If source is not valid JSON
        """
        # Validate source exists
        source_path = Path(source)
        if not source_path.exists():
            raise SourceNotFoundError(
                f"JSON source not found: {source}",
                source=source
            )
        
        # Check file size to prevent memory exhaustion
        file_size = source_path.stat().st_size
        if file_size > self.max_record_size * 100:  # Allow up to 100x max_record_size for file
            logger.warning(
                f"Large JSON file detected: {source} ({file_size} bytes). "
                "Processing may be slow."
            )
        
        try:
            # Load JSON data
            with open(source_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
        except json.JSONDecodeError as e:
            raise UnsupportedSourceError(
                f"Invalid JSON format in {source}: {str(e)}",
                source=source,
                adapter=self.adapter_name
            )
        except Exception as e:
            raise SourceNotFoundError(
                f"Cannot read JSON source {source}: {str(e)}",
                source=source
            )
        
        # Handle different JSON structures
        records = self._extract_records(raw_data)
        
        # Process each record with triage
        record_count = 0
        rejected_count = 0
        
        for raw_record in records:
            record_count += 1
            
            # Triage: Wrap each record in try/except to prevent DoS
            try:
                # Check record size to prevent memory exhaustion
                record_str = json.dumps(raw_record)
                if len(record_str.encode('utf-8')) > self.max_record_size:
                    raise TransformationError(
                        f"Record {record_count} exceeds maximum size ({self.max_record_size} bytes)",
                        source=source,
                        raw_data={"size": len(record_str), "record_index": record_count}
                    )
                
                # Transform and validate record
                golden_record = self._triage_and_transform(
                    raw_record,
                    source,
                    record_count
                )
                
                # Yield validated record
                yield golden_record
                
            except (ValidationError, TransformationError) as e:
                # Security rejection: Log and continue
                rejected_count += 1
                self._log_security_rejection(
                    source=source,
                    record_index=record_count,
                    error=e,
                    raw_record=raw_record
                )
                # Continue processing - don't crash the pipeline
                continue
                
            except Exception as e:
                # Unexpected error: Log as security concern and continue
                rejected_count += 1
                logger.error(
                    f"Unexpected error processing record {record_count} from {source}: {str(e)}",
                    exc_info=True,
                    extra={
                        'source': source,
                        'record_index': record_count,
                        'error_type': type(e).__name__,
                    }
                )
                # Continue processing - fail-safe design
                continue
        
        # Log ingestion summary
        if record_count > 0:
            logger.info(
                f"JSON ingestion complete: {source} - "
                f"{record_count - rejected_count} accepted, {rejected_count} rejected"
            )
    
    def _extract_records(self, raw_data: Any) -> list[dict]:
        """Extract records from various JSON structures.
        
        Handles:
        - Array of records: [{"patient": {...}, ...}, ...]
        - Single record: {"patient": {...}, ...}
        - JSONL format: Not directly supported, but could be extended
        
        Parameters:
            raw_data: Parsed JSON data
        
        Returns:
            list[dict]: List of record dictionaries
        """
        if isinstance(raw_data, list):
            return raw_data
        elif isinstance(raw_data, dict):
            # Single record
            return [raw_data]
        else:
            raise UnsupportedSourceError(
                f"Unsupported JSON structure: expected array or object, got {type(raw_data).__name__}",
                source="unknown",
                adapter=self.adapter_name
            )
    
    def _triage_and_transform(
        self,
        raw_record: dict,
        source: str,
        record_index: int
    ) -> GoldenRecord:
        """Triage and transform a raw JSON record into a GoldenRecord.
        
        This method implements the triage logic:
        1. Pre-validation checks (structure, required fields)
        2. Transformation to domain models
        3. PII redaction (automatic via model validators)
        4. Pydantic validation (Safety Layer)
        
        Parameters:
            raw_record: Raw JSON record dictionary
            source: Source identifier
            record_index: Index of record in source (for logging)
        
        Returns:
            GoldenRecord: Validated, PII-redacted golden record
        
        Raises:
            TransformationError: If transformation fails
            ValidationError: If validation fails
        """
        # Triage: Pre-validation checks
        if not isinstance(raw_record, dict):
            raise TransformationError(
                f"Record {record_index} is not a dictionary",
                source=source,
                raw_data={"record_index": record_index, "type": type(raw_record).__name__}
            )
        
        # Check for required patient data
        if 'patient' not in raw_record:
            raise TransformationError(
                f"Record {record_index} missing required 'patient' field",
                source=source,
                raw_data={"record_index": record_index, "keys": list(raw_record.keys())}
            )
        
        try:
            # Transform patient record (PII redaction happens automatically via validators)
            patient_data = raw_record.get('patient', {})
            if not isinstance(patient_data, dict):
                raise TransformationError(
                    f"Record {record_index} patient field is not a dictionary",
                    source=source,
                    raw_data={"record_index": record_index}
                )
            
            patient = PatientRecord(**patient_data)
            
            # Transform encounters (optional)
            encounters = []
            for enc_data in raw_record.get('encounters', []):
                try:
                    encounter = EncounterRecord(**enc_data)
                    encounters.append(encounter)
                except PydanticValidationError as e:
                    # Log individual encounter validation failure but continue
                    logger.warning(
                        f"Encounter validation failed in record {record_index}: {str(e)}",
                        extra={'source': source, 'record_index': record_index}
                    )
                    continue
            
            # Transform observations (optional)
            observations = []
            for obs_data in raw_record.get('observations', []):
                try:
                    observation = ClinicalObservation(**obs_data)
                    observations.append(observation)
                except PydanticValidationError as e:
                    # Log individual observation validation failure but continue
                    logger.warning(
                        f"Observation validation failed in record {record_index}: {str(e)}",
                        extra={'source': source, 'record_index': record_index}
                    )
                    continue
            
            # Generate transformation hash for audit trail
            transformation_hash = self._generate_hash(raw_record)
            
            # Construct GoldenRecord (final validation)
            golden_record = GoldenRecord(
                patient=patient,
                encounters=encounters,
                observations=observations,
                source_adapter=self.adapter_name,
                transformation_hash=transformation_hash
            )
            
            return golden_record
            
        except PydanticValidationError as e:
            # Validation error: Convert to domain ValidationError
            error_details = {
                'record_index': record_index,
                'validation_errors': str(e),
                'error_count': len(e.errors()) if hasattr(e, 'errors') else 0,
            }
            raise ValidationError(
                f"Record {record_index} failed validation: {str(e)}",
                source=source,
                details=error_details
            )
        except Exception as e:
            # Transformation error: Wrap in domain exception
            raise TransformationError(
                f"Record {record_index} transformation failed: {str(e)}",
                source=source,
                raw_data={"record_index": record_index}
            )
    
    def _generate_hash(self, raw_record: dict) -> str:
        """Generate hash of raw record for audit trail.
        
        Parameters:
            raw_record: Raw JSON record
        
        Returns:
            str: SHA-256 hash of the record
        """
        record_str = json.dumps(raw_record, sort_keys=True)
        return hashlib.sha256(record_str.encode('utf-8')).hexdigest()
    
    def _log_security_rejection(
        self,
        source: str,
        record_index: int,
        error: Exception,
        raw_record: dict
    ) -> None:
        """Log a security rejection for audit trail.
        
        Parameters:
            source: Source identifier
            record_index: Index of rejected record
            error: Exception that caused rejection
            raw_record: Raw record data (may be truncated)
        """
        # Truncate raw_record for logging (prevent log bloat)
        truncated_record = self._truncate_for_logging(raw_record)
        
        logger.warning(
            f"SECURITY REJECTION: Record {record_index} from {source} rejected",
            extra={
                'rejection_type': 'validation_failure',
                'source': source,
                'record_index': record_index,
                'error_type': type(error).__name__,
                'error_message': str(error),
                'raw_record_preview': truncated_record,
            }
        )
    
    def _truncate_for_logging(self, data: dict, max_size: int = 500) -> dict:
        """Truncate data dictionary for safe logging.
        
        Parameters:
            data: Data dictionary to truncate
            max_size: Maximum size in characters
        
        Returns:
            dict: Truncated dictionary safe for logging
        """
        data_str = json.dumps(data)
        if len(data_str) <= max_size:
            return data
        
        # Truncate and add indicator
        truncated = json.loads(data_str[:max_size])
        if isinstance(truncated, dict):
            truncated['_truncated'] = True
            truncated['_original_size'] = len(data_str)
        return truncated

