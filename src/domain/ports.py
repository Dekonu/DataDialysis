"""Domain Ports - Abstract Contracts for Data Ingestion.

This module defines the Port interfaces (abstract contracts) that Adapters must implement.
Following Hexagonal Architecture, the Domain Core defines what it needs, not how it's provided.

Security Impact:
    - Ports enforce that adapters yield validated, PII-redacted GoldenRecord objects
    - Streaming interface prevents memory exhaustion with large datasets
    - Type safety ensures only safe records enter the domain

Architecture:
    - Pure abstract interfaces with zero infrastructure dependencies
    - Adapters (JSON, XML, API, etc.) implement these ports
    - Domain Core is isolated from data source specifics
    - Iterator pattern enables memory-efficient streaming ingestion
"""

from abc import ABC, abstractmethod
from typing import Iterator, Optional, AsyncIterator
from pathlib import Path

from src.domain.golden_record import GoldenRecord


# ============================================================================
# Custom Exception Hierarchy
# ============================================================================

class IngestionError(Exception):
    """Base exception for all ingestion-related errors.
    
    This exception should be raised when ingestion fails due to
    adapter-specific issues (file format, network, etc.).
    """
    pass


class ValidationError(IngestionError):
    """Raised when data fails validation or transformation.
    
    This exception indicates that the data cannot be transformed
    into a valid GoldenRecord (schema mismatch, missing fields, etc.).
    
    Attributes:
        source: The source identifier that failed validation
        details: Additional error details or validation messages
    """
    
    def __init__(self, message: str, source: Optional[str] = None, details: Optional[dict] = None):
        super().__init__(message)
        self.source = source
        self.details = details or {}


class TransformationError(IngestionError):
    """Raised when data transformation fails.
    
    This exception indicates that raw data cannot be transformed
    into domain models (type conversion, missing mappings, etc.).
    
    Attributes:
        source: The source identifier that failed transformation
        raw_data: The raw data that failed transformation (may be truncated)
    """
    
    def __init__(self, message: str, source: Optional[str] = None, raw_data: Optional[dict] = None):
        super().__init__(message)
        self.source = source
        self.raw_data = raw_data


class SourceNotFoundError(IngestionError):
    """Raised when the source cannot be found or accessed.
    
    This exception indicates that the source file, URL, or connection
    cannot be located or accessed (file not found, network error, etc.).
    
    Attributes:
        source: The source identifier that was not found
    """
    
    def __init__(self, message: str, source: Optional[str] = None):
        super().__init__(message)
        self.source = source


class UnsupportedSourceError(IngestionError):
    """Raised when the source format is not supported by the adapter.
    
    This exception indicates that the adapter cannot handle the
    given source format or structure.
    
    Attributes:
        source: The source identifier that is unsupported
        adapter: The adapter that cannot handle the source
    """
    
    def __init__(self, message: str, source: Optional[str] = None, adapter: Optional[str] = None):
        super().__init__(message)
        self.source = source
        self.adapter = adapter


class IngestionPort(ABC):
    """Abstract contract for data ingestion adapters.
    
    This port defines how the Domain Core wants to receive data, regardless of
    whether it comes from JSON, XML, CSV, REST API, or any other source.
    
    Key Principles:
        - Streaming: Yields records one-by-one to prevent memory exhaustion
        - Validated: All records must be GoldenRecord instances (PII-redacted, validated)
        - Source-agnostic: Domain doesn't care about file format or transport
        - Fail-fast: Adapters should validate and transform before yielding
    
    Security Impact:
        - Adapters must ensure all PII is redacted before yielding GoldenRecord
        - Records must pass Pydantic validation (Safety Layer)
        - Invalid records should raise ValidationError, not be silently skipped
    
    Example Usage:
        ```python
        class JSONAdapter(IngestionPort):
            def ingest(self, source: str) -> Iterator[GoldenRecord]:
                # Parse JSON, validate, redact PII, yield GoldenRecord
                ...
        
        adapter = JSONAdapter()
        for golden_record in adapter.ingest("data.json"):
            # Process validated, redacted record
            ...
        ```
    """
    
    @abstractmethod
    def ingest(self, source: str) -> Iterator[GoldenRecord]:
        """Ingest data from a source and yield validated GoldenRecord objects.
        
        This method is the primary entry point for data ingestion. Adapters must:
        1. Parse the source (file, URL, stream, etc.)
        2. Transform raw data to domain models (PatientRecord, ClinicalObservation, etc.)
        3. Apply PII redaction via RedactorService
        4. Validate using Pydantic (Safety Layer)
        5. Construct GoldenRecord instances
        6. Yield records one-by-one (streaming)
        
        Parameters:
            source: Source identifier (file path, URL, connection string, etc.)
                   The format is adapter-specific but typically a string path or URI.
        
        Yields:
            GoldenRecord: Validated, PII-redacted golden record ready for persistence.
                         Each record has been through the Safety Layer and Sieve.
        
        Raises:
            SourceNotFoundError: If source file/URL doesn't exist or cannot be accessed
            ValidationError: If data cannot be validated or transformed
            TransformationError: If data transformation fails
            UnsupportedSourceError: If source format is invalid or unsupported
            IOError: If source cannot be read (permissions, network, etc.)
        
        Security Impact:
            - Must redact all PII before yielding GoldenRecord
            - Must validate schema before yielding (fail-fast)
            - Should log transformation events for audit trail
        
        Memory Impact:
            - Uses Iterator pattern to stream records, preventing memory exhaustion
            - Adapters should process records incrementally, not load entire dataset
        """
        pass
    
    @abstractmethod
    def can_ingest(self, source: str) -> bool:
        """Check if this adapter can handle the given source.
        
        Allows the system to select the appropriate adapter for a source
        without attempting ingestion. Useful for routing logic.
        
        Parameters:
            source: Source identifier to check
        
        Returns:
            bool: True if this adapter can handle the source, False otherwise
        
        Example:
            ```python
            if json_adapter.can_ingest("data.json"):
                adapter = json_adapter
            elif xml_adapter.can_ingest("data.xml"):
                adapter = xml_adapter
            ```
        """
        pass
    
    def get_source_info(self, source: str) -> Optional[dict]:
        """Get metadata about the source (optional, adapter-specific).
        
        Provides information about the source without ingesting it.
        Useful for logging, validation, or user feedback.
        
        Parameters:
            source: Source identifier
        
        Returns:
            Optional[dict]: Metadata dictionary with keys like:
                - 'format': File format (json, xml, csv, etc.)
                - 'size': Source size in bytes (if applicable)
                - 'record_count': Estimated number of records (if available)
                - 'encoding': Character encoding (if applicable)
                - 'schema_version': Schema version (if applicable)
            Returns None if metadata cannot be determined.
        
        Note:
            This is a default implementation that returns None.
            Adapters can override to provide source-specific metadata.
        """
        return None


