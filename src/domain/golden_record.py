"""Golden Record Schema Definitions.

This module defines the canonical data models (Golden Records) for clinical entities.
These schemas represent the "ideal" structure that all ingested data must conform to
after passing through the Safety Layer and Sieve.

Security Impact:
    - All PII fields are explicitly marked and will be redacted by the Sieve
    - Schema validation prevents malformed data from reaching persistence
    - Type safety enforced at runtime via Pydantic V2

Architecture:
    - Pure domain models with zero infrastructure dependencies
    - Models are immutable and validated before use
    - Follows Hexagonal Architecture: Domain Core is isolated from Adapters
"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class PatientRecord(BaseModel):
    """Golden record for patient demographic information.
    
    Security Impact: Contains PII fields (name, ssn, dob) that must be redacted
    before persistence. The Sieve layer will mask these values.
    
    Parameters:
        patient_id: Unique identifier (non-PII, safe to persist)
        first_name: Patient first name (PII - will be redacted)
        last_name: Patient last name (PII - will be redacted)
        date_of_birth: Patient date of birth (PII - will be redacted)
        ssn: Social Security Number (PII - will be redacted)
        gender: Patient gender (standardized values)
        address_line1: Street address (PII - will be redacted)
        address_line2: Apartment/suite (PII - will be redacted)
        city: City name (may be redacted depending on policy)
        state: State code (standardized 2-letter code)
        zip_code: ZIP code (may be partially redacted)
        phone: Phone number (PII - will be redacted)
        email: Email address (PII - will be redacted)
    """
    
    patient_id: str = Field(..., description="Unique patient identifier")
    first_name: Optional[str] = Field(None, description="Patient first name (PII)")
    last_name: Optional[str] = Field(None, description="Patient last name (PII)")
    date_of_birth: Optional[date] = Field(None, description="Date of birth (PII)")
    ssn: Optional[str] = Field(None, description="Social Security Number (PII)")
    gender: Optional[str] = Field(None, description="Gender (M/F/O/U)")
    address_line1: Optional[str] = Field(None, description="Street address (PII)")
    address_line2: Optional[str] = Field(None, description="Address line 2 (PII)")
    city: Optional[str] = Field(None, description="City name")
    state: Optional[str] = Field(None, description="State code (2-letter)")
    zip_code: Optional[str] = Field(None, description="ZIP code")
    phone: Optional[str] = Field(None, description="Phone number (PII)")
    email: Optional[str] = Field(None, description="Email address (PII)")
    
    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: Optional[str]) -> Optional[str]:
        """Standardize gender values."""
        if v is None:
            return v
        v_upper = v.upper().strip()
        valid_genders = {"M", "F", "O", "U", "MALE", "FEMALE", "OTHER", "UNKNOWN"}
        if v_upper in valid_genders:
            # Normalize to single letter
            mapping = {"MALE": "M", "FEMALE": "F", "OTHER": "O", "UNKNOWN": "U"}
            return mapping.get(v_upper, v_upper[0])
        return v
    
    @field_validator("state")
    @classmethod
    def validate_state(cls, v: Optional[str]) -> Optional[str]:
        """Normalize state codes to uppercase."""
        if v is None:
            return v
        return v.upper().strip()[:2] if len(v.strip()) >= 2 else v.upper().strip()
    
    @field_validator("ssn")
    @classmethod
    def validate_ssn_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate SSN format (will be redacted by Sieve, but validate structure)."""
        if v is None:
            return v
        # Remove common separators
        cleaned = v.replace("-", "").replace(" ", "")
        if cleaned.isdigit() and len(cleaned) == 9:
            return cleaned
        # If format is invalid, return as-is (Sieve will handle redaction)
        return v
    
    model_config = ConfigDict(
        frozen=True,  # Immutable records
        str_strip_whitespace=True,
    )


