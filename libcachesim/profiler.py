"""Profiling utilities for libCacheSim performance analysis.

This module provides comprehensive profiling capabilities for analyzing the performance
of cache simulations, particularly plugin caches and trace processing operations.
"""

import cProfile
import pstats
import io
import time
import tracemalloc
import psutil
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from contextlib import contextmanager
import json
import csv


@dataclass
class ProfileResult:
    """Container for profiling results."""
    method_name: str
    execution_time: float
    memory_peak: float
    memory_current: float
    cpu_percent: float
    profile_stats: Optional[pstats.Stats] = None
    custom_metrics: Dict[str, Any] = field(default_factory=dict)


class CacheSimProfiler:
    """Comprehensive profiler for cache simulation operations."""
    
    def __init__(self, output_dir: str = "profiling_results"):
        """Initialize the profiler.
        
        Args:
            output_dir: Directory to save profiling results
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results: List[ProfileResult] = []
        self.current_profile: Optional[cProfile.Profile] = None
        self.start_time: float = 0
        self.process = psutil.Process(os.getpid())
        
    def profile_function(
        self, 
        func: Callable, 
        *args, 
        method_name: str = None,
        **kwargs
    ) -> Tuple[Any, ProfileResult]:
        """Profile a single function call with comprehensive metrics.
        
        Args:
            func: Function to profile
            *args: Arguments for the function
            method_name: Name for this profiling run
            **kwargs: Keyword arguments for the function
            
        Returns:
            Tuple of (function_result, ProfileResult)
        """
        if method_name is None:
            method_name = func.__name__
            
        # Start memory tracking
        tracemalloc.start()
        
        # Create profiler
        profiler = cProfile.Profile()
        
        # Record initial state
        memory_before = self.process.memory_info().rss / 1024 / 1024  # MB
        start_time = time.perf_counter()
        
        # Run function with profiling
        profiler.enable()
        try:
            result = func(*args, **kwargs)
        finally:
            profiler.disable()
            
        # Record final state
        end_time = time.perf_counter()
        memory_after = self.process.memory_info().rss / 1024 / 1024  # MB
        
        # Get memory peak from tracemalloc
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Get CPU usage (approximate)
        cpu_percent = self.process.cpu_percent()
        
        # Create stats object
        stats_io = io.StringIO()
        stats = pstats.Stats(profiler, stream=stats_io)
        
        # Create result
        profile_result = ProfileResult(
            method_name=method_name,
            execution_time=end_time - start_time,
            memory_peak=peak / 1024 / 1024,  # Convert to MB
            memory_current=memory_after - memory_before,
            cpu_percent=cpu_percent,
            profile_stats=stats
        )
        
        self.results.append(profile_result)
        return result, profile_result
    
    @contextmanager
    def profile_context(self, method_name: str):
        """Context manager for profiling a block of code.
        
        Args:
            method_name: Name for this profiling session
            
        Yields:
            ProfileResult that will be populated when context exits
        """
        # Start memory tracking
        tracemalloc.start()
        
        # Create profiler
        profiler = cProfile.Profile()
        
        # Record initial state
        memory_before = self.process.memory_info().rss / 1024 / 1024  # MB
        start_time = time.perf_counter()
        
        # Create result object (will be populated on exit)
        profile_result = ProfileResult(
            method_name=method_name,
            execution_time=0,
            memory_peak=0,
            memory_current=0,
            cpu_percent=0
        )
        
        profiler.enable()
        try:
            yield profile_result
        finally:
            profiler.disable()
            
            # Record final state
            end_time = time.perf_counter()
            memory_after = self.process.memory_info().rss / 1024 / 1024  # MB
            
            # Get memory peak from tracemalloc
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            # Get CPU usage
            cpu_percent = self.process.cpu_percent()
            
            # Create stats object
            stats_io = io.StringIO()
            stats = pstats.Stats(profiler, stream=stats_io)
            
            # Update result
            profile_result.execution_time = end_time - start_time
            profile_result.memory_peak = peak / 1024 / 1024  # Convert to MB
            profile_result.memory_current = memory_after - memory_before
            profile_result.cpu_percent = cpu_percent
            profile_result.profile_stats = stats
            
            self.results.append(profile_result)
    
    def profile_plugin_cache_operations(
        self, 
        cache, 
        reader, 
        num_requests: int = 1000,
        method_name: str = "plugin_cache_operations"
    ) -> ProfileResult:
        """Profile plugin cache operations with detailed function-level analysis.
        
        Args:
            cache: Cache object to profile
            reader: Reader object for trace data
            num_requests: Number of requests to process
            method_name: Name for this profiling run
            
        Returns:
            ProfileResult with detailed profiling information
        """
        def run_cache_operations():
            """Run cache operations for profiling."""
            reader.reset()
            n_hit = 0
            n_miss = 0
            
            for i, request in enumerate(reader):
                if i >= num_requests:
                    break
                    
                hit = cache.get(request)
                if hit:
                    n_hit += 1
                else:
                    n_miss += 1
            
            return {
                'n_hit': n_hit,
                'n_miss': n_miss,
                'n_total': i + 1,
                'hit_ratio': n_hit / (i + 1) if i >= 0 else 0
            }
        
        result, profile_result = self.profile_function(run_cache_operations, method_name=method_name)
        profile_result.custom_metrics = result
        return profile_result
    
    def profile_trace_processing(
        self, 
        cache, 
        reader, 
        method_name: str = "trace_processing"
    ) -> ProfileResult:
        """Profile complete trace processing operation.
        
        Args:
            cache: Cache object to use
            reader: Reader object for trace data  
            method_name: Name for this profiling run
            
        Returns:
            ProfileResult with profiling information
        """
        def run_trace_processing():
            """Run trace processing for profiling."""
            # Try to use process_trace if available
            if hasattr(cache, 'process_trace'):
                return cache.process_trace(reader)
            else:
                # Fallback to manual processing
                reader.reset()
                n_hit = 0
                n_total = 0
                bytes_hit = 0
                bytes_total = 0
                
                for request in reader:
                    n_total += 1
                    bytes_total += getattr(request, 'obj_size', 1)
                    
                    if cache.get(request):
                        n_hit += 1
                        bytes_hit += getattr(request, 'obj_size', 1)
                
                obj_miss_ratio = 1.0 - (n_hit / n_total) if n_total > 0 else 0.0
                byte_miss_ratio = 1.0 - (bytes_hit / bytes_total) if bytes_total > 0 else 0.0
                
                return obj_miss_ratio, byte_miss_ratio
        
        result, profile_result = self.profile_function(run_trace_processing, method_name=method_name)
        if isinstance(result, tuple) and len(result) == 2:
            profile_result.custom_metrics = {
                'obj_miss_ratio': result[0],
                'byte_miss_ratio': result[1]
            }
        else:
            profile_result.custom_metrics = {'result': str(result)}
            
        return profile_result
    
    def analyze_profile_stats(self, result: ProfileResult, top_n: int = 20) -> Dict[str, Any]:
        """Analyze profile statistics and extract key insights.
        
        Args:
            result: ProfileResult to analyze
            top_n: Number of top functions to analyze
            
        Returns:
            Dictionary with analysis results
        """
        if not result.profile_stats:
            return {}
        
        stats = result.profile_stats
        
        # Get top functions by cumulative time
        stats.sort_stats('cumulative')
        
        # Capture stats output
        stats_io = io.StringIO()
        stats.print_stats(top_n)
        stats_output = stats_io.getvalue()
        
        # Get total function calls
        total_calls = stats.total_calls
        
        # Get top functions by total time
        stats.sort_stats('tottime')
        top_time_io = io.StringIO() 
        old_stdout = sys.stdout
        sys.stdout = top_time_io
        stats.print_stats(top_n)
        sys.stdout = old_stdout
        top_time_output = top_time_io.getvalue()
        
        # Extract function call information
        function_stats = []
        for func, (cc, nc, tt, ct, callers) in stats.stats.items():
            function_stats.append({
                'function': f"{func[0]}:{func[1]}({func[2]})",
                'call_count': cc,
                'total_time': tt,
                'cumulative_time': ct,
                'time_per_call': tt / cc if cc > 0 else 0
            })
        
        # Sort by total time and get top functions
        function_stats.sort(key=lambda x: x['total_time'], reverse=True)
        top_functions = function_stats[:top_n]
        
        return {
            'total_calls': total_calls,
            'top_functions_by_time': top_functions,
            'cumulative_stats_output': stats_output,
            'total_time_stats_output': top_time_output,
            'function_count': len(function_stats)
        }
    
    def save_profile_stats(self, result: ProfileResult, filename: str = None) -> str:
        """Save detailed profile statistics to file.
        
        Args:
            result: ProfileResult to save
            filename: Optional filename, otherwise auto-generated
            
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = int(time.time())
            filename = f"profile_{result.method_name}_{timestamp}.txt"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            f.write(f"Profile Results for: {result.method_name}\n")
            f.write("=" * 60 + "\n")
            f.write(f"Execution Time: {result.execution_time:.4f} seconds\n")
            f.write(f"Memory Peak: {result.memory_peak:.2f} MB\n")
            f.write(f"Memory Change: {result.memory_current:.2f} MB\n")
            f.write(f"CPU Percent: {result.cpu_percent:.1f}%\n")
            f.write("\nCustom Metrics:\n")
            for key, value in result.custom_metrics.items():
                f.write(f"  {key}: {value}\n")
            f.write("\n" + "=" * 60 + "\n")
            
            if result.profile_stats:
                # Save cumulative time stats
                f.write("\nTop Functions by Cumulative Time:\n")
                f.write("-" * 40 + "\n")
                result.profile_stats.sort_stats('cumulative')
                
                # Capture stats output using StringIO
                stats_io = io.StringIO()
                result.profile_stats.stream = stats_io
                result.profile_stats.print_stats(30)
                f.write(stats_io.getvalue())
                
                f.write("\n" + "-" * 40 + "\n")
                f.write("Top Functions by Total Time:\n")
                f.write("-" * 40 + "\n")
                
                result.profile_stats.sort_stats('tottime')
                stats_io = io.StringIO()
                result.profile_stats.stream = stats_io
                result.profile_stats.print_stats(30)
                f.write(stats_io.getvalue())
        
        return str(filepath)
    
    def generate_performance_report(self, filename: str = None) -> str:
        """Generate a comprehensive performance report for all profiling results.
        
        Args:
            filename: Optional filename, otherwise auto-generated
            
        Returns:
            Path to generated report
        """
        if filename is None:
            timestamp = int(time.time())
            filename = f"performance_report_{timestamp}.txt"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            f.write("libCacheSim Performance Analysis Report\n")
            f.write("=" * 60 + "\n")
            f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Profile Runs: {len(self.results)}\n\n")
            
            # Summary table
            f.write("Summary of All Profile Runs:\n")
            f.write("-" * 60 + "\n")
            f.write(f"{'Method':<25} {'Time (s)':<12} {'Memory (MB)':<12} {'CPU %':<8}\n")
            f.write("-" * 60 + "\n")
            
            total_time = 0
            for result in self.results:
                f.write(f"{result.method_name:<25} {result.execution_time:<12.4f} "
                       f"{result.memory_peak:<12.2f} {result.cpu_percent:<8.1f}\n")
                total_time += result.execution_time
            
            f.write("-" * 60 + "\n")
            f.write(f"{'TOTAL':<25} {total_time:<12.4f}\n")
            f.write("\n")
            
            # Detailed analysis for each run
            for i, result in enumerate(self.results, 1):
                f.write(f"\n{i}. Detailed Analysis: {result.method_name}\n")
                f.write("=" * 50 + "\n")
                
                f.write(f"Execution Time: {result.execution_time:.4f} seconds\n")
                f.write(f"Memory Peak: {result.memory_peak:.2f} MB\n")
                f.write(f"Memory Change: {result.memory_current:.2f} MB\n")
                f.write(f"CPU Usage: {result.cpu_percent:.1f}%\n")
                
                if result.custom_metrics:
                    f.write("\nCustom Metrics:\n")
                    for key, value in result.custom_metrics.items():
                        f.write(f"  {key}: {value}\n")
                
                # Add function analysis
                analysis = self.analyze_profile_stats(result)
                if analysis:
                    f.write(f"\nFunction Call Analysis:\n")
                    f.write(f"  Total Function Calls: {analysis.get('total_calls', 'N/A')}\n")
                    f.write(f"  Unique Functions: {analysis.get('function_count', 'N/A')}\n")
                    
                    top_funcs = analysis.get('top_functions_by_time', [])[:5]
                    if top_funcs:
                        f.write("\n  Top 5 Functions by Time:\n")
                        for func in top_funcs:
                            f.write(f"    {func['function']}: {func['total_time']:.4f}s "
                                   f"({func['call_count']} calls)\n")
                
                f.write("\n")
        
        return str(filepath)
    
    def export_results_json(self, filename: str = None) -> str:
        """Export all results to JSON format.
        
        Args:
            filename: Optional filename, otherwise auto-generated
            
        Returns:
            Path to exported JSON file
        """
        if filename is None:
            timestamp = int(time.time())
            filename = f"profile_results_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        # Convert results to JSON-serializable format
        json_results = []
        for result in self.results:
            json_result = {
                'method_name': result.method_name,
                'execution_time': result.execution_time,
                'memory_peak': result.memory_peak,
                'memory_current': result.memory_current,
                'cpu_percent': result.cpu_percent,
                'custom_metrics': result.custom_metrics
            }
            
            # Add function stats if available
            if result.profile_stats:
                analysis = self.analyze_profile_stats(result)
                json_result['analysis'] = analysis
            
            json_results.append(json_result)
        
        with open(filepath, 'w') as f:
            json.dump({
                'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_runs': len(self.results),
                'results': json_results
            }, f, indent=2)
        
        return str(filepath)
    
    def export_results_csv(self, filename: str = None) -> str:
        """Export results summary to CSV format.
        
        Args:
            filename: Optional filename, otherwise auto-generated
            
        Returns:
            Path to exported CSV file
        """
        if filename is None:
            timestamp = int(time.time())
            filename = f"profile_summary_{timestamp}.csv"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            header = ['method_name', 'execution_time', 'memory_peak_mb', 'memory_change_mb', 'cpu_percent']
            
            # Add custom metrics columns
            all_metrics = set()
            for result in self.results:
                all_metrics.update(result.custom_metrics.keys())
            
            header.extend(sorted(all_metrics))
            writer.writerow(header)
            
            # Write data rows
            for result in self.results:
                row = [
                    result.method_name,
                    result.execution_time,
                    result.memory_peak,
                    result.memory_current,
                    result.cpu_percent
                ]
                
                # Add custom metrics values
                for metric in sorted(all_metrics):
                    row.append(result.custom_metrics.get(metric, ''))
                
                writer.writerow(row)
        
        return str(filepath)
    
    def compare_results(self, method_names: List[str] = None) -> Dict[str, Any]:
        """Compare performance across different profiled methods.
        
        Args:
            method_names: Optional list of method names to compare. If None, compares all.
            
        Returns:
            Dictionary with comparison analysis
        """
        if method_names is None:
            results_to_compare = self.results
        else:
            results_to_compare = [r for r in self.results if r.method_name in method_names]
        
        if len(results_to_compare) < 2:
            return {'error': 'Need at least 2 results to compare'}
        
        # Find best and worst performers
        fastest = min(results_to_compare, key=lambda r: r.execution_time)
        slowest = max(results_to_compare, key=lambda r: r.execution_time)
        
        lowest_memory = min(results_to_compare, key=lambda r: r.memory_peak)
        highest_memory = max(results_to_compare, key=lambda r: r.memory_peak)
        
        # Calculate relative performance
        comparisons = []
        for result in results_to_compare:
            relative_time = result.execution_time / fastest.execution_time
            relative_memory = result.memory_peak / lowest_memory.memory_peak if lowest_memory.memory_peak > 0 else 1
            
            comparisons.append({
                'method_name': result.method_name,
                'execution_time': result.execution_time,
                'relative_time': relative_time,
                'memory_peak': result.memory_peak,
                'relative_memory': relative_memory,
                'speedup_vs_slowest': slowest.execution_time / result.execution_time
            })
        
        return {
            'fastest_method': fastest.method_name,
            'slowest_method': slowest.method_name,
            'lowest_memory_method': lowest_memory.method_name,
            'highest_memory_method': highest_memory.method_name,
            'performance_ratio': slowest.execution_time / fastest.execution_time,
            'memory_ratio': highest_memory.memory_peak / lowest_memory.memory_peak if lowest_memory.memory_peak > 0 else 1,
            'detailed_comparisons': comparisons
        }
    
    def clear_results(self):
        """Clear all stored profiling results."""
        self.results.clear()


# Convenience function for quick profiling
def profile_cache_operations(cache, reader, num_requests: int = 1000, output_dir: str = "profiling_results") -> ProfileResult:
    """Quick profiling of cache operations.
    
    Args:
        cache: Cache object to profile
        reader: Reader object for trace data
        num_requests: Number of requests to process
        output_dir: Directory to save results
        
    Returns:
        ProfileResult with profiling information
    """
    profiler = CacheSimProfiler(output_dir)
    result = profiler.profile_plugin_cache_operations(cache, reader, num_requests)
    
    # Save detailed results
    profiler.save_profile_stats(result)
    profiler.generate_performance_report()
    
    return result


def profile_trace_processing(cache, reader, output_dir: str = "profiling_results") -> ProfileResult:
    """Quick profiling of trace processing.
    
    Args:
        cache: Cache object to use
        reader: Reader object for trace data
        output_dir: Directory to save results
        
    Returns:
        ProfileResult with profiling information
    """
    profiler = CacheSimProfiler(output_dir)
    result = profiler.profile_trace_processing(cache, reader)
    
    # Save detailed results
    profiler.save_profile_stats(result)
    profiler.generate_performance_report()
    
    return result