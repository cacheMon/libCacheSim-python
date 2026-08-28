#!/usr/bin/env python3
"""
Simple test for profiler functionality without compiled libcachesim package.
"""

import sys
from pathlib import Path

# Add libcachesim to path
sys.path.insert(0, str(Path(__file__).parent.parent / "libcachesim"))

from profiler import CacheSimProfiler


def test_basic_profiling():
    """Test basic profiling functionality."""
    profiler = CacheSimProfiler("test_output")
    
    # Profile a simple function
    def slow_function():
        """Simple function that takes some time."""
        result = 0
        for i in range(100000):
            result += i * i
        return result
    
    # Test function profiling
    result, profile_result = profiler.profile_function(slow_function, method_name="slow_math")
    
    print(f"Function result: {result}")
    print(f"Execution time: {profile_result.execution_time:.4f}s")
    print(f"Memory peak: {profile_result.memory_peak:.2f}MB")
    
    # Test context manager
    with profiler.profile_context("context_test") as profile_result:
        data = [i**2 for i in range(10000)]
        profile_result.custom_metrics['list_length'] = len(data)
    
    print(f"Context execution time: {profile_result.execution_time:.4f}s")
    print(f"List length: {profile_result.custom_metrics['list_length']}")
    
    # Generate reports
    report = profiler.generate_performance_report("test_report.txt")
    json_file = profiler.export_results_json("test_results.json")
    
    print(f"Report saved: {report}")
    print(f"JSON saved: {json_file}")
    
    print("Basic profiling test passed!")


if __name__ == "__main__":
    test_basic_profiling()