# 插件系统

## PluginCache

我们允许用户通过 libCacheSim 的插件系统添加任意自定义缓存。

借助用户自定义的 Python hook 函数，

```c++
  py::function cache_init_hook;
  py::function cache_hit_hook;
  py::function cache_miss_hook;
  py::function cache_eviction_hook;
  py::function cache_remove_hook;
  py::function cache_free_hook;
```

我们可以完全从 Python 一侧模拟并决定缓存的淘汰行为。

这些 hook 函数的签名要求如下。
```python
def cache_init_hook(ccparams: CommonCacheParams) -> CustomizedCacheData: ...
def cache_hit_hook(data: CustomizedCacheData, req: Request) -> None: ...
def cache_miss_hook(data: CustomizedCacheData, req: Request) -> None: ...
def cache_eviction_hook(data: CustomizedCacheData, req: Request) -> int | str: ...
def cache_remove_hook(data: CustomizedCacheData, obj_id: int | str) ->: ...
def cache_free_hook(data: CustomizedCacheData) ->: ...
```

- **注意：** `CustomizedCacheData` 并不是本库提供的类型。它只是表示用户自行决定从 `cache_init_hook` 返回、并作为 `data` 传给其他 hook 函数的那个对象。

## PluginAdmissioner

我们允许用户通过 libCacheSim 的插件系统定义自己的准入策略，并将其与已有的缓存实现（如 `LRU`、`S3FIFO`）配合使用。

借助用户自定义的 Python hook 函数：

```c++
  py::function admissioner_init_hook;
  py::function admissioner_admit_hook;
  py::function admissioner_update_hook;
  py::function admissioner_clone_hook;
  py::function admissioner_free_hook;
```

我们可以在 Python 中方便地完全掌控哪些对象被准入底层缓存。

这些 hook 函数的签名要求如下。
```python
def admissioner_init_hook() -> CustomizedAdmissionerData: ...
def admissioner_admit_hook(data: CustomizedAdmissionerData, req: Request) -> bool: ...
def admissioner_update_hook(data: CustomizedAdmissionerData, req: Request, cache_size: int) -> None: ...
def admissioner_clone_hook(data: CustomizedAdmissionerData) -> AdmissionerBase: ...
def admissioner_free_hook(data: CustomizedAdmissionerData) -> None: ...
```

- **注意：** `CustomizedAdmissionerData` 并不是本库提供的类型。它只是表示用户自行决定从 `admissioner_init_hook` 返回、并作为 `data` 传给其他 hook 函数的那个对象。
