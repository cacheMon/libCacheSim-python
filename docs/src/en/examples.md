# Examples

This page provides practical examples of using libCacheSim Python bindings for various cache simulation scenarios.

## Basic Cache Simulation

### Simple LRU Cache Example

```python
import libcachesim as lcs

# Create an LRU cache with 1MB capacity
cache = lcs.LRU(cache_size=1024*1024)

# Generate synthetic Zipf trace
reader = lcs.SyntheticReader(
    num_of_req=10000,
    obj_size=1024,
    dist="zipf",
    alpha=1.0,
    num_objects=1000,
    seed=42
)

# Simulate cache behavior
hits = 0
total = 0

for req in reader:
    if cache.get(req):
        hits += 1
    total += 1

print(f"Hit ratio: {hits/total:.4f}")
print(f"Total requests: {total}")
```

### Comparing Multiple Cache Algorithms

```python
import libcachesim as lcs

def compare_algorithms(trace_file, cache_size):
    """Compare hit ratios of different cache algorithms."""
    
    algorithms = {
        "LRU": lcs.LRU,
        "LFU": lcs.LFU, 
        "FIFO": lcs.FIFO,
        "Clock": lcs.Clock,
        "ARC": lcs.ARC,
        "S3FIFO": lcs.S3FIFO
    }
    
    results = {}
    
    for name, cache_class in algorithms.items():
        # Create fresh reader for each algorithm
        reader = lcs.SyntheticReader(
            num_of_req=10000,
            obj_size=1024,
            dist="zipf", 
            alpha=1.0,
            seed=42  # Same seed for fair comparison
        )
        
        cache = cache_class(cache_size=cache_size)
        hits = 0
        
        for req in reader:
            if cache.get(req):
                hits += 1
                
        hit_ratio = hits / reader.get_num_of_req()
        results[name] = hit_ratio
        print(f"{name:8}: {hit_ratio:.4f}")
    
    return results

# Compare with 64KB cache
results = compare_algorithms("trace.csv", 64*1024)
```

## Working with Real Traces

### Reading CSV Traces

```python
import libcachesim as lcs

def simulate_csv_trace(csv_file):
    """Simulate cache behavior on CSV trace."""
    
    # Configure CSV reader
    reader_params = lcs.ReaderInitParam(
        has_header=True,
        delimiter=",",
        obj_id_is_num=True
    )
    
    # Set field mappings (1-indexed)
    reader_params.time_field = 1
    reader_params.obj_id_field = 2
    reader_params.obj_size_field = 3
    reader_params.op_field = 4
    
    reader = lcs.TraceReader(
        trace=csv_file,
        trace_type=lcs.TraceType.CSV_TRACE,
        reader_init_params=reader_params
    )
    
    print(f"Loaded trace with {reader.get_num_of_req()} requests")
    
    # Test different cache sizes
    cache_sizes = [1024*1024*i for i in [1, 2, 4, 8, 16]]  # 1MB to 16MB
    
    for size in cache_sizes:
        cache = lcs.LRU(cache_size=size)
        reader.reset()  # Reset to beginning
        
        hits = 0
        for req in reader:
            if cache.get(req):
                hits += 1
        
        hit_ratio = hits / reader.get_num_of_req()
        print(f"Cache size: {size//1024//1024}MB, Hit ratio: {hit_ratio:.4f}")

# Usage
simulate_csv_trace("workload.csv")
```

### Handling Large Traces with Sampling

```python
import libcachesim as lcs

def analyze_large_trace(trace_file, sample_ratio=0.1):
    """Analyze large trace using sampling."""
    
    # Create sampler
    sampler = lcs.Sampler(
        sample_ratio=sample_ratio,
        type=lcs.SamplerType.SPATIAL_SAMPLER
    )
    
    reader_params = lcs.ReaderInitParam(
        has_header=True,
        delimiter=",",
        obj_id_is_num=True
    )
    reader_params.sampler = sampler
    
    reader = lcs.TraceReader(
        trace=trace_file,
        trace_type=lcs.TraceType.CSV_TRACE,
        reader_init_params=reader_params
    )
    
    print(f"Sampling {sample_ratio*100}% of trace")
    print(f"Sampled requests: {reader.get_num_of_req()}")
    
    # Run simulation on sampled trace
    cache = lcs.LRU(cache_size=10*1024*1024)  # 10MB
    hits = 0
    
    for req in reader:
        if cache.get(req):
            hits += 1
    
    hit_ratio = hits / reader.get_num_of_req()
    print(f"Hit ratio on sampled trace: {hit_ratio:.4f}")

# Sample 5% of a large trace
analyze_large_trace("large_trace.csv", sample_ratio=0.05)
```

