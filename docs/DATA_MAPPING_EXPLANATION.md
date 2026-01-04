# Data Mapping: CSV/JSON → Database Tables

This document explains how data flows from CSV and JSON files into the PostgreSQL database tables.

## Overview

The system uses a **two-stage transformation**:

1. **Ingestion Stage**: CSV/JSON → `GoldenRecord` structure
2. **Persistence Stage**: `GoldenRecord` → Database tables (patients, encounters, observations)

## Architecture

```
CSV/JSON File
    ↓
[Ingester] → Maps source data to domain models
    ↓
GoldenRecord {
    patient: PatientRecord
    encounters: List[EncounterRecord]
    observations: List[ClinicalObservation]
}
    ↓
[Storage Adapter] → Persists to database
    ↓
PostgreSQL Tables {
    patients
    encounters
    observations
}
```

## CSV Data Mapping

### Column Mapping

CSV columns are mapped to domain model fields using a **column mapping dictionary**:

```python
column_mapping = {
    "patient_id": "MRN",           # CSV column "MRN" → PatientRecord.patient_id
    "first_name": "FirstName",      # CSV column "FirstName" → PatientRecord.first_name
    "last_name": "LastName",       # CSV column "LastName" → PatientRecord.last_name
    "date_of_birth": "DOB",        # CSV column "DOB" → PatientRecord.date_of_birth
    "gender": "Gender",            # CSV column "Gender" → PatientRecord.gender
    # ... etc
}
```

### Example CSV File

```csv
MRN,FirstName,LastName,DOB,Gender,SSN,Phone,Email,Address,City,State,ZIP
MRN001,John,Doe,1990-01-01,male,123-45-6789,555-123-4567,john@example.com,123 Main St,Springfield,IL,62701
```

### How CSV Data Maps to Tables

1. **Patient Data** (always present):
   - All columns that map to `PatientRecord` fields → `patients` table
   - Example: `MRN` → `patient_id`, `FirstName` → `family_name` (after redaction), etc.

2. **Encounter Data** (optional):
   - If CSV has columns like `encounter_id`, `class_code`, `period_start`, etc.
   - These are extracted via `_extract_encounter_data()` method
   - Mapped to `EncounterRecord` → `encounters` table

3. **Observation Data** (optional):
   - If CSV has columns like `observation_id`, `category`, `code`, `value`, etc.
   - These are extracted via `_extract_observation_data()` method
   - Mapped to `ClinicalObservation` → `observations` table

### CSV Processing Flow

```python
# 1. Read CSV row
row = {"MRN": "MRN001", "FirstName": "John", "LastName": "Doe", ...}

# 2. Map columns using column_mapping
patient_data = {
    "patient_id": row["MRN"],           # "MRN001"
    "first_name": row["FirstName"],     # "John" (will be redacted)
    "last_name": row["LastName"],       # "Doe" (will be redacted)
    ...
}

# 3. Create PatientRecord (PII redaction happens here)
patient = PatientRecord(**patient_data)

# 4. Check for encounter/observation columns
encounter_data = _extract_encounter_data(row, column_mapping)
observation_data = _extract_observation_data(row, column_mapping)

# 5. Create GoldenRecord
golden_record = GoldenRecord(
    patient=patient,
    encounters=[encounter] if encounter_data else [],
    observations=[observation] if observation_data else []
)

# 6. Persist to database
storage_adapter.persist(golden_record)
# → patient → patients table
# → encounters → encounters table
# → observations → observations table
```

## JSON Data Mapping

### JSON Structure

JSON files are expected to have a nested structure:

```json
{
  "patient": {
    "patient_id": "MRN001",
    "first_name": "John",
    "last_name": "Doe",
    "date_of_birth": "1990-01-01",
    ...
  },
  "encounters": [
    {
      "encounter_id": "ENC001",
      "patient_id": "MRN001",
      "status": "finished",
      "class_code": "outpatient",
      ...
    }
  ],
  "observations": [
    {
      "observation_id": "OBS001",
      "patient_id": "MRN001",
      "category": "vital-signs",
      "code": "8480-6",
      "value": "120/80",
      ...
    }
  ]
}
```

