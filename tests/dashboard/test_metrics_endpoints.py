"""Tests for metrics endpoints.

This test suite verifies that the metrics endpoints return correct data
and handle edge cases properly.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from src.dashboard.api.main import app
from src.domain.ports import Result, StoragePort


@pytest.fixture
def mock_storage_adapter():
    """Create a mock storage adapter with query capabilities."""
    mock = Mock(spec=StoragePort)
    mock.db_config = Mock()
    mock.db_config.db_type = "duckdb"
    mock.db_config.db_path = ":memory:"
    mock._initialized = True
    
    # Mock connection and query results
    mock_conn = Mock()
    
    # Mock query results for different tables
    def mock_execute(query, params=None):
        result_mock = Mock()
        
        # Patients count query
        if "FROM patients" in query and "COUNT(*)" in query:
            result_mock.fetchone.return_value = (100,)
        # Encounters count query
        elif "FROM encounters" in query and "COUNT(*)" in query:
            result_mock.fetchone.return_value = (50,)
        # Observations count query
        elif "FROM observations" in query and "COUNT(*)" in query:
            result_mock.fetchone.return_value = (200,)
        # Logs queries
        elif "FROM logs" in query:
            if "COUNT(*)" in query and "GROUP BY" not in query:
                result_mock.fetchone.return_value = (150,)
            elif "GROUP BY field_name" in query:
                result_mock.fetchall.return_value = [
                    ("ssn", 50),
                    ("phone", 60),
                    ("email", 40)
                ]
            elif "GROUP BY rule_triggered" in query:
                result_mock.fetchall.return_value = [
                    ("SSN_PATTERN", 50),
                    ("PHONE_PATTERN", 60),
                    ("EMAIL_PATTERN", 40)
                ]
            elif "GROUP BY source_adapter" in query:
                result_mock.fetchall.return_value = [
                    ("csv_ingester", 80),
                    ("json_ingester", 50),
                    ("xml_ingester", 20)
                ]
            elif "GROUP BY DATE" in query:
                result_mock.fetchall.return_value = [
                    (datetime.now().date(), 25),
                    ((datetime.now() - timedelta(days=1)).date(), 30),
                ]
            elif "COUNT(DISTINCT ingestion_id)" in query:
                result_mock.fetchone.return_value = (10,)
            else:
                result_mock.fetchone.return_value = (0,)
        # Audit log queries
        elif "FROM audit_log" in query:
            if "COUNT(*)" in query and "GROUP BY" not in query:
                result_mock.fetchone.return_value = (75,)
            elif "GROUP BY severity" in query:
                result_mock.fetchall.return_value = [
                    ("CRITICAL", 40),
                    ("WARNING", 25),
                    ("INFO", 10)
                ]
            elif "GROUP BY event_type" in query:
                result_mock.fetchall.return_value = [
                    ("REDACTION", 40),
                    ("VALIDATION_ERROR", 25),
                    ("PERSISTENCE", 10)
                ]
            else:
                result_mock.fetchone.return_value = (0,)
        else:
            result_mock.fetchone.return_value = (0,)
        
        return result_mock
    
    mock_conn.execute.side_effect = mock_execute
    mock._get_connection = Mock(return_value=mock_conn)
    
    return mock


@pytest.fixture
def client(mock_storage_adapter):
    """Create a test client with mocked storage adapter."""
    from src.dashboard.api.dependencies import get_storage_adapter
    
    app.dependency_overrides[get_storage_adapter] = lambda: mock_storage_adapter
    
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


class TestOverviewMetricsEndpoint:
    """Test the overview metrics endpoint."""
    
    def test_overview_metrics_returns_200(self, client):
        """Test that overview metrics endpoint returns 200."""
        response = client.get("/api/metrics/overview")
        
        assert response.status_code == 200
    
    def test_overview_metrics_has_required_fields(self, client):
        """Test that overview metrics has all required fields."""
        response = client.get("/api/metrics/overview")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "time_range" in data
        assert "ingestions" in data
        assert "records" in data
        assert "redactions" in data
        
        # Check ingestions structure
        assert "total" in data["ingestions"]
        assert "successful" in data["ingestions"]
        assert "failed" in data["ingestions"]
        assert "success_rate" in data["ingestions"]
        
        # Check records structure
        assert "total_processed" in data["records"]
        assert "total_successful" in data["records"]
        assert "total_failed" in data["records"]
        
        # Check redactions structure
        assert "total" in data["redactions"]
        assert "by_field" in data["redactions"]
    
    def test_overview_metrics_accepts_time_range(self, client):
        """Test that overview metrics accepts time_range parameter."""
        response = client.get("/api/metrics/overview?time_range=7d")
        
        assert response.status_code == 200
        data = response.json()
        assert data["time_range"] == "7d"
    
    def test_overview_metrics_validates_time_range(self, client):
        """Test that overview metrics validates time_range parameter."""
        response = client.get("/api/metrics/overview?time_range=invalid")
        
        # Should return 422 (validation error) for invalid time range
        assert response.status_code == 422
    
    def test_overview_metrics_returns_numeric_values(self, client):
        """Test that overview metrics returns numeric values."""
        response = client.get("/api/metrics/overview")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check that numeric fields are numbers
        assert isinstance(data["ingestions"]["total"], int)
        assert isinstance(data["ingestions"]["successful"], int)
        assert isinstance(data["ingestions"]["failed"], int)
        assert isinstance(data["ingestions"]["success_rate"], (int, float))
        assert isinstance(data["records"]["total_processed"], int)
        assert isinstance(data["redactions"]["total"], int)


class TestSecurityMetricsEndpoint:
    """Test the security metrics endpoint."""
    
    def test_security_metrics_returns_200(self, client):
        """Test that security metrics endpoint returns 200."""
        response = client.get("/api/metrics/security")
        
        assert response.status_code == 200
    
    def test_security_metrics_has_required_fields(self, client):
        """Test that security metrics has all required fields."""
        response = client.get("/api/metrics/security")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "time_range" in data
        assert "redactions" in data
        assert "audit_events" in data
        
        # Check redactions structure
        assert "total" in data["redactions"]
        assert "by_rule" in data["redactions"]
        assert "by_adapter" in data["redactions"]
        assert "trend" in data["redactions"]
        
        # Check audit_events structure
        assert "total" in data["audit_events"]
        assert "by_severity" in data["audit_events"]
        assert "by_type" in data["audit_events"]
    
    def test_security_metrics_accepts_time_range(self, client):
        """Test that security metrics accepts time_range parameter."""
        response = client.get("/api/metrics/security?time_range=30d")
        
        assert response.status_code == 200
        data = response.json()
        assert data["time_range"] == "30d"
    
    def test_security_metrics_trend_is_list(self, client):
        """Test that security metrics trend is a list."""
        response = client.get("/api/metrics/security")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["redactions"]["trend"], list)


class TestPerformanceMetricsEndpoint:
    """Test the performance metrics endpoint."""
    
    def test_performance_metrics_returns_200(self, client):
        """Test that performance metrics endpoint returns 200."""
        response = client.get("/api/metrics/performance")
        
        assert response.status_code == 200
    
    def test_performance_metrics_has_required_fields(self, client):
        """Test that performance metrics has all required fields."""
        response = client.get("/api/metrics/performance")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "time_range" in data
        assert "throughput" in data
        assert "latency" in data
        assert "file_processing" in data
        assert "memory" in data
        
        # Check throughput structure
        assert "records_per_second" in data["throughput"]
        
        # Check latency structure
        assert "avg_processing_time_ms" in data["latency"]
        
        # Check file_processing structure
        assert "total_files" in data["file_processing"]
        
        # Check memory structure
        assert "avg_peak_memory_mb" in data["memory"]
    
    def test_performance_metrics_accepts_time_range(self, client):
        """Test that performance metrics accepts time_range parameter."""
        response = client.get("/api/metrics/performance?time_range=1h")
        
        assert response.status_code == 200
        data = response.json()
        assert data["time_range"] == "1h"
    
    def test_performance_metrics_throughput_is_numeric(self, client):
        """Test that performance metrics throughput is numeric."""
        response = client.get("/api/metrics/performance")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["throughput"]["records_per_second"], (int, float))


class TestMetricsErrorHandling:
    """Test error handling in metrics endpoints."""
    
    def test_metrics_endpoints_handle_database_errors(self, client, mock_storage_adapter):
        """Test that metrics endpoints handle database errors gracefully."""
        # Make _get_connection raise an exception
        mock_storage_adapter._get_connection.side_effect = Exception("Database error")
        
        # All metrics endpoints should still return 200 (graceful degradation)
        # or 500 with proper error message
        response = client.get("/api/metrics/overview")
        assert response.status_code in [200, 500]
        
        response = client.get("/api/metrics/security")
        assert response.status_code in [200, 500]
        
        response = client.get("/api/metrics/performance")
        assert response.status_code in [200, 500]
    
    def test_metrics_endpoints_handle_missing_tables(self, client, mock_storage_adapter):
        """Test that metrics endpoints handle missing tables gracefully."""
        # Make queries raise exceptions (simulating missing tables)
        mock_conn = mock_storage_adapter._get_connection.return_value
        mock_conn.execute.side_effect = Exception("Table does not exist")
        
        # Should return 200 with zero values or 500
        response = client.get("/api/metrics/overview")
        assert response.status_code in [200, 500]

