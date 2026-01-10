"""Tests for XML streaming mode selection and functionality.

These tests verify that the XML ingester correctly:
- Selects streaming mode for large files automatically
- Uses traditional mode for small files automatically
- Respects explicit streaming_enabled setting
- Handles both modes correctly
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.adapters.ingesters.xml_ingester import XMLIngester
from src.domain.ports import Result
from src.domain.golden_record import GoldenRecord


@pytest.fixture
def xml_config_dict():
    """XML configuration dictionary for testing."""
    return {
        "root_element": "./PatientRecord",
        "fields": {
            "patient_id": "./MRN",
            "first_name": "./Demographics/FullName",
            "date_of_birth": "./Demographics/BirthDate",
            "gender": "./Demographics/Gender",
            "ssn": "./Demographics/SSN",
            "phone": "./Demographics/Phone",
            "email": "./Demographics/Email",
            "address_line1": "./Demographics/Address/Street",
            "city": "./Demographics/Address/City",
            "state": "./Demographics/Address/State",
            "postal_code": "./Demographics/Address/ZIP",
        }
    }


@pytest.fixture
def small_xml_file(tmp_path, xml_config_dict):
    """Create a small XML file (< 100MB threshold)."""
    test_file = tmp_path / "small_test.xml"
    
    # Create XML with a few records (small file)
    xml_data = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalData>
    <PatientRecord>
        <MRN>MRN001</MRN>
        <Demographics>
            <FullName>John Doe</FullName>
            <BirthDate>1990-01-01</BirthDate>
            <Gender>male</Gender>
            <SSN>123-45-6789</SSN>
            <Phone>555-123-4567</Phone>
            <Email>john.doe@example.com</Email>
            <Address>
                <Street>123 Main St</Street>
                <City>Springfield</City>
                <State>IL</State>
                <ZIP>62701</ZIP>
            </Address>
        </Demographics>
    </PatientRecord>
    <PatientRecord>
        <MRN>MRN002</MRN>
        <Demographics>
            <FullName>Jane Smith</FullName>
            <BirthDate>1995-05-15</BirthDate>
            <Gender>female</Gender>
            <SSN>987-65-4321</SSN>
            <Phone>555-987-6543</Phone>
            <Email>jane.smith@example.com</Email>
            <Address>
                <Street>456 Oak Ave</Street>
                <City>Los Angeles</City>
                <State>CA</State>
                <ZIP>90210</ZIP>
            </Address>
        </Demographics>
    </PatientRecord>
</ClinicalData>"""
    
    test_file.write_text(xml_data, encoding='utf-8')
    return test_file


@pytest.fixture
def large_xml_file(tmp_path, xml_config_dict):
    """Create a large XML file (>= 100MB threshold) by repeating records.
    
    Note: For actual testing, we create a smaller file but use mocking
    to simulate a large file size. In production, this would be a genuinely
    large file that exceeds the threshold.
    """
    test_file = tmp_path / "large_test.xml"
    
    # Create a single record template
    record_template = """    <PatientRecord>
        <MRN>MRN{index:04d}</MRN>
        <Demographics>
            <FullName>Patient {index}</FullName>
            <BirthDate>1990-01-01</BirthDate>
            <Gender>male</Gender>
            <SSN>123-45-6789</SSN>
            <Phone>555-123-4567</Phone>
            <Email>patient{index}@example.com</Email>
            <Address>
                <Street>123 Main St {index}</Street>
                <City>Springfield</City>
                <State>IL</State>
                <ZIP>62701</ZIP>
            </Address>
        </Demographics>
    </PatientRecord>
"""
    
    # Write header
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<ClinicalData>\n')
        
        # Write enough records for testing (actual size will be mocked)
        # Each record is ~300 bytes
        for i in range(1000):  # 1000 records for testing
            f.write(record_template.format(index=i))
        
        f.write('</ClinicalData>\n')
    
    return test_file


@pytest.fixture
def xml_config_file(tmp_path, xml_config_dict):
    """Create XML configuration file."""
    config_file = tmp_path / "xml_config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(xml_config_dict, f, indent=2)
    return config_file