## Advanced Analysis

### Comprehensive Trace Analysis

```python
import libcachesim as lcs
import os

def comprehensive_analysis(trace_file, output_dir="analysis_results"):
    """Run comprehensive trace analysis."""
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Load trace
    reader = lcs.TraceReader(trace_file, lcs.TraceType.CSV_TRACE)
    
    # Run trace analysis
    analyzer = lcs.TraceAnalyzer(reader, f"{output_dir}/trace_analysis")
    print("Running trace analysis...")
    analyzer.run()
    
    print(f"Analysis complete. Results saved to {output_dir}/")
    print("Generated files:")
    for file in os.listdir(output_dir):
        print(f"  - {file}")

# Run analysis
comprehensive_analysis("workload.csv")
```

### Hit Ratio Curves

```python
import libcachesim as lcs
import matplotlib.pyplot as plt

def plot_hit_ratio_curve(trace_file, algorithms=None):
    """Plot hit ratio curves for different algorithms."""
    
    if algorithms is None:
        algorithms = ["LRU", "LFU", "FIFO", "ARC"]
    
    # Cache sizes from 1MB to 100MB
    cache_sizes = [1024*1024*i for i in range(1, 101, 5)]
    
    plt.figure(figsize=(10, 6))
    
    for algo_name in algorithms:
        hit_ratios = []
        
        for cache_size in cache_sizes:
            reader = lcs.SyntheticReader(
                num_of_req=5000,
                obj_size=1024,
                dist="zipf",
                alpha=1.0,
                seed=42
            )
            
            cache = getattr(lcs, algo_name)(cache_size=cache_size)
            hits = 0
            
            for req in reader:
                if cache.get(req):
                    hits += 1
            
            hit_ratio = hits / reader.get_num_of_req()
            hit_ratios.append(hit_ratio)
        
        # Convert to MB for plotting
        sizes_mb = [size // 1024 // 1024 for size in cache_sizes]
        plt.plot(sizes_mb, hit_ratios, label=algo_name, marker='o')
    
    plt.xlabel('Cache Size (MB)')
    plt.ylabel('Hit Ratio')
    plt.title('Hit Ratio vs Cache Size')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.show()

# Generate hit ratio curves
plot_hit_ratio_curve("trace.csv")
```

## Custom Cache Policies

### Implementing a Custom LRU with Python Hooks

```python
import libcachesim as lcs
from collections import OrderedDict

def create_python_lru(cache_size):
    """Create a custom LRU cache using Python hooks."""
    
    def init_hook(size):
        """Initialize cache data structure."""
        return {
            'data': OrderedDict(),
            'size': 0,
            'capacity': size
        }
    
    def hit_hook(cache_dict, obj_id, obj_size):
        """Handle cache hit."""
        # Move to end (most recently used)
        cache_dict['data'].move_to_end(obj_id)
    
    def miss_hook(cache_dict, obj_id, obj_size):
        """Handle cache miss."""
        # Add new item
        cache_dict['data'][obj_id] = obj_size
        cache_dict['size'] += obj_size
    
    def eviction_hook(cache_dict, obj_id, obj_size):
        """Handle eviction when cache is full."""
        # Remove least recently used items
        while cache_dict['size'] + obj_size > cache_dict['capacity']:
            if not cache_dict['data']:
                break
            lru_id, lru_size = cache_dict['data'].popitem(last=False)
            cache_dict['size'] -= lru_size
    
    return lcs.PythonHookCache(
        cache_size=cache_size,
        init_hook=init_hook,
        hit_hook=hit_hook,
        miss_hook=miss_hook,
        eviction_hook=eviction_hook
    )

# Test custom LRU
custom_cache = create_python_lru(1024*1024)
reader = lcs.SyntheticReader(num_of_req=1000, obj_size=1024)

hits = 0
for req in reader:
    if custom_cache.get(req):
        hits += 1

print(f"Custom LRU hit ratio: {hits/1000:.4f}")
```

### Time-based Cache with TTL