# ============================================================================
# Async Ports
# ============================================================================

class AsyncIngestionPort(ABC):
    """Abstract contract for asynchronous data ingestion adapters.
    
    This port defines how the Domain Core wants to receive data asynchronously,
    enabling non-blocking I/O operations for better performance with large
    datasets or network-based sources.
    
    Key Principles:
        - Async streaming: Yields records asynchronously to prevent blocking
        - Validated: All records must be GoldenRecord instances (PII-redacted, validated)
        - Source-agnostic: Domain doesn't care about file format or transport
        - Fail-fast: Adapters should validate and transform before yielding
    
    Security Impact:
        - Adapters must ensure all PII is redacted before yielding GoldenRecord
        - Records must pass Pydantic validation (Safety Layer)
        - Invalid records should raise ValidationError, not be silently skipped
    
    Example Usage:
        ```python
        class AsyncJSONAdapter(AsyncIngestionPort):
            async def ingest(self, source: str) -> AsyncIterator[GoldenRecord]:
                # Parse JSON asynchronously, validate, redact PII, yield GoldenRecord
                ...
        
        adapter = AsyncJSONAdapter()
        async for golden_record in adapter.ingest("data.json"):
            # Process validated, redacted record
            ...
        ```
    """
    
    @abstractmethod
    async def ingest(self, source: str) -> AsyncIterator[GoldenRecord]:
        """Ingest data from a source asynchronously and yield validated GoldenRecord objects.
        
        This method is the primary entry point for async data ingestion. Adapters must:
        1. Parse the source asynchronously (file, URL, stream, etc.)
        2. Transform raw data to domain models (PatientRecord, ClinicalObservation, etc.)
        3. Apply PII redaction via RedactorService
        4. Validate using Pydantic (Safety Layer)
        5. Construct GoldenRecord instances
        6. Yield records one-by-one asynchronously (streaming)
        
        Parameters:
            source: Source identifier (file path, URL, connection string, etc.)
                   The format is adapter-specific but typically a string path or URI.
        
        Yields:
            GoldenRecord: Validated, PII-redacted golden record ready for persistence.
                         Each record has been through the Safety Layer and Sieve.
        
        Raises:
            SourceNotFoundError: If source file/URL doesn't exist or cannot be accessed
            ValidationError: If data cannot be validated or transformed
            TransformationError: If data transformation fails
            UnsupportedSourceError: If source format is invalid or unsupported
            IOError: If source cannot be read (permissions, network, etc.)
        
        Security Impact:
            - Must redact all PII before yielding GoldenRecord
            - Must validate schema before yielding (fail-fast)
            - Should log transformation events for audit trail
        
        Memory Impact:
            - Uses AsyncIterator pattern to stream records, preventing memory exhaustion
            - Adapters should process records incrementally, not load entire dataset
            - Non-blocking I/O enables better resource utilization
        """
        pass
    
    @abstractmethod
    async def can_ingest(self, source: str) -> bool:
        """Check asynchronously if this adapter can handle the given source.
        
        Allows the system to select the appropriate adapter for a source
        without attempting ingestion. Useful for routing logic.
        
        Parameters:
            source: Source identifier to check
        
        Returns:
            bool: True if this adapter can handle the source, False otherwise
        
        Example:
            ```python
            if await json_adapter.can_ingest("data.json"):
                adapter = json_adapter
            elif await xml_adapter.can_ingest("data.xml"):
                adapter = xml_adapter
            ```
        """
        pass
    
    async def get_source_info(self, source: str) -> Optional[dict]:
        """Get metadata about the source asynchronously (optional, adapter-specific).
        
        Provides information about the source without ingesting it.
        Useful for logging, validation, or user feedback.
        
        Parameters:
            source: Source identifier
        
        Returns:
            Optional[dict]: Metadata dictionary with keys like:
                - 'format': File format (json, xml, csv, etc.)
                - 'size': Source size in bytes (if applicable)
                - 'record_count': Estimated number of records (if available)
                - 'encoding': Character encoding (if applicable)
                - 'schema_version': Schema version (if applicable)
            Returns None if metadata cannot be determined.
        
        Note:
            This is a default implementation that returns None.
            Adapters can override to provide source-specific metadata.
        """
        return None

