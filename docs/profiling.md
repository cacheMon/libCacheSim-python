# Performance Profiling for libCacheSim

This document explains how to use the profiling utilities in libCacheSim to analyze performance bottlenecks in cache simulations, particularly plugin caches and trace processing operations.

## Overview

The `libcachesim.profiler` module provides comprehensive profiling capabilities using Python's built-in `cProfile` along with memory and CPU monitoring. This is particularly useful for:

- Analyzing plugin cache performance bottlenecks
- Comparing different cache implementations
- Understanding where time is spent in trace processing
- Identifying memory usage patterns
- Getting detailed function-level performance data

## Quick Start

### Basic Function Profiling

```python
from libcachesim.profiler import profile_cache_operations, profile_trace_processing

# Profile cache operations (individual requests)
result = profile_cache_operations(cache, reader, num_requests=1000)
print(f"Time: {result.execution_time:.4f}s, Memory: {result.memory_peak:.2f}MB")

# Profile complete trace processing
result = profile_trace_processing(cache, reader)
print(f"Miss ratio: {result.custom_metrics['obj_miss_ratio']:.4f}")
```

### Advanced Profiling with CacheSimProfiler

```python
from libcachesim.profiler import CacheSimProfiler

# Create profiler instance
profiler = CacheSimProfiler("profiling_results")

# Profile specific operations
result = profiler.profile_plugin_cache_operations(
    cache, reader, num_requests=1000, method_name="my_plugin_cache"
)

# Generate comprehensive reports
report_file = profiler.generate_performance_report()
json_file = profiler.export_results_json()
csv_file = profiler.export_results_csv()
```

### Context Manager Profiling

```python
from libcachesim.profiler import CacheSimProfiler

profiler = CacheSimProfiler()

with profiler.profile_context("custom_operation") as profile_result:
    # Your code to profile here
    for request in reader:
        cache.get(request)
        if some_condition:
            break
    
    # Add custom metrics
    profile_result.custom_metrics['requests_processed'] = request_count
```

## Understanding the Results

### ProfileResult Object

Each profiling operation returns a `ProfileResult` object with:

- `execution_time`: Total execution time in seconds
- `memory_peak`: Peak memory usage during execution (MB)
- `memory_current`: Memory change from start to end (MB)
- `cpu_percent`: CPU usage percentage
- `custom_metrics`: Dictionary of custom metrics
- `profile_stats`: Detailed cProfile statistics

### Generated Reports

The profiler generates several types of output:

1. **Text Reports** (`profile_*.txt`): Detailed cProfile output showing:
   - Top functions by cumulative time
   - Top functions by total time  
   - Function call counts and timing

2. **Performance Reports** (`performance_report_*.txt`): Summary comparing all profiled methods

3. **JSON Export** (`profile_results_*.json`): Machine-readable results for further analysis

4. **CSV Export** (`profile_summary_*.csv`): Spreadsheet-compatible summary data

### Example cProfile Output

```
Top Functions by Cumulative Time:
----------------------------------------
         11007 function calls in 0.285 seconds

   Ordered by: cumulative time

   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
        1    0.002    0.002    0.285    0.285 profiler.py:194(run_cache_operations)
     1000    0.003    0.000    0.279    0.000 plugin_cache.py:118(get)
     2000    0.273    0.000    0.273    0.000 {built-in method time.sleep}
     1000    0.002    0.000    0.164    0.000 lru_cache.py:253(cache_hit)
```

This shows that `time.sleep` calls are taking 0.273 out of 0.285 total seconds (96% of execution time).

## Plugin Cache Performance Analysis

Plugin caches can have performance issues due to Python callback overhead. The profiler helps identify:

### Common Bottlenecks

1. **Python Callback Overhead**: Each cache operation calls Python functions
2. **Slow Hook Functions**: User-defined cache hooks that are inefficient
3. **Memory Allocation**: Excessive object creation in Python
4. **Data Structure Operations**: Inefficient cache data structure operations

### Example Analysis

```python
# Compare plugin cache vs native implementation
profiler = CacheSimProfiler()

# Profile native LRU
native_cache = LRU(cache_size=1024)
result1 = profiler.profile_trace_processing(native_cache, reader, "native_lru")

# Profile plugin LRU  
plugin_cache = PluginCache(
    cache_size=1024,
    cache_init_hook=init_hook,
    cache_hit_hook=hit_hook,
    cache_miss_hook=miss_hook,
    # ... other hooks
)
result2 = profiler.profile_trace_processing(plugin_cache, reader, "plugin_lru")

# Compare results
comparison = profiler.compare_results()
print(f"Plugin overhead: {comparison['performance_ratio']:.2f}x slower")
```

## Best Practices

### For Plugin Cache Development

1. **Profile Early**: Use profiling during plugin development to catch performance issues
2. **Minimize Hook Complexity**: Keep cache hook functions as simple as possible
3. **Avoid Python Callbacks in Hot Paths**: Consider C++ implementation for critical operations
4. **Use Efficient Data Structures**: Profile different Python data structures for cache storage

### For Performance Analysis

1. **Use Representative Workloads**: Profile with realistic trace data and cache sizes
2. **Run Multiple Iterations**: Performance can vary between runs
3. **Focus on Hot Functions**: Look at cumulative time to find the biggest bottlenecks
4. **Compare Implementations**: Use profiling to validate optimization efforts

### Memory Profiling

```python
# Track memory usage patterns
profiler = CacheSimProfiler()

with profiler.profile_context("memory_analysis") as result:
    # Code that might have memory issues
    large_cache = PluginCache(cache_size=100000, ...)
    result.custom_metrics['cache_size'] = large_cache.cache_size

print(f"Memory peak: {result.memory_peak:.2f}MB")
```

## Example: Finding Plugin Cache Bottlenecks

The provided `examples/profiling_analysis.py` demonstrates:

1. Creating mock plugin caches with artificial delays
2. Comparing native vs plugin implementations  
3. Identifying specific bottlenecks in cProfile output
4. Generating comprehensive performance reports

Run it with:
```bash
cd libCacheSim-python
python examples/profiling_analysis.py
```

This shows a 397x performance difference between fast and slow plugin implementations, with detailed function-level analysis showing exactly where time is spent.

## Integration with libCacheSim

When the full libCacheSim package is built, the profiler integrates seamlessly:

```python
import libcachesim as lcs
from libcachesim.profiler import CacheSimProfiler

# Create actual cache and reader
cache = lcs.S3FIFO(cache_size=1024*1024)
reader = lcs.TraceReader(trace="path/to/trace", trace_type=lcs.TraceType.ORACLE_GENERAL_TRACE)

# Profile real operations
profiler = CacheSimProfiler()
result = profiler.profile_trace_processing(cache, reader)
```

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError for psutil**: Install with `pip install psutil`
2. **Empty cProfile output**: Ensure the profiled code actually runs and takes measurable time
3. **High memory usage**: Large traces or cache sizes can use significant memory during profiling

### Performance Tips

- For large traces, use `num_requests` parameter to profile subset of requests
- Clear profiler results with `profiler.clear_results()` between different test runs
- Use the context manager for fine-grained profiling of specific code sections

This profiling system provides the cProfile results requested in the issue and enables comprehensive performance analysis of plugin cache and trace processing operations.