#!/usr/bin/env python3
"""
Example demonstrating profiling analysis for plugin cache and trace processing.

This script shows how to use the profiling utilities to analyze performance
bottlenecks in plugin cache implementations and trace processing operations.

This is a standalone example that works without the compiled libcachesim package.
"""

import sys
import os
from pathlib import Path
import time
from collections import OrderedDict

# Import profiler directly
sys.path.insert(0, str(Path(__file__).parent.parent / "libcachesim"))
from profiler import CacheSimProfiler, profile_cache_operations, profile_trace_processing


# Simulate libcachesim imports (these would normally come from the built package)
class MockRequest:
    """Mock request class for testing."""
    def __init__(self, obj_id, obj_size=1, valid=True):
        self.obj_id = obj_id
        self.obj_size = obj_size
        self.valid = valid


class MockReader:
    """Mock trace reader for testing."""
    def __init__(self, num_requests=10000, num_objects=1000):
        self.num_requests = num_requests
        self.num_objects = num_objects
        self.current_req = 0
        
    def reset(self):
        self.current_req = 0
        
    def __iter__(self):
        return self
        
    def __next__(self):
        if self.current_req >= self.num_requests:
            raise StopIteration
            
        # Simple zipf-like distribution
        obj_id = hash(str(self.current_req)) % self.num_objects
        req = MockRequest(obj_id, obj_size=100)
        self.current_req += 1
        return req


class MockCommonCacheParams:
    """Mock common cache parameters."""
    def __init__(self, cache_size):
        self.cache_size = cache_size


# Plugin cache implementation - simulates real libcachesim.PluginCache
class StandaloneLRU:
    """Standalone LRU implementation for plugin cache example."""
    def __init__(self, cache_size):
        self.cache_data = OrderedDict()
        self.cache_size = cache_size

    def cache_hit(self, obj_id):
        if obj_id in self.cache_data:
            obj_size = self.cache_data.pop(obj_id)
            self.cache_data[obj_id] = obj_size
            return True
        return False

    def cache_miss(self, obj_id, obj_size):
        # Add to cache, evict if necessary
        while len(self.cache_data) >= self.cache_size:
            self.cache_data.popitem(last=False)  # Remove oldest
        self.cache_data[obj_id] = obj_size

    def cache_eviction(self):
        if self.cache_data:
            evicted_id, _ = self.cache_data.popitem(last=False)
            return evicted_id
        return None

    def cache_remove(self, obj_id):
        if obj_id in self.cache_data:
            del self.cache_data[obj_id]

    def get_size(self):
        return len(self.cache_data)


class MockPluginCache:
    """Mock plugin cache that simulates the real PluginCache with Python hooks."""
    
    def __init__(self, cache_size, cache_init_hook, cache_hit_hook, cache_miss_hook,
                 cache_eviction_hook, cache_remove_hook, cache_free_hook=None, cache_name="MockPlugin"):
        self.cache_size = cache_size
        self.cache_name = cache_name
        
        # Initialize hooks
        self.cache_hit_hook = cache_hit_hook
        self.cache_miss_hook = cache_miss_hook
        self.cache_eviction_hook = cache_eviction_hook
        self.cache_remove_hook = cache_remove_hook
        self.cache_free_hook = cache_free_hook
        
        # Initialize cache data using init hook
        common_params = MockCommonCacheParams(cache_size)
        self.cache_data = cache_init_hook(common_params)
        
        # Statistics
        self.n_hits = 0
        self.n_misses = 0
    
    def get(self, request):
        """Process a cache request."""
        # Check if it's a hit
        if self.cache_data.cache_hit(request.obj_id):
            self.cache_hit_hook(self.cache_data, request)
            self.n_hits += 1
            return True
        else:
            # Cache miss
            self.cache_miss_hook(self.cache_data, request)
            self.n_misses += 1
            
            # Check if eviction is needed
            if self.cache_data.get_size() >= self.cache_size:
                evicted = self.cache_eviction_hook(self.cache_data, request)
            
            return False
    
    def process_trace(self, reader):
        """Process entire trace (simulated)."""
        reader.reset()
        n_hit = 0
        n_total = 0
        bytes_hit = 0
        bytes_total = 0
        
        for request in reader:
            n_total += 1
            bytes_total += request.obj_size
            
            if self.get(request):
                n_hit += 1
                bytes_hit += request.obj_size
        
        obj_miss_ratio = 1.0 - (n_hit / n_total) if n_total > 0 else 0.0
        byte_miss_ratio = 1.0 - (bytes_hit / bytes_total) if bytes_total > 0 else 0.0
        
        return obj_miss_ratio, byte_miss_ratio


