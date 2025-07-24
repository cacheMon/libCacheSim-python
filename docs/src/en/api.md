# API Reference

This page provides detailed API documentation for the libCacheSim Python bindings.

## Core Classes

### Cache Classes

All cache classes inherit from the base cache interface and provide the following methods:

```python
class Cache:
    """Base cache interface."""
    
    def get(self, obj_id: int, obj_size: int = 1) -> bool:
        """Request an object from the cache.
        
        Args:
            obj_id: Object identifier
            obj_size: Object size in bytes
            
        Returns:
            True if cache hit, False if cache miss
        """
    
    def get_hit_ratio(self) -> float:
        """Get the current cache hit ratio."""
    
    def get_miss_ratio(self) -> float:
        """Get the current cache miss ratio."""
        
    def get_num_hits(self) -> int:
        """Get the total number of cache hits."""
        
    def get_num_misses(self) -> int:
        """Get the total number of cache misses."""
```

### Available Cache Algorithms

```python
# Basic algorithms
def LRU(cache_size: int) -> Cache: ...
def LFU(cache_size: int) -> Cache: ...
def FIFO(cache_size: int) -> Cache: ...
def Clock(cache_size: int) -> Cache: ...
def Random(cache_size: int) -> Cache: ...

# Advanced algorithms  
def ARC(cache_size: int) -> Cache: ...
def S3FIFO(cache_size: int) -> Cache: ...
def Sieve(cache_size: int) -> Cache: ...
def TinyLFU(cache_size: int) -> Cache: ...
def TwoQ(cache_size: int) -> Cache: ...
```ence

This page provides detailed API documentation for libCacheSim Python bindings.

## Core Classes

### Cache Classes

All cache classes inherit from the base cache interface and provide the following methods:

::: libcachesim.cache

### TraceReader

```python
class TraceReader:
    """Read trace files in various formats."""
    
    def __init__(self, trace_path: str, trace_type: TraceType, 
                 reader_params: ReaderInitParam = None):
        """Initialize trace reader.
        
        Args:
            trace_path: Path to trace file
            trace_type: Type of trace format
            reader_params: Optional reader configuration
        """
    
    def __iter__(self):
        """Iterate over requests in the trace."""
        
    def reset(self):
        """Reset reader to beginning of trace."""
        
    def skip(self, n: int):
        """Skip n requests."""
        
    def clone(self):
        """Create a copy of the reader."""
```

### SyntheticReader  

```python
class SyntheticReader:
    """Generate synthetic workloads."""
    
    def __init__(self, num_objects: int, num_requests: int,
                 distribution: str = "zipf", alpha: float = 1.0,
                 obj_size: int = 1, seed: int = None):
        """Initialize synthetic reader.
        
        Args:
            num_objects: Number of unique objects
            num_requests: Total requests to generate
            distribution: Distribution type ("zipf", "uniform")
            alpha: Zipf skewness parameter
            obj_size: Object size in bytes
            seed: Random seed for reproducibility
        """
```

### TraceAnalyzer

```python
class TraceAnalyzer:
    """Analyze trace characteristics."""
    
    def __init__(self, trace_path: str, trace_type: TraceType,
                 reader_params: ReaderInitParam = None):
        """Initialize trace analyzer."""
        
    def get_num_requests(self) -> int:
        """Get total number of requests."""
        
    def get_num_objects(self) -> int:
        """Get number of unique objects."""
        
    def get_working_set_size(self) -> int:
        """Get working set size."""
```

## Enumerations and Constants

### TraceType

```python
class TraceType:
    """Supported trace file formats."""
    CSV_TRACE = "csv"
    BINARY_TRACE = "binary"  
    ORACLE_GENERAL_TRACE = "oracle"
    PLAIN_TXT_TRACE = "txt"
```

### SamplerType

```python
class SamplerType:
    """Sampling strategies."""
    SPATIAL_SAMPLER = "spatial"
    TEMPORAL_SAMPLER = "temporal"
```

### ReqOp

```python
class ReqOp:
    """Request operation types."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
```

## Data Structures

### Request

```python
class Request:
    """Represents a cache request."""
    
    def __init__(self):
        self.obj_id: int = 0
        self.obj_size: int = 1
        self.timestamp: int = 0
        self.op: str = "read"
```

### ReaderInitParam

```python
class ReaderInitParam:
    """Configuration parameters for trace readers."""
    
    def __init__(self):
        self.has_header: bool = False
        self.delimiter: str = ","
        self.obj_id_is_num: bool = True
        self.ignore_obj_size: bool = False
        self.ignore_size_zero_req: bool = True
        self.cap_at_n_req: int = -1
        self.block_size: int = 4096
        self.trace_start_offset: int = 0
        
        # Field mappings (1-indexed)
        self.time_field: int = 1
        self.obj_id_field: int = 2
        self.obj_size_field: int = 3
        self.op_field: int = 4
        
        self.sampler: Sampler = None
```