### How JSON Data Maps to Tables

1. **Patient Data**:
   - `patient` object → `PatientRecord` → `patients` table
   - The JSON ingester extracts `record.get('patient', {})` and flattens it

2. **Encounter Data**:
   - `encounters` array → List of `EncounterRecord` → `encounters` table
   - Each object in the array becomes one row in the `encounters` table

3. **Observation Data**:
   - `observations` array → List of `ClinicalObservation` → `observations` table
   - Each object in the array becomes one row in the `observations` table

### JSON Processing Flow

```python
# 1. Read JSON record
record = {
    "patient": {"patient_id": "MRN001", "first_name": "John", ...},
    "encounters": [{"encounter_id": "ENC001", ...}],
    "observations": [{"observation_id": "OBS001", ...}]
}

# 2. Extract patient data
patient_data = record.get('patient', {})

# 3. Create PatientRecord (PII redaction happens here)
patient = PatientRecord(**patient_data)

# 4. Extract encounters
encounters = []
for enc_data in record.get('encounters', []):
    encounter = EncounterRecord(**enc_data)
    encounters.append(encounter)

# 5. Extract observations
observations = []
for obs_data in record.get('observations', []):
    observation = ClinicalObservation(**obs_data)
    observations.append(observation)

# 6. Create GoldenRecord
golden_record = GoldenRecord(
    patient=patient,
    encounters=encounters,
    observations=observations
)

# 7. Persist to database
storage_adapter.persist(golden_record)
# → patient → patients table
# → encounters → encounters table (one row per encounter)
# → observations → observations table (one row per observation)
```

## Database Table Mapping

The `GoldenRecord` structure directly maps to database tables:

### `patients` Table

All fields from `PatientRecord` model:

```python
patient = record.patient  # PatientRecord instance
patient_dict = patient.model_dump()

# Inserted into patients table:
INSERT INTO patients (
    patient_id, identifiers, family_name, given_names, 
    date_of_birth, gender, ...
) VALUES (
    patient_dict['patient_id'],
    patient_dict['identifiers'],  # Array
    patient_dict['family_name'],
    patient_dict['given_names'],  # Array
    ...
)
```

### `encounters` Table

Each `EncounterRecord` in `record.encounters` becomes one row:

```python
for encounter in record.encounters:  # List[EncounterRecord]
    encounter_dict = encounter.model_dump()
    
    # Inserted into encounters table:
    INSERT INTO encounters (
        encounter_id, patient_id, status, class_code, ...
    ) VALUES (
        encounter_dict['encounter_id'],
        encounter_dict['patient_id'],  # Links to patients table
        encounter_dict['status'],
        ...
    )
```

### `observations` Table

Each `ClinicalObservation` in `record.observations` becomes one row:

```python
for observation in record.observations:  # List[ClinicalObservation]
    observation_dict = observation.model_dump()
    
    # Inserted into observations table:
    INSERT INTO observations (
        observation_id, patient_id, encounter_id, 
        category, code, value, ...
    ) VALUES (
        observation_dict['observation_id'],
        observation_dict['patient_id'],  # Links to patients table
        observation_dict.get('encounter_id'),  # Optional link to encounters
        observation_dict['category'],
        ...
    )
```

## Key Points

1. **CSV**: One row = One `GoldenRecord` (typically only patient data, encounters/observations optional)
2. **JSON**: One JSON object = One `GoldenRecord` (can contain patient + multiple encounters + multiple observations)
3. **GoldenRecord**: Container that holds patient + encounters + observations
4. **Database**: 
   - One `GoldenRecord` → One row in `patients` table
   - One `GoldenRecord` → N rows in `encounters` table (one per encounter)
   - One `GoldenRecord` → N rows in `observations` table (one per observation)

## Foreign Key Relationships

- `encounters.patient_id` → `patients.patient_id`
- `observations.patient_id` → `patients.patient_id`
- `observations.encounter_id` → `encounters.encounter_id` (optional)

These relationships are enforced by the database schema and ensure referential integrity.

