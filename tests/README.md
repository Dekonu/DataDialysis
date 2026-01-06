# Data-Dialysis Test Suite

Comprehensive test suite for the Data-Dialysis pipeline, organized by test type and component.

## Directory Structure

```
tests/
├── unit/              # Unit tests (fast, isolated)
│   ├── test_config_manager_connection_string.py
│   └── test_golden_record.py
├── integration/        # Integration tests (components working together)
│   ├── test_csv_ingestion.py
│   ├── test_json_ingestion.py
│   ├── test_xml_ingestion.py
│   ├── test_xml_streaming.py
│   ├── test_duckdb_integration.py
│   └── test_security_bad_data.py
├── adapters/          # Storage adapter tests
│   ├── test_postgres_adapter.py
│   └── test_postgresql_adapter_dataframe.py
├── dashboard/         # Dashboard API tests
│   ├── test_dashboard_api.py
│   └── README.md
├── test_data/         # Test data files
│   ├── test_batch.csv
│   ├── test_batch.json
│   └── test_batch.xml
└── docs/              # Test documentation
    ├── README_DUCKDB_SETUP.md
    └── TEST_PLAN.md
```

## Running Tests

### Run All Tests
```bash
pytest tests/ -v
```

### Run by Category

**Unit Tests:**
```bash
pytest tests/unit/ -v
```

**Integration Tests:**
```bash
pytest tests/integration/ -v
```

**Adapter Tests:**
```bash
pytest tests/adapters/ -v
```

**Dashboard Tests:**
```bash
pytest tests/dashboard/ -v
```

### Run Specific Test File
```bash
pytest tests/unit/test_golden_record.py -v
```

### Run with Coverage
```bash
pytest tests/ --cov=src --cov-report=html
```

## Test Organization Principles

1. **Unit Tests** (`tests/unit/`)
   - Test individual functions/classes in isolation
   - Fast execution (< 1 second per test)
   - Minimal dependencies
   - Mock external dependencies

2. **Integration Tests** (`tests/integration/`)
   - Test multiple components working together
   - May use real databases/files
   - Slower execution (acceptable)
   - Test end-to-end flows

3. **Adapter Tests** (`tests/adapters/`)
   - Test storage adapter implementations
   - Verify database interactions
   - Test adapter-specific features

4. **Dashboard Tests** (`tests/dashboard/`)
   - Test dashboard API endpoints
   - Verify API responses and behavior
   - Test middleware and error handling

## Test Data

Test data files are stored in `tests/test_data/`:
- `test_batch.csv` - CSV test data
- `test_batch.json` - JSON test data
- `test_batch.xml` - XML test data

Additional test data may be generated during test execution in temporary directories.

## Documentation

- `docs/README_DUCKDB_SETUP.md` - DuckDB setup instructions
- `docs/TEST_PLAN.md` - Overall test plan and strategy
- `dashboard/README.md` - Dashboard-specific test documentation

## Best Practices

1. **Isolation**: Each test should be independent
2. **Naming**: Use descriptive test names (`test_<what>_<expected_behavior>`)
3. **Fixtures**: Use pytest fixtures for common setup
4. **Assertions**: Clear, specific assertions
5. **Documentation**: Tests serve as documentation

## Continuous Integration

All tests should pass before merging:
- Unit tests: Fast feedback (< 30 seconds)
- Integration tests: Comprehensive validation (< 5 minutes)
- Full suite: Complete verification

---

**Last Updated**: January 2025

