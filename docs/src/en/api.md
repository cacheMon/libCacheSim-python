# API Reference

This page documents everything exported from the `libcachesim` package. For task-oriented
guides, see [Cache Simulation](examples/simulation.md), [Trace Reader](examples/reader.md),
[Trace Analysis](examples/analysis.md), and [Plugin System](examples/plugins.md).

```python
import libcachesim as lcs
```

## Requests and objects

### `Request`

A single access in a trace. Readers fill and return `Request` objects; caches consume them.

```python
Request(
    obj_size: int = 1,
    op: ReqOp = ReqOp.OP_NOP,
    valid: bool = True,
    obj_id: int = 0,
    clock_time: int = 0,
    hv: int = 0,
    next_access_vtime: int = -2,
    ttl: int = 0,
)
```

| Attribute | Type | Description |
|---|---|---|
| `obj_id` | `int` | Object identifier |
| `obj_size` | `int` | Object size in bytes |
| `clock_time` | `int` | Wall-clock timestamp of the request |
| `next_access_vtime` | `int` | Logical time of this object's next access; only present in oracle traces, and required by `Belady` / `BeladySize` |
| `op` | `ReqOp` | Operation type |
| `ttl` | `int` | Time-to-live in seconds |
| `hv` | `int` | Hash value |
| `valid` | `bool` | `False` marks the end of a trace; iteration stops on it |

### `CacheObject`

Returned by `Cache.find`, `insert`, `evict`, and `to_evict`. Exposes read-only `obj_id` and
`obj_size`.

## Enumerations

### `ReqOp`

```
OP_NOP      OP_GET      OP_GETS     OP_SET      OP_ADD
OP_CAS      OP_REPLACE  OP_APPEND   OP_PREPEND  OP_DELETE
OP_INCR     OP_DECR     OP_READ     OP_WRITE    OP_UPDATE
OP_INVALID
```

### `TraceType`

```
CSV_TRACE               BIN_TRACE               PLAIN_TXT_TRACE
ORACLE_GENERAL_TRACE    LCS_TRACE               VSCSI_TRACE
TWR_TRACE               TWRNS_TRACE             ORACLE_SIM_TWR_TRACE
ORACLE_SYS_TWR_TRACE    ORACLE_SIM_TWRNS_TRACE  ORACLE_SYS_TWRNS_TRACE
VALPIN_TRACE            UNKNOWN_TRACE
```

`UNKNOWN_TRACE` is the default and asks `TraceReader` to infer the format from the file name.

### `SamplerType`

```
SPATIAL_SAMPLER   TEMPORAL_SAMPLER   SHARDS_SAMPLER   INVALID_SAMPLER
```

## Configuration objects

### `ReaderInitParam`

Controls how a trace file is parsed. Passed to `TraceReader` as `reader_init_params`.

```python
ReaderInitParam(
    binary_fmt_str: str = "",
    ignore_obj_size: bool = False,
    ignore_size_zero_req: bool = True,
    obj_id_is_num: bool = True,
    obj_id_is_num_set: bool = False,
    cap_at_n_req: int = -1,
    block_size: int = -1,
    has_header: bool = False,
    has_header_set: bool = False,
    delimiter: str = ",",
    trace_start_offset: int = 0,
    sampler: Optional[Sampler] = None,
)
```

| Attribute | Description |
|---|---|
| `ignore_obj_size` | Treat every object as size 1, so the byte miss ratio equals the request miss ratio |
| `ignore_size_zero_req` | Skip requests whose object size is zero |
| `obj_id_is_num` | Parse object IDs as integers rather than strings |
| `cap_at_n_req` | Stop after this many requests; `-1` for no cap |
| `block_size` | Block size for block-level traces; `-1` to disable |
| `has_header` | Whether a CSV trace has a header row |
| `delimiter` | Field separator for CSV traces |
| `trace_start_offset` | Byte offset at which to start reading |
| `binary_fmt_str` | Struct format string for `BIN_TRACE` |
| `sampler` | Optional `Sampler` applied while reading |

CSV field positions are set as attributes after construction, and are **1-indexed**:
`time_field`, `obj_id_field`, `obj_size_field`, `op_field`, `ttl_field`, `cnt_field`,
`tenant_field`, `next_access_vtime_field`, `n_feature_fields`.

### `CommonCacheParams`

The parameter bundle every cache is built from. Constructed for you by the cache classes; you
only encounter it directly as the argument to a `PluginCache` init hook.

| Attribute | Type |
|---|---|
| `cache_size` | `int` |
| `default_ttl` | `int` |
| `hashpower` | `int` |
| `consider_obj_metadata` | `bool` |

### `AnalysisOption` and `AnalysisParam`

