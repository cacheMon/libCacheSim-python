"""Benchmark the simulation performance of the library.

This module contains benchmarks for various components of the library,
including request processing times, memory usage, and overall throughput.
"""

import libcachesim as lcs
import os
import sys
import tracemalloc
from time import perf_counter
import subprocess
import matplotlib.pyplot as plt
import numpy as np
import statistics
import psutil
import logging
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass

# Configuration
NUM_ITERATIONS = 20
CACHE_SIZE_RATIO = 0.1

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
        return statistics.mean(self.memory_usage)
    
    @property
    def mean_miss_ratio(self) -> float:
        return statistics.mean(self.miss_ratios)

class CacheSimulationBenchmark:
    """Comprehensive benchmark for cache simulation performance."""
    
    def __init__(self, trace_path: str, num_iterations: int = NUM_ITERATIONS):
        self.trace_path = trace_path
        self.num_iterations = num_iterations
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
    
    def _benchmark_native_c(self) -> BenchmarkResult:
        """Benchmark native C binary execution."""
        self.logger.info("Benchmarking native C binary...")
        
        execution_times = []
        memory_usage = []
        miss_ratios = []
        
        # Try to find the cachesim binary
        possible_paths = [
            "./src/libCacheSim/build/bin/cachesim",
            "./build/bin/cachesim",
            "cachesim"
        ]
        
        cachesim_path = None
        for path in possible_paths:
            if os.path.exists(path) or subprocess.run(["which", path.split('/')[-1]], 
                                                     capture_output=True).returncode == 0:
                cachesim_path = path
                break
        
        if not cachesim_path:
            self.logger.warning("Native C binary not found, skipping native benchmark")
            return BenchmarkResult("Native C", [], [], [])
        
        for i in range(self.num_iterations):
            self.logger.info(f"Native C - Iteration {i+1}/{self.num_iterations}")
            
            memory_before = self._get_process_memory()
            
            try:
                start_time = perf_counter()
                result = subprocess.run([
                    cachesim_path,
                    self.trace_path,
                    "oracleGeneral",
                    "LRU",
                    "1",
                    "--ignore-obj-size", "1"
                ], check=True, capture_output=True, text=True)
                end_time = perf_counter()
                
                execution_time = end_time - start_time
                memory_after = self._get_process_memory()
                
                # Parse miss ratio from output (this may need adjustment based on actual output format)
                miss_ratio = 0.0  # Default value
                try:
                    # Look for miss ratio in output
                    for line in result.stdout.split('\n'):
                        if 'miss ratio' in line.lower():
                            miss_ratio = float(line.split()[-1])
                            break
                except:
                    pass
                
                execution_times.append(execution_time)
                memory_usage.append(memory_after - memory_before)
                miss_ratios.append(miss_ratio)
                
            except subprocess.CalledProcessError as e:
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
            
            # Setup reader and cache
            reader = lcs.TraceReader(
                trace=self.trace_path,
                trace_type=lcs.TraceType.ORACLE_GENERAL_TRACE,
                reader_init_params=lcs.ReaderInitParam(ignore_obj_size=True)
            )
            
            wss_size = reader.get_working_set_size()
            cache_size = int(wss_size[0] * CACHE_SIZE_RATIO)
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
            
            # Setup reader and cache
            reader = lcs.TraceReader(
                trace=self.trace_path,
                trace_type=lcs.TraceType.ORACLE_GENERAL_TRACE,
                reader_init_params=lcs.ReaderInitParam(ignore_obj_size=True)
            )
            
            wss_size = reader.get_working_set_size()
            cache_size = int(wss_size[0] * CACHE_SIZE_RATIO)
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
        
        return BenchmarkResult("Python loop", execution_times, memory_usage, miss_ratios)
    
    def run_benchmark(self) -> Dict[str, BenchmarkResult]:
        """Run all benchmarks and return results."""
        self.logger.info(f"Starting benchmark with {self.num_iterations} iterations")
        self.logger.info(f"Trace file: {self.trace_path}")
        
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
            if result.execution_times:  # Only check methods that ran
                miss_ratios.append((name, result.mean_miss_ratio))
        
        if len(miss_ratios) < 2:
            self.logger.warning("Not enough results to validate")
            return True
        
        # Check if all miss ratios are within 1% of each other
        base_ratio = miss_ratios[0][1]
        for name, ratio in miss_ratios[1:]:
            if abs(ratio - base_ratio) > 0.01:
                self.logger.warning(f"Miss ratio mismatch: {miss_ratios[0][0]}={base_ratio:.4f}, {name}={ratio:.4f}")
                return False
        
        self.logger.info("All miss ratios match within tolerance")
        return True
    
    def print_statistics(self):
        """Print detailed performance statistics."""
        print("\n" + "="*80)
        print("COMPREHENSIVE PERFORMANCE ANALYSIS")
        print("="*80)
        
        # Basic statistics
        for name, result in self.results.items():
            if not result.execution_times:
                continue
                
            print(f"\n{result.method_name} Performance:")
            print(f"  Execution Time:")
            print(f"    Mean: {result.mean_time:.4f} ± {result.std_time:.4f} seconds")
            print(f"    Range: [{result.min_time:.4f}, {result.max_time:.4f}] seconds")
            print(f"  Memory Usage:")
            print(f"    Mean: {result.mean_memory:.2f} MB")
            print(f"  Cache Performance:")
            print(f"    Mean Miss Ratio: {result.mean_miss_ratio:.4f}")
        
        # Comparative analysis
        if len([r for r in self.results.values() if r.execution_times]) >= 2:
            print(f"\n{'Comparative Analysis':=^60}")
            
            # Find fastest method
            fastest_method = min(
                [(name, result) for name, result in self.results.items() if result.execution_times],
                key=lambda x: x[1].mean_time
            )
            
            print(f"\nFastest Method: {fastest_method[1].method_name} ({fastest_method[1].mean_time:.4f}s)")
            
            # Compare all methods to fastest
            for name, result in self.results.items():
                if not result.execution_times or name == fastest_method[0]:
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
            
            # Estimate requests per second (this would need actual request count)
            print(f"{result.method_name}: ~{1/result.mean_time:.1f} traces/second")
    
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
        methods = [result.method_name for result in valid_results.values() if result.memory_usage]
        memory_means = [result.mean_memory for result in valid_results.values() if result.memory_usage]
        
        if methods and memory_means:
            bars = ax3.bar(methods, memory_means, color=['blue', 'red', 'green'][:len(methods)])
            ax3.set_ylabel('Memory Usage (MB)')
            ax3.set_title('Average Memory Usage')
            ax3.tick_params(axis='x', rotation=45)
            
            # Add value labels on bars
            for bar, value in zip(bars, memory_means):
                ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
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
                    f'({self.num_iterations} iterations, Trace: {os.path.basename(self.trace_path)})', 
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
                
                for i, (exec_time, mem_usage, miss_ratio) in enumerate(
                    zip(result.execution_times, result.memory_usage, result.miss_ratios)
                ):
                    writer.writerow({
                        'method': result.method_name,
                        'iteration': i + 1,
                        'execution_time': exec_time,
                        'memory_usage': mem_usage,
                        'miss_ratio': miss_ratio
                    })
        
        self.logger.info(f"Results exported to '{csv_path}'")


def main():
    global CACHE_SIZE_RATIO
    global NUM_ITERATIONS

    """Main function to run the benchmark."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive Cache Simulation Performance Benchmark")
    parser.add_argument("--trace_path", type=str, required=True, 
                       help="Path to the trace file")
    parser.add_argument("--iterations", type=int, default=NUM_ITERATIONS,
                       help=f"Number of iterations (default: {NUM_ITERATIONS})")
    parser.add_argument("--cache_size_ratio", type=float, default=CACHE_SIZE_RATIO,
                       help=f"Cache size as ratio of working set (default: {CACHE_SIZE_RATIO})")
    parser.add_argument("--output_dir", type=str, default=".",
                       help="Output directory for results (default: current directory)")
    parser.add_argument("--export_csv", action="store_true",
                       help="Export results to CSV file")
    parser.add_argument("--no_visualize", action="store_true",
                       help="Skip visualization generation")
    
    args = parser.parse_args()
    
    # Update global configuration
    CACHE_SIZE_RATIO = args.cache_size_ratio
    NUM_ITERATIONS = args.iterations

    try:
        # Create benchmark instance
        benchmark = CacheSimulationBenchmark(args.trace_path, args.iterations)
        
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