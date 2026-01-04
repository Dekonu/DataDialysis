# DuckDB Integration Tests Setup Guide

This guide explains how to set up and run the DuckDB integration tests that verify the complete data flow.

## Prerequisites

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify DuckDB Installation**
   ```bash
   python -c "import duckdb; print(duckdb.__version__)"
   ```

## Test Structure

The integration tests (`test_duckdb_integration.py`) verify:

1. **CSV Flow**: CSV → Pandas → Redaction → DuckDB
2. **JSON Flow**: JSON → Pandas → Redaction → DuckDB  
3. **XML Flow**: XML → GoldenRecord → Redaction → DuckDB
4. **Audit Trail**: Verification that audit logs are maintained
5. **End-to-End**: Complete flow with validation

## Running Tests

### Run All DuckDB Integration Tests
```bash
pytest tests/test_duckdb_integration.py -v
```

### Run Specific Test Class
```bash
# CSV flow tests
pytest tests/test_duckdb_integration.py::TestCSVToDuckDBFlow -v

# JSON flow tests
pytest tests/test_duckdb_integration.py::TestJSONToDuckDBFlow -v

# XML flow tests
pytest tests/test_duckdb_integration.py::TestXMLToDuckDBFlow -v

# Audit trail tests
pytest tests/test_duckdb_integration.py::TestAuditTrail -v
```

### Run Specific Test
```bash
pytest tests/test_duckdb_integration.py::TestCSVToDuckDBFlow::test_csv_ingestion_to_duckdb -v
```

## What the Tests Verify

### 1. Data Ingestion
- Files are correctly parsed (CSV/JSON/XML)
- Adapters are selected automatically
- Data is converted to appropriate format (DataFrame or GoldenRecord)

### 2. PII Redaction
- Names are redacted (set to None or "[REDACTED]")
- SSNs are redacted
- Phone numbers are redacted
- Email addresses are redacted
- Dates of birth are redacted
- Addresses are redacted
- Notes containing PII are redacted

### 3. Data Validation
- Records pass Pydantic validation
- Invalid records are rejected
- Schema constraints are enforced

### 4. Persistence
- Data is successfully persisted to DuckDB
- Tables are created correctly
- Foreign key relationships are maintained
- Indexes are created

### 5. Audit Trail
- Audit log entries are created
- Event types are correct
- Severity levels are appropriate
- Source adapter information is recorded

## Test Data

Tests use temporary files created by pytest fixtures:
- `csv_test_file`: Sample CSV with PII
- `json_test_file`: Sample JSON with patient/encounter/observation data
- `xml_test_file`: Sample XML with PII
- `xml_config_file`: XML mapping configuration

All test data is cleaned up automatically after tests complete.

## Database Location

Tests use temporary DuckDB databases created in pytest's `tmp_path` directory. These are automatically cleaned up after tests complete.

## Troubleshooting

### Import Errors
If you see `ModuleNotFoundError`, ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### DuckDB Connection Errors
- Ensure DuckDB is installed: `pip install duckdb>=1.0.0`
- Check file permissions for database directory
- Verify sufficient disk space

### Test Failures
- Check that PII redaction is working (names should be None or "[REDACTED]")
- Verify schema initialization succeeds
- Check audit log entries are being created

## Example Output

Successful test run should show:
```
tests/test_duckdb_integration.py::TestCSVToDuckDBFlow::test_csv_ingestion_to_duckdb PASSED
tests/test_duckdb_integration.py::TestJSONToDuckDBFlow::test_json_ingestion_to_duckdb PASSED
tests/test_duckdb_integration.py::TestXMLToDuckDBFlow::test_xml_ingestion_to_duckdb PASSED
tests/test_duckdb_integration.py::TestAuditTrail::test_audit_trail_logging PASSED
```

## Next Steps

After running tests, you can:
1. Run the end-to-end example: `python examples/end_to_end_flow.py`
2. Use the main entry point: `python -m src.main --input data/patients.csv`
3. Inspect the DuckDB database using DuckDB CLI or Python