### Sampler

```python
class Sampler:
    """Configuration for request sampling."""
    
    def __init__(self, sample_ratio: float = 1.0, 
                 type: str = "spatial"):
        """Initialize sampler.
        
        Args:
            sample_ratio: Fraction of requests to sample (0.0-1.0)
            type: Sampling type ("spatial" or "temporal")
        """
        self.sample_ratio = sample_ratio
        self.type = type
```

## Utility Functions

### Synthetic Trace Generation

```python
def create_zipf_requests(num_objects, num_requests, alpha, obj_size, seed=None):
    """
    Create Zipf-distributed synthetic requests.
    
    Args:
        num_objects (int): Number of unique objects
        num_requests (int): Total number of requests to generate
        alpha (float): Zipf skewness parameter (higher = more skewed)
        obj_size (int): Size of each object in bytes
        seed (int, optional): Random seed for reproducibility
        
    Returns:
        List[Request]: List of generated requests
    """
    
def create_uniform_requests(num_objects, num_requests, obj_size, seed=None):
    """
    Create uniformly-distributed synthetic requests.
    
    Args:
        num_objects (int): Number of unique objects
        num_requests (int): Total number of requests to generate  
        obj_size (int): Size of each object in bytes
        seed (int, optional): Random seed for reproducibility
        
    Returns:
        List[Request]: List of generated requests
    """
```

### Cache Algorithms

Available cache algorithms with their factory functions:

```python
# Basic algorithms
LRU(cache_size: int) -> Cache
LFU(cache_size: int) -> Cache  
FIFO(cache_size: int) -> Cache
Clock(cache_size: int) -> Cache
Random(cache_size: int) -> Cache

# Advanced algorithms
ARC(cache_size: int) -> Cache
S3FIFO(cache_size: int) -> Cache
Sieve(cache_size: int) -> Cache
TinyLFU(cache_size: int) -> Cache
TwoQ(cache_size: int) -> Cache
LRB(cache_size: int) -> Cache

# Experimental algorithms
cache_3L(cache_size: int) -> Cache
```

### Performance Metrics

```python
class CacheStats:
    """Cache performance statistics."""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.bytes_written = 0
        self.bytes_read = 0
    
    @property
    def hit_ratio(self) -> float:
        """Calculate hit ratio."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    @property
    def miss_ratio(self) -> float:
        """Calculate miss ratio."""
        return 1.0 - self.hit_ratio
```

## Error Handling

The library uses standard Python exceptions:

- `ValueError`: Invalid parameters or configuration
- `FileNotFoundError`: Trace file not found
- `RuntimeError`: Runtime errors from underlying C++ library
- `MemoryError`: Out of memory conditions

Example error handling:

```python
try:
    reader = lcs.TraceReader("nonexistent.csv", lcs.TraceType.CSV_TRACE)
except FileNotFoundError:
    print("Trace file not found")
except ValueError as e:
    print(f"Invalid configuration: {e}")
```

## Configuration Options

### Reader Configuration

```python
reader_params = lcs.ReaderInitParam(
    has_header=True,           # CSV has header row
    delimiter=",",             # Field delimiter
    obj_id_is_num=True,       # Object IDs are numeric
    ignore_obj_size=False,    # Don't ignore object sizes
    ignore_size_zero_req=True, # Ignore zero-size requests
    cap_at_n_req=1000000,     # Limit number of requests
    block_size=4096,          # Block size for block-based traces
    trace_start_offset=0,     # Skip initial requests
)

# Field mappings (1-indexed)
reader_params.time_field = 1
reader_params.obj_id_field = 2  
reader_params.obj_size_field = 3
reader_params.op_field = 4
```

### Sampling Configuration

```python
sampler = lcs.Sampler(
    sample_ratio=0.1,                    # Sample 10% of requests
    type=lcs.SamplerType.SPATIAL_SAMPLER # Spatial sampling
)
reader_params.sampler = sampler
```

## Thread Safety

The library provides thread-safe operations for most use cases:

- Cache operations are thread-safe within a single cache instance
- Multiple readers can be used concurrently  
- Analysis operations can utilize multiple threads

For high-concurrency scenarios, consider using separate cache instances per thread.

## Memory Management

The library automatically manages memory for most operations:

- Cache objects handle their own memory allocation
- Trace readers manage buffering automatically  
- Request objects are lightweight and reusable

For large-scale simulations, monitor memory usage and consider:

- Using sampling to reduce trace size
- Processing traces in chunks
- Limiting cache sizes appropriately

## Best Practices

1. **Use appropriate cache sizes**: Size caches based on your simulation goals
2. **Set random seeds**: For reproducible results in synthetic traces
3. **Handle errors**: Always wrap file operations in try-catch blocks
4. **Monitor memory**: For large traces, consider sampling or chunking
5. **Use threading**: Leverage multi-threading for analysis tasks
6. **Validate traces**: Check trace format and content before simulation
