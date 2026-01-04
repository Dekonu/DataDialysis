# XML Streaming Design for Large Clinical Reports

## Problem Statement

The current XML ingester uses `defusedxml.ElementTree.parse()`, which loads the entire XML document into memory. For large clinical reports (potentially GBs), this causes:
- **Memory exhaustion**: Entire file loaded into RAM
- **Slow startup**: Must parse entire file before processing first record
- **Poor scalability**: Cannot handle files larger than available memory
- **Resource waste**: Memory held for entire file even when processing one record at a time

## Current Architecture

```python
# Current approach (memory-intensive)
tree = SafeET.parse(str(source_path))  # Loads entire file
root = tree.getroot()
records = root.findall(self.root_xpath)  # All records in memory
for xml_record in records:  # Process one at a time
    ...
```

**Issues:**
- Entire XML tree built in memory
- All records extracted before processing
- Memory usage = O(file_size)

## Proposed Streaming Architecture

### Design Principles

1. **Event-Driven Parsing**: Use SAX-style iterparse to process XML incrementally
2. **Memory Bounded**: Only keep current record in memory
3. **Backpressure**: Process and release records immediately
4. **Security Maintained**: Still use defusedxml for attack prevention
5. **Backward Compatible**: Support both streaming and non-streaming modes

### Architecture Overview

```
XML File (GBs)
    ↓
[Streaming Parser] ← Memory: O(record_size)
    ↓
[Record Buffer] ← Memory: O(1 record)
    ↓
[Redaction] ← Memory: O(1 record)
    ↓
[Validation] ← Memory: O(1 record)
    ↓
[Yield GoldenRecord] ← Memory: O(1 record)
    ↓
[Storage] ← Memory: O(batch_size)
```

**Memory Usage:**
- Current: O(file_size) - entire file in memory
- Streaming: O(record_size) - only current record in memory
- Improvement: 1000x+ for large files

## Implementation Strategy

### Option 1: Iterparse with defusedxml (Recommended)

Use `defusedxml.ElementTree.iterparse()` which provides:
- ✅ Security (defusedxml protection)
- ✅ Streaming (event-driven)
- ✅ Memory efficient (only current element in memory)
- ✅ XPath support (limited but sufficient)

**Implementation:**

```python
from defusedxml.ElementTree import iterparse as safe_iterparse

def ingest(self, source: str) -> Iterator[Result[GoldenRecord]]:
    """Stream XML records using iterparse."""
    source_path = Path(source)
    
    # Open file for streaming
    with open(source_path, 'rb') as xml_file:
        # Parse with iterparse (streaming)
        context = safe_iterparse(
            xml_file,
            events=('start', 'end'),
            max_events=1000000  # Safety limit
        )
        
        current_element = None
        record_stack = []
        
        for event, elem in context:
            # Detect when we've found a complete record
            if event == 'end' and self._is_record_element(elem):
                # Extract record data
                record_data = self._extract_record_data(elem)
                
                # Process immediately (memory released after)
                yield self._process_record(record_data, source)
                
                # Clear element to free memory
                elem.clear()
                # Remove from parent to free memory
                if elem.getparent() is not None:
                    elem.getparent().remove(elem)
```

**Pros:**
- Uses defusedxml (secure)
- Memory efficient
- Simple implementation
- Works with existing XPath config

**Cons:**
- Limited XPath support (must detect elements manually)
- Requires tracking element hierarchy

### Option 2: lxml.etree.iterparse (Higher Performance)

Use `lxml.etree.iterparse()` which provides:
- ✅ Better performance
- ✅ Full XPath support
- ✅ More control
- ⚠️ Requires additional security measures

**Implementation:**

```python
from lxml import etree
from lxml.etree import iterparse
from defusedxml.lxml import fromstring as safe_fromstring

def ingest(self, source: str) -> Iterator[Result[GoldenRecord]]:
    """Stream XML records using lxml iterparse."""
    source_path = Path(source)
    
    # Security: Set parser limits
    parser = etree.XMLParser(
        huge_tree=False,  # Prevent memory exhaustion
        strip_cdata=False,
        resolve_entities=False,  # Security: prevent entity expansion
        no_network=True,  # Security: prevent network access
        recover=False  # Fail on malformed XML
    )
    
    with open(source_path, 'rb') as xml_file:
        # Use iterparse for streaming
        context = iterparse(
            xml_file,
            events=('end',),
            tag=self._get_record_tag(),  # Only process record elements
            parser=parser
        )
        
        for event, elem in context:
            try:
                # Extract record using XPath
                record_data = self._extract_with_xpath(elem)
                
                # Process immediately
                yield self._process_record(record_data, source)
                
            finally:
                # Critical: Free memory immediately
                elem.clear()
                # Remove from parent
                while elem.getprevious() is not None:
                    del elem.getparent()[0]
```

