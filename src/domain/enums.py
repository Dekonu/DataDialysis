"""FHIR-Compliant Enumeration Definitions.

This module defines enumerations that conform to Fast Healthcare Interoperability
Resources (FHIR) R5 standards. These enums ensure interoperability with FHIR-compliant
systems and provide standardized values for clinical data.

Security Impact:
    - Enums provide type safety and prevent invalid values from entering the system
    - FHIR compliance ensures compatibility with healthcare data exchange standards
    - Standardized values reduce data quality issues and improve auditability

Architecture:
    - Pure domain enums with zero infrastructure dependencies
    - Values align with FHIR R5 specification (https://www.hl7.org/fhir/resourcelist.html)
    - Enums are used in domain models to enforce data quality at the boundary
"""

from enum import Enum


class AdministrativeGender(str, Enum):
    """FHIR R5 AdministrativeGender code system.
    
    Represents the gender of a person for administrative purposes.
    Aligns with FHIR Patient.gender field.
    
    Values:
        MALE: Male
        FEMALE: Female
        OTHER: Other gender identity
        UNKNOWN: Unknown or not specified
    """
    
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"


class ObservationStatus(str, Enum):
    """FHIR R5 ObservationStatus code system.
    
    Represents the status of an observation result.
    Aligns with FHIR Observation.status field.
    
    Values:
        REGISTERED: Registered but not yet verified
        PRELIMINARY: Preliminary result
        FINAL: Final result
        AMENDED: Amended result
        CORRECTED: Corrected result
        CANCELLED: Cancelled
        ENTERED_IN_ERROR: Entered in error
        UNKNOWN: Unknown status
    """
    
    REGISTERED = "registered"
    PRELIMINARY = "preliminary"
    FINAL = "final"
    AMENDED = "amended"
    CORRECTED = "corrected"
    CANCELLED = "cancelled"
    ENTERED_IN_ERROR = "entered-in-error"
    UNKNOWN = "unknown"


class EncounterStatus(str, Enum):
    """FHIR R5 EncounterStatus code system.
    
    Represents the status of an encounter.
    Aligns with FHIR Encounter.status field.
    
    Values:
        PLANNED: Planned encounter
        ARRIVED: Patient has arrived
        TRIAGED: Patient is being triaged
        IN_PROGRESS: Encounter in progress
        ONLEAVE: Patient on leave
        FINISHED: Encounter finished
        CANCELLED: Cancelled
        ENTERED_IN_ERROR: Entered in error
        UNKNOWN: Unknown status
    """
    
    PLANNED = "planned"
    ARRIVED = "arrived"
    TRIAGED = "triaged"
    IN_PROGRESS = "in-progress"
    ONLEAVE = "onleave"
    FINISHED = "finished"
    CANCELLED = "cancelled"
    ENTERED_IN_ERROR = "entered-in-error"
    UNKNOWN = "unknown"


class IdentifierUse(str, Enum):
    """FHIR R5 IdentifierUse code system.
    
    Represents the use of an identifier.
    Aligns with FHIR Identifier.use field.
    
    Values:
        USUAL: Usual identifier
        OFFICIAL: Official identifier
        TEMP: Temporary identifier
        SECONDARY: Secondary identifier
        OLD: Old identifier (deprecated)
    """
    
    USUAL = "usual"
    OFFICIAL = "official"
    TEMP = "temp"
    SECONDARY = "secondary"
    OLD = "old"


class AddressUse(str, Enum):
    """FHIR R5 AddressUse code system.
    
    Represents the use of an address.
    Aligns with FHIR Address.use field.
    
    Values:
        HOME: Home address
        WORK: Work address
        TEMP: Temporary address
        OLD: Old address (deprecated)
        BILLING: Billing address
    """
    
    HOME = "home"
    WORK = "work"
    TEMP = "temp"
    OLD = "old"
    BILLING = "billing"


class ContactPointSystem(str, Enum):
    """FHIR R5 ContactPointSystem code system.
    
    Represents the type of contact point (telecom).
    Aligns with FHIR ContactPoint.system field.
    
    Values:
        PHONE: Phone
        FAX: Fax
        EMAIL: Email
        PAGER: Pager
        URL: URL
        SMS: SMS
        OTHER: Other
    """
    
    PHONE = "phone"
    FAX = "fax"
    EMAIL = "email"
    PAGER = "pager"
    URL = "url"
    SMS = "sms"
    OTHER = "other"


class EncounterClass(str, Enum):
    """FHIR R5 Encounter.class code system.
    
    Represents the classification of patient encounter type.
    Aligns with FHIR Encounter.class field.
    
    Values:
        INPATIENT: Patient admitted to hospital
        OUTPATIENT: Patient visit without admission
        AMBULATORY: Ambulatory care encounter
        EMERGENCY: Emergency department encounter
        VIRTUAL: Virtual/telehealth encounter
        OBSERVATION: Observation stay
        URGENT_CARE: Urgent care facility encounter
    """
    
    INPATIENT = "inpatient"
    OUTPATIENT = "outpatient"
    AMBULATORY = "ambulatory"
    EMERGENCY = "emergency"
    VIRTUAL = "virtual"
    OBSERVATION = "observation"
    URGENT_CARE = "urgent-care"


class ObservationCategory(str, Enum):
    """FHIR R5 ObservationCategoryCodes code system.
    
    Represents the category of clinical observation.
    Aligns with FHIR Observation.category field.
    
    Values:
        VITAL_SIGNS: Vital signs measurements
        LABORATORY: Laboratory test results
        IMAGING: Imaging studies
        PROCEDURE: Procedure-related observations
        SURVEY: Survey/assessment results
        EXAM: Physical examination findings
        THERAPY: Therapy-related observations
        ACTIVITY: Activity-related observations
    """
    
    VITAL_SIGNS = "vital-signs"
    LABORATORY = "laboratory"
    IMAGING = "imaging"
    PROCEDURE = "procedure"
    SURVEY = "survey"
    EXAM = "exam"
    THERAPY = "therapy"
    ACTIVITY = "activity"

