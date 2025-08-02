# libCacheSim Python Binding

[![Build](https://github.com/cacheMon/libCacheSim-python/actions/workflows/build.yml/badge.svg)](https://github.com/cacheMon/libCacheSim-python/actions/workflows/build.yml)
[![Documentation](https://github.com/cacheMon/libCacheSim-python/actions/workflows/docs.yml/badge.svg)](docs.libcachesim.com/python)

Python bindings for [libCacheSim](https://github.com/1a1a11a/libCacheSim), a high-performance cache simulator and analysis library.

## Installation

Binary installers for the latest released version are available at the [Python Package Index (PyPI)](https://pypi.org/project/libcachesim).

```bash
pip install libcachesim
```

### Installation from sources

If there are no wheels suitable for your environment, consider building from source.

```bash
bash scripts/install.sh
```

Run all tests to ensure the package works.

```bash
python -m pytest tests/
```

## Quick Start

### Basic Usage

```python
import libcachesim as lcs

# Create a cache
cache = lcs.LRU(cache_size=1024*1024)  # 1MB cache

# Process requests
req = lcs.Request()
req.obj_id = 1
req.obj_size = 100

print(cache.get(req))  # False (first access)
print(cache.get(req))  # True (second access)
```

### Trace Processing

```python
import libcachesim as lcs

# Step 1: Get one trace from S3 bucket
URI = "cache_dataset_oracleGeneral/2007_msr/msr_hm_0.oracleGeneral.zst"
dl = lcs.DataLoader()
dl.load(URI)

# Step 2: Open trace and process efficiently
reader = lcs.TraceReader(dl.get_cache_path(URI))

# Step 3: Initialize cache
cache = lcs.S3FIFO(cache_size=1024*1024)

# Step 4: Process entire trace efficiently (C++ backend)
obj_miss_ratio, byte_miss_ratio = cache.process_trace(reader)
print(f"Object miss ratio: {obj_miss_ratio:.4f}, Byte miss ratio: {byte_miss_ratio:.4f}")
```

> [!NOTE]
> We DO NOT ignore the object size by defaults, you can add `reader_init_params = lcs.ReaderInitParam(ignore_obj_size=False)` to the initialization of `TraceReader` if needed.

## Custom Cache Policies

Implement custom cache replacement algorithms using pure Python functions - **no C/C++ compilation required**.

### Python Hook Cache Overview

The `PluginCache` allows you to define custom caching behavior through Python callback functions. You need to implement these callback functions:

| Function | Signature | Description |
|----------|-----------|-------------|
| `init_hook` | `((common_cache_params: CommonCacheParams)) -> Any` | Initialize your data structure |
| `hit_hook` | `(data: Any, request: Request) -> None` | Handle cache hits |
| `miss_hook` | `(data: Any, request: Request) -> None` | Handle cache misses |
| `eviction_hook` | `(data: Any, request: Request) -> int` | Return object ID to evict |
| `remove_hook` | `(data: Any, obj_id: int) -> None` | Clean up when object removed |
| `free_hook` | `(data: Any) -> None` | [Optional] Final cleanup |

<details>
<summary>An example for LRU</summary>

```python
from collections import OrderedDict
from libcachesim import PluginCache, CommonCacheParams, Request, SyntheticReader, LRU


class StandaloneLRU:
    def __init__(self):
        self.cache_data = OrderedDict()

    def cache_hit(self, obj_id):
        if obj_id in self.cache_data:
            obj_size = self.cache_data.pop(obj_id)
            self.cache_data[obj_id] = obj_size

    def cache_miss(self, obj_id, obj_size):
        self.cache_data[obj_id] = obj_size

    def cache_eviction(self):
        evicted_id, _ = self.cache_data.popitem(last=False)
        return evicted_id

    def cache_remove(self, obj_id):
        if obj_id in self.cache_data:
            del self.cache_data[obj_id]


def cache_init_hook(common_cache_params: CommonCacheParams):
    return StandaloneLRU()


def cache_hit_hook(cache, request: Request):
    cache.cache_hit(request.obj_id)


def cache_miss_hook(cache, request: Request):
    cache.cache_miss(request.obj_id, request.obj_size)


def cache_eviction_hook(cache, request: Request):
    return cache.cache_eviction()


def cache_remove_hook(cache, obj_id):
    cache.cache_remove(obj_id)


def cache_free_hook(cache):
    cache.cache_data.clear()


plugin_lru_cache = PluginCache(
    cache_size=1024,
    cache_init_hook=cache_init_hook,
    cache_hit_hook=cache_hit_hook,
    cache_miss_hook=cache_miss_hook,
    cache_eviction_hook=cache_eviction_hook,
    cache_remove_hook=cache_remove_hook,
    cache_free_hook=cache_free_hook,
    cache_name="CustomizedLRU",
)
```
</details>


Another simple implementation via hook functions for S3FIFO respectively is given in [examples](examples/plugin_cache/s3fifo.py).

### Getting Help

- Check [project documentation](docs.libcachesim.com/python) for detailed guides
- Open issues on [GitHub](https://github.com/cacheMon/libCacheSim-python/issues)
- Review [examples](/example) in the main repository

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