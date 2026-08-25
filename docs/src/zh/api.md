# API 参考

本页记录 `libcachesim` 包对外导出的全部内容。若需面向任务的教程，请参阅[缓存模拟](examples/simulation.md)、[Trace Reader](examples/reader.md)、[Trace 分析](examples/analysis.md)和[插件系统](examples/plugins.md)。

```python
import libcachesim as lcs
```

## 请求与对象

### `Request`

trace 中的一次访问。reader 负责填充并返回 `Request` 对象，缓存则消费它们。

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

| 属性 | 类型 | 说明 |
|---|---|---|
| `obj_id` | `int` | 对象标识 |
| `obj_size` | `int` | 对象大小（字节） |
| `clock_time` | `int` | 该请求的墙钟时间戳 |
| `next_access_vtime` | `int` | 该对象下一次访问的逻辑时间；仅 oracle trace 中存在，`Belady` / `BeladySize` 需要它 |
| `op` | `ReqOp` | 操作类型 |
| `ttl` | `int` | 存活时间（秒） |
| `hv` | `int` | 哈希值 |
| `valid` | `bool` | `False` 表示 trace 结束，遍历会随之停止 |

### `CacheObject`

由 `Cache.find`、`insert` 和 `to_evict` 返回，暴露只读的 `obj_id` 和 `obj_size`。注意 `evict` 返回的是 `None`——它转发到缓存的 `void` 淘汰回调；若需要在对象被移除前查看淘汰候选，请使用 `to_evict`。

## 枚举类型

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

`UNKNOWN_TRACE` 是默认值，它要求 `TraceReader` 根据文件名推断格式。

### `SamplerType`

```
SPATIAL_SAMPLER   TEMPORAL_SAMPLER   SHARDS_SAMPLER   INVALID_SAMPLER
```

## 配置对象

### `ReaderInitParam`

控制 trace 文件的解析方式，通过 `reader_init_params` 传给 `TraceReader`。

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

| 属性 | 说明 |
|---|---|
| `ignore_obj_size` | 把每个对象都当作大小为 1，于是字节缺失率等于请求缺失率 |
| `ignore_size_zero_req` | 跳过对象大小为零的请求 |
| `obj_id_is_num` | 把对象 ID 解析为整数而非字符串 |
| `cap_at_n_req` | 读到该请求数后停止；`-1` 表示不限制 |
| `block_size` | 块级 trace 的块大小；`-1` 表示禁用 |
| `has_header` | CSV trace 是否带表头行 |
| `delimiter` | CSV trace 的字段分隔符 |
| `trace_start_offset` | 开始读取的字节偏移 |
| `binary_fmt_str` | `BIN_TRACE` 的 struct 格式串 |
| `sampler` | 读取时应用的可选 `Sampler` |

CSV 的字段位置在构造之后以属性方式设置，且**从 1 开始计数**：`time_field`、`obj_id_field`、`obj_size_field`、`op_field`、`ttl_field`、`cnt_field`、`tenant_field`、`next_access_vtime_field`、`n_feature_fields`。

### `CommonCacheParams`

每个缓存都由这组参数构建而成。缓存类会替你构造它；你唯一会直接接触它的场合，是把它作为参数传给 `PluginCache` 的 init hook。

| 属性 | 类型 |
|---|---|
| `cache_size` | `int` |
| `default_ttl` | `int` |
| `hashpower` | `int` |
| `consider_obj_metadata` | `bool` |

### `AnalysisOption` 与 `AnalysisParam`