class TestXMLStreamingModeSelection:
    """Test automatic mode selection based on file size."""
    
    def test_automatic_mode_small_file_uses_traditional(self, small_xml_file, xml_config_file):
        """Test that small files automatically use traditional mode."""
        ingester = XMLIngester(
            config_path=str(xml_config_file),
            streaming_enabled=None  # Auto-detect
        )
        
        # Small file should use traditional mode (file is actually small)
        # The file is only a few KB, well below 100MB threshold
        assert ingester._should_use_streaming(str(small_xml_file)) == False
        
        # Verify it actually processes (traditional mode)
        results = list(ingester.ingest(str(small_xml_file)))
        assert len(results) > 0
    
    def test_automatic_mode_large_file_uses_streaming(self, large_xml_file, xml_config_file):
        """Test that large files automatically use streaming mode."""
        # Skip if lxml not available
        try:
            from lxml import etree
        except ImportError:
            pytest.skip("lxml not available, skipping streaming tests")
        
        ingester = XMLIngester(
            config_path=str(xml_config_file),
            streaming_enabled=None  # Auto-detect
        )
        
        # Mock Path.stat() to return large file size
        with patch('pathlib.Path.stat') as mock_stat:
            mock_stat_result = MagicMock()
            mock_stat_result.st_size = 150 * 1024 * 1024  # 150MB (> 100MB)
            mock_stat.return_value = mock_stat_result
            
            # Should use streaming mode
            assert ingester._should_use_streaming(str(large_xml_file)) == True
        
        # Verify streaming parser is initialized
        assert ingester._streaming_parser is not None
    
    def test_automatic_mode_respects_settings(self, small_xml_file, xml_config_file):
        """Test that automatic mode respects global settings."""
        # Test by explicitly setting streaming_enabled=False (simulating settings)
        # This tests the same behavior as when settings.xml_streaming_enabled=False
        ingester = XMLIngester(
            config_path=str(xml_config_file),
            streaming_enabled=False  # Simulates settings.xml_streaming_enabled=False
        )
        
        # Should not use streaming (explicitly disabled)
        assert ingester.streaming_enabled == False
        assert ingester._should_use_streaming(str(small_xml_file)) == False
        
        # Verify it works in traditional mode
        results = list(ingester.ingest(str(small_xml_file)))
        assert len(results) > 0


class TestXMLStreamingExplicitMode:
    """Test explicitly enabling/disabling streaming mode."""
    
    def test_explicit_streaming_enabled(self, small_xml_file, xml_config_file):
        """Test explicitly enabling streaming mode."""
        # Skip if lxml not available
        try:
            from lxml import etree
        except ImportError:
            pytest.skip("lxml not available, skipping streaming tests")
        
        ingester = XMLIngester(
            config_path=str(xml_config_file),
            streaming_enabled=True  # Explicitly enable
        )
        
        # Should use streaming regardless of file size when explicitly enabled
        # The file is small (< threshold), but streaming is explicitly enabled
        assert ingester._should_use_streaming(str(small_xml_file)) == True
        
        # Verify streaming parser is initialized
        assert ingester._streaming_parser is not None
    
    def test_explicit_streaming_disabled(self, large_xml_file, xml_config_file):
        """Test explicitly disabling streaming mode."""
        ingester = XMLIngester(
            config_path=str(xml_config_file),
            streaming_enabled=False  # Explicitly disable
        )
        
        # Should not use streaming regardless of file size
        with patch.object(Path, 'stat') as mock_stat:
            mock_stat.return_value.st_size = 150 * 1024 * 1024  # Large file
            assert ingester._should_use_streaming(str(large_xml_file)) == False
        
        # Verify traditional mode is used
        results = list(ingester.ingest(str(large_xml_file)))
        assert len(results) > 0


class TestXMLStreamingFunctionality:
    """Test that streaming mode actually works correctly."""
    
    def test_streaming_mode_processes_records(self, small_xml_file, xml_config_file):
        """Test that streaming mode processes records correctly."""
        # Skip if lxml not available
        try:
            from lxml import etree
        except ImportError:
            pytest.skip("lxml not available, skipping streaming tests")
        
        ingester = XMLIngester(
            config_path=str(xml_config_file),
            streaming_enabled=True,
            streaming_threshold=0  # Force streaming for any file
        )
        
        # Process file
        results = list(ingester.ingest(str(small_xml_file)))
        
        # Should yield results
        assert len(results) > 0
        
        # Check successful results
        success_results = [r for r in results if r.is_success()]
        assert len(success_results) > 0
        
        # Verify records are valid
        for result in success_results:
            # Unpack tuple: (GoldenRecord, original_record_data)
            golden_record, _ = result.value
            assert isinstance(golden_record, GoldenRecord)
            assert golden_record.patient.patient_id is not None
    
    def test_streaming_mode_redacts_pii(self, small_xml_file, xml_config_file):
        """Test that streaming mode correctly redacts PII."""
        # Skip if lxml not available
        try:
            from lxml import etree
        except ImportError:
            pytest.skip("lxml not available, skipping streaming tests")
        
        ingester = XMLIngester(
            config_path=str(xml_config_file),
            streaming_enabled=True,
            streaming_threshold=0
        )
        
        results = list(ingester.ingest(str(small_xml_file)))
        
        # Check PII redaction
        for result in results:
            if result.is_success():
                # Unpack tuple: (GoldenRecord, original_record_data)
                golden_record, _ = result.value
                patient = golden_record.patient
                # PII should be redacted
                assert patient.first_name == "[REDACTED]" or patient.first_name is None
                assert patient.date_of_birth is None  # DOB always redacted
                if patient.ssn:
                    assert patient.ssn == "***-**-****"
    
    def test_streaming_mode_handles_errors_gracefully(self, tmp_path, xml_config_file):
        """Test that streaming mode handles errors gracefully."""
        # Skip if lxml not available
        try:
            from lxml import etree
        except ImportError:
            pytest.skip("lxml not available, skipping streaming tests")
        
        # Create XML with invalid record
        invalid_xml = tmp_path / "invalid.xml"
        invalid_xml.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<ClinicalData>
    <PatientRecord>
        <MRN>MRN001</MRN>
        <Demographics>
            <FullName>Valid Patient</FullName>
            <BirthDate>1990-01-01</BirthDate>
            <Gender>male</Gender>
        </Demographics>
    </PatientRecord>
    <PatientRecord>
        <MRN>AB</MRN>  <!-- Invalid: too short -->
        <Demographics>
            <FullName>Invalid Patient</FullName>
        </Demographics>
    </PatientRecord>