Configuration for `TraceAnalyzer`. Fields and defaults are documented in
[Trace Analysis](examples/analysis.md#selecting-analyses).

## Caches

### `CacheBase`

Base class of every cache. See
[Working with individual requests](examples/simulation.md#working-with-individual-requests) for
the full method table.

```python
process_trace(reader: ReaderProtocol, start_req: int = 0, max_req: int = -1) -> tuple[float, float]
```

Replays the trace and returns `(request_miss_ratio, byte_miss_ratio)`. With a C-backed reader
the whole loop runs in C++ with the GIL released; with a Python reader it falls back to a
Python loop.

Other methods: `get`, `find`, `can_insert`, `insert`, `need_eviction`, `evict`, `remove`,
`to_evict`, `get_occupied_byte`, `get_n_obj`, `set_cache_size`, `print_cache`. Read-only
properties: `cache_size`, `cache_name`.

### Cache algorithms

All take the common arguments `cache_size`, `default_ttl=25920000`, `hashpower=24`,
`consider_obj_metadata=False`, `admissioner=None`, `reader=None`, plus the extras below. See
[Cache Simulation](examples/simulation.md#caches) for what each algorithm does.

| Class | Algorithm-specific parameters |
|---|---|
| `LHD` | — |
| `LRU` | — |
| `FIFO` | — |
| `LFU` | — |
| `ARC` | — |
| `Clock` | `init_freq=0`, `n_bit_counter=1` |
| `Random` | — |
| `S3FIFO` | `small_size_ratio=0.1`, `ghost_size_ratio=0.9`, `move_to_main_threshold=2` |
| `Sieve` | — |
| `LIRS` | — |
| `TwoQ` | `a_in_size_ratio=0.25`, `a_out_size_ratio=0.5` |
| `SLRU` | — |
| `WTinyLFU` | `main_cache="SLRU"`, `window_size=0.01` |
| `LeCaR` | `update_weight=True`, `lru_weight=0.5` |
| `LFUDA` | — |
| `ClockPro` | `init_ref=0`, `init_ratio_cold=0.5` |
| `Cacheus` | — |
| `Belady` | — |
| `BeladySize` | `n_samples=128` |
| `LRUProb` | `prob=0.5` |
| `FlashProb` | `ram_size_ratio=0.05`, `disk_admit_prob=0.2`, `ram_cache="LRU"`, `disk_cache="FIFO"` |
| `Size` | — |
| `GDSF` | — |
| `Hyperbolic` | — |
| `ThreeLCache` | `objective="byte-miss-ratio"` — requires `-DENABLE_3L_CACHE=ON` |
| `GLCache` | `segment_size=100`, `n_merge=2`, `type="learned"`, `rank_intvl=0.02`, `merge_consecutive_segs=True`, `train_source_y="online"`, `retrain_intvl=86400` — requires `-DENABLE_GLCACHE=ON` |
| `LRB` | `objective="byte-miss-ratio"` — requires `-DENABLE_LRB=ON` |

`cache_size` may be an `int` (bytes) or a `float` in `(0, 1]` (a fraction of the working set,
which requires `reader`). See
[Cache size as a ratio](examples/simulation.md#cache-size-as-a-ratio).

### `PluginCache`

```python
PluginCache(
    cache_size: int | float,
    cache_init_hook: Callable,
    cache_hit_hook: Callable,
    cache_miss_hook: Callable,
    cache_eviction_hook: Callable,
    cache_remove_hook: Callable,
    cache_free_hook: Optional[Callable] = None,
    cache_name: str = "PythonHookCache",
    default_ttl: int = 25920000,
    hashpower: int = 24,
    consider_obj_metadata: bool = False,
    admissioner: Optional[AdmissionerBase] = None,
    reader: Optional[ReaderProtocol] = None,
)
```

Hook signatures are documented in [Plugin System](examples/plugins.md#plugincache).
`set_hooks(...)` replaces the hooks on an existing instance.

## Admission policies

Every admissioner derives from `AdmissionerBase`, which exposes `admit(req)`, `update(req,
cache_size)`, `clone()`, and `free()`. Pass an instance as the `admissioner` argument of any
cache.

| Class | Parameters |
|---|---|
| `BloomFilterAdmissioner` | — |
| `ProbAdmissioner` | `prob: float = None` |
| `SizeAdmissioner` | `size_threshold: int = None` |
| `SizeProbabilisticAdmissioner` | `exponent: float = None` |
| `AdaptSizeAdmissioner` | `max_iteration: int = None`, `reconf_interval: int = None` |
| `PluginAdmissioner` | `admissioner_name` plus five hooks |

Leaving a parameter as `None` uses the C library's own default; those defaults are listed in
[Admission Policies](examples/simulation.md#admission-policies).

```python
PluginAdmissioner(
    admissioner_name: str,
    admissioner_init_hook: Callable,
    admissioner_admit_hook: Callable,
    admissioner_clone_hook: Callable,
    admissioner_update_hook: Callable,
    admissioner_free_hook: Callable,
)
```

## Readers

### `ReaderProtocol`

A `runtime_checkable` protocol describing what any reader must provide, so custom readers can be
used wherever `TraceReader` is accepted:

```python
get_num_of_req() -> int
read_one_req() -> Request
skip_n_req(n: int) -> int
reset() -> None
close() -> None
clone() -> ReaderProtocol
get_working_set_size() -> tuple[int, int]
__iter__() / __next__() / __len__()
```

### `TraceReader`

```python
TraceReader(
    trace: str | Reader,
    trace_type: TraceType = TraceType.UNKNOWN_TRACE,
    reader_init_params: Optional[ReaderInitParam] = None,
)
```

`trace` is a local path or an `s3://bucket/key` URI; S3 objects are downloaded and cached
locally on first use. See [Trace Reader](examples/reader.md).

- Iteration and `len()` work directly on the reader.
- Indexing and slicing are supported: `reader[0]`, `reader[:100]`, `reader[-100:]`. A slice
  returns an iterator over a cloned reader, leaving the original position untouched.
- Navigation: `read_one_req()`, `read_first_req(req)`, `read_last_req(req)`, `skip_n_req(n)`,
  `go_back_one_req()`, `read_one_req_above()`, `set_read_pos(pos)`, `reset()`, `close()`,
  `clone()`.
- `get_working_set_size()` returns `(n_object, n_byte)`.
- Read-only properties include `n_read_req`, `n_total_req`, `n_req_left`, `trace_path`,
  `file_size`, `trace_type`, `trace_format`, `is_zstd_file`, `cloned`, `sampler`,
  `read_direction`, `lcs_ver`, `init_params`. `ignore_obj_size`, `ignore_size_zero_req`, and
  `block_size` are writable.

`read_one_req()` raises `RuntimeError` at end of trace, whereas iteration stops cleanly.

### `SyntheticReader`

Generates requests in memory — no trace file needed.

```python
SyntheticReader(
    num_of_req: int,
    obj_size: int = 4000,
    time_span: int = 604800,
    start_obj_id: int = 0,
    seed: Optional[int] = None,
    alpha: float = 1.0,
    dist: str = "zipf",
    num_objects: Optional[int] = None,
)
```

`dist` is `"zipf"` or `"uniform"`; `alpha` only applies to Zipf. `num_objects` defaults to
`num_of_req`. Invalid arguments raise `ValueError`.

!!! note
    `SyntheticReader` is a pure-Python reader (`c_reader = False`). `process_trace` still works,
    but falls back to a Python loop, and `TraceAnalyzer` rejects it outright.

### Trace generators

```python
create_zipf_requests(num_objects, num_requests, alpha=1.0, obj_size=4000,
                     time_span=604800, start_obj_id=0, seed=None) -> Iterator[Request]

create_uniform_requests(num_objects, num_requests, obj_size=4000,
                        time_span=604800, start_obj_id=0, seed=None) -> Iterator[Request]
```

Both return an **iterator**, not a list; wrap in `list(...)` if you need to replay them twice.

## `TraceAnalyzer`

```python
TraceAnalyzer(
    reader: ReaderProtocol,
    output_path: str,
    analysis_param: Optional[AnalysisParam] = None,
    analysis_option: Optional[AnalysisOption] = None,
)
```

Methods: `run()`, `cleanup()`. Requires a C-backed reader; anything else raises
`ReaderException`. See [Trace Analysis](examples/analysis.md).

## `Util`

Static helpers for trace conversion and simulation.

```python
Util.convert_to_oracleGeneral(reader, ofilepath, output_txt=False, remove_size_change=False)
Util.convert_to_lcs(reader, ofilepath, output_txt=False, remove_size_change=False, lcs_ver=1)
Util.process_trace(cache, reader, start_req=0, max_req=-1) -> tuple[float, float]
```

- `convert_to_oracleGeneral` rewrites a trace into the oracleGeneral format, computing the
  next-access field needed by `Belady`.
- `convert_to_lcs` writes the LCS format; `lcs_ver` selects the version (1–8).
- `Util.process_trace` is equivalent to `cache.process_trace(...)` but requires a C-backed
  reader, raising `ValueError` otherwise.

## Metadata

`libcachesim.__version__` is the installed package version; `libcachesim.__doc__` is the
extension module's docstring.

## Exceptions

The bindings use standard Python exceptions:

| Exception | Raised when |
|---|---|
| `ValueError` | Invalid arguments — a malformed S3 URI, a `cache_size` float outside `(0, 1]` or without a `reader`, an unsupported `dist`, or a non-C reader passed to `Util.process_trace` |
| `TypeError` | `reader_init_params` is not a `ReaderInitParam`; a reader is indexed with something other than an `int` or `slice` |
| `IndexError` | Reader index out of range, or end of trace reached while seeking |
| `RuntimeError` | `read_one_req()` called past the end of a trace |
| `ImportError` | Constructing `LRB`, `ThreeLCache`, or `GLCache` in a build compiled without the corresponding flag |
| `ReaderException` | A non-C reader was passed to `TraceAnalyzer` |

`ReaderException` is not re-exported at package level; import it from
`libcachesim.trace_analyzer` if you need to catch it by type.