`TraceAnalyzer` 的配置。各字段及其默认值见 [Trace 分析](examples/analysis.md#selecting-analyses)。

## 缓存

### `CacheBase`

所有缓存的基类。完整的方法列表见[逐请求操作](examples/simulation.md#working-with-individual-requests)。

```python
process_trace(reader: ReaderProtocol, start_req: int = 0, max_req: int = -1) -> tuple[float, float]
```

回放 trace 并返回 `(request_miss_ratio, byte_miss_ratio)`。使用 C 实现的 reader 时，整个循环在 C++ 中运行并释放 GIL；使用 Python reader 时，则回退为 Python 循环。

其他方法：`get`、`find`、`can_insert`、`insert`、`need_eviction`、`evict`、`remove`、`to_evict`、`get_occupied_byte`、`get_n_obj`、`set_cache_size`、`print_cache`。只读属性：`cache_size`、`cache_name`。

### 缓存算法

所有算法都接受公共参数 `cache_size`、`default_ttl=25920000`、`hashpower=24`、`consider_obj_metadata=False`、`admissioner=None`、`reader=None`，以及下表中的额外参数。各算法的原理见[缓存模拟](examples/simulation.md#caches)。

| 类 | 算法特有参数 |
|---|---|
| `LHD` | — |
| `LRU` | — |
| `FIFO` | — |
| `LFU` | — |
| `ARC` | — |
| `Clock` | `init_freq=0`、`n_bit_counter=1` |
| `Random` | — |
| `S3FIFO` | `small_size_ratio=0.1`、`ghost_size_ratio=0.9`、`move_to_main_threshold=2` |
| `Sieve` | — |
| `LIRS` | — |
| `TwoQ` | `a_in_size_ratio=0.25`、`a_out_size_ratio=0.5` |
| `SLRU` | — |
| `WTinyLFU` | `main_cache="SLRU"`、`window_size=0.01` |
| `LeCaR` | `update_weight=True`、`lru_weight=0.5` |
| `LFUDA` | — |
| `ClockPro` | `init_ref=0`、`init_ratio_cold=0.5` |
| `Cacheus` | — |
| `Belady` | — |
| `BeladySize` | `n_samples=128` |
| `LRUProb` | `prob=0.5` |
| `FlashProb` | `ram_size_ratio=0.05`、`disk_admit_prob=0.2`、`ram_cache="LRU"`、`disk_cache="FIFO"` |
| `Size` | — |
| `GDSF` | — |
| `Hyperbolic` | — |
| `ThreeLCache` | `objective="byte-miss-ratio"` —— 需要 `-DENABLE_3L_CACHE=ON` |
| `GLCache` | `segment_size=100`、`n_merge=2`、`type="learned"`、`rank_intvl=0.02`、`merge_consecutive_segs=True`、`train_source_y="online"`、`retrain_intvl=86400` —— 需要 `-DENABLE_GLCACHE=ON` |
| `LRB` | `objective="byte-miss-ratio"` —— 需要 `-DENABLE_LRB=ON` |

`cache_size` 可以是 `int`（字节），也可以是 `(0, 1]` 区间内的 `float`（工作集的比例，此时需要提供 `reader`）。参见[按比例设置缓存大小](examples/simulation.md#cache-size-as-a-ratio)。

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

各 hook 的签名见[插件系统](examples/plugins.md#plugincache)。hook 在构造时固定，如需更换请新建一个 `PluginCache`。

## 准入策略

所有准入器都派生自 `AdmissionerBase`，后者暴露 `admit(req)`、`update(req, cache_size)`、`clone()` 和 `free()`。把实例作为任意缓存的 `admissioner` 参数传入即可。

| 类 | 参数 |
|---|---|
| `BloomFilterAdmissioner` | — |
| `ProbAdmissioner` | `prob: float = None` |
| `SizeAdmissioner` | `size_threshold: int = None` |
| `SizeProbabilisticAdmissioner` | `exponent: float = None` |
| `AdaptSizeAdmissioner` | `max_iteration: int = None`、`reconf_interval: int = None` |
| `PluginAdmissioner` | `admissioner_name` 加五个 hook |

参数保持为 `None` 时会使用 C 库自身的默认值，这些默认值列在[准入策略](examples/simulation.md#admission-policies)中。

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

## Reader

### `ReaderProtocol`

一个 `runtime_checkable` 的协议，描述任何 reader 必须提供的接口，因此自定义 reader 可以用在所有接受 `TraceReader` 的地方：

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

`trace` 可以是本地路径，也可以是 `s3://bucket/key` 形式的 URI；S3 对象会在首次使用时下载并缓存到本地。参见 [Trace Reader](examples/reader.md)。

- 可以直接对 reader 进行遍历和 `len()`。
- 支持下标和切片：`reader[0]`、`reader[:100]`、`reader[-100:]`。切片返回的是一个基于克隆 reader 的迭代器，原 reader 的位置不受影响。
- 定位相关方法：`read_one_req()`、`read_first_req(req)`、`read_last_req(req)`、`skip_n_req(n)`、`go_back_one_req()`、`read_one_req_above()`、`set_read_pos(pos)`、`reset()`、`close()`、`clone()`。
- `get_working_set_size()` 返回 `(n_object, n_byte)`。
- 只读属性包括 `n_read_req`、`n_total_req`、`n_req_left`、`trace_path`、`file_size`、`trace_type`、`trace_format`、`is_zstd_file`、`cloned`、`sampler`、`read_direction`、`lcs_ver`、`init_params`。`ignore_obj_size`、`ignore_size_zero_req` 和 `block_size` 可写。

`read_one_req()` 在 trace 结束后调用会抛出 `RuntimeError`，而遍历则会正常结束。

### `SyntheticReader`

在内存中生成请求，无需 trace 文件。

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

`dist` 取 `"zipf"` 或 `"uniform"`；`alpha` 仅对 Zipf 生效。`num_objects` 默认等于 `num_of_req`。参数非法时抛出 `ValueError`。

!!! note
    `SyntheticReader` 是纯 Python 实现的 reader（`c_reader = False`）。`process_trace` 仍然可用，但会回退为 Python 循环，而 `TraceAnalyzer` 会直接拒绝它。

### Trace 生成器

```python
create_zipf_requests(num_objects, num_requests, alpha=1.0, obj_size=4000,
                     time_span=604800, start_obj_id=0, seed=None) -> Iterator[Request]

create_uniform_requests(num_objects, num_requests, obj_size=4000,
                        time_span=604800, start_obj_id=0, seed=None) -> Iterator[Request]
```

两者返回的都是**可重复迭代**的生成器对象而非列表：每次 `for` 循环都会重新开始一轮，且在固定 `seed` 下每轮产生的序列完全相同。因此无需用 `list(...)` 包一层来重复回放；对于大规模负载更不应这样做，否则会一次性把所有 `Request` materialize 到内存中。

## `TraceAnalyzer`

```python
TraceAnalyzer(
    reader: ReaderProtocol,
    output_path: str,
    analysis_param: Optional[AnalysisParam] = None,
    analysis_option: Optional[AnalysisOption] = None,
)
```

方法：`run()`、`cleanup()`。要求使用 C 实现的 reader，否则抛出 `ReaderException`。参见 [Trace 分析](examples/analysis.md)。

## `Util`

用于 trace 转换和模拟的静态辅助方法。

```python
Util.convert_to_oracleGeneral(reader, ofilepath, output_txt=False, remove_size_change=False)
Util.convert_to_lcs(reader, ofilepath, output_txt=False, remove_size_change=False, lcs_ver=1)
Util.process_trace(cache, reader, start_req=0, max_req=-1) -> tuple[float, float]
```

- `convert_to_oracleGeneral` 把 trace 改写为 oracleGeneral 格式，并计算 `Belady` 所需的下次访问字段。
- `convert_to_lcs` 写出 LCS 格式；`lcs_ver` 用于选择版本（1–8）。
- `Util.process_trace` 等价于 `cache.process_trace(...)`，但要求使用 C 实现的 reader，否则抛出 `ValueError`。

## 元信息

`libcachesim.__version__` 是已安装的包版本；`libcachesim.__doc__` 是扩展模块的 docstring。

## 异常

绑定层使用标准的 Python 异常：

| 异常 | 触发场景 |
|---|---|
| `ValueError` | 参数非法——S3 URI 格式错误、`cache_size` 为超出 `(0, 1]` 的 float 或缺少 `reader`、`dist` 取值不支持，或把非 C reader 传给了 `Util.process_trace` |
| `TypeError` | `reader_init_params` 不是 `ReaderInitParam`；用 `int` 或 `slice` 以外的类型给 reader 取下标 |
| `IndexError` | reader 下标越界，或定位过程中已到达 trace 末尾 |
| `RuntimeError` | trace 已结束后仍调用 `read_one_req()` |
| `ImportError` | 在未开启对应编译选项的构建中构造 `LRB`、`ThreeLCache` 或 `GLCache` |
| `ReaderException` | 把非 C reader 传给了 `TraceAnalyzer` |

`ReaderException` 未在包级别重新导出；如果需要按类型捕获它，请从 `libcachesim.trace_analyzer` 导入。