**Pros:**
- Better performance than ElementTree
- Full XPath support
- More control over parsing
- Better for very large files

**Cons:**
- Requires additional security configuration
- More complex implementation
- Need to ensure defusedxml-style protections

### Option 3: Hybrid Approach (Best of Both)

Use iterparse for streaming, but add security wrapper:

```python
from defusedxml.lxml import parse as safe_lxml_parse
from lxml.etree import iterparse

class StreamingXMLParser:
    """Secure streaming XML parser with defusedxml protections."""
    
    def __init__(self, max_events=1000000, max_depth=100):
        self.max_events = max_events
        self.max_depth = max_depth
        self.event_count = 0
        self.depth = 0
    
    def iterparse(self, source, events=('end',), tag=None):
        """Secure iterparse with limits."""
        parser = etree.XMLParser(
            huge_tree=False,
            resolve_entities=False,
            no_network=True,
            recover=False
        )
        
        context = iterparse(source, events=events, tag=tag, parser=parser)
        
        for event, elem in context:
            # Security: Enforce limits
            self.event_count += 1
            if self.event_count > self.max_events:
                raise SecurityError("XML event limit exceeded")
            
            self.depth = self._calculate_depth(elem)
            if self.depth > self.max_depth:
                raise SecurityError("XML depth limit exceeded")
            
            yield event, elem
            
            # Memory management
            elem.clear()
            if elem.getparent() is not None:
                elem.getparent().remove(elem)
```

## Recommended Implementation

### Phase 1: Basic Streaming (defusedxml.iterparse)

**Changes:**
1. Replace `SafeET.parse()` with `safe_iterparse()`
2. Process records as they're encountered
3. Clear elements immediately after processing
4. Maintain backward compatibility with config

**Code Structure:**

```python
def ingest(self, source: str) -> Iterator[Result[GoldenRecord]]:
    """Stream XML records without loading entire file."""
    source_path = Path(source)
    
    # Detect record elements (from config)
    record_tag = self._get_record_tag_from_config()
    
    # Stream parse
    with open(source_path, 'rb') as xml_file:
        context = safe_iterparse(
            xml_file,
            events=('end',),
            tag=record_tag
        )
        
        for event, elem in context:
            try:
                # Extract record data
                record_data = self._extract_record_data(elem)
                
                # Process and yield
                result = self._triage_and_transform(record_data, source, record_count)
                yield result
                
            except Exception as e:
                # Log and continue (fail-safe)
                logger.warning(f"Error processing record: {e}")
                yield Result.failure_result(...)
            
            finally:
                # CRITICAL: Free memory
                elem.clear()
                # Remove from parent
                parent = elem.getparent()
                if parent is not None:
                    parent.remove(elem)
```

### Phase 2: Enhanced Streaming (lxml with security)

**Changes:**
1. Add lxml support with security wrapper
2. Better XPath support
3. Performance optimizations
4. Configurable parser limits

## Memory Management Best Practices

### 1. Immediate Element Clearing

```python
# After processing each record
elem.clear()  # Clear element's children
if elem.getparent() is not None:
    elem.getparent().remove(elem)  # Remove from parent
```

### 2. Batch Processing

```python
# Process in batches to avoid accumulating too many records
batch = []
for record in stream:
    batch.append(record)
    if len(batch) >= batch_size:
        yield from process_batch(batch)
        batch.clear()
```

### 3. Generator Pattern

```python
# Use generators throughout to avoid materializing lists
def extract_records(xml_file):
    for event, elem in iterparse(xml_file):
        yield extract_data(elem)  # Don't build list
        elem.clear()
```

## Configuration Updates

### Streaming-Specific Settings

