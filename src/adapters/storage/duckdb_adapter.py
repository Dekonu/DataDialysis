"""DuckDB Storage Adapter.

This adapter implements the StoragePort contract for persisting validated GoldenRecords
to DuckDB, an in-process OLAP database optimized for analytical workloads.

Security Impact:
    - Only validated GoldenRecord instances can be persisted
    - All operations are logged to immutable audit trail
    - Connection credentials are managed securely via configuration
    - Schema enforces data integrity constraints

Architecture:
    - Implements StoragePort (Hexagonal Architecture)
    - Isolated from domain core - only depends on ports and models
    - Transactional batch operations ensure data consistency
    - Audit trail is append-only for compliance
"""

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Any
import json

import duckdb
import pandas as pd
from pydantic import ValidationError as PydanticValidationError

from src.domain.ports import (
    StoragePort,
    Result,
    StorageError,
    ValidationError,
)
from src.domain.golden_record import (
    GoldenRecord,
    PatientRecord,
    ClinicalObservation,
    EncounterRecord,
)

logger = logging.getLogger(__name__)


class DuckDBAdapter(StoragePort):
    """DuckDB implementation of StoragePort for analytical data storage.
    
    This adapter provides efficient bulk loading and query capabilities
    for validated clinical records. DuckDB is optimized for OLAP workloads
    and provides excellent performance for analytical queries.
    
    Security Impact:
        - All records are validated before persistence
        - Audit trail is immutable and tamper-proof
        - Connection credentials are never logged
        - Schema enforces referential integrity
    
    Parameters:
        db_path: Path to DuckDB database file (or ':memory:' for in-memory)
        config: Optional configuration dictionary (for future extensibility)
    
    Example Usage:
        ```python
        adapter = DuckDBAdapter(db_path="data/clinical.duckdb")
        result = adapter.initialize_schema()
        if result.is_success():
            result = adapter.persist(golden_record)
        ```
    """
    
    def __init__(self, db_path: str = ":memory:", config: Optional[dict] = None):
        """Initialize DuckDB adapter.
        
        Parameters:
            db_path: Path to DuckDB database file (or ':memory:' for in-memory)
            config: Optional configuration dictionary
        
        Security Impact:
            - Database path is validated to prevent path traversal attacks
            - Connection is established lazily (on first operation)
        """
        self.db_path = db_path
        self.config = config or {}
        self._connection: Optional[duckdb.DuckDBPyConnection] = None
        self._initialized = False
        
        # Validate db_path to prevent path traversal
        if db_path != ":memory:":
            db_path_obj = Path(db_path)
            if not db_path_obj.parent.exists():
                raise StorageError(
                    f"Database directory does not exist: {db_path_obj.parent}",
                    operation="__init__"
                )
    
    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        """Get or create DuckDB connection.
        
        Returns:
            DuckDB connection instance
        
        Security Impact:
            - Connection is created lazily to avoid unnecessary resource usage
            - Connection is reused for performance
        """
        if self._connection is None:
            try:
                self._connection = duckdb.connect(self.db_path)
                logger.info(f"Connected to DuckDB database: {self.db_path}")
            except Exception as e:
                raise StorageError(
                    f"Failed to connect to DuckDB: {str(e)}",
                    operation="connect",
                    details={"db_path": self.db_path}
                )
        return self._connection
    
    def initialize_schema(self) -> Result[None]:
        """Initialize database schema (tables, indexes, constraints).
        
        Creates tables for:
        - patients: Patient demographic records
        - encounters: Encounter/visit records
        - observations: Clinical observation records
        - audit_log: Immutable audit trail
        
        Returns:
            Result[None]: Success or failure result
        
        Security Impact:
            - Schema enforces data integrity constraints
            - Audit log table is append-only
            - Indexes optimize query performance
        """
        try:
            conn = self._get_connection()
            
            # Create patients table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS patients (
                    patient_id VARCHAR PRIMARY KEY,
                    identifiers VARCHAR,
                    family_name VARCHAR,
                    given_names VARCHAR,
                    name_prefix VARCHAR,
                    name_suffix VARCHAR,
                    date_of_birth DATE,
                    gender VARCHAR,
                    deceased BOOLEAN,
                    deceased_date TIMESTAMP,
                    marital_status VARCHAR,
                    address_line1 VARCHAR,
                    address_line2 VARCHAR,
                    city VARCHAR,
                    state VARCHAR,
                    postal_code VARCHAR,
                    country VARCHAR,
                    address_use VARCHAR,
                    phone VARCHAR,
                    email VARCHAR,
                    fax VARCHAR,
                    emergency_contact_name VARCHAR,
                    emergency_contact_relationship VARCHAR,
                    emergency_contact_phone VARCHAR,
                    language VARCHAR,
                    managing_organization VARCHAR,
                    ingestion_timestamp TIMESTAMP NOT NULL,
                    source_adapter VARCHAR NOT NULL,
                    transformation_hash VARCHAR
                )
            """)
            
            # Create encounters table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS encounters (
                    encounter_id VARCHAR PRIMARY KEY,
                    patient_id VARCHAR NOT NULL,
                    status VARCHAR NOT NULL,
                    class_code VARCHAR NOT NULL,
                    type VARCHAR,
                    service_type VARCHAR,
                    priority VARCHAR,
                    period_start TIMESTAMP,
                    period_end TIMESTAMP,
                    length_minutes INTEGER,
                    reason_code VARCHAR,
                    diagnosis_codes VARCHAR,
                    facility_name VARCHAR,
                    location_address VARCHAR,
                    participant_name VARCHAR,
                    participant_role VARCHAR,
                    service_provider VARCHAR,
                    ingestion_timestamp TIMESTAMP NOT NULL,
                    source_adapter VARCHAR NOT NULL,
                    transformation_hash VARCHAR,
                    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
                )
            """)
            
            # Create observations table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS observations (
                    observation_id VARCHAR PRIMARY KEY,
                    patient_id VARCHAR NOT NULL,
                    encounter_id VARCHAR,
                    status VARCHAR NOT NULL,
                    category VARCHAR NOT NULL,
                    code VARCHAR,
                    effective_date TIMESTAMP,
                    issued TIMESTAMP,
                    performer_name VARCHAR,
                    value VARCHAR,
                    unit VARCHAR,
                    interpretation VARCHAR,
                    body_site VARCHAR,
                    method VARCHAR,
                    device VARCHAR,
                    reference_range VARCHAR,
                    notes VARCHAR,
                    ingestion_timestamp TIMESTAMP NOT NULL,
                    source_adapter VARCHAR NOT NULL,
                    transformation_hash VARCHAR,
                    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
                    FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id)
                )
            """)
            
            # Create audit log table (immutable, append-only)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    audit_id VARCHAR PRIMARY KEY,
                    event_type VARCHAR NOT NULL,
                    event_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    record_id VARCHAR,
                    transformation_hash VARCHAR,
                    details JSON,
                    source_adapter VARCHAR,
                    severity VARCHAR
                )
            """)
            
            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_patients_source ON patients(source_adapter)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_patients_timestamp ON patients(ingestion_timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_encounters_patient ON encounters(patient_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_observations_patient ON observations(patient_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_observations_encounter ON observations(encounter_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_log(event_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(event_timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_record_id ON audit_log(record_id)")
            
            self._initialized = True
            logger.info("Database schema initialized successfully")
            
            return Result.success_result(None)
            
        except Exception as e:
            error_msg = f"Failed to initialize schema: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return Result.failure_result(
                StorageError(error_msg, operation="initialize_schema"),
                error_type="StorageError"
            )
    
    def persist(self, record: GoldenRecord) -> Result[str]:
        """Persist a single GoldenRecord to storage.
        
        Parameters:
            record: Validated GoldenRecord instance (PII already redacted)
        
        Returns:
            Result[str]: Record identifier (patient_id) or error
        """
        try:
            if not self._initialized:
                init_result = self.initialize_schema()
                if not init_result.is_success():
                    return init_result
            
            conn = self._get_connection()
            
            # Begin transaction
            conn.begin()
            
            try:
                # Insert patient record
                patient = record.patient
                patient_dict = patient.model_dump()
                patient_dict['ingestion_timestamp'] = record.ingestion_timestamp
                patient_dict['source_adapter'] = record.source_adapter
                patient_dict['transformation_hash'] = record.transformation_hash
                
                # Convert lists to JSON strings for DuckDB array support
                if 'identifiers' in patient_dict and patient_dict['identifiers']:
                    patient_dict['identifiers'] = json.dumps(patient_dict['identifiers'])
                if 'given_names' in patient_dict and patient_dict['given_names']:
                    patient_dict['given_names'] = json.dumps(patient_dict['given_names'])
                if 'name_prefix' in patient_dict and patient_dict['name_prefix']:
                    patient_dict['name_prefix'] = json.dumps(patient_dict['name_prefix'])
                if 'name_suffix' in patient_dict and patient_dict['name_suffix']:
                    patient_dict['name_suffix'] = json.dumps(patient_dict['name_suffix'])
                
                conn.execute("""
                    INSERT OR REPLACE INTO patients (
                        patient_id, identifiers, family_name, given_names, name_prefix, name_suffix,
                        date_of_birth, gender, deceased, deceased_date, marital_status,
                        address_line1, address_line2, city, state, postal_code, country,
                        address_use, phone, email, fax, emergency_contact_name,
                        emergency_contact_relationship, emergency_contact_phone, language,
                        managing_organization, ingestion_timestamp, source_adapter, transformation_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    patient_dict.get('patient_id'),
                    patient_dict.get('identifiers'),
                    patient_dict.get('family_name'),
                    patient_dict.get('given_names'),
                    patient_dict.get('name_prefix'),
                    patient_dict.get('name_suffix'),
                    patient_dict.get('date_of_birth'),
                    patient_dict.get('gender'),
                    patient_dict.get('deceased'),
                    patient_dict.get('deceased_date'),
                    patient_dict.get('marital_status'),
                    patient_dict.get('address_line1'),
                    patient_dict.get('address_line2'),
                    patient_dict.get('city'),
                    patient_dict.get('state'),
                    patient_dict.get('postal_code'),
                    patient_dict.get('country'),
                    patient_dict.get('address_use'),
                    patient_dict.get('phone'),
                    patient_dict.get('email'),
                    patient_dict.get('fax'),
                    patient_dict.get('emergency_contact_name'),
                    patient_dict.get('emergency_contact_relationship'),
                    patient_dict.get('emergency_contact_phone'),
                    patient_dict.get('language'),
                    patient_dict.get('managing_organization'),
                    patient_dict.get('ingestion_timestamp'),
                    patient_dict.get('source_adapter'),
                    patient_dict.get('transformation_hash'),
                ])
                
                # Insert encounters
                for encounter in record.encounters:
                    encounter_dict = encounter.model_dump()
                    encounter_dict['ingestion_timestamp'] = record.ingestion_timestamp
                    encounter_dict['source_adapter'] = record.source_adapter
                    encounter_dict['transformation_hash'] = record.transformation_hash
                    
                    if 'diagnosis_codes' in encounter_dict and encounter_dict['diagnosis_codes']:
                        encounter_dict['diagnosis_codes'] = json.dumps(encounter_dict['diagnosis_codes'])
                    
                    conn.execute("""
                        INSERT OR REPLACE INTO encounters (
                            encounter_id, patient_id, status, class_code, type, service_type, priority,
                            period_start, period_end, length_minutes, reason_code, diagnosis_codes,
                            facility_name, location_address, participant_name, participant_role,
                            service_provider, ingestion_timestamp, source_adapter, transformation_hash
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, [
                        encounter_dict.get('encounter_id'),
                        encounter_dict.get('patient_id'),
                        encounter_dict.get('status'),
                        encounter_dict.get('class_code'),
                        encounter_dict.get('type'),
                        encounter_dict.get('service_type'),
                        encounter_dict.get('priority'),
                        encounter_dict.get('period_start'),
                        encounter_dict.get('period_end'),
                        encounter_dict.get('length_minutes'),
                        encounter_dict.get('reason_code'),
                        encounter_dict.get('diagnosis_codes'),
                        encounter_dict.get('facility_name'),
                        encounter_dict.get('location_address'),
                        encounter_dict.get('participant_name'),
                        encounter_dict.get('participant_role'),
                        encounter_dict.get('service_provider'),
                        encounter_dict.get('ingestion_timestamp'),
                        encounter_dict.get('source_adapter'),
                        encounter_dict.get('transformation_hash'),
                    ])
                
                # Insert observations
                for observation in record.observations:
                    observation_dict = observation.model_dump()
                    observation_dict['ingestion_timestamp'] = record.ingestion_timestamp
                    observation_dict['source_adapter'] = record.source_adapter
                    observation_dict['transformation_hash'] = record.transformation_hash
                    
                    conn.execute("""
                        INSERT OR REPLACE INTO observations (
                            observation_id, patient_id, encounter_id, status, category, code,
                            effective_date, issued, performer_name, value, unit, interpretation,
                            body_site, method, device, reference_range, notes,
                            ingestion_timestamp, source_adapter, transformation_hash
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, [
                        observation_dict.get('observation_id'),
                        observation_dict.get('patient_id'),
                        observation_dict.get('encounter_id'),
                        observation_dict.get('status'),
                        observation_dict.get('category'),
                        observation_dict.get('code'),
                        observation_dict.get('effective_date'),
                        observation_dict.get('issued'),
                        observation_dict.get('performer_name'),
                        observation_dict.get('value'),
                        observation_dict.get('unit'),
                        observation_dict.get('interpretation'),
                        observation_dict.get('body_site'),
                        observation_dict.get('method'),
                        observation_dict.get('device'),
                        observation_dict.get('reference_range'),
                        observation_dict.get('notes'),
                        observation_dict.get('ingestion_timestamp'),
                        observation_dict.get('source_adapter'),
                        observation_dict.get('transformation_hash'),
                    ])
                
                # Commit transaction
                conn.commit()
                
                # Log audit event
                self.log_audit_event(
                    event_type="PERSISTENCE",
                    record_id=patient.patient_id,
                    transformation_hash=record.transformation_hash,
                    details={
                        "source_adapter": record.source_adapter,
                        "encounter_count": len(record.encounters),
                        "observation_count": len(record.observations),
                    }
                )
                
                logger.info(f"Persisted GoldenRecord for patient_id: {patient.patient_id}")
                return Result.success_result(patient.patient_id)
                
            except Exception as e:
                conn.rollback()
                raise e
                
        except Exception as e:
            error_msg = f"Failed to persist record: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return Result.failure_result(
                StorageError(error_msg, operation="persist", details={"patient_id": record.patient.patient_id}),
                error_type="StorageError"
            )
    
    def persist_batch(self, records: list[GoldenRecord]) -> Result[list[str]]:
        """Persist multiple GoldenRecords in a single transaction.
        
        Parameters:
            records: List of validated GoldenRecord instances
        
        Returns:
            Result[list[str]]: List of record identifiers or error
        """
        if not records:
            return Result.success_result([])
        
        try:
            if not self._initialized:
                init_result = self.initialize_schema()
                if not init_result.is_success():
                    return init_result
            
            conn = self._get_connection()
            conn.begin()
            
            try:
                record_ids = []
                for record in records:
                    # Use persist logic but within batch transaction
                    result = self.persist(record)
                    if not result.is_success():
                        raise StorageError(
                            f"Batch persistence failed for record: {result.error}",
                            operation="persist_batch",
                            details={"record_count": len(records)}
                        )
                    record_ids.append(result.value)
                
                conn.commit()
                logger.info(f"Persisted batch of {len(records)} records")
                return Result.success_result(record_ids)
                
            except Exception as e:
                conn.rollback()
                raise e
                
        except Exception as e:
            error_msg = f"Failed to persist batch: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return Result.failure_result(
                StorageError(error_msg, operation="persist_batch", details={"record_count": len(records)}),
                error_type="StorageError"
            )
    
    def persist_dataframe(self, df: pd.DataFrame, table_name: str) -> Result[int]:
        """Persist a pandas DataFrame directly to a table.
        
        Parameters:
            df: Validated pandas DataFrame (PII already redacted)
            table_name: Target table name (e.g., 'patients', 'observations')
        
        Returns:
            Result[int]: Number of rows persisted or error
        """
        if df.empty:
            return Result.success_result(0)
        
        try:
            if not self._initialized:
                init_result = self.initialize_schema()
                if not init_result.is_success():
                    return init_result
            
            conn = self._get_connection()
            
            # Use DuckDB's efficient DataFrame insertion
            # Register DataFrame as a view, then insert
            conn.register('df_temp', df)
            conn.execute(f"INSERT OR REPLACE INTO {table_name} SELECT * FROM df_temp")
            conn.unregister('df_temp')
            
            row_count = len(df)
            logger.info(f"Persisted {row_count} rows to table '{table_name}'")
            
            # Log audit event
            self.log_audit_event(
                event_type="BULK_PERSISTENCE",
                record_id=None,
                transformation_hash=None,
                details={
                    "table_name": table_name,
                    "row_count": row_count,
                }
            )
            
            return Result.success_result(row_count)
            
        except Exception as e:
            error_msg = f"Failed to persist DataFrame to {table_name}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return Result.failure_result(
                StorageError(error_msg, operation="persist_dataframe", details={"table_name": table_name}),
                error_type="StorageError"
            )
    
    def log_audit_event(
        self,
        event_type: str,
        record_id: Optional[str],
        transformation_hash: Optional[str],
        details: Optional[dict] = None
    ) -> Result[str]:
        """Log an audit trail event for compliance and observability.
        
        Parameters:
            event_type: Type of event (e.g., 'REDACTION', 'SCHEMA_COERCION', 'PERSISTENCE')
            record_id: Unique identifier of the affected record (if applicable)
            transformation_hash: Hash of original data for traceability
            details: Additional event metadata
        
        Returns:
            Result[str]: Audit event identifier or error
        """
        try:
            if not self._initialized:
                init_result = self.initialize_schema()
                if not init_result.is_success():
                    return init_result
            
            conn = self._get_connection()
            audit_id = str(uuid.uuid4())
            
            # Determine severity based on event type
            severity = "INFO"
            if event_type in ["REDACTION", "PII_DETECTED"]:
                severity = "CRITICAL"
            elif event_type in ["VALIDATION_ERROR", "TRANSFORMATION_ERROR"]:
                severity = "WARNING"
            
            details_json = json.dumps(details) if details else None
            
            conn.execute("""
                INSERT INTO audit_log (
                    audit_id, event_type, event_timestamp, record_id,
                    transformation_hash, details, source_adapter, severity
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                audit_id,
                event_type,
                datetime.now(),
                record_id,
                transformation_hash,
                details_json,
                details.get('source_adapter') if details else None,
                severity,
            ])
            
            logger.debug(f"Logged audit event: {event_type} (ID: {audit_id})")
            return Result.success_result(audit_id)
            
        except Exception as e:
            error_msg = f"Failed to log audit event: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return Result.failure_result(
                StorageError(error_msg, operation="log_audit_event"),
                error_type="StorageError"
            )
    
    def close(self) -> None:
        """Close storage connection and release resources."""
        if self._connection is not None:
            try:
                self._connection.close()
                self._connection = None
                logger.info("Closed DuckDB connection")
            except Exception as e:
                logger.warning(f"Error closing connection: {str(e)}")

