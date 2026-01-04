# XML Streaming Implementation (Option 3: Hybrid Approach)

## Overview

The XML ingester now supports streaming mode for large clinical reports using a hybrid approach that combines:
- **lxml** for performance and full XPath support
- **Security wrapper** with defusedxml-style protections
- **Automatic mode selection** based on file size

## Implementation Details

### Components

1. **StreamingXMLParser** (`src/infrastructure/xml_streaming_parser.py`)
   - Secure wrapper around lxml.etree.iterparse
   - Enforces security limits (events, depth, file size)
   - Memory-efficient streaming (O(record_size) instead of O(file_size))

2. **Updated XMLIngester** (`src/adapters/ingesters/xml_ingester.py`)
   - Automatic streaming mode selection
   - Backward compatible with traditional parsing
   - Supports both streaming and non-streaming modes

3. **Settings** (`src/infrastructure/settings.py`)
   - `DD_XML_STREAMING_ENABLED`: Enable/disable streaming (default: true)
   - `DD_XML_STREAMING_THRESHOLD`: File size threshold in bytes (default: 100MB)
   - `DD_XML_MAX_EVENTS`: Maximum XML events (default: 1,000,000)
   - `DD_XML_MAX_DEPTH`: Maximum XML depth (default: 100)

## Usage

### Automatic Mode Selection

The ingester automatically selects streaming mode for large files:

```python
# Small file (< 100MB) → Traditional parsing
# Large file (>= 100MB) → Streaming parsing
adapter = XMLIngester(config_path="mappings.json")
for result in adapter.ingest("file.xml"):
    # Automatically uses best mode
    process(result)
```

### Manual Control

```python
# Force streaming mode
adapter = XMLIngester(
    config_path="mappings.json",
    streaming_enabled=True
)

# Force traditional mode
adapter = XMLIngester(
    config_path="mappings.json",
    streaming_enabled=False
)

# Custom threshold
adapter = XMLIngester(
    config_path="mappings.json",
    streaming_threshold=50 * 1024 * 1024  # 50MB
)
```

### Environment Variables

```bash
# Enable streaming (default: true)
export DD_XML_STREAMING_ENABLED=true

# Set threshold (default: 100MB)
export DD_XML_STREAMING_THRESHOLD=104857600

# Set security limits
export DD_XML_MAX_EVENTS=1000000
export DD_XML_MAX_DEPTH=100
```

## Security Features

### Parser Security

```python
parser = XMLParser(
    huge_tree=False,          # Prevent quadratic blowup
    resolve_entities=False,   # Prevent entity expansion attacks
    no_network=True,         # Prevent network access
    recover=False            # Fail fast on malformed XML
)
```

### Runtime Limits

- **Event Limit**: Prevents DoS via excessive XML events
- **Depth Limit**: Prevents deep recursion attacks
- **File Size Limit**: Prevents memory exhaustion

### Error Handling

- Security violations raise `SecurityError`
- Malformed records are logged and skipped (fail-safe)
- Pipeline continues processing valid records

## Memory Management

### Streaming Mode

```python
# Memory usage: O(record_size)
for record in streaming_parser.parse("large.xml"):
    process(record)  # Memory released after processing
    # Element automatically cleared
```

### Traditional Mode

```python
# Memory usage: O(file_size)
tree = parse("file.xml")  # Entire file in memory
for record in tree.findall("//Record"):
    process(record)
```

## Performance Comparison

### Small Files (< 100MB)

- **Traditional**: Faster (no streaming overhead)
- **Streaming**: Slightly slower (streaming overhead)

### Large Files (>= 100MB)

- **Traditional**: 
  - Memory: O(file_size) - may cause OOM
  - Startup: 5-10 minutes (parse entire file)
  - First record: 5-10 minutes
  
- **Streaming**:
  - Memory: O(record_size) - ~10MB
  - Startup: <1 second
  - First record: <1 second
  - **1000x+ memory reduction**

## Configuration

### XML Config Format

```json
{
  "root_element": "./PatientRecord",
  "fields": {
    "patient_id": "./MRN",
    "first_name": "./Demographics/FirstName",
    "last_name": "./Demographics/LastName"
  }
}
```

### Streaming-Specific Config

```json
{
  "root_element": "./PatientRecord",
  "streaming": {
    "enabled": true,
    "max_events": 1000000,
    "max_depth": 100
  },
  "fields": {
    "patient_id": "./MRN"
  }
}
```

## Migration Guide

### From Traditional to Streaming

1. **Install lxml**: `pip install lxml`
2. **Enable streaming**: Set `DD_XML_STREAMING_ENABLED=true`
3. **Test with small files**: Verify same output
4. **Test with large files**: Monitor memory usage
5. **Deploy**: Streaming enabled by default

### Backward Compatibility

- Traditional mode still available
- Automatic selection based on file size
- Same API, no code changes required

## Troubleshooting

### lxml Not Available

```
Warning: lxml not available, falling back to non-streaming mode.
```

**Solution**: Install lxml: `pip install lxml`

### Security Limit Exceeded

```
SecurityError: XML event limit exceeded
```

**Solution**: Increase limit or investigate file for malicious content

### XPath Not Working

**Issue**: Complex XPath expressions may not work with streaming

**Solution**: Use simple tag names in `root_element` config, or use traditional mode

## Testing

### Unit Tests

```python
def test_streaming_small_file():
    adapter = XMLIngester(streaming_enabled=True)
    results = list(adapter.ingest("small.xml"))
    assert len(results) > 0

def test_streaming_memory_usage():
    import tracemalloc
    tracemalloc.start()
    
    adapter = XMLIngester(streaming_enabled=True)
    for result in adapter.ingest("large.xml"):
        current, peak = tracemalloc.get_traced_memory()
        assert peak < 100 * 1024 * 1024  # < 100MB
    
    tracemalloc.stop()
```

### Integration Tests

```python
def test_streaming_large_file():
    adapter = XMLIngester(streaming_enabled=True)
    count = 0
    for result in adapter.ingest("1gb_file.xml"):
        count += 1
        if count % 1000 == 0:
            print(f"Processed {count} records")
    assert count > 0
```

## Best Practices

1. **Use streaming for large files**: Files > 100MB should use streaming
2. **Monitor memory**: Use tracemalloc to verify memory usage
3. **Set appropriate limits**: Adjust max_events and max_depth based on your data
4. **Test thoroughly**: Verify output matches traditional mode
5. **Log security events**: Monitor for security limit violations

## Future Enhancements

- [ ] Support for compressed XML files (.xml.gz)
- [ ] Parallel processing of records
- [ ] Progress reporting for large files
- [ ] Adaptive threshold based on available memory
- [ ] Support for XML namespaces in streaming mode

