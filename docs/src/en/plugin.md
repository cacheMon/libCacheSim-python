# Plugin System

We enable user add any customized cache via libCacheSim's plugin system.

With user-defined sive python hook functions, 

```c++
  py::function cache_init_hook;
  py::function cache_hit_hook;
  py::function cache_miss_hook;
  py::function cache_eviction_hook;
  py::function cache_remove_hook;
  py::function cache_free_hook;
```

We can simulate and determine the cache eviction behavior from the python side.

Here is the signature requirement for these hook functions.

```python
def cache_init_hook(ccparams: CommonCacheParams) -> CustomizedCacheData: ...
def cache_hit_hook(data: CustomizedCacheData, req: Request) -> None: ...
def cache_miss_hook(data: CustomizedCacheData, req: Request) -> None: ...
def cache_eviction_hook(data: CustomizedCacheData, req: Request) -> int | str: ...
def cache_remove_hook(data: CustomizedCacheData, obj_id: int | str) ->: ...
def cache_free_hook(data: CustomizedCacheData) ->: ...
```
