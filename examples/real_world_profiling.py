#!/usr/bin/env python3
"""
Real-world profiling example for libCacheSim plugin cache performance.

This example demonstrates profiling with actual libcachesim components
when the package is properly built and installed.
"""

try:
    import libcachesim as lcs
    from libcachesim.profiler import CacheSimProfiler
    LIBCACHESIM_AVAILABLE = True
except ImportError:
    # Fallback for when libcachesim is not built
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "libcachesim"))
    from profiler import CacheSimProfiler
    LIBCACHESIM_AVAILABLE = False
    print("Note: Using standalone profiler without compiled libcachesim")


def profile_with_real_libcachesim():
    """Profile using real libcachesim components."""
    profiler = CacheSimProfiler("real_profiling_results")
    
    # Create synthetic reader (works without compiled package)
    reader = lcs.SyntheticReader(
        num_of_req=10000,
        num_objects=1000,
        obj_size=100,
        seed=42,
        alpha=0.8,
        dist="zipf"
    )
    
    # Compare different cache types
    caches_to_test = [
        ("LRU", lcs.LRU(cache_size=1024)),
        ("S3FIFO", lcs.S3FIFO(cache_size=1024)),
        ("Plugin LRU", create_plugin_lru_cache())
    ]
    
    for cache_name, cache in caches_to_test:
        print(f"Profiling {cache_name}...")
        
        # Profile trace processing
        result = profiler.profile_trace_processing(
            cache, reader, method_name=f"{cache_name}_processing"
        )
        print(f"  Time: {result.execution_time:.4f}s")
        print(f"  Miss ratio: {result.custom_metrics.get('obj_miss_ratio', 'N/A'):.4f}")
    
    # Generate comparison report
    comparison = profiler.compare_results()
    print(f"\nFastest: {comparison['fastest_method']}")
    print(f"Slowest: {comparison['slowest_method']}")
    print(f"Performance range: {comparison['performance_ratio']:.2f}x")
    
    # Save detailed results
    profiler.generate_performance_report()
    profiler.export_results_json()


def create_plugin_lru_cache():
    """Create a plugin LRU cache for comparison."""
    from collections import OrderedDict
    
    class PluginLRUData:
        def __init__(self, cache_size):
            self.cache_data = OrderedDict()
            self.cache_size = cache_size
    
    def cache_init_hook(common_params):
        return PluginLRUData(common_params.cache_size)
    
    def cache_hit_hook(data, request):
        if request.obj_id in data.cache_data:
            data.cache_data.move_to_end(request.obj_id)
    
    def cache_miss_hook(data, request):
        while len(data.cache_data) >= data.cache_size:
            data.cache_data.popitem(last=False)
        data.cache_data[request.obj_id] = request.obj_size
    
    def cache_eviction_hook(data, request):
        if data.cache_data:
            return next(iter(data.cache_data))
        return None
    
    def cache_remove_hook(data, obj_id):
        data.cache_data.pop(obj_id, None)
    
    def cache_free_hook(data):
        data.cache_data.clear()
    
    return lcs.PluginCache(
        cache_size=1024,
        cache_init_hook=cache_init_hook,
        cache_hit_hook=cache_hit_hook,
        cache_miss_hook=cache_miss_hook,
        cache_eviction_hook=cache_eviction_hook,
        cache_remove_hook=cache_remove_hook,
        cache_free_hook=cache_free_hook,
        cache_name="PluginLRU"
    )


def profile_with_fallback():
    """Fallback profiling when libcachesim is not available."""
    print("Running fallback profiling example...")
    
    # Use the mock implementation from profiling_analysis.py
    import sys
    from pathlib import Path
    
    # Import the mock classes
    exec(open(Path(__file__).parent / "profiling_analysis.py").read())
    
    profiler = CacheSimProfiler("fallback_profiling_results")
    
    # Create test components
    reader = MockReader(num_requests=5000, num_objects=500)
    
    caches = [
        ("Native LRU", MockLRUCache(1024)),
        ("Plugin LRU", create_plugin_cache(1024))
    ]
    
    for cache_name, cache in caches:
        print(f"Profiling {cache_name}...")
        result = profiler.profile_trace_processing(cache, reader, f"{cache_name}_test")
        print(f"  Time: {result.execution_time:.4f}s")
        print(f"  Miss ratio: {result.custom_metrics.get('obj_miss_ratio', 'N/A'):.4f}")
    
    profiler.generate_performance_report()


def main():
    """Main function to run appropriate profiling example."""
    print("libCacheSim Real-World Profiling Example")
    print("=" * 50)
    
    if LIBCACHESIM_AVAILABLE:
        try:
            profile_with_real_libcachesim()
        except Exception as e:
            print(f"Error with real libcachesim: {e}")
            print("Falling back to mock profiling...")
            profile_with_fallback()
    else:
        profile_with_fallback()
    
    print("\nProfiling completed! Check the generated report files.")


if __name__ == "__main__":
    main()