```python
import libcachesim as lcs
import time

def create_ttl_cache(cache_size, ttl_seconds=300):
    """Create a cache with time-to-live (TTL) expiration."""
    
    def init_hook(size):
        return {
            'data': {},
            'timestamps': {},
            'size': 0,
            'capacity': size,
            'ttl': ttl_seconds
        }
    
    def is_expired(cache_dict, obj_id):
        """Check if object has expired."""
        if obj_id not in cache_dict['timestamps']:
            return True
        return time.time() - cache_dict['timestamps'][obj_id] > cache_dict['ttl']
    
    def hit_hook(cache_dict, obj_id, obj_size):
        """Handle cache hit."""
        if is_expired(cache_dict, obj_id):
            # Expired, treat as miss
            if obj_id in cache_dict['data']:
                del cache_dict['data'][obj_id]
                del cache_dict['timestamps'][obj_id]
                cache_dict['size'] -= obj_size
            return False
        return True
    
    def miss_hook(cache_dict, obj_id, obj_size):
        """Handle cache miss."""
        current_time = time.time()
        cache_dict['data'][obj_id] = obj_size
        cache_dict['timestamps'][obj_id] = current_time
        cache_dict['size'] += obj_size
    
    def eviction_hook(cache_dict, obj_id, obj_size):
        """Handle eviction."""
        # First try to evict expired items
        current_time = time.time()
        expired_items = []
        
        for oid, timestamp in cache_dict['timestamps'].items():
            if current_time - timestamp > cache_dict['ttl']:
                expired_items.append(oid)
        
        for oid in expired_items:
            if oid in cache_dict['data']:
                cache_dict['size'] -= cache_dict['data'][oid]
                del cache_dict['data'][oid]
                del cache_dict['timestamps'][oid]
        
        # If still need space, evict oldest items
        while cache_dict['size'] + obj_size > cache_dict['capacity']:
            if not cache_dict['data']:
                break
            # Find oldest item
            oldest_id = min(cache_dict['timestamps'].keys(), 
                          key=lambda x: cache_dict['timestamps'][x])
            cache_dict['size'] -= cache_dict['data'][oldest_id]
            del cache_dict['data'][oldest_id]
            del cache_dict['timestamps'][oldest_id]
    
    return lcs.PythonHookCache(
        cache_size=cache_size,
        init_hook=init_hook,
        hit_hook=hit_hook,
        miss_hook=miss_hook,
        eviction_hook=eviction_hook
    )

# Test TTL cache
ttl_cache = create_ttl_cache(1024*1024, ttl_seconds=60)
```

## Performance Optimization

### Batch Processing for Large Workloads

```python
import libcachesim as lcs

def batch_simulation(trace_file, batch_size=10000):
    """Process large traces in batches to optimize memory usage."""
    
    reader = lcs.TraceReader(trace_file, lcs.TraceType.CSV_TRACE)
    cache = lcs.LRU(cache_size=10*1024*1024)
    
    total_requests = 0
    total_hits = 0
    batch_count = 0
    
    while True:
        batch_hits = 0
        batch_requests = 0
        
        # Process a batch of requests
        for _ in range(batch_size):
            try:
                req = reader.read_one_req()
                if req.valid:
                    if cache.get(req):
                        batch_hits += 1
                    batch_requests += 1
                else:
                    break  # End of trace
            except:
                break
        
        if batch_requests == 0:
            break
            
        total_hits += batch_hits
        total_requests += batch_requests
        batch_count += 1
        
        # Print progress
        hit_ratio = batch_hits / batch_requests
        print(f"Batch {batch_count}: {batch_requests} requests, "
              f"hit ratio: {hit_ratio:.4f}")
    
    overall_hit_ratio = total_hits / total_requests
    print(f"Overall: {total_requests} requests, hit ratio: {overall_hit_ratio:.4f}")

# Process in batches
batch_simulation("large_trace.csv", batch_size=50000)
```

### Multi-threaded Analysis

```python
import libcachesim as lcs
import concurrent.futures
import threading

def parallel_cache_comparison(trace_file, algorithms, cache_size):
    """Compare cache algorithms in parallel."""
    
    def simulate_algorithm(algo_name):
        """Simulate single algorithm."""
        reader = lcs.TraceReader(trace_file, lcs.TraceType.CSV_TRACE)
        cache = getattr(lcs, algo_name)(cache_size=cache_size)
        
        hits = 0
        total = 0
        
        for req in reader:
            if cache.get(req):
                hits += 1
            total += 1
        
        hit_ratio = hits / total if total > 0 else 0
        return algo_name, hit_ratio
    
    # Run simulations in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(simulate_algorithm, algo): algo 
                  for algo in algorithms}
        
        results = {}
        for future in concurrent.futures.as_completed(futures):
            algo_name, hit_ratio = future.result()
            results[algo_name] = hit_ratio
            print(f"{algo_name}: {hit_ratio:.4f}")
    
    return results

# Compare algorithms in parallel
algorithms = ["LRU", "LFU", "FIFO", "ARC", "S3FIFO"]
results = parallel_cache_comparison("trace.csv", algorithms, 1024*1024)
```

These examples demonstrate the versatility and power of libCacheSim Python bindings for cache simulation, analysis, and research. You can modify and extend these examples for your specific use cases.
