# Comprehensive Test Plan for Patient Data System

Based on FHIR R5 compliance, HIPAA security requirements, and clinical data validation best practices.

## 1. Pattern Validation Tests

### 1.1 State Code Pattern Validation
- [ ] Valid 2-letter state codes (CA, NY, TX, etc.)
- [ ] Invalid 3+ letter state codes should fail
- [ ] Invalid single letter should fail
- [ ] Lowercase state codes should be normalized to uppercase
- [ ] Empty string should pass (optional field)
- [ ] Special characters should fail

### 1.2 Postal Code Pattern Validation
- [ ] Valid 5-digit ZIP (12345)
- [ ] Valid 9-digit ZIP with dash (12345-6789)
- [ ] Invalid 4-digit ZIP should fail
- [ ] Invalid 6-digit ZIP should fail
- [ ] ZIP with letters should fail
- [ ] ZIP with spaces should fail
- [ ] Empty string should pass (optional field)

### 1.3 Country Code Pattern Validation
- [ ] Valid 2-letter ISO codes (US, CA, MX)
- [ ] Valid 3-letter ISO codes (USA, CAN)
- [ ] Invalid 1-letter should fail
- [ ] Invalid 4+ letter should fail
- [ ] Lowercase should be normalized
- [ ] Empty string should pass (optional field)

### 1.4 Language Code Pattern Validation
- [ ] Valid 2-letter language code (en, es, fr)
- [ ] Valid language-region code (en-US, es-MX)
- [ ] Invalid single letter should fail
- [ ] Invalid format without dash should fail
- [ ] Empty string should pass (optional field)

### 1.5 Observation Code Pattern Validation
- [ ] Valid LOINC format (85354-9)
- [ ] Valid SNOMED format (123456789)
- [ ] Invalid format with special chars should fail
- [ ] Empty string should pass (optional field)

### 1.6 ICD-10 Diagnosis Code Pattern Validation
- [ ] Valid ICD-10 code (I10, E11.9)
- [ ] Valid ICD-10 with decimal (A00.1)
- [ ] Invalid format without letter prefix should fail
- [ ] Invalid format with wrong structure should fail
- [ ] Empty list should pass

## 2. FHIR R5 Enum Validation Tests

### 2.1 ObservationStatus Enum
- [ ] All valid status values (registered, preliminary, final, amended, corrected, cancelled, entered-in-error, unknown)
- [ ] Case-insensitive matching
- [ ] Underscore/hyphen variations (entered-in-error vs entered_in_error)
- [ ] Invalid status values should default to 'final'
- [ ] None should default to 'final'

### 2.2 EncounterStatus Enum
- [ ] All valid status values (planned, arrived, triaged, in-progress, onleave, finished, cancelled, entered-in-error, unknown)
- [ ] Case-insensitive matching
- [ ] Underscore/hyphen variations
- [ ] Invalid status values should default to 'finished'
- [ ] None should default to 'finished'

### 2.3 AddressUse Enum
- [ ] All valid values (home, work, temp, old, billing)
- [ ] Case-insensitive matching
- [ ] "temporary" should map to "temp"
- [ ] Invalid values should default to 'home'
- [ ] None should pass (optional field)

### 2.4 AdministrativeGender Enum
- [ ] All valid values (male, female, other, unknown)
- [ ] Single letter abbreviations (m, f, o, u)
- [ ] Case-insensitive matching
- [ ] Invalid values should default to 'unknown'
- [ ] None should pass (optional field)

## 3. PII Redaction Comprehensive Tests

