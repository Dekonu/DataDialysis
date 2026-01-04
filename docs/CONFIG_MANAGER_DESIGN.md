# Configuration Manager Design

## Overview

The Configuration Manager provides secure, type-safe handling of database credentials and application settings. It follows security best practices for credential management in clinical environments and supports multiple credential sources.

## Security Principles

### 1. **Never Log Credentials**
- All passwords and connection strings are stored as `SecretStr` (Pydantic's secure string type)
- Credentials are never included in error messages or stack traces
- Logging is explicitly disabled for sensitive fields

### 2. **Fail-Fast Validation**
- Configuration is validated at load time using Pydantic models
- Invalid configurations are rejected immediately, preventing runtime errors
- Type safety ensures correct usage throughout the application

### 3. **Multiple Credential Sources**
- **Environment Variables**: Primary method for containerized deployments
- **Configuration Files**: JSON/YAML files for local development
- **Secrets Managers**: AWS Secrets Manager, Azure Key Vault, HashiCorp Vault (extensible)

### 4. **Path Traversal Protection**
- File paths are validated to prevent directory traversal attacks
- Database paths are checked for existence before use
- Relative paths are resolved safely

## Architecture

### Hexagonal Architecture Compliance
- **Infrastructure Layer**: Configuration manager is isolated from domain core
- **Port Interface**: `DatabaseConfig` model defines the contract
- **Adapter Pattern**: Multiple credential source adapters (env, file, secrets managers)

### Type Safety
- Pydantic models ensure type correctness at runtime
- `SecretStr` prevents accidental credential exposure
- Validation happens at initialization, not at use time

## Usage Examples

### Environment Variables (Recommended for Production)

```bash
# Set environment variables
export DD_DB_TYPE=duckdb
export DD_DB_PATH=/data/clinical.duckdb
export DD_DB_PASSWORD=secret_password  # Never log this!
```

```python
from src.infrastructure.config_manager import get_database_config
from src.adapters.storage.duckdb_adapter import DuckDBAdapter

# Load from environment
db_config = get_database_config()
adapter = DuckDBAdapter(db_config=db_config)
```

### Configuration File (Recommended for Development)

```json
{
  "database": {
    "db_type": "duckdb",
    "db_path": "data/clinical.duckdb",
    "username": "admin",
    "password": "dev_password"
  }
}
```

```python
from src.infrastructure.config_manager import ConfigManager
from src.adapters.storage.duckdb_adapter import DuckDBAdapter

# Load from file
config = ConfigManager.from_file("config.json")
db_config = config.get_database_config()
adapter = DuckDBAdapter(db_config=db_config)
```

### PostgreSQL Example

```python
from src.infrastructure.config_manager import ConfigManager
from src.adapters.storage.postgresql_adapter import PostgreSQLAdapter

# Set environment variables
os.environ["DD_DB_TYPE"] = "postgresql"
os.environ["DD_DB_HOST"] = "db.example.com"
os.environ["DD_DB_PORT"] = "5432"
os.environ["DD_DB_NAME"] = "clinical_db"
os.environ["DD_DB_USER"] = "admin"
os.environ["DD_DB_PASSWORD"] = "secret_password"
os.environ["DD_DB_SSL_MODE"] = "require"

config = ConfigManager.from_environment()
db_config = config.get_database_config()

# Create PostgreSQL adapter using DatabaseConfig (recommended)
adapter = PostgreSQLAdapter(db_config=db_config)

# Or use connection string directly (backward compatibility)
# adapter = PostgreSQLAdapter(connection_string=db_config.get_connection_string())

result = adapter.initialize_schema()
if result.is_success():
    result = adapter.persist(golden_record)
```

## Supported Database Types

1. **DuckDB** (Default)
   - File-based or in-memory
   - No authentication required
   - Best for analytical workloads

2. **PostgreSQL**
   - Network-based
   - Requires host, port, database, username, password
   - Supports SSL connections

3. **MySQL**
   - Network-based
   - Requires host, port, database, username, password
   - Supports SSL connections

4. **SQLite**
   - File-based
   - No authentication required
   - Best for small-scale deployments

## Security Best Practices

### 1. **File Permissions**
Configuration files containing credentials should have restricted permissions:
```bash
chmod 600 config.json  # Owner read/write only
```

### 2. **Environment Variables**
- Never commit `.env` files to version control
- Use secrets management in CI/CD pipelines
- Rotate credentials regularly

### 3. **Connection Strings**
- Prefer individual parameters over connection strings when possible
- Connection strings are stored as `SecretStr` to prevent logging
- SSL is required for production network databases

### 4. **Validation**
- All configuration is validated at load time
- Invalid configurations fail immediately (fail-fast)
- Type safety prevents common errors

## Extension Points

### Adding New Credential Sources

To add support for a new credential source (e.g., AWS Secrets Manager):

```python
class ConfigManager:
    @classmethod
    def from_aws_secrets_manager(cls, secret_name: str) -> 'ConfigManager':
        """Load configuration from AWS Secrets Manager."""
        import boto3
        
        client = boto3.client('secretsmanager')
        response = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(response['SecretString'])
        
        return cls(secret)
```

### Adding New Database Types

To add support for a new database type:

1. Add to `DatabaseConfig.validate_db_type()`:
```python
supported_types = ["duckdb", "postgresql", "mysql", "sqlite", "new_db_type"]
```

2. Add connection string logic to `DatabaseConfig.get_connection_string()`:
```python
if self.db_type == "new_db_type":
    return f"newdb://{username}:{password}@{host}:{port}/{database}"
```

## Testing

### Unit Tests
- Test configuration loading from various sources
- Test validation of invalid configurations
- Test credential masking in logs

### Integration Tests
- Test actual database connections with test credentials
- Test connection string generation
- Test error handling for missing credentials

## Future Enhancements

1. **Secrets Manager Integration**
   - AWS Secrets Manager
   - Azure Key Vault
   - HashiCorp Vault

2. **Credential Rotation**
   - Automatic credential refresh
   - Support for multiple credential versions

3. **Configuration Validation**
   - Schema validation for configuration files
   - Environment-specific validation rules

4. **Audit Logging**
   - Log configuration changes (without credentials)
   - Track credential access