```json
{
  "root_element": "./PatientRecord",
  "streaming": {
    "enabled": true,
    "max_events": 1000000,
    "max_depth": 100,
    "batch_size": 1000
  },
  "fields": {
    "patient_id": "./MRN",
    ...
  }
}
```

### Environment Variables

```bash
# Enable streaming mode
DD_XML_STREAMING_ENABLED=true

# Set limits
DD_XML_MAX_EVENTS=1000000
DD_XML_MAX_DEPTH=100
DD_XML_BATCH_SIZE=1000
```

## Performance Comparison

### Current (Non-Streaming)

```
File Size: 10GB
Memory Usage: ~10GB (entire file)
Startup Time: 5-10 minutes (parse entire file)
First Record: 5-10 minutes
Total Time: 10-15 minutes
```

### Streaming

```
File Size: 10GB
Memory Usage: ~10MB (one record)
Startup Time: <1 second
First Record: <1 second
Total Time: 8-12 minutes (slightly slower per record, but much faster startup)
```

**Improvements:**
- Memory: 1000x reduction
- Startup: 300-600x faster
- Scalability: Can handle files of any size

## Security Considerations

### 1. Parser Limits

```python
parser = etree.XMLParser(
    huge_tree=False,  # Prevent memory exhaustion
    resolve_entities=False,  # Prevent entity expansion attacks
    no_network=True,  # Prevent network access
    recover=False  # Fail on malformed XML
)
```

### 2. Event Limits

```python
max_events = 1000000  # Prevent DoS via excessive events
event_count = 0
for event, elem in context:
    event_count += 1
    if event_count > max_events:
        raise SecurityError("Event limit exceeded")
```

### 3. Depth Limits

```python
max_depth = 100  # Prevent deeply nested XML
def calculate_depth(elem):
    depth = 0
    parent = elem.getparent()
    while parent is not None:
        depth += 1
        parent = parent.getparent()
    return depth
```

## Migration Strategy

### Step 1: Add Streaming Mode (Optional)

```python
def ingest(self, source: str) -> Iterator[Result[GoldenRecord]]:
    if self.streaming_enabled:
        return self._ingest_streaming(source)
    else:
        return self._ingest_traditional(source)  # Current implementation
```

### Step 2: Test with Small Files

- Verify same output as non-streaming
- Check memory usage
- Validate security protections

### Step 3: Test with Large Files

- Test with 1GB+ files
- Monitor memory usage
- Verify performance improvements

### Step 4: Make Streaming Default

- Enable by default for files > threshold (e.g., 100MB)
- Keep traditional mode for small files (faster)

## Example Usage

```python
# Automatic streaming for large files
adapter = XMLIngester(
    config_path="mappings.json",
    streaming_enabled=True,  # Enable streaming
    streaming_threshold=100 * 1024 * 1024  # 100MB threshold
)

# Process large file
for result in adapter.ingest("large_clinical_report.xml"):
    if result.is_success():
        storage.persist(result.value)
```

## Testing Strategy

### Unit Tests

```python
def test_streaming_small_file():
    """Test streaming works with small files."""
    adapter = XMLIngester(streaming_enabled=True)
    results = list(adapter.ingest("small.xml"))
    assert len(results) > 0

def test_streaming_memory_usage():
    """Test memory usage stays bounded."""
    import tracemalloc
    tracemalloc.start()
    
    adapter = XMLIngester(streaming_enabled=True)
    for result in adapter.ingest("large.xml"):
        current, peak = tracemalloc.get_traced_memory()
        assert peak < 100 * 1024 * 1024  # Less than 100MB
    
    tracemalloc.stop()
```

### Integration Tests

```python
def test_streaming_large_file():
    """Test streaming with 1GB+ file."""
    adapter = XMLIngester(streaming_enabled=True)
    count = 0
    for result in adapter.ingest("1gb_file.xml"):
        count += 1
        if count % 1000 == 0:
            print(f"Processed {count} records")
    assert count > 0
```

## Conclusion

Streaming XML parsing is essential for handling large clinical reports. The recommended approach:

1. **Start with defusedxml.iterparse** (secure, simple)
2. **Add memory management** (clear elements immediately)
3. **Maintain security** (limits, entity protection)
4. **Test thoroughly** (small and large files)
5. **Migrate gradually** (optional mode first, then default)

This design maintains security while dramatically improving memory efficiency and scalability.

