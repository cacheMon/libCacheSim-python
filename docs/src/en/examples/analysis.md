# Trace Analysis

Beyond simulating caches, libCacheSim can characterise a workload directly: request rate, object
size distribution, reuse distance, popularity, and more. This is done with `TraceAnalyzer`, a
thin wrapper over the analyzer in the underlying libCacheSim lib.

## Basic usage

`TraceAnalyzer` takes a reader, an output path prefix, and two optional configuration objects:

```python
import libcachesim as lcs

# Step 1: Open a trace (see the Trace Reader page for details)
URI = "s3://cache-datasets/cache_dataset_oracleGeneral/2007_msr/msr_hm_0.oracleGeneral.zst"
reader = lcs.TraceReader(
    trace=URI,
    trace_type=lcs.TraceType.ORACLE_GENERAL_TRACE,
    reader_init_params=lcs.ReaderInitParam(ignore_obj_size=False),
)

# Step 2: Run the analysis
analyzer = lcs.TraceAnalyzer(reader, "example_analysis")
analyzer.run()
```

The constructor arguments are:

- `reader: ReaderProtocol` — the trace to analyse.
- `output_path: str` — prefix for the generated result files.
- `analysis_option: AnalysisOption` (optional) — which analyses to run. Defaults to
  `AnalysisOption()`.
- `analysis_param: AnalysisParam` (optional) — tuning knobs for those analyses. Defaults to
  `AnalysisParam()`.

!!! important
    The analyzer runs entirely in the C++ backend, so it only accepts a C-backed reader — in
    practice, [`TraceReader`](reader.md). Passing a `SyntheticReader` raises
    `ReaderException: Only C/C++ reader is supported`. To analyse a synthetic workload, write it
    out first with `Util.convert_to_oracleGeneral` and reopen it with `TraceReader`.

## Selecting analyses

Each field of `AnalysisOption` toggles one analysis. Five are on by default:

| Option | Default | What it measures |
|---|---|---|
| `req_rate` | `True` | Request and object rate over time |
| `access_pattern` | `True` | Access pattern of individual objects over time |
| `size` | `True` | Object size distribution, by request and by object |
| `reuse` | `True` | Reuse time / reuse distance distribution |
| `popularity` | `True` | Object popularity distribution (Zipf fit) |
| `ttl` | `False` | TTL distribution (only meaningful for traces with TTLs) |
| `popularity_decay` | `False` | How object popularity decays with age |
| `lifetime` | `False` | Object lifetime distribution |
| `create_future_reuse_ccdf` | `False` | Experimental — CCDF of future reuse |
| `prob_at_age` | `False` | Experimental — access probability as a function of age |
| `size_change` | `False` | How object sizes change across accesses |

Analyses are independent, so disabling the ones you do not need makes the run considerably
faster on large traces:

```python
analysis_option = lcs.AnalysisOption(
    req_rate=True,       # Keep basic request rate analysis
    access_pattern=False,
    size=True,           # Keep size analysis
    reuse=False,
    popularity=False,
    ttl=False,
    popularity_decay=False,
    lifetime=False,
    create_future_reuse_ccdf=False,
    prob_at_age=False,
    size_change=False,
)

analyzer = lcs.TraceAnalyzer(reader, "example_analysis", analysis_option=analysis_option)
analyzer.run()
```

## Tuning the analyses

`AnalysisParam` controls how the enabled analyses behave:

| Parameter | Default | Meaning |
|---|---|---|
| `access_pattern_sample_ratio_inv` | `10` | Inverse sampling ratio for the access-pattern analysis — a value of `n` keeps roughly `1/n` of the data |
| `track_n_popular` | `10` | How many of the most popular objects to report request counts for |
| `track_n_hit` | `5` | How many "X-hit wonder" buckets to track, i.e. the number of objects accessed exactly once, twice, ... `track_n_hit` times |
| `time_window` | `60` | Width, in seconds, of the buckets used for time-series output |
| `warmup_time` | `0` | Seconds of trace to skip before collecting statistics |

```python
analysis_param = lcs.AnalysisParam(
    track_n_popular=4,
    track_n_hit=4,
    time_window=300,
)

analyzer = lcs.TraceAnalyzer(
    reader, "example_analysis",
    analysis_option=analysis_option,
    analysis_param=analysis_param,
)
analyzer.run()
```

!!! warning
    Two constraints are easy to trip over:

    - `warmup_time` must be an exact multiple of `time_window`; the analyzer errors out
      otherwise, because the popularity-decay computation depends on that relationship.
    - The popularity and reuse analyses need a reasonably large working set to produce
      meaningful output. On a tiny trace — a handful of distinct objects — set
      `track_n_popular` and `track_n_hit` no higher than the number of objects, or disable
      `popularity` and `reuse` altogether.

## Results

`run()` writes plain-text result files, all sharing the `output_path` prefix. Each enabled
analysis contributes at least one file — the size analysis writes `example_analysis.size`, and
some analyses additionally emit time-windowed variants such as
`example_analysis.sizeWindow_w60_req`.

```python
with open("example_analysis.size") as f:
    print(f.read())
```

A summary of the run — trace path, request and object counts, compulsory miss ratio, mean object
size, mean frequency, time span, and the X-hit-wonder and popularity histograms — is written to
a file named `stat` in the **current working directory**. Note that this path is fixed rather
than derived from `output_path`, and the analyzer *appends* to it, so results from successive
runs accumulate in the same file.

When you are finished, `cleanup()` releases the analyzer's internal state:

```python
analyzer.cleanup()
```

## Working set size

For the single most common statistic — how much data the trace touches — you do not need the
analyzer at all. `TraceReader` exposes it directly:

```python
n_obj, n_byte = reader.get_working_set_size()
print(f"{n_obj} unique objects, {n_byte} bytes")
```

This is also what a fractional `cache_size` is measured against; see
[Cache Simulation](simulation.md#cache-size-as-a-ratio).
