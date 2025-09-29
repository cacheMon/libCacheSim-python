# Plugin System

## PluginCache

We enable users to add any customized cache via libCacheSim's plugin system.

With user-defined python hook functions,

```c++
  py::function cache_init_hook;
  py::function cache_hit_hook;
  py::function cache_miss_hook;
  py::function cache_eviction_hook;
  py::function cache_remove_hook;
  py::function cache_free_hook;
```

We can simulate and determine the cache eviction behavior from the python side.

Here are the signature requirements for these hook functions.
```python
def cache_init_hook(ccparams: CommonCacheParams) -> CustomizedCacheData: ...
def cache_hit_hook(data: CustomizedCacheData, req: Request) -> None: ...
def cache_miss_hook(data: CustomizedCacheData, req: Request) -> None: ...
def cache_eviction_hook(data: CustomizedCacheData, req: Request) -> int | str: ...
def cache_remove_hook(data: CustomizedCacheData, obj_id: int | str) ->: ...
def cache_free_hook(data: CustomizedCacheData) ->: ...
```

- **Note:** `CustomizedCacheData` is not a type provided by the library. It simply represents what ever object the user decides to return from `cache_init_hook` and pass to the other hook functions as `data`.

## PluginAdmissioner

We enable users to define their own admission policies via libCacheSim's plugin system, which can be used in conjunction with existing cache implementations (e.g., `LRU`, `S3FIFO`).

With user-defined python hook functions:

```c++
  py::function admissioner_init_hook;
  py::function admissioner_admit_hook;
  py::function admissioner_update_hook;
  py::function admissioner_clone_hook;
  py::function admissioner_free_hook;
```

We have complete control over which objects are admitted into the underlying cache conveniently from Python.

Here are the signature requirements for these hook functions.
```python
def admissioner_init_hook() -> CustomizedAdmissionerData: ...
def admissioner_admit_hook(data: CustomizedAdmissionerData, req: Request) -> bool: ...
def admissioner_update_hook(data: CustomizedAdmissionerData, req: Request, cache_size: int) -> None: ...
def admissioner_clone_hook(data: CustomizedAdmissionerData) -> AdmissionerBase: ...
def admissioner_free_hook(data: CustomizedAdmissionerData) -> None: ...
```

- **Note:** `CustomizedAdmissionerData` is not a type provided by the library. It simply represents what ever object the user decides to return from `admissioner_init_hook` and pass to the other hook functions as `data`.
