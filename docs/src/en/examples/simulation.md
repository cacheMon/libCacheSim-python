# Cache Simulation

## Basic Usage

The cache classes are the core of cache simulation. When an instance of a cache is created (e.g., `LRU`, `S3FIFO`), we can configure the cache size and any cache-specific parameters such as promotion thresholds.

```py
import libcachesim as lcs

# Initialize cache
cache = lcs.S3FIFO(
    cache_size=1024 * 1024,
    # Cache specific parameters
    small_size_ratio=0.2,
    ghost_size_ratio=0.8,
    move_to_main_threshold=2,
)
```

Admission policies are optional - if none is provided, the cache will simply admit all objects according to the replacement policy. An admissioner (e.g., `BloomFilterAdmissioner`) can be placed infront of the cache by specifying the `admissioner` argument.

```py
import libcachesim as lcs

# Initialize admissioner
admissioner = lcs.BloomFilterAdmissioner()

# Step 2: Initialize cache
cache = lcs.S3FIFO(
    cache_size=1024 * 1024,
    # Cache specific parameters
    small_size_ratio=0.2,
    ghost_size_ratio=0.8,
    move_to_main_threshold=2,
    # Optionally provide admissioner
    admissioner=admissioner,
)
```

Then we can run cache simulations using real world workloads leveraging trace readers (see [Trace Reader](reader.md) for more on using `TraceReader`):

```py
# Process entire trace efficiently (C++ backend)
req_miss_ratio, byte_miss_ratio = cache.process_trace(reader)
print(f"Request miss ratio: {req_miss_ratio:.4f}, Byte miss ratio: {byte_miss_ratio:.4f}")
```

`process_trace` accepts two further arguments for restricting the replay to part of the trace:

```py
# Skip the first 10,000 requests, then process the next 1,000
req_miss_ratio, byte_miss_ratio = cache.process_trace(reader, start_req=10_000, max_req=1_000)
```

- `start_req: int` - Index of the first request to process (default: `0`)
- `max_req: int` - Maximum number of requests to process; `-1` means the whole trace (default: `-1`)

!!! note
    `process_trace` rewinds the reader before replaying, so you do not need to call `reset()`
    yourself. The *cache*, however, keeps its state across calls — create a fresh cache for each
    configuration you measure, rather than reusing one already warmed by a previous run.

## Cache size as a ratio

`cache_size` accepts either an absolute byte count (`int`) or a fraction of the trace's working
set (`float`). A float must be in `(0, 1]` and requires the `reader` argument, which is used to
call `reader.get_working_set_size()`:

```py
# 10% of the trace's total working set size in bytes
cache = lcs.S3FIFO(
    cache_size=0.1,
    reader=reader,  # Required when cache_size is a float
)
```

Passing a float without a `reader`, or a float outside `(0, 1]`, raises `ValueError`. Note that
`1024` and `1024.0` therefore mean very different things - the former is 1 KiB, the latter is
rejected.

## Working with individual requests

`process_trace` runs the whole replay in the C++ backend and is by far the fastest option. When
you need to observe or intervene per request, `CacheBase` exposes the underlying operations:

```py
for req in reader:
    hit = cache.get(req)  # Look up, and insert on miss (evicting as needed)
    if not hit:
        print(f"miss on {req.obj_id}, cache now holds {cache.get_n_obj()} objects")
```

| Method | Description |
|---|---|
| `get(req)` | Full request path: look up `req`, and on a miss insert it, evicting if necessary. Returns `True` on a hit. |
| `find(req, update_cache=True)` | Look up an object without inserting on miss. Set `update_cache=False` for a side-effect-free probe. |
| `can_insert(req)` | Whether the object would be admitted. |
| `insert(req)` | Insert an object without checking for space. |
| `need_eviction(req)` | Whether inserting `req` would require an eviction. |
| `to_evict(req)` | The object that would be evicted next, without evicting it. |
| `evict(req)` | Evict one object according to the policy. |
| `remove(obj_id)` | Remove a specific object. Returns `False` if it was not cached. |
| `get_occupied_byte()` | Bytes currently occupied. |
| `get_n_obj()` | Number of objects currently cached. |
| `set_cache_size(new_size)` | Resize the cache in place. |
| `print_cache()` | A string describing the current cache state, useful when debugging. |

The `cache_size` and `cache_name` properties are read-only.

## Caches

The following cache classes all inherit from `CacheBase` and share a common interface, sharing the following arguments in all cache classes unless otherwise specified:

