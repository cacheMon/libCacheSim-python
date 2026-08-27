# Quickstart

This guide will help you get started with libCacheSim.

## Prerequisites

- OS: Linux / macOS
- Python: 3.11 -- 3.14

## Installation

You can install libCacheSim using [pip](https://pypi.org/project/libcachesim/) directly.

It's recommended to use [uv](https://docs.astral.sh/uv/), a very fast Python environment manager, to create and manage Python environments. Please follow the [documentation](https://docs.astral.sh/uv/#getting-started) to install `uv`. After installing `uv`, you can create a new Python environment and install libCacheSim using the following commands:

```bash
uv venv --python 3.12 --seed
source .venv/bin/activate
uv pip install libcachesim
```

See [Installation](installation.md) for building from source, and for enabling the LRB,
ThreeLCache, and GLCache eviction algorithms, which are excluded from source builds by default.

## Cache Simulation

With libcachesim installed, you can start cache simulation for some eviction algorithm and cache traces. See the example script: 

??? code
    ```python
    import libcachesim as lcs

    # Step 1: Open a trace hosted on S3 (find more via https://github.com/cacheMon/cache_dataset)
    URI = "s3://cache-datasets/cache_dataset_oracleGeneral/2007_msr/msr_hm_0.oracleGeneral.zst"
    reader = lcs.TraceReader(
        trace = URI,
        trace_type = lcs.TraceType.ORACLE_GENERAL_TRACE,
        reader_init_params = lcs.ReaderInitParam(ignore_obj_size=False)
    )

    # Step 2: Initialize cache
    cache = lcs.S3FIFO(
        cache_size=1024*1024,
        # Cache specific parameters
        small_size_ratio=0.2,
        ghost_size_ratio=0.8,
        move_to_main_threshold=2,
    )

    # Step 3: Process entire trace efficiently (C++ backend)
    req_miss_ratio, byte_miss_ratio = cache.process_trace(reader)
    print(f"Request miss ratio: {req_miss_ratio:.4f}, Byte miss ratio: {byte_miss_ratio:.4f}")

    # Step 3.1: Process the first 1000 requests
    cache = lcs.S3FIFO(
        cache_size=1024 * 1024,
        # Cache specific parameters
        small_size_ratio=0.2,
        ghost_size_ratio=0.8,
        move_to_main_threshold=2,
    )
    req_miss_ratio, byte_miss_ratio = cache.process_trace(reader, start_req=0, max_req=1000)
    print(f"Request miss ratio: {req_miss_ratio:.4f}, Byte miss ratio: {byte_miss_ratio:.4f}")
    ```

The above example demonstrates the basic workflow of using `libcachesim` for cache simulation:

1. Open and efficiently process the trace file with `TraceReader`.
2. Initialize a cache object (here, `S3FIFO`) with a specified cache size (e.g., 1MB).
3. Run the simulation on the entire trace using `process_trace` to obtain object and byte miss ratios.
4. Optionally, process only a portion of the trace by specifying `start_req` and `max_req` for partial simulation.

This workflow applies to most cache algorithms and trace types, making it easy to get started and customize your experiments.

### Sizing the cache relative to the trace

Absolute byte counts are awkward when comparing traces of very different sizes. Passing
`cache_size` as a `float` in `(0, 1]` instead interprets it as a fraction of the trace's working
set, which requires handing the cache a `reader`:

```python
cache = lcs.S3FIFO(
    cache_size=0.1,  # 10% of the trace's working set size in bytes
    reader=reader,   # Required whenever cache_size is a float
)
```

An `int` is always an absolute byte count, so `1024` means 1 KiB while `1024.0` is out of range
and raises `ValueError`.

## Trace Analysis

Here is an example demonstrating how to use `TraceAnalyzer`.

??? code
    ```python
    import libcachesim as lcs

    # Step 1: Get one trace from S3 bucket
    URI = "s3://cache-datasets/cache_dataset_oracleGeneral/2007_msr/msr_hm_0.oracleGeneral.zst"
    reader = lcs.TraceReader(
        trace = URI,
        trace_type = lcs.TraceType.ORACLE_GENERAL_TRACE,
        reader_init_params = lcs.ReaderInitParam(ignore_obj_size=False)
    )

    analysis_option = lcs.AnalysisOption(
            req_rate=True,  # Keep basic request rate analysis
            access_pattern=False,  # Disable access pattern analysis
            size=True,  # Keep size analysis
            reuse=False,  # Disable reuse analysis for small datasets
            popularity=False,  # Disable popularity analysis for small datasets (< 200 objects)
            ttl=False,  # Disable TTL analysis
            popularity_decay=False,  # Disable popularity decay analysis
            lifetime=False,  # Disable lifetime analysis
            create_future_reuse_ccdf=False,  # Disable experimental features
            prob_at_age=False,  # Disable experimental features
            size_change=False,  # Disable size change analysis
        )

    analysis_param = lcs.AnalysisParam()

    analyzer = lcs.TraceAnalyzer(
        reader, "example_analysis", analysis_option=analysis_option, analysis_param=analysis_param
    )

    analyzer.run()
    ```

The above code demonstrates how to perform trace analysis using `libcachesim`. The workflow is as follows:

1. Open the trace file with `TraceReader`, specifying the trace type and any reader initialization parameters. The URI starting with `s3://`, will download a trace file from an S3 bucket.
2. Configure the analysis options with `AnalysisOption` to enable or disable specific analyses (such as request rate, size, etc.).
3. Optionally, set additional analysis parameters with `AnalysisParam`.
4. Create a `TraceAnalyzer` object with the reader, output directory, and the chosen options and parameters.
5. Run the analysis with `analyzer.run()`.

After running, you can access the analysis results, such as summary statistics (`stat`) or detailed results (e.g., `example_analysis.size`).

## Plugin System

libCacheSim also allows user to develop their own cache eviction algorithms and test them via the plugin system.

Here is an example of implement `LRU` via the plugin system.

??? code
    ```python
    from collections import OrderedDict
    from typing import Any

    from libcachesim import PluginCache, LRU, CommonCacheParams, Request, SyntheticReader

    def init_hook(_: CommonCacheParams) -> Any:
        return OrderedDict()

    def hit_hook(data: Any, req: Request) -> None:
        data.move_to_end(req.obj_id, last=True)

    def miss_hook(data: Any, req: Request) -> None:
        data.__setitem__(req.obj_id, req.obj_size)

    def eviction_hook(data: Any, _: Request) -> int:
        return data.popitem(last=False)[0]

    def remove_hook(data: Any, obj_id: int) -> None:
        data.pop(obj_id, None)

    def free_hook(data: Any) -> None:
        data.clear()


    plugin_lru_cache = PluginCache(
        cache_size=128,
        cache_init_hook=init_hook,
        cache_hit_hook=hit_hook,
        cache_miss_hook=miss_hook,
        cache_eviction_hook=eviction_hook,
        cache_remove_hook=remove_hook,
        cache_free_hook=free_hook,
        cache_name="Plugin_LRU",
    )

    reader = SyntheticReader(num_objects=1000, num_of_req=10000, obj_size=1)
    req_miss_ratio, byte_miss_ratio = plugin_lru_cache.process_trace(reader)
    ref_req_miss_ratio, ref_byte_miss_ratio = LRU(128).process_trace(reader)
    print(f"plugin req miss ratio {req_miss_ratio}, ref req miss ratio {ref_req_miss_ratio}")
    print(f"plugin byte miss ratio {byte_miss_ratio}, ref byte miss ratio {ref_byte_miss_ratio}")
    ```

By defining custom hook functions for cache initialization, hit, miss, eviction, removal, and cleanup, users can easily prototype and test their own cache eviction algorithms.

## Next steps

- [Trace Reader](../examples/reader.md) — opening local and S3 traces, slicing, and iteration
- [Cache Simulation](../examples/simulation.md) — every eviction algorithm and admission policy,
  with their parameters
- [Trace Analysis](../examples/analysis.md) — workload characterisation with `TraceAnalyzer`
- [Plugin System](../examples/plugins.md) — hook signatures for custom caches and admissioners
- [API Reference](../api.md) — the complete exported surface
