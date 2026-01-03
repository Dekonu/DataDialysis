"""Tests for golden record schemas.

These tests verify that the domain models correctly validate and transform
clinical data according to the golden record schema.
"""

from datetime import date, datetime
import pytest
from pydantic import ValidationError

from src.domain.golden_record import (
    PatientRecord,
    ClinicalObservation,
    EncounterRecord,
    GoldenRecord,
)


class TestPatientRecord:
    """Test suite for PatientRecord model."""
    
    def test_valid_patient_record(self):
        """Test creating a valid patient record."""
        patient = PatientRecord(
            patient_id="P001",
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1980, 1, 15),
            ssn="123456789",
            gender="M",
            state="CA",
        )
        assert patient.patient_id == "P001"
        assert patient.first_name == "John"
        assert patient.gender == "M"
    
    def test_gender_normalization(self):
        """Test that gender values are normalized correctly."""
        patient_male = PatientRecord(patient_id="P001", gender="male")
        assert patient_male.gender == "M"
        
        patient_female = PatientRecord(patient_id="P002", gender="FEMALE")
        assert patient_female.gender == "F"
        
        patient_other = PatientRecord(patient_id="P003", gender="O")
        assert patient_other.gender == "O"
    
    def test_state_normalization(self):
        """Test that state codes are normalized to uppercase."""
        patient = PatientRecord(patient_id="P001", state="ca")
        assert patient.state == "CA"
        
        patient_long = PatientRecord(patient_id="P002", state="california")
        assert patient_long.state == "CA"
    
    def test_ssn_validation(self):
        """Test SSN format validation."""
        # Valid SSN with dashes
        patient = PatientRecord(patient_id="P001", ssn="123-45-6789")
        assert patient.ssn == "123456789"
        
        # Valid SSN without dashes
        patient2 = PatientRecord(patient_id="P002", ssn="987654321")
        assert patient2.ssn == "987654321"
    
    def test_immutable_record(self):
        """Test that records are immutable."""
        patient = PatientRecord(patient_id="P001", first_name="John")
        
        with pytest.raises(ValidationError):
            # Attempting to modify should raise an error
            patient.first_name = "Jane"


class TestClinicalObservation:
    """Test suite for ClinicalObservation model."""
    
    def test_valid_observation(self):
        """Test creating a valid clinical observation."""
        observation = ClinicalObservation(
            observation_id="O001",
            patient_id="P001",
            observation_type="VITAL_SIGN",
            observation_code="85354-9",
            value="120/80",
            unit="mmHg",
            effective_date=datetime(2024, 1, 15, 10, 30),
        )
        assert observation.observation_id == "O001"
        assert observation.observation_type == "VITAL_SIGN"
        assert observation.value == "120/80"


class TestEncounterRecord:
    """Test suite for EncounterRecord model."""
    
    def test_valid_encounter(self):
        """Test creating a valid encounter record."""
        encounter = EncounterRecord(
            encounter_id="E001",
            patient_id="P001",
            encounter_type="OUTPATIENT",
            start_date=datetime(2024, 1, 15, 9, 0),
            end_date=datetime(2024, 1, 15, 10, 0),
            diagnosis_codes=["I10", "E11.9"],
        )
        assert encounter.encounter_id == "E001"
        assert encounter.encounter_type == "OUTPATIENT"
        assert len(encounter.diagnosis_codes) == 2
    
    def test_encounter_type_normalization(self):
        """Test that encounter types are normalized."""
        encounter = EncounterRecord(
            encounter_id="E001",
            patient_id="P001",
            encounter_type="inpatient",
        )
        assert encounter.encounter_type == "INPATIENT"
        
        encounter2 = EncounterRecord(
            encounter_id="E002",
            patient_id="P001",
            encounter_type="urgent care",
        )
        assert encounter2.encounter_type == "URGENT_CARE"


class TestGoldenRecord:
    """Test suite for GoldenRecord container model."""
    
    def test_complete_golden_record(self):
        """Test creating a complete golden record."""
        patient = PatientRecord(patient_id="P001", first_name="John")
        encounter = EncounterRecord(
            encounter_id="E001",
            patient_id="P001",
            encounter_type="OUTPATIENT",
        )
        observation = ClinicalObservation(
            observation_id="O001",
            patient_id="P001",
            observation_type="LAB_RESULT",
        )
        
        golden = GoldenRecord(
            patient=patient,
            encounters=[encounter],
            observations=[observation],
            source_adapter="json_adapter",
        )
        
        assert golden.patient.patient_id == "P001"
        assert len(golden.encounters) == 1
        assert len(golden.observations) == 1
        assert golden.source_adapter == "json_adapter"
        assert golden.ingestion_timestamp is not None