- `cache_size: int | float` - Cache size in bytes, or a fraction of the working set (see [above](#cache-size-as-a-ratio))
- `default_ttl: int` (optional) - Default TTL in seconds (default: `25920000`, i.e. 300 days)
- `hashpower: int` (optional) - Log2 of the initial hash table size (default: `24`)
- `consider_obj_metadata: bool` (optional) - Whether per-object cache metadata counts against the cache size (default: `False`)
- `admissioner: AdmissionerBase` (optional) - Admission policy placed in front of the cache (default: `None`)
- `reader: ReaderProtocol` (optional) - Only needed when `cache_size` is a fraction (default: `None`)

### LHD
**Least Hit Density** evicts objects based on each objects expected hits-per-space-consumed (hit density).

- *No additional parameters beyond the common arguments*

### LRU
**Least Recently Used** evicts the object that has not been accessed for the longest time.

- *No additional parameters beyond the common arguments*

### LRUK
**LRU-K** evicts the object with the largest backward K-distance, that is the one whose K-th most recent access is oldest. Objects seen fewer than K times have an infinite backward K-distance and are evicted first in FIFO order, so a single access is not enough to earn a place in the cache.

- `k: int` - Number of recent accesses tracked per object (default: `2`)

### FIFO
**First-In, First-Out** evicts objects in order regardless of frequency or recency.

- *No additional parameters beyond the common arguments*

### LFU
**Least Frequently Used** evicts the object with the lowest access frequency.

- *No additional parameters beyond the common arguments*

### ARC
**Adaptive Replacement Cache** a hybrid algorithm which balances recency and frequency.

- *No additional parameters beyond the common arguments*

### Clock
**Clock** is an low-complexity approximation of `LRU`.

- `init_freq: int` - Initial frequency counter value which is used for new objects (default: `0`)
- `n_bit_counter: int` - Number of bits used for the frequency counter (default: `1`)

### Random
**Random** evicts objects at random.

- *No additional parameters beyond the common arguments*

### S3FIFO
**Simple, Scalable FIFO** splits the cache into a small FIFO queue for newly admitted objects and a main FIFO queue for objects that prove popular, backed by a ghost queue of recently evicted identifiers. One-hit wonders are demoted quickly out of the small queue instead of polluting the main one.

- `small_size_ratio: float` - Fraction of the cache given to the small queue (default: `0.1`)
- `ghost_size_ratio: float` - Size of the ghost queue as a fraction of the cache (default: `0.9`)
- `move_to_main_threshold: int` - Number of accesses in the small queue before an object is promoted to the main queue (default: `2`)

### Sieve
**Sieve** sweeps a hand over a FIFO queue and evicts the first object whose visited bit is unset, clearing the bits it passes. It achieves LRU-like miss ratios while keeping FIFO's simplicity, with no promotion on hit.

- *No additional parameters beyond the common arguments*

### LIRS
**Low Inter-reference Recency Set** ranks objects by the recency of their second-to-last access rather than their last, which lets it distinguish genuinely hot objects from ones touched a single time during a scan.

- *No additional parameters beyond the common arguments*

### TwoQ
**2Q** admits new objects to a FIFO queue (`Ain`), promoting them into an LRU main queue only if they are accessed again while their identifier is still in the ghost queue (`Aout`).

- `a_in_size_ratio: float` - Size of the `Ain` queue as a fraction of the cache (default: `0.25`)
- `a_out_size_ratio: float` - Size of the `Aout` ghost queue as a fraction of the cache (default: `0.5`)

### SLRU
**Segmented LRU** partitions the cache into ordered LRU segments; an object is promoted one segment on each hit and demoted towards eviction as newer objects arrive.

- *No additional parameters beyond the common arguments*

### MQ
**Multi-Queue** spreads objects over a hierarchy of LRU queues ordered by access frequency, promoting an object a queue at a time as it is reused and demoting it again if it goes untouched for its lifetime. Eviction always takes the tail of the lowest non-empty queue, and a FIFO ghost queue (`Qout`) remembers the frequency of evicted objects so a quick return restores an object to its former queue.

- `n_queue: int` - Number of queues in the hierarchy, must be in `[1, 64]` (default: `8`)
- `lifetime: int` - Requests an object may go unaccessed before it is demoted a queue (default: `10000`)
- `qout_size_ratio: float` - Size of the `Qout` ghost queue as a multiple of the cache size, must be in `(0, 64]` (default: `4.0`)

### WTinyLFU
**Window TinyLFU** places a small LRU window in front of a larger main cache, and uses a frequency sketch to decide whether an object leaving the window deserves to displace the main cache's eviction candidate.

- `main_cache: str` - Eviction algorithm used for the main cache (default: `"SLRU"`)
- `window_size: float` - Size of the LRU window as a fraction of the **total** cache size, must be in `[0, 1)`; the main cache receives the remainder (default: `0.01`)

### LeCaR
**Learning Cache Replacement** maintains both an LRU and an LFU candidate and picks between them using weights updated by regret minimisation, so it adapts as the workload shifts between recency- and frequency-friendly.

- `update_weight: bool` - Whether to keep learning the weights during the replay (default: `True`)
- `lru_weight: float` - Initial probability of choosing the LRU candidate; the LFU weight is `1 - lru_weight` (default: `0.5`)

### LFUDA
**LFU with Dynamic Aging** is `LFU` plus a global age value added to each object's priority on access, so objects that were popular long ago eventually age out instead of pinning the cache.

- *No additional parameters beyond the common arguments*

### ClockPro
**CLOCK-Pro** approximates `LIRS` using CLOCK hands, tracking hot and cold pages plus a test period for recently evicted cold pages.

- `init_ref: int` - Initial reference count given to newly admitted objects (default: `0`)
- `init_ratio_cold: float` - Initial fraction of the cache designated as cold (default: `0.5`)

### Clock2QPlus
**Clock-2Q+** is a 2Q variant that puts a small FIFO probationary queue in front of a Clock main cache. A ghost queue tracks recently evicted identifiers, and an adaptive correlation window tunes how long an object must survive the FIFO queue before it is considered worth promoting.

- `fifo_size_ratio: float` - Size of the FIFO queue as a fraction of the cache (default: `0.1`)
- `ghost_size_ratio: float` - Size of the ghost queue as a fraction of the cache (default: `0.9`)
- `move_to_main_threshold: int` - Number of hits before an object is promoted to the main cache (default: `1`)
- `corr_window_ratio: float` - Initial size of the correlation window as a fraction of the FIFO queue (default: `0.5`)

### Cacheus
**Cacheus** builds on `LeCaR`, adding lightweight adaptation of the learning rate and scan/churn detection so that it degrades gracefully on the workloads where `LeCaR` struggles.

- *No additional parameters beyond the common arguments*

### Belady
**Belady's MIN** is the optimal offline policy: it evicts the object whose next access is furthest in the future. It is not implementable online and exists as a lower bound on the achievable miss ratio.

- *No additional parameters beyond the common arguments*

!!! important
    `Belady` and `BeladySize` read `req.next_access_vtime`, which only oracle traces carry. Use a
    trace in `ORACLE_GENERAL_TRACE` format (as in the examples on this page); on an ordinary trace
    the future-access field is absent and the results are meaningless.

### BeladySize
**Size-aware Belady** extends `Belady` to variable object sizes, choosing among a sample of candidates by both next access time and size.

- `n_samples: int` - Number of objects sampled when picking a victim (default: `128`)

### LRUProb
**LRU with Probabilistic Promotion** behaves like `LRU`, except an object is only moved to the head of the queue with probability `prob`. Lower values make it behave more like `FIFO` at lower promotion cost.

- `prob: float` - Probability of promoting an object on a hit (default: `0.5`)

### FlashProb
**FlashProb** models a two-tier RAM-plus-flash cache, admitting objects evicted from RAM to the flash tier only probabilistically so as to limit write amplification on the flash device.

- `ram_size_ratio: float` - Size of the RAM tier as a fraction of the total cache (default: `0.05`)
- `disk_admit_prob: float` - Probability of admitting an object to the disk tier (default: `0.2`)
- `ram_cache: str` - Eviction algorithm used for the RAM tier (default: `"LRU"`)
- `disk_cache: str` - Eviction algorithm used for the disk tier (default: `"FIFO"`)

### Size
**Size** evicts the largest object first, maximising the number of objects retained. Useful as a baseline on workloads with highly variable object sizes.

- *No additional parameters beyond the common arguments*

### GDSF
**GreedyDual-Size with Frequency** ranks objects by frequency divided by size, offset by a global aging factor, favouring small and frequently accessed objects.

- *No additional parameters beyond the common arguments*

### Hyperbolic
**Hyperbolic** samples a few objects on each eviction and evicts the one with the lowest access count divided by time resident in the cache, approximating a priority ordering without maintaining a global structure.

- *No additional parameters beyond the common arguments*

### ThreeLCache
**3LCache** is a learned policy that predicts, for each object, how valuable it is to retain, and organises objects across three levels accordingly.

- `objective: str` - Metric the learned model optimises for (default: `"byte-miss-ratio"`)

!!! warning
    Requires a build with `-DENABLE_3L_CACHE=ON`. See [Installation](../getting_started/installation.md#optional-eviction-algorithms).
    Constructing it in a build without the flag raises `ImportError`.

### GLCache
**Group-Learned Cache** groups objects into segments, learns to predict each segment's future utility, and evicts by merging the least useful segments rather than making per-object decisions.

- `segment_size: int` - Number of objects per segment (default: `100`)
- `n_merge: int` - Number of segments merged in one eviction (default: `2`)
- `type: str` - Cache type, e.g. the learned variant or a baseline (default: `"learned"`)
- `rank_intvl: float` - How often segments are re-ranked, as a fraction of the cache (default: `0.02`)
- `merge_consecutive_segs: bool` - Whether merges are restricted to consecutive segments (default: `True`)
- `train_source_y: str` - Source of the training labels (default: `"online"`)
- `retrain_intvl: int` - Seconds between model retraining (default: `86400`)

!!! warning
    Requires a build with `-DENABLE_GLCACHE=ON`. See [Installation](../getting_started/installation.md#optional-eviction-algorithms).
    Constructing it in a build without the flag raises `ImportError`.

### LRB
**Learning Relaxed Belady** trains a model to approximate Belady's decision online, evicting objects predicted to have a distant next access.

- `objective: str` - Metric the learned model optimises for (default: `"byte-miss-ratio"`)

!!! warning
    Requires a build with `-DENABLE_LRB=ON`. See [Installation](../getting_started/installation.md#optional-eviction-algorithms).
    Constructing it in a build without the flag raises `ImportError`.

### PluginCache
**PluginCache** lets you implement an eviction policy in pure Python via hook functions, with no
compilation. It is documented separately in [Plugin System](plugins.md).

## Admission Policies

### BloomFilterAdmissioner
Uses a Bloom filter to decide admissions based on how many times an object has been seen.

- *No parameters*

### ProbAdmissioner
Admits objects with a fixed probability.

- `prob: float` (optional) - Probability of admitting an object (default: `0.5`)

### SizeAdmissioner
Admits objects only if they are below a specified size threshold.

- `size_threshold: int` (optional) - Maximum allowed object size (in bytes) for admission (default: `9_223_372_036_854_775_807`, or `INT64_MAX`)

### SizeProbabilisticAdmissioner
Admits objects with a probability that decreases with object size, favoring smaller objects over large.

- `exponent: float` (optional) - Exponent controlling how aggressively larger objects are filtered out (default: `1e-6`)

### AdaptSizeAdmissioner
Implements **AdaptSize**, a feedback-driven policy that periodically adjusts its size threshold.

- `max_iteration: int` (optional) - Maximum number of iterators for parameter tuning (default: `15`)
- `reconf_interval: int` (optional) - Interval (with respect to request count) at which the threshold is re-evaluated (default: `30_000`)

### PluginAdmissioner
Lets you implement an admission policy in Python via hook functions. See
[Plugin System](plugins.md#pluginadmissioner).

## Comparing algorithms

Because every cache exposes the same interface, sweeping over algorithms is straightforward.
`process_trace` rewinds the reader before it starts, so the same reader can be handed to each
run without an explicit `reset()`:

```py
import libcachesim as lcs

URI = "s3://cache-datasets/cache_dataset_oracleGeneral/2007_msr/msr_hm_0.oracleGeneral.zst"
reader = lcs.TraceReader(trace=URI, trace_type=lcs.TraceType.ORACLE_GENERAL_TRACE)

CACHE_SIZE = 1024 * 1024
for cls in (lcs.LRU, lcs.FIFO, lcs.ARC, lcs.S3FIFO, lcs.Sieve):
    cache = cls(cache_size=CACHE_SIZE)
    req_miss_ratio, byte_miss_ratio = cache.process_trace(reader)
    print(f"{cache.cache_name:>10}: req {req_miss_ratio:.4f}  byte {byte_miss_ratio:.4f}")
```
