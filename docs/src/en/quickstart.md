# Quick Start Guide

This guide will help you get started with libCacheSim Python bindings.

## Installation

### From PyPI (Recommended)

```bash
pip install libcachesim
```

### From Source

```bash
git clone https://github.com/cacheMon/libCacheSim-python.git
cd libCacheSim-python
git submodule update --init --recursive
pip install -e .
```

## Basic Usage

### 1. Creating a Cache

```python
import libcachesim as lcs

# Create different types of caches
lru_cache = lcs.LRU(cache_size=1024*1024)  # 1MB LRU cache
lfu_cache = lcs.LFU(cache_size=1024*1024)  # 1MB LFU cache
fifo_cache = lcs.FIFO(cache_size=1024*1024)  # 1MB FIFO cache
```

### 2. Using Synthetic Traces

```python
# Generate Zipf-distributed requests
reader = lcs.SyntheticReader(
    num_of_req=10000,
    obj_size=1024,
    dist="zipf",
    alpha=1.0,
    num_objects=1000,
    seed=42
)

# Simulate cache behavior
cache = lcs.LRU(cache_size=50*1024)
hit_count = 0

for req in reader:
    if cache.get(req):
        hit_count += 1

print(f"Hit ratio: {hit_count/reader.get_num_of_req():.4f}")
```

### 3. Reading Real Traces

```python
# Read CSV trace
reader = lcs.TraceReader(
    trace="path/to/trace.csv",
    trace_type=lcs.TraceType.CSV_TRACE,
    has_header=True,
    delimiter=",",
    obj_id_is_num=True
)

# Process requests
cache = lcs.LRU(cache_size=1024*1024)
for req in reader:
    result = cache.get(req)
    # Process result...
```

### 4. Cache Performance Analysis

```python
# Run comprehensive analysis
analyzer = lcs.TraceAnalyzer(reader, "output_prefix")
analyzer.run()

# This generates various analysis files:
# - Hit ratio curves
# - Access pattern analysis
# - Temporal locality analysis
# - And more...
```

## Available Cache Algorithms

libCacheSim supports numerous cache algorithms:

### Basic Algorithms
- **LRU**: Least Recently Used
- **LFU**: Least Frequently Used  
- **FIFO**: First In, First Out
- **Clock**: Clock algorithm
- **Random**: Random replacement

### Advanced Algorithms
- **ARC**: Adaptive Replacement Cache
- **S3FIFO**: Simple, Fast, Fair FIFO
- **Sieve**: Sieve eviction algorithm
- **TinyLFU**: Tiny LFU with admission control
- **TwoQ**: Two-Queue algorithm
- **LRB**: Learning Relaxed Belady

### Experimental Algorithms
- **3LCache**: Three-Level Cache
- **And many more...**

## Trace Formats

Supported trace formats include:

- **CSV**: Comma-separated values
- **Binary**: Custom binary format
- **OracleGeneral**: Oracle general format
- **Vscsi**: VMware vSCSI format
- **And more...**

## Advanced Features

### Custom Cache Policies

You can implement custom cache policies using Python hooks:

```python
from collections import OrderedDict

def create_custom_lru():
    def init_hook(cache_size):
        return OrderedDict()
    
    def hit_hook(cache_dict, obj_id, obj_size):
        cache_dict.move_to_end(obj_id)
    
    def miss_hook(cache_dict, obj_id, obj_size):
        cache_dict[obj_id] = obj_size
    
    def eviction_hook(cache_dict, obj_id, obj_size):
        if cache_dict:
            cache_dict.popitem(last=False)
    
    return lcs.PythonHookCache(
        cache_size=1024*1024,
        init_hook=init_hook,
        hit_hook=hit_hook,
        miss_hook=miss_hook,
        eviction_hook=eviction_hook
    )

custom_cache = create_custom_lru()
```

### Trace Sampling

```python
# Sample 10% of requests spatially
reader = lcs.TraceReader(
    trace="large_trace.csv",
    trace_type=lcs.TraceType.CSV_TRACE,
    sampling_ratio=0.1,
    sampling_type=lcs.SamplerType.SPATIAL_SAMPLER
)
```

### Multi-threaded Analysis

```python
# Use multiple threads for analysis
analyzer = lcs.TraceAnalyzer(reader, "output", n_threads=4)
analyzer.run()
```

## Next Steps

- Explore the [API Reference](api.md) for detailed documentation
- Check out [Examples](examples.md) for more complex use cases
- Visit our [GitHub repository](https://github.com/cacheMon/libCacheSim-python) for source code and issues