</ClinicalData>""", encoding='utf-8')
        
        ingester = XMLIngester(
            config_path=str(xml_config_file),
            streaming_enabled=True,
            streaming_threshold=0
        )
        
        results = list(ingester.ingest(str(invalid_xml)))
        
        # Should have both success and failure results
        success_results = [r for r in results if r.is_success()]
        failure_results = [r for r in results if r.is_failure()]
        
        # At least one valid record
        assert len(success_results) >= 1
        # At least one invalid record
        assert len(failure_results) >= 1


class TestXMLStreamingMemoryEfficiency:
    """Test that streaming mode is memory efficient."""
    
    def test_streaming_mode_memory_usage(self, large_xml_file, xml_config_file):
        """Test that streaming mode uses less memory."""
        # Skip if lxml not available
        try:
            from lxml import etree
        except ImportError:
            pytest.skip("lxml not available, skipping streaming tests")
        
        import tracemalloc
        
        ingester = XMLIngester(
            config_path=str(xml_config_file),
            streaming_enabled=True,
            streaming_threshold=0
        )
        
        # Start memory tracking
        tracemalloc.start()
        
        # Process file
        count = 0
        for result in ingester.ingest(str(large_xml_file)):
            count += 1
            if count % 100 == 0:
                # Check memory usage periodically
                current, peak = tracemalloc.get_traced_memory()
                # Streaming should use < 50MB even for large files
                assert peak < 50 * 1024 * 1024, f"Memory usage too high: {peak / 1024 / 1024:.2f}MB"
            if count >= 500:  # Limit for test speed
                break
        
        tracemalloc.stop()
        
        # Verify we processed records
        assert count > 0


class TestXMLStreamingConfiguration:
    """Test streaming configuration options."""
    
    def test_custom_streaming_threshold(self, small_xml_file, xml_config_file):
        """Test custom streaming threshold."""
        # Skip if lxml not available
        try:
            from lxml import etree
        except ImportError:
            pytest.skip("lxml not available, skipping streaming tests")
        
        # Set very low threshold (1KB)
        ingester = XMLIngester(
            config_path=str(xml_config_file),
            streaming_enabled=True,
            streaming_threshold=1024  # 1KB
        )
        
        # Small file should use streaming (threshold is low, file is > 1KB)
        # The small_xml_file is actually a few KB, so it exceeds 1KB threshold
        assert ingester._should_use_streaming(str(small_xml_file)) == True
    
    def test_streaming_fallback_when_lxml_unavailable(self, small_xml_file, xml_config_file):
        """Test that ingester falls back to traditional mode when lxml unavailable."""
        # Mock the StreamingXMLParser import to raise ImportError
        # This simulates the scenario where lxml is not installed
        import sys
        original_import = __import__
        
        def mock_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == 'src.infrastructure.xml_streaming_parser' and 'StreamingXMLParser' in (fromlist or []):
                raise ImportError("lxml not available")
            return original_import(name, globals, locals, fromlist, level)
        
        # Patch __import__ to intercept the import
        with patch('builtins.__import__', side_effect=mock_import):
            # Clear module cache to force re-import
            if 'src.adapters.ingesters.xml_ingester' in sys.modules:
                del sys.modules['src.adapters.ingesters.xml_ingester']
            
            # Re-import to get fresh module with mocked import
            from src.adapters.ingesters.xml_ingester import XMLIngester
            
            # Create ingester - should catch ImportError in __init__ and disable streaming
            ingester = XMLIngester(
                config_path=str(xml_config_file),
                streaming_enabled=True  # Try to enable streaming
            )
            
            # Should fall back to traditional mode (streaming_enabled set to False in __init__)
            assert ingester.streaming_enabled == False
            assert ingester._streaming_parser is None
            
            # Should still work in traditional mode
            results = list(ingester.ingest(str(small_xml_file)))
            assert len(results) > 0