class ClinicalObservation(BaseModel):
    """Golden record for clinical measurements and observations.
    
    Security Impact: May contain PHI in notes field. The Sieve will redact
    any PII detected in unstructured text.
    
    Parameters:
        observation_id: Unique observation identifier
        patient_id: Reference to patient (foreign key)
        encounter_id: Reference to encounter/visit
        observation_type: Type of observation (e.g., "VITAL_SIGN", "LAB_RESULT")
        observation_code: Standardized code (e.g., LOINC, SNOMED)
        value: Numeric or text value of observation
        unit: Unit of measurement
        effective_date: When observation was taken
        notes: Unstructured clinical notes (may contain PII)
    """
    
    observation_id: str = Field(..., description="Unique observation identifier")
    patient_id: str = Field(..., description="Reference to patient")
    encounter_id: Optional[str] = Field(None, description="Reference to encounter")
    observation_type: str = Field(..., description="Type of observation")
    observation_code: Optional[str] = Field(None, description="Standardized code (LOINC/SNOMED)")
    value: Optional[str] = Field(None, description="Observation value")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    effective_date: Optional[datetime] = Field(None, description="When observation was taken")
    notes: Optional[str] = Field(None, description="Clinical notes (may contain PII)")
    
    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
    )


class EncounterRecord(BaseModel):
    """Golden record for patient encounters/visits.
    
    Security Impact: Contains encounter dates and types. May reference
    PII indirectly through patient_id.
    
    Parameters:
        encounter_id: Unique encounter identifier
        patient_id: Reference to patient
        encounter_type: Type of encounter (e.g., "INPATIENT", "OUTPATIENT", "EMERGENCY")
        start_date: Encounter start date/time
        end_date: Encounter end date/time
        facility_name: Name of facility (may be redacted if contains location PII)
        diagnosis_codes: List of diagnosis codes (e.g., ICD-10)
    """
    
    encounter_id: str = Field(..., description="Unique encounter identifier")
    patient_id: str = Field(..., description="Reference to patient")
    encounter_type: str = Field(..., description="Type of encounter")
    start_date: Optional[datetime] = Field(None, description="Encounter start")
    end_date: Optional[datetime] = Field(None, description="Encounter end")
    facility_name: Optional[str] = Field(None, description="Facility name")
    diagnosis_codes: list[str] = Field(default_factory=list, description="Diagnosis codes")
    
    @field_validator("encounter_type")
    @classmethod
    def validate_encounter_type(cls, v: str) -> str:
        """Standardize encounter types."""
        v_upper = v.upper().strip()
        valid_types = {
            "INPATIENT", "OUTPATIENT", "EMERGENCY", "AMBULATORY",
            "OBSERVATION", "URGENT_CARE", "TELEHEALTH"
        }
        if v_upper in valid_types:
            return v_upper
        # If not in standard list, return normalized version
        return v_upper.replace(" ", "_")
    
    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
    )


class GoldenRecord(BaseModel):
    """Container for a complete golden record set.
    
    This model represents a fully validated, standardized clinical record
    that has passed through the Safety Layer and Sieve. All PII has been
    redacted and schema validation has been enforced.
    
    Security Impact: This is the "safe" record that can be persisted.
    All PII fields in nested models have been processed by the Sieve.
    
    Parameters:
        patient: Patient demographic record (PII redacted)
        encounters: List of encounter records
        observations: List of clinical observations
        ingestion_timestamp: When this record was ingested and validated
        source_adapter: Which adapter provided the raw data
        transformation_hash: Hash of original data for audit trail
    """
    
    patient: PatientRecord = Field(..., description="Patient record (PII redacted)")
    encounters: list[EncounterRecord] = Field(
        default_factory=list,
        description="List of encounter records"
    )
    observations: list[ClinicalObservation] = Field(
        default_factory=list,
        description="List of clinical observations"
    )
    ingestion_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When record was ingested"
    )
    source_adapter: str = Field(..., description="Source adapter identifier")
    transformation_hash: Optional[str] = Field(
        None,
        description="Hash of original data for audit trail"
    )
    
    model_config = ConfigDict(frozen=True)