class MockLRUCache:
    """Simple LRU cache for comparison."""
    
    def __init__(self, cache_size):
        self.cache_size = cache_size
        self.cache_data = OrderedDict()
        self.n_hits = 0
        self.n_misses = 0
    
    def get(self, request):
        """Process a cache request."""
        if request.obj_id in self.cache_data:
            # Hit - move to end
            self.cache_data.move_to_end(request.obj_id)
            self.n_hits += 1
            return True
        else:
            # Miss - add to cache
            if len(self.cache_data) >= self.cache_size:
                self.cache_data.popitem(last=False)  # Remove oldest
            
            self.cache_data[request.obj_id] = request.obj_size
            self.n_misses += 1
            return False
    
    def process_trace(self, reader):
        """Process entire trace."""
        reader.reset()
        n_hit = 0
        n_total = 0
        bytes_hit = 0
        bytes_total = 0
        
        for request in reader:
            n_total += 1
            bytes_total += request.obj_size
            
            if self.get(request):
                n_hit += 1
                bytes_hit += request.obj_size
        
        obj_miss_ratio = 1.0 - (n_hit / n_total) if n_total > 0 else 0.0
        byte_miss_ratio = 1.0 - (bytes_hit / bytes_total) if bytes_total > 0 else 0.0
        
        return obj_miss_ratio, byte_miss_ratio


# Plugin cache hook functions
def cache_init_hook(common_cache_params):
    return StandaloneLRU(common_cache_params.cache_size)


def cache_hit_hook(cache_data, request):
    # This gets called on every cache hit
    pass  # In real implementation, might update statistics


def cache_miss_hook(cache_data, request):
    # This gets called on every cache miss
    pass  # In real implementation, might update statistics


def cache_eviction_hook(cache_data, request):
    # This gets called when eviction is needed
    return cache_data.cache_eviction()


def cache_remove_hook(cache_data, obj_id):
    cache_data.cache_remove(obj_id)


def cache_free_hook(cache_data):
    cache_data.cache_data.clear()


def create_plugin_cache(cache_size=1024):
    """Create a plugin cache for testing."""
    return MockPluginCache(
        cache_size=cache_size,
        cache_init_hook=cache_init_hook,
        cache_hit_hook=cache_hit_hook,
        cache_miss_hook=cache_miss_hook,
        cache_eviction_hook=cache_eviction_hook,
        cache_remove_hook=cache_remove_hook,
        cache_free_hook=cache_free_hook,
        cache_name="ProfiledPluginLRU"
    )


def simulate_slow_plugin_operations():
    """Simulate slow plugin cache operations with artificial delays."""
    
    class SlowStandaloneLRU(StandaloneLRU):
        """LRU with artificial delays to simulate performance issues."""
        
        def cache_hit(self, obj_id):
            # Simulate slow hit processing
            time.sleep(0.0001)  # 0.1ms delay
            return super().cache_hit(obj_id)
            
        def cache_miss(self, obj_id, obj_size):
            # Simulate slow miss processing  
            time.sleep(0.0002)  # 0.2ms delay
            super().cache_miss(obj_id, obj_size)
            
        def cache_eviction(self):
            # Simulate slow eviction
            time.sleep(0.0003)  # 0.3ms delay
            return super().cache_eviction()
    
    def slow_cache_init_hook(common_cache_params):
        return SlowStandaloneLRU(common_cache_params.cache_size)
    
    def slow_cache_hit_hook(cache_data, request):
        # Simulate slow Python callback
        time.sleep(0.00005)  # 0.05ms delay
        
    def slow_cache_miss_hook(cache_data, request):
        # Simulate slow Python callback
        time.sleep(0.00005)  # 0.05ms delay
    
    return MockPluginCache(
        cache_size=1024,
        cache_init_hook=slow_cache_init_hook,
        cache_hit_hook=slow_cache_hit_hook,
        cache_miss_hook=slow_cache_miss_hook,
        cache_eviction_hook=cache_eviction_hook,
        cache_remove_hook=cache_remove_hook,
        cache_free_hook=cache_free_hook,
        cache_name="SlowPluginLRU"
    )


