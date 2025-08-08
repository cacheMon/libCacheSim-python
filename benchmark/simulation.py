"""Benchmark the simulation performance of the library.

This module contains benchmarks for various components of the library,
including request processing times, memory usage, and overall throughput.
"""

import libcachesim as lcs
import os
import sys
import tracemalloc
from time import perf_counter, sleep
import subprocess
import matplotlib.pyplot as plt
import numpy as np
import statistics
import psutil
import logging
import threading
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass

# Default configuration
DEFAULT_NUM_ITERATIONS = 20
DEFAULT_CACHE_SIZE_RATIO = 0.1

@dataclass
class BenchmarkResult:
    """Store benchmark results for a single method."""
    method_name: str
    execution_times: List[float]
    memory_usage: List[float]
    miss_ratios: List[float]
    
    @property
    def mean_time(self) -> float:
        return statistics.mean(self.execution_times)
    
    @property
    def std_time(self) -> float:
        return statistics.stdev(self.execution_times) if len(self.execution_times) > 1 else 0.0
    
    @property
    def min_time(self) -> float:
        return min(self.execution_times)
    
    @property
    def max_time(self) -> float:
        return max(self.execution_times)
    
    @property
    def mean_memory(self) -> float:
        return statistics.mean(self.memory_usage) if self.memory_usage else 0.0
    
    @property
    def mean_miss_ratio(self) -> float:
        return statistics.mean(self.miss_ratios)

