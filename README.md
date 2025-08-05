# libCacheSim Python Binding

[![Build](https://github.com/cacheMon/libCacheSim-python/actions/workflows/build.yml/badge.svg)](https://github.com/cacheMon/libCacheSim-python/actions/workflows/build.yml)
[![Documentation](https://github.com/cacheMon/libCacheSim-python/actions/workflows/docs.yml/badge.svg)](docs.libcachesim.com/python)


libCacheSim is fast with the features from [underlying libCacheSim lib](https://github.com/1a1a11a/libCacheSim):

- **High performance** - over 20M requests/sec for a realistic trace replay
- **High memory efficiency** - predictable and small memory footprint
- **Parallelism out-of-the-box** - uses the many CPU cores to speed up trace analysis and cache simulations

libCacheSim is flexible and easy to use with:

- **Seamless integration** with [open-source cache dataset](https://github.com/cacheMon/cache_dataset) consisting of thousands traces hosted on S3
- **High-throughput simulation** with the [underlying libCacheSim lib](https://github.com/1a1a11a/libCacheSim)
- **Detailed cache requests** and other internal data control
- **Customized plugin cache development** without any compilation

## Installation

### Quick Install

Binary installers for the latest released version are available at the [Python Package Index (PyPI)](https://pypi.org/project/libcachesim).

```bash
pip install libcachesim
```

Visit our [documentation](https://cachemon.github.io/libCacheSim-python/getting_started/quickstart/) to learn more.

### Installation from sources

If there are no wheels suitable for your environment, consider building from source.

```bash
git clone https://github.com/cacheMon/libCacheSim-python.git
cd libCacheSim-python
bash scripts/install.sh
```

Run all tests to ensure the package works.

```bash
python -m pytest tests/
```

## Quick Start

### Cache Simulation

With libcachesim installed, you can start cache simulation for some eviction algorithm and cache traces:

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

## Plugin System

libCacheSim allows you to develop your own cache eviction algorithms and test them via the plugin system without any C/C++ compilation required.

### Plugin Cache Overview

The `PluginCache` allows you to define custom caching behavior through Python callback functions. You need to implement these callback functions:

| Function | Signature | Description |
|----------|-----------|-------------|
| `init_hook` | `(common_cache_params: CommonCacheParams) -> Any` | Initialize your data structure |
| `hit_hook` | `(data: Any, request: Request) -> None` | Handle cache hits |
| `miss_hook` | `(data: Any, request: Request) -> None` | Handle cache misses |
| `eviction_hook` | `(data: Any, request: Request) -> int` | Return object ID to evict |
| `remove_hook` | `(data: Any, obj_id: int) -> None` | Clean up when object removed |
| `free_hook` | `(data: Any) -> None` | [Optional] Final cleanup |

### Example: Implementing LRU via Plugin System

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

reader = SyntheticReader(
    num_objects=1000, num_of_req=10000, obj_size=1, alpha=1.0, dist="zipf"
)
req_miss_ratio, byte_miss_ratio = plugin_lru_cache.process_trace(reader)
```

By defining custom hook functions for cache initialization, hit, miss, eviction, removal, and cleanup, users can easily prototype and test their own cache eviction algorithms.

### Getting Help

- Check [project documentation](https://docs.libcachesim.com/python) for detailed guides
- Open issues on [GitHub](https://github.com/cacheMon/libCacheSim-python/issues/new/choose)
- Review [examples](/examples) in the main repository

---
## Reference
<details>
<summary> Please cite the following papers if you use libCacheSim. </summary>

```
@inproceedings{yang2020-workload,
    author = {Juncheng Yang and Yao Yue and K. V. Rashmi},
    title = {A large-scale analysis of hundreds of in-memory cache clusters at Twitter},
    booktitle = {14th USENIX Symposium on Operating Systems Design and Implementation (OSDI 20)},
    year = {2020},
    isbn = {978-1-939133-19-9},
    pages = {191--208},
    url = {https://www.usenix.org/conference/osdi20/presentation/yang},
    publisher = {USENIX Association},
}

@inproceedings{yang2023-s3fifo,
  title = {FIFO Queues Are All You Need for Cache Eviction},
  author = {Juncheng Yang and Yazhuo Zhang and Ziyue Qiu and Yao Yue and K.V. Rashmi},
  isbn = {9798400702297},
  publisher = {Association for Computing Machinery},
  booktitle = {Symposium on Operating Systems Principles (SOSP'23)},
  pages = {130–149},
  numpages = {20},
  year={2023}
}

@inproceedings{yang2023-qdlp,
  author = {Juncheng Yang and Ziyue Qiu and Yazhuo Zhang and Yao Yue and K.V. Rashmi},
  title = {FIFO Can Be Better than LRU: The Power of Lazy Promotion and Quick Demotion},
  year = {2023},
  isbn = {9798400701955},
  publisher = {Association for Computing Machinery},
  doi = {10.1145/3593856.3595887},
  booktitle = {Proceedings of the 19th Workshop on Hot Topics in Operating Systems (HotOS23)},
  pages = {70–79},
  numpages = {10},
}
```
If you used libCacheSim in your research, please cite the above papers.

</details>

---

## License
See [LICENSE](LICENSE) for details.

---
