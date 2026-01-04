# Hybrid Redaction Logging Implementation

## Overview

This document describes the implementation of the hybrid approach for redaction logging using context variables. This approach maintains architectural integrity while providing complete logging coverage.

## Architecture

### Components

1. **`redaction_context.py`** - Context variable management
   - `ContextVar` for thread-safe context passing
   - `redaction_context()` context manager
   - `log_redaction_if_context()` helper function

2. **Domain Validators** (`golden_record.py`)
   - Updated to call `log_redaction_if_context()` after redaction
   - Graceful degradation if context not available (tests work)

3. **Main Pipeline** (`main.py`)
   - Sets redaction context before processing
   - Context available to all validators during ingestion

4. **Ingesters** (CSV, JSON, XML)
   - Update context with `record_id` when available
   - Allows validators to log with correct record context

## Implementation Details

### Context Variable System

```python
# Infrastructure layer
from contextvars import ContextVar

_redaction_context = ContextVar('redaction_context', default=None)

def log_redaction_if_context(field_name, original_value, rule_triggered):
    """Log if context available, gracefully skip if not."""
    context = get_redaction_context()
    if context and context.get('logger'):
        context['logger'].log_redaction(...)
```

### Domain Validator Integration

```python
# Domain layer (golden_record.py)
@field_validator("phone", mode="before")
@classmethod
def redact_phone(cls, v: Optional[str]) -> Optional[str]:
    original = v
    result = RedactorService.redact_phone(v)
    if result != original:
        log_redaction_if_context("phone", original, "PHONE_PATTERN")
    return result
```

### Main Pipeline Integration

```python
# main.py
with redaction_context(
    logger=redaction_logger,
    source_adapter=adapter.adapter_name,
    ingestion_id=ingestion_id
):
    for result in adapter.ingest(source):
        # All validators can access context
        ...
```

### Ingester Integration

```python
# In ingesters (CSV/JSON/XML)
# Update context with record_id before validation
patient_id = row_dict.get('patient_id')
if patient_id:
    context = get_redaction_context()
    if context:
        set_redaction_context(
            logger=context.get('logger'),
            record_id=str(patient_id),
            source_adapter=context.get('source_adapter'),
            ingestion_id=context.get('ingestion_id')
        )

# Now create model - validators can log with record_id
patient = PatientRecord(**row_dict)
```

## Updated Validators

The following validators now log redactions:

- `redact_family_name` - NAME_PATTERN
- `redact_given_names` - NAME_PATTERN
- `redact_identifiers` - SSN_PATTERN
- `redact_phone` - PHONE_PATTERN
- `redact_email` - EMAIL_PATTERN
- `redact_ssn` - SSN_PATTERN
- `redact_address_line1` - ADDRESS_PATTERN
- `redact_address_line2` - ADDRESS_PATTERN
- `redact_emergency_contact_name` - NAME_PATTERN
- `redact_emergency_contact_phone` - PHONE_PATTERN
- `redact_fax` - PHONE_PATTERN
- `redact_performer_name` - NAME_PATTERN
- `redact_notes` - OBSERVATION_NOTES_PII_DETECTION
- `redact_interpretation` - UNSTRUCTURED_TEXT_PII_DETECTION

## Benefits

1. **Complete Coverage**: Logs all redactions (ingesters + validators)
2. **Architectural Integrity**: Domain doesn't directly import infrastructure
3. **Context Preservation**: record_id and source_adapter available
4. **Testable**: Works without context (graceful degradation)
5. **Thread-Safe**: Uses contextvars for concurrent execution

## Testing

Domain tests work without context:
```python
# No context set - logging gracefully skipped
patient = PatientRecord(patient_id="MRN001", phone="555-1234")
# Redaction happens, logging skipped (no context)
```

Integration tests with context:
```python
# Context set - logging enabled
with redaction_context(logger, record_id="MRN001", source_adapter="test"):
    patient = PatientRecord(patient_id="MRN001", phone="555-1234")
    # Redaction happens AND is logged
```

## Usage

The system automatically logs redactions when:
1. Context is set in `main.py` (always during ingestion)
2. Validators detect redaction (value changed)
3. Context has logger available

No code changes needed in domain models - logging is automatic when context is available.