def main():
    """Main demonstration of profiling capabilities."""
    print("libCacheSim Profiling Analysis Example")
    print("=" * 50)
    
    # Create output directory
    output_dir = "profiling_example_results"
    profiler = CacheSimProfiler(output_dir)
    
    # Create test data
    print("Setting up test environment...")
    reader = MockReader(num_requests=10000, num_objects=1000)
    
    # Test different cache implementations
    caches_to_test = [
        ("Native LRU", MockLRUCache(1024)),
        ("Plugin LRU", create_plugin_cache(1024)),
        ("Slow Plugin LRU", simulate_slow_plugin_operations())
    ]
    
    print(f"Created mock trace with {reader.num_requests} requests across {reader.num_objects} objects")
    print()
    
    # Profile each cache implementation
    for cache_name, cache in caches_to_test:
        print(f"Profiling {cache_name}...")
        
        # Profile cache operations (individual get requests)
        print(f"  - Cache operations (1000 requests)...")
        result = profiler.profile_plugin_cache_operations(
            cache, reader, num_requests=1000, 
            method_name=f"{cache_name}_operations"
        )
        print(f"    Time: {result.execution_time:.4f}s, Memory: {result.memory_peak:.2f}MB")
        
        # Profile full trace processing
        print(f"  - Full trace processing...")
        result = profiler.profile_trace_processing(
            cache, reader, 
            method_name=f"{cache_name}_trace_processing"
        )
        print(f"    Time: {result.execution_time:.4f}s, Memory: {result.memory_peak:.2f}MB")
        print(f"    Miss ratio: {result.custom_metrics.get('obj_miss_ratio', 'N/A'):.4f}")
        print()
    
    # Generate comprehensive analysis
    print("Generating analysis reports...")
    
    # Save detailed profile stats for each result
    for result in profiler.results:
        stats_file = profiler.save_profile_stats(result)
        print(f"  Saved detailed stats: {stats_file}")
    
    # Generate performance report
    report_file = profiler.generate_performance_report()
    print(f"  Generated performance report: {report_file}")
    
    # Export results in different formats
    json_file = profiler.export_results_json()
    print(f"  Exported JSON results: {json_file}")
    
    csv_file = profiler.export_results_csv()
    print(f"  Exported CSV summary: {csv_file}")
    
    # Compare results
    print("\nPerformance Comparison:")
    print("-" * 30)
    comparison = profiler.compare_results()
    
    if 'error' not in comparison:
        print(f"Fastest method: {comparison['fastest_method']}")
        print(f"Slowest method: {comparison['slowest_method']}")
        print(f"Performance ratio: {comparison['performance_ratio']:.2f}x")
        print(f"Memory ratio: {comparison['memory_ratio']:.2f}x")
        
        print("\nDetailed Comparisons:")
        for comp in comparison['detailed_comparisons']:
            print(f"  {comp['method_name']}: {comp['relative_time']:.2f}x time, "
                  f"{comp['relative_memory']:.2f}x memory")
    else:
        print(f"Comparison failed: {comparison['error']}")
    
    # Demonstrate context manager usage
    print("\nDemonstrating context manager profiling...")
    cache = create_plugin_cache(512)
    reader_small = MockReader(num_requests=1000, num_objects=100)
    
    with profiler.profile_context("context_example") as profile_result:
        # Your code to profile goes here
        n_processed = 0
        reader_small.reset()
        for request in reader_small:
            cache.get(request)
            n_processed += 1
            if n_processed >= 500:
                break
        
        # You can add custom metrics within the context
        profile_result.custom_metrics['requests_processed'] = n_processed
        profile_result.custom_metrics['cache_hits'] = cache.n_hits
        profile_result.custom_metrics['cache_misses'] = cache.n_misses
    
    print(f"Context profiling completed: {profile_result.execution_time:.4f}s")
    print(f"Processed {profile_result.custom_metrics['requests_processed']} requests")
    
    print("\n" + "=" * 50)
    print("Profiling analysis complete!")
    print(f"Results saved in: {output_dir}/")
    print("=" * 50)


if __name__ == "__main__":
    main()