class SubprocessMemoryMonitor:
    """Monitor memory usage of a subprocess."""
    
    def __init__(self, pid: int):
        self.pid = pid
        self.peak_memory = 0.0
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self):
        """Start monitoring memory usage in a separate thread."""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_memory)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_monitoring(self) -> float:
        """Stop monitoring and return peak memory usage in MB."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        return self.peak_memory
    
    def _monitor_memory(self):
        """Monitor memory usage of the subprocess."""
        try:
            process = psutil.Process(self.pid)
            while self.monitoring:
                try:
                    memory_info = process.memory_info()
                    current_memory = memory_info.rss / 1024 / 1024  # Convert to MB
                    self.peak_memory = max(self.peak_memory, current_memory)
                    sleep(0.01)  # Sample every 10ms
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # Process ended or access denied
                    break
        except psutil.NoSuchProcess:
            # Process doesn't exist
            pass

class CacheSimulationBenchmark:
    """Comprehensive benchmark for cache simulation performance."""
    
    def __init__(self, trace_path: str, num_iterations: int = DEFAULT_NUM_ITERATIONS, 
                 cache_size_ratio: float = DEFAULT_CACHE_SIZE_RATIO):
        self.trace_path = trace_path
        self.num_iterations = num_iterations
        self.cache_size_ratio = cache_size_ratio
        self.results: Dict[str, BenchmarkResult] = {}
        self.logger = self._setup_logging()
        
        # Validate trace file
        if not os.path.exists(trace_path):
            raise FileNotFoundError(f"Trace file not found: {trace_path}")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def _get_process_memory(self) -> float:
        """Get current process memory usage in MB."""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    
    def _find_cachesim_binary(self) -> Optional[str]:
        """Find the cachesim binary in common locations."""
        possible_paths = [
            "./src/libCacheSim/build/bin/cachesim",
            "./build/bin/cachesim",
            "../build/bin/cachesim",
            "cachesim"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
            elif path == "cachesim":
                # Check if it's in PATH
                try:
                    result = subprocess.run(["which", "cachesim"], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        return "cachesim"
                except FileNotFoundError:
                    # 'which' command not available (e.g., on Windows)
                    pass
        
        return None
    
    def _parse_native_c_output(self, output: str) -> float:
        """Parse miss ratio from native C binary output."""
        try:
            for line in output.split('\n'):
                line = line.strip()
                if 'miss ratio' in line.lower():
                    # Try to extract the last number from the line
                    parts = line.split()
                    for part in reversed(parts):
                        try:
                            return float(part.rstrip('%,.:'))
                        except ValueError:
                            continue
                # Alternative patterns
                elif 'miss rate' in line.lower():
                    parts = line.split()
                    for part in reversed(parts):
                        try:
                            return float(part.rstrip('%,.:'))
                        except ValueError:
                            continue
        except (ValueError, IndexError, AttributeError) as e:
            self.logger.warning(f"Could not parse miss ratio from native C output: {e}")
        
        return 0.0  # Default value if parsing fails
    
    def _benchmark_native_c(self) -> BenchmarkResult:
        """Benchmark native C binary execution with proper subprocess memory monitoring."""
        self.logger.info("Benchmarking native C binary...")
        
        execution_times = []
        memory_usage = []
        miss_ratios = []
        
        cachesim_path = self._find_cachesim_binary()
        if not cachesim_path:
            self.logger.warning("Native C binary not found, skipping native benchmark")
            return BenchmarkResult("Native C", [], [], [])
        
        for i in range(self.num_iterations):
            self.logger.info(f"Native C - Iteration {i+1}/{self.num_iterations}")
            
            try:
                start_time = perf_counter()
                
                # Use Popen for better control over the subprocess
                process = subprocess.Popen([
                    cachesim_path,
                    self.trace_path,
                    "oracleGeneral",
                    "LRU",
                    "1",
                    "--ignore-obj-size", "1"
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                
                # Start memory monitoring
                memory_monitor = SubprocessMemoryMonitor(process.pid)
                memory_monitor.start_monitoring()
                
                # Wait for process to complete
                stdout, stderr = process.communicate()
                end_time = perf_counter()
                
                # Stop memory monitoring
                peak_memory = memory_monitor.stop_monitoring()
                
                if process.returncode != 0:
                    self.logger.warning(f"Native C execution failed with return code {process.returncode}")
                    self.logger.warning(f"stderr: {stderr}")
                    continue
                
                execution_time = end_time - start_time
                miss_ratio = self._parse_native_c_output(stdout)
                
                execution_times.append(execution_time)
                memory_usage.append(peak_memory)
                miss_ratios.append(miss_ratio)
                
            except (subprocess.SubprocessError, OSError) as e:
                self.logger.warning(f"Native C execution failed: {e}")
                continue
        
        return BenchmarkResult("Native C", execution_times, memory_usage, miss_ratios)
    
    def _benchmark_c_process_trace(self) -> BenchmarkResult:
        """Benchmark Python with c_process_trace method."""
        self.logger.info("Benchmarking Python c_process_trace...")
        
        execution_times = []
        memory_usage = []
        miss_ratios = []
        
        for i in range(self.num_iterations):
            self.logger.info(f"c_process_trace - Iteration {i+1}/{self.num_iterations}")
            
            # Start memory tracking
            tracemalloc.start()
            memory_before = self._get_process_memory()
            
            start_time = perf_counter()
            
            try:
                # Setup reader and cache
                reader = lcs.TraceReader(
                    trace=self.trace_path,
                    trace_type=lcs.TraceType.ORACLE_GENERAL_TRACE,
                    reader_init_params=lcs.ReaderInitParam(ignore_obj_size=True)
                )
                
                wss_size = reader.get_working_set_size()
                cache_size = int(wss_size[0] * self.cache_size_ratio)
                cache = lcs.LRU(cache_size=cache_size)
                
                # Process trace
                req_miss_ratio, byte_miss_ratio = cache.process_trace(reader)
                
                end_time = perf_counter()
                
                # Memory tracking
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                memory_after = self._get_process_memory()
                
                execution_times.append(end_time - start_time)
                memory_usage.append(memory_after - memory_before)
                miss_ratios.append(req_miss_ratio)
                
            except Exception as e:
                self.logger.error(f"c_process_trace iteration {i+1} failed: {e}")
                tracemalloc.stop()
                continue
        
        return BenchmarkResult("Python c_process_trace", execution_times, memory_usage, miss_ratios)
    
    def _benchmark_python_loop(self) -> BenchmarkResult:
        """Benchmark Python with manual loop."""
        self.logger.info("Benchmarking Python loop...")
        
        execution_times = []
        memory_usage = []
        miss_ratios = []
        
        for i in range(self.num_iterations):
            self.logger.info(f"Python loop - Iteration {i+1}/{self.num_iterations}")
            
            # Start memory tracking
            tracemalloc.start()
            memory_before = self._get_process_memory()
            
            start_time = perf_counter()
            
            try:
                # Setup reader and cache
                reader = lcs.TraceReader(
                    trace=self.trace_path,
                    trace_type=lcs.TraceType.ORACLE_GENERAL_TRACE,
                    reader_init_params=lcs.ReaderInitParam(ignore_obj_size=True)
                )
                
                wss_size = reader.get_working_set_size()
                cache_size = int(wss_size[0] * self.cache_size_ratio)
                cache = lcs.LRU(cache_size=cache_size)
                
                # Manual loop processing
                n_miss = 0
                n_req = 0
                reader.reset()
                
                for request in reader:
                    n_req += 1
                    hit = cache.get(request)
                    if not hit:
                        n_miss += 1
                
                req_miss_ratio = n_miss / n_req if n_req > 0 else 0.0
                
                end_time = perf_counter()
                
                # Memory tracking
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                memory_after = self._get_process_memory()
                
                execution_times.append(end_time - start_time)
                memory_usage.append(memory_after - memory_before)
                miss_ratios.append(req_miss_ratio)
                
            except Exception as e:
                self.logger.error(f"Python loop iteration {i+1} failed: {e}")
                tracemalloc.stop()
                continue
        
        return BenchmarkResult("Python loop", execution_times, memory_usage, miss_ratios)
    
    def run_benchmark(self) -> Dict[str, BenchmarkResult]:
        """Run all benchmarks and return results."""
        self.logger.info(f"Starting benchmark with {self.num_iterations} iterations")
        self.logger.info(f"Trace file: {self.trace_path}")
        self.logger.info(f"Cache size ratio: {self.cache_size_ratio}")
        
        # Run benchmarks
        self.results["native_c"] = self._benchmark_native_c()
        self.results["c_process_trace"] = self._benchmark_c_process_trace()
        self.results["python_loop"] = self._benchmark_python_loop()
        
        return self.results
    
    def validate_results(self) -> bool:
        """Validate that all methods produce similar miss ratios."""
        self.logger.info("Validating results...")
        
        miss_ratios = []
        for name, result in self.results.items():
            if result.execution_times and result.miss_ratios:  # Only check methods that ran successfully
                miss_ratios.append((name, result.mean_miss_ratio))
        
        if len(miss_ratios) < 2:
            self.logger.warning("Not enough results to validate")
            return True
        
        # Check if all miss ratios are within 1% of each other
        base_ratio = miss_ratios[0][1]
        validation_passed = True
        
        for name, ratio in miss_ratios[1:]:
            relative_diff = abs(ratio - base_ratio) / max(base_ratio, 1e-10)  # Avoid division by zero
            if relative_diff > 0.01:  # 1% tolerance
                self.logger.warning(f"Miss ratio mismatch: {miss_ratios[0][0]}={base_ratio:.4f}, {name}={ratio:.4f} (diff: {relative_diff:.2%})")
                validation_passed = False
        
        if validation_passed:
            self.logger.info("All miss ratios match within tolerance")
        
        return validation_passed
    
    def print_statistics(self):
        """Print detailed performance statistics."""
        print("\n" + "="*80)
        print("COMPREHENSIVE PERFORMANCE ANALYSIS")
        print("="*80)
        print(f"Configuration: {self.num_iterations} iterations, cache size ratio: {self.cache_size_ratio}")
        print(f"Trace file: {os.path.basename(self.trace_path)}")
        
        # Basic statistics
        for name, result in self.results.items():
            if not result.execution_times:
                print(f"\n{result.method_name}: No valid results")
                continue
                
            print(f"\n{result.method_name} Performance:")
            print(f"  Execution Time:")
            print(f"    Mean: {result.mean_time:.4f} ± {result.std_time:.4f} seconds")
            print(f"    Range: [{result.min_time:.4f}, {result.max_time:.4f}] seconds")
            print(f"  Memory Usage:")
            if result.memory_usage:
                print(f"    Mean: {result.mean_memory:.2f} MB")
            else:
                print(f"    Mean: N/A")
            print(f"  Cache Performance:")
            print(f"    Mean Miss Ratio: {result.mean_miss_ratio:.4f}")
            print(f"  Successful Iterations: {len(result.execution_times)}/{self.num_iterations}")
        
        # Comparative analysis
        valid_results = [(name, result) for name, result in self.results.items() if result.execution_times]
        if len(valid_results) >= 2:
            print(f"\n{'Comparative Analysis':=^60}")
            
            # Find fastest method
            fastest_method = min(valid_results, key=lambda x: x[1].mean_time)
            
            print(f"\nFastest Method: {fastest_method[1].method_name} ({fastest_method[1].mean_time:.4f}s)")
            
            # Compare all methods to fastest
            for name, result in valid_results:
                if name == fastest_method[0]:
                    continue
                
                speedup_factor = result.mean_time / fastest_method[1].mean_time
                overhead_percent = (speedup_factor - 1) * 100
                
                print(f"  {result.method_name}:")
                print(f"    {speedup_factor:.2f}x slower ({overhead_percent:.1f}% overhead)")
        
        # Throughput analysis
        print(f"\n{'Throughput Analysis':=^60}")
        for name, result in self.results.items():
            if not result.execution_times:
                continue
            
            # Estimate traces per second
            throughput = 1 / result.mean_time
            print(f"{result.method_name}: ~{throughput:.1f} traces/second")
    
    def create_visualizations(self, save_path: str = "benchmark_comprehensive_analysis.png"):
        """Create comprehensive visualizations."""
        # Filter out empty results
        valid_results = {name: result for name, result in self.results.items() 
                        if result.execution_times}
        
        if not valid_results:
            self.logger.warning("No valid results to visualize")
            return
        
        fig = plt.figure(figsize=(20, 15))
        
        # Setup subplots
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # Plot 1: Execution times across iterations
        ax1 = fig.add_subplot(gs[0, :2])
        iterations = range(1, self.num_iterations + 1)
        colors = ['blue', 'red', 'green', 'orange', 'purple']
        
        for i, (name, result) in enumerate(valid_results.items()):
            if result.execution_times:
                ax1.plot(iterations[:len(result.execution_times)], result.execution_times, 
                        color=colors[i % len(colors)], label=result.method_name, 
                        marker='o', markersize=4, alpha=0.7)
        
        ax1.set_xlabel('Iteration')
        ax1.set_ylabel('Execution Time (seconds)')
        ax1.set_title('Execution Times Across Iterations')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Box plot of execution times
        ax2 = fig.add_subplot(gs[0, 2])
        execution_data = [result.execution_times for result in valid_results.values() if result.execution_times]
        labels = [result.method_name.replace(' ', '\n') for result in valid_results.values() if result.execution_times]
        
        if execution_data:
            ax2.boxplot(execution_data, tick_labels=labels)  # Fixed matplotlib warning
            ax2.set_ylabel('Execution Time (seconds)')
            ax2.set_title('Execution Time Distribution')
            ax2.grid(True, alpha=0.3)
        
        # Plot 3: Memory usage comparison
        ax3 = fig.add_subplot(gs[1, 0])
        methods_with_memory = [(result.method_name, result.mean_memory) for result in valid_results.values() if result.memory_usage]
        
        if methods_with_memory:
            methods, memory_means = zip(*methods_with_memory)
            bars = ax3.bar(methods, memory_means, color=['blue', 'red', 'green'][:len(methods)])
            ax3.set_ylabel('Memory Usage (MB) (Python show extra memory usage)')
            ax3.set_title('Average Memory Usage')
            ax3.tick_params(axis='x', rotation=45)
            
            # Add value labels on bars
            for bar, value in zip(bars, memory_means):
                if value > 0:  # Only add label if we have valid memory data
                    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(memory_means)*0.01, 
                            f'{value:.1f}', ha='center', va='bottom')
        
        # Plot 4: Performance comparison (relative to fastest)
        ax4 = fig.add_subplot(gs[1, 1])
        if len(valid_results) >= 2:
            fastest_time = min(result.mean_time for result in valid_results.values() if result.execution_times)
            relative_times = []
            method_names = []
            
            for result in valid_results.values():
                if result.execution_times:
                    relative_times.append(result.mean_time / fastest_time)
                    method_names.append(result.method_name)
            
            bars = ax4.bar(method_names, relative_times, color=['green', 'orange', 'red'][:len(method_names)])
            ax4.set_ylabel('Relative Performance (1.0 = fastest)')
            ax4.set_title('Relative Performance Comparison')
            ax4.tick_params(axis='x', rotation=45)
            ax4.axhline(y=1, color='black', linestyle='--', alpha=0.5)
            
            # Add value labels
            for bar, value in zip(bars, relative_times):
                ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, 
                        f'{value:.2f}x', ha='center', va='bottom')
        
        # Plot 5: Miss ratio consistency
        ax5 = fig.add_subplot(gs[1, 2])
        miss_ratio_data = [result.miss_ratios for result in valid_results.values() if result.miss_ratios]
        miss_ratio_labels = [result.method_name.replace(' ', '\n') for result in valid_results.values() if result.miss_ratios]
        
        if miss_ratio_data:
            ax5.boxplot(miss_ratio_data, tick_labels=miss_ratio_labels)
            ax5.set_ylabel('Miss Ratio')
            ax5.set_title('Miss Ratio Consistency')
            ax5.grid(True, alpha=0.3)
        
        # Plot 6: Execution time histogram for each method
        ax6 = fig.add_subplot(gs[2, :])
        for i, (name, result) in enumerate(valid_results.items()):
            if result.execution_times:
                ax6.hist(result.execution_times, alpha=0.6, label=result.method_name, 
                        bins=min(10, len(result.execution_times)), 
                        color=colors[i % len(colors)])
        
        ax6.set_xlabel('Execution Time (seconds)')
        ax6.set_ylabel('Frequency')
        ax6.set_title('Execution Time Distribution by Method')
        ax6.legend()
        ax6.grid(True, alpha=0.3)
        
        plt.suptitle(f'Cache Simulation Performance Benchmark\n'
                    f'({self.num_iterations} iterations, Cache ratio: {self.cache_size_ratio}, Trace: {os.path.basename(self.trace_path)})', 
                    fontsize=16, y=0.98)
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        self.logger.info(f"Visualization saved as '{save_path}'")
        
        return save_path
    
    def export_results(self, csv_path: str = "benchmark_results.csv"):
        """Export results to CSV file."""
        import csv
        
        with open(csv_path, 'w', newline='') as csvfile:
            fieldnames = ['method', 'iteration', 'execution_time', 'memory_usage', 'miss_ratio']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for name, result in self.results.items():
                if not result.execution_times:
                    continue
                
                max_len = max(len(result.execution_times), 
                             len(result.memory_usage) if result.memory_usage else 0,
                             len(result.miss_ratios) if result.miss_ratios else 0)
                
                for i in range(max_len):
                    exec_time = result.execution_times[i] if i < len(result.execution_times) else None
                    mem_usage = result.memory_usage[i] if result.memory_usage and i < len(result.memory_usage) else None
                    miss_ratio = result.miss_ratios[i] if result.miss_ratios and i < len(result.miss_ratios) else None
                    
                    writer.writerow({
                        'method': result.method_name,
                        'iteration': i + 1,
                        'execution_time': exec_time,
                        'memory_usage': mem_usage,
                        'miss_ratio': miss_ratio
                    })
        
        self.logger.info(f"Results exported to '{csv_path}'")


def main():
    """Main function to run the benchmark."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive Cache Simulation Performance Benchmark")
    parser.add_argument("--trace_path", type=str, required=True, 
                       help="Path to the trace file")
    parser.add_argument("--iterations", type=int, default=DEFAULT_NUM_ITERATIONS,
                       help=f"Number of iterations (default: {DEFAULT_NUM_ITERATIONS})")
    parser.add_argument("--cache_size_ratio", type=float, default=DEFAULT_CACHE_SIZE_RATIO,
                       help=f"Cache size as ratio of working set (default: {DEFAULT_CACHE_SIZE_RATIO})")
    parser.add_argument("--output_dir", type=str, default=".",
                       help="Output directory for results (default: current directory)")
    parser.add_argument("--export_csv", action="store_true",
                       help="Export results to CSV file")
    parser.add_argument("--no_visualize", action="store_true",
                       help="Skip visualization generation")
    
    args = parser.parse_args()
    
    try:
        # Create benchmark instance with proper parameters (no more global variables)
        benchmark = CacheSimulationBenchmark(
            trace_path=args.trace_path,
            num_iterations=args.iterations,
            cache_size_ratio=args.cache_size_ratio
        )
        
        # Run benchmark
        results = benchmark.run_benchmark()
        
        # Validate results
        benchmark.validate_results()
        
        # Print statistics
        benchmark.print_statistics()
        
        # Create visualizations
        if not args.no_visualize:
            viz_path = os.path.join(args.output_dir, "benchmark_comprehensive_analysis.png")
            benchmark.create_visualizations(viz_path)
        
        # Export CSV
        if args.export_csv:
            csv_path = os.path.join(args.output_dir, "benchmark_results.csv")
            benchmark.export_results(csv_path)
        
        print(f"\n{'='*80}")
        print("BENCHMARK COMPLETED SUCCESSFULLY")
        print(f"{'='*80}")
        
    except Exception as e:
        logging.error(f"Benchmark failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()