# libCacheSim Python Bindings

Welcome to libCacheSim Python bindings! This is a high-performance cache simulation library with Python interface.

## Overview

libCacheSim is a high-performance cache simulation framework that supports various cache algorithms and trace formats. The Python bindings provide an easy-to-use interface for cache simulation, analysis, and research.

## Key Features

- **High Performance**: Built on top of the optimized C++ libCacheSim library
- **Multiple Cache Algorithms**: Support for LRU, LFU, FIFO, ARC, Clock, S3FIFO, Sieve, and many more
- **Trace Support**: Read various trace formats (CSV, binary, OracleGeneral, etc.)
- **Synthetic Traces**: Generate synthetic workloads with Zipf and uniform distributions
- **Analysis Tools**: Built-in trace analysis and cache performance evaluation
- **Easy Integration**: Simple Python API for research and production use

## Quick Example

```python
import libcachesim as lcs

# Create a cache
cache = lcs.LRU(cache_size=1024*1024)  # 1MB cache

# Generate synthetic trace
reader = lcs.SyntheticReader(
    num_of_req=10000,
    obj_size=1024,
    dist="zipf",
    alpha=1.0
)

# Simulate cache behavior
hit_count = 0
for req in reader:
    if cache.get(req):
        hit_count += 1

hit_ratio = hit_count / reader.get_num_of_req()
print(f"Hit ratio: {hit_ratio:.4f}")
```

## Installation

```bash
pip install libcachesim
```

Or install from source:

```bash
git clone https://github.com/cacheMon/libCacheSim-python.git
cd libCacheSim-python
pip install -e .
```

## Getting Started

Check out our [Quick Start Guide](quickstart.md) to begin using libCacheSim Python bindings, or explore the [API Reference](api.md) for detailed documentation.

## Contributing

We welcome contributions! Please see our [GitHub repository](https://github.com/cacheMon/libCacheSim-python) for more information.

## License

This project is licensed under the GPL-3.0 License.