### 3.1 Name Redaction Edge Cases
- [ ] Single letter names (should not redact if not capitalized)
- [ ] Multiple middle names in given_names list
- [ ] Hyphenated names (Mary-Jane, O'Brien)
- [ ] Names with apostrophes
- [ ] Very long names (>50 characters)
- [ ] Names with numbers (should not redact)
- [ ] Empty name strings
- [ ] Names with special characters
- [ ] Name prefixes (Dr., Mr., Mrs., Ms.)
- [ ] Name suffixes (Jr., Sr., III, IV)

### 3.2 SSN Redaction Edge Cases
- [ ] SSN with spaces (123 45 6789)
- [ ] SSN with mixed separators
- [ ] Partial SSN matches (should not redact)
- [ ] SSN in different positions in text
- [ ] Multiple SSNs in same field
- [ ] SSN-like numbers that aren't SSNs (phone numbers, etc.)
- [ ] Empty SSN field

### 3.3 Phone Number Redaction Edge Cases
- [ ] International format (+1-555-123-4567)
- [ ] Phone with extension (555-123-4567 ext 123)
- [ ] Phone with parentheses ((555) 123-4567)
- [ ] Phone with dots (555.123.4567)
- [ ] Phone with spaces (555 123 4567)
- [ ] Toll-free numbers (800, 888, 877, etc.)
- [ ] Invalid phone formats should not redact

### 3.4 Email Redaction Edge Cases
- [ ] Email with subdomain (user@mail.example.com)
- [ ] Email with plus addressing (user+tag@example.com)
- [ ] Email with special characters (user.name@example.com)
- [ ] Invalid email formats should not redact
- [ ] Multiple emails in same field

### 3.5 Address Redaction Edge Cases
- [ ] PO Box addresses
- [ ] Rural route addresses (RR 1 Box 123)
- [ ] Apartment/suite numbers
- [ ] Addresses with unit numbers
- [ ] International addresses
- [ ] Addresses without street numbers (should not redact)

### 3.6 Date of Birth Redaction
- [ ] DOB is always redacted to None (regardless of format)
- [ ] None DOB remains None
- [ ] Valid DOB becomes None after redaction
- [ ] Invalid DOB (after validation) should still be None

### 3.7 ZIP Code Partial Redaction
- [ ] 5-digit ZIP (12345 -> 12***)
- [ ] 9-digit ZIP (12345-6789 -> 12***)
- [ ] Invalid ZIP formats should not be redacted
- [ ] Empty ZIP should remain empty

### 3.8 Unstructured Text Redaction
- [ ] Clinical notes with mixed PII types
- [ ] PII at beginning of text
- [ ] PII at end of text
- [ ] PII in middle of text
- [ ] Multiple instances of same PII type
- [ ] PII across line breaks
- [ ] Very long text (>1000 characters)
- [ ] Text with no PII (should remain unchanged)
- [ ] Text with only partial PII matches

## 4. Data Quality & Validation Tests

### 4.1 MRN Format Validation
- [ ] Valid alphanumeric MRNs
- [ ] MRNs with hyphens
- [ ] MRNs with underscores
- [ ] MRNs that are too short (<3 chars)
- [ ] MRNs that are too long (>20 chars)
- [ ] MRNs with special characters (should fail)
- [ ] Empty MRN (should fail)
- [ ] Whitespace-only MRN (should fail)

### 4.2 Date Validation Edge Cases
- [ ] Leap year dates (Feb 29)
- [ ] Invalid month (13) should fail
- [ ] Invalid day (32) should fail
- [ ] Date strings in various formats
- [ ] Timezone-aware datetimes
- [ ] Timezone-naive datetimes
- [ ] Dates at boundary (1900-01-01, today)

### 4.3 Age Validation
- [ ] Age exactly 150 years (should pass)
- [ ] Age 150.1 years (should fail)
- [ ] Age 0 years (newborn, should pass)
- [ ] Negative age calculation (should not occur)

### 4.4 Required Field Validation
- [ ] Missing required patient_id (should fail)
- [ ] Missing required observation_id (should fail)
- [ ] Missing required encounter_id (should fail)
- [ ] Missing required category (should fail)
- [ ] Missing required class_code (should fail)

## 5. FHIR R5 Field Tests

### 5.1 PatientRecord FHIR R5 Fields
- [ ] identifiers list with multiple identifiers
- [ ] given_names list with multiple names
- [ ] name_prefix list functionality
- [ ] name_suffix list functionality
- [ ] deceased boolean and deceased_date consistency
- [ ] address_use enum validation
- [ ] emergency_contact fields redaction
- [ ] language code validation
- [ ] Backward compatibility with deprecated fields

### 5.2 ClinicalObservation FHIR R5 Fields
- [ ] status enum validation
- [ ] category enum validation (new field)
- [ ] code pattern validation
- [ ] issued datetime validation
- [ ] performer_name redaction
- [ ] interpretation text redaction
- [ ] body_site pattern validation
- [ ] method pattern validation
- [ ] device pattern validation
- [ ] Backward compatibility with observation_type

### 5.3 EncounterRecord FHIR R5 Fields
- [ ] status enum validation
- [ ] class_code enum validation (new field)
- [ ] type pattern validation
- [ ] service_type pattern validation
- [ ] priority pattern validation
- [ ] reason_code pattern validation
- [ ] diagnosis_codes list validation
- [ ] location_address redaction
- [ ] participant_name redaction
- [ ] Backward compatibility with encounter_type

## 6. Security & Compliance Tests

### 6.1 PII Leakage Prevention
- [ ] No PII in patient_id field
- [ ] No PII in observation_id field
- [ ] No PII in encounter_id field
- [ ] No PII in diagnosis_codes
- [ ] No PII in non-PII fields after redaction

### 6.2 Reversibility Tests
- [ ] Redacted SSN cannot be reversed
- [ ] Redacted names cannot be reversed
- [ ] Redacted DOB (None) cannot be reversed
- [ ] Redacted addresses cannot be reversed
- [ ] Redacted phone/email cannot be reversed

### 6.3 Audit Trail Tests
- [ ] transformation_hash is generated
- [ ] ingestion_timestamp is set
- [ ] source_adapter is recorded
- [ ] All fields are immutable after creation

### 6.4 Data Integrity Tests
- [ ] Redaction doesn't corrupt data structure
- [ ] List fields remain lists after redaction
- [ ] Optional fields can be None
- [ ] Required fields cannot be None

## 7. Edge Cases & Error Handling

### 7.1 Malformed Data Tests
- [ ] SQL injection attempts in string fields
- [ ] XSS attempts in text fields
- [ ] Extremely long strings (>10,000 chars)
- [ ] Unicode characters in names
- [ ] Emoji in text fields
- [ ] Null bytes in strings
- [ ] Control characters in strings

### 7.2 Boundary Value Tests
- [ ] Minimum valid MRN length (3 chars)
- [ ] Maximum valid MRN length (20 chars)
- [ ] Minimum valid date (1900-01-01)
- [ ] Maximum valid date (today)
- [ ] Maximum age (150 years)
- [ ] Minimum age (0 years, born today)

### 7.3 Type Coercion Tests
- [ ] String numbers converted to appropriate types
- [ ] String dates converted to date objects
- [ ] String booleans converted to boolean
- [ ] Invalid type conversions should fail gracefully

## 8. Integration & Composition Tests

### 8.1 GoldenRecord Composition
- [ ] Patient with multiple encounters
- [ ] Patient with multiple observations
- [ ] Encounter with multiple diagnosis codes
- [ ] Observation with all optional fields populated
- [ ] Empty lists for encounters/observations
- [ ] Very large lists (100+ items)

### 8.2 Cross-Reference Validation
- [ ] patient_id consistency across records
- [ ] encounter_id references in observations
- [ ] Foreign key relationships maintained

## 9. Performance Tests

### 9.1 Redaction Performance
- [ ] Large text redaction (<100ms for 10KB text)
- [ ] Multiple PII types in single field
- [ ] Batch processing of 1000+ records
- [ ] Memory usage with large datasets

### 9.2 Validation Performance
- [ ] Pattern validation performance
- [ ] Enum validation performance
- [ ] Date validation performance
- [ ] Large list validation performance

## 10. Adversarial Tests (Security)

### 10.1 Injection Attempts
- [ ] Script injection in name fields
- [ ] SQL injection in identifier fields
- [ ] Command injection in text fields
- [ ] Path traversal in file references

### 10.2 Data Poisoning
- [ ] Extremely large values causing overflow
- [ ] Negative values where not expected
- [ ] Special Unicode characters causing parsing issues
- [ ] Zero-width characters in text

### 10.3 Bypass Attempts
- [ ] Attempting to bypass redaction by encoding
- [ ] Attempting to bypass validation with edge cases
- [ ] Attempting to modify immutable records
- [ ] Attempting to inject PII in non-PII fields

## 11. FHIR R5 Compliance Tests

### 11.1 Resource Structure
- [ ] Patient resource structure matches FHIR R5
- [ ] Observation resource structure matches FHIR R5
- [ ] Encounter resource structure matches FHIR R5
- [ ] Required FHIR fields are present
- [ ] Optional FHIR fields are handled correctly

### 11.2 Code System Compliance
- [ ] AdministrativeGender values match FHIR spec
- [ ] ObservationStatus values match FHIR spec
- [ ] EncounterStatus values match FHIR spec
- [ ] ObservationCategory values match FHIR spec
- [ ] EncounterClass values match FHIR spec

## 12. Data Consistency Tests

### 12.1 Temporal Consistency
- [ ] Encounter end_date after start_date
- [ ] Observation effective_date not in future
- [ ] Deceased_date after date_of_birth
- [ ] Issued date after effective_date (if both present)

### 12.2 Logical Consistency
- [ ] Deceased flag matches deceased_date
- [ ] Address use matches address type
- [ ] Emergency contact relationship is valid
- [ ] Participant role is valid

## Priority Levels

**P0 (Critical - Must Have):**
- Pattern validation tests (1.1-1.6)
- PII redaction basic tests (3.1-3.8)
- MRN validation (4.1)
- Date validation (4.2)
- Required field validation (4.4)
- Security tests (6.1-6.2)

**P1 (High - Should Have):**
- FHIR enum validation (2.1-2.4)
- FHIR R5 field tests (5.1-5.3)
- Edge cases (7.1-7.3)
- Integration tests (8.1-8.2)

**P2 (Medium - Nice to Have):**
- Performance tests (9.1-9.2)
- Adversarial tests (10.1-10.3)
- Data consistency tests (12.1-12.2)

**P3 (Low - Future):**
- Advanced FHIR compliance (11.1-11.2)
- Extended edge cases

