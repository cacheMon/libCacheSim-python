# Cache Simulation

## Basic Usage

The cache classes are the core of cache simulation. When an instance of a cache is creates (e.g., `LRU`, `S3FIFO`), we can configure the cache size and any cache-specific parameters such as promotion thresholds.

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

## Caches
The following cache classes all inherit from `CacheBase` and share a common interface, sharing the following arguments in all cache classes unless otherwise specified:

- `cache_size: int`
- `default_ttl: int` (optional)
- `hashpower: int` (optional)
- `consider_obj_metadata: bool` (optional)
- `admissioner: AdmissionerBase` (optional)

### LHD
**Lest Hit Density** evicts objects based on each objects expected hits-per-space-consumed (hit density).

- *No additional parameters beyond the common arguments*

### LRU
**Least Recently Used** evicts the object that has not been accessed for the longest time.

- *No additional parameters beyond the common arguments*

### FIFO
**First-In, First-Out** evicts objects in order regardless of frequency or recency.

- *No additional parameters beyond the common arguments*

### LFU
**Least Frequently Used** evicts the object with the lowest access frequency.

- *No additional parameters beyond the common arguments*

### Arc
**Adaptive Replacement Cache** a hybrid algorithm which balances recency and frequency.

- *No additional parameters beyond the common arguments*

### Clock
**Clock** is an low-complexity approximation of `LRU`.

- `int_freq: int` - Initial frequency counter value which is used for new objects (default: `0`)
- `n_bit_counter: int` - Number of bits used for the frequency counter (default: `1`)

### Random
**Random** evicts objects at random.

- *No additional parameters beyond the common arguments*

### S3FIFO
[TBD]

### Sieve
[TBD]

### LIRS
[TBD]

### TwoQ
[TBD]

### SLRU
[TBD]

### WTinyLFU
[TBD]

### LeCaR
[TBD]

### LFUDA
[TBD]

### ClockPro
[TBD]

### Cacheus
[TBD]

### Belady
[TBD]

### BeladySize
[TBD]

### LRUProb
[TBD]

### FlashProb
[TBD]

### GDSF
[TBD]

### Hyperbolic
[TBD]

### ThreeLCache
[TBD]

### GLCache
[TBD]

### LRB
[TBD]

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
