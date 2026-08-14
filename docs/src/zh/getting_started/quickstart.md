# 快速开始

本指南将帮助你快速上手 libCacheSim。

## 前置条件

- 操作系统：Linux / macOS
- Python：3.10 -- 3.13

## 安装

你可以直接使用 [pip](https://pypi.org/project/libcachesim/) 安装 libCacheSim。

我们推荐使用 [uv](https://docs.astral.sh/uv/)——一个非常快的 Python 环境管理器——来创建和管理 Python 环境。请参照其[官方文档](https://docs.astral.sh/uv/#getting-started)安装 `uv`。装好 `uv` 之后，用下面的命令创建新环境并安装 libCacheSim：

```bash
uv venv --python 3.12 --seed
source .venv/bin/activate
uv pip install libcachesim
```

如需从源码构建，或需要启用 LRB、ThreeLCache 和 GLCache 这三个在源码构建中默认被排除的淘汰算法，请参阅[安装指南](installation.md)。

## 缓存模拟

装好 libcachesim 之后，你就可以针对某个淘汰算法和缓存 trace 开始模拟了。示例脚本如下：

??? code
    ```python
    import libcachesim as lcs

    # 第 1 步：打开一条托管在 S3 上的 trace（更多 trace 见 https://github.com/cacheMon/cache_dataset）
    URI = "s3://cache-datasets/cache_dataset_oracleGeneral/2007_msr/msr_hm_0.oracleGeneral.zst"
    reader = lcs.TraceReader(
        trace = URI,
        trace_type = lcs.TraceType.ORACLE_GENERAL_TRACE,
        reader_init_params = lcs.ReaderInitParam(ignore_obj_size=False)
    )

    # 第 2 步：初始化缓存
    cache = lcs.S3FIFO(
        cache_size=1024*1024,
        # 算法特有参数
        small_size_ratio=0.2,
        ghost_size_ratio=0.8,
        move_to_main_threshold=2,
    )

    # 第 3 步：高效处理整条 trace（C++ 后端）
    req_miss_ratio, byte_miss_ratio = cache.process_trace(reader)
    print(f"Request miss ratio: {req_miss_ratio:.4f}, Byte miss ratio: {byte_miss_ratio:.4f}")

    # 第 3.1 步：只处理前 1000 条请求
    cache = lcs.S3FIFO(
        cache_size=1024 * 1024,
        # 算法特有参数
        small_size_ratio=0.2,
        ghost_size_ratio=0.8,
        move_to_main_threshold=2,
    )
    req_miss_ratio, byte_miss_ratio = cache.process_trace(reader, start_req=0, max_req=1000)
    print(f"Request miss ratio: {req_miss_ratio:.4f}, Byte miss ratio: {byte_miss_ratio:.4f}")
    ```

上面的例子展示了用 `libcachesim` 做缓存模拟的基本流程：

1. 用 `TraceReader` 打开并高效处理 trace 文件。
2. 初始化一个缓存对象（这里是 `S3FIFO`），并指定缓存大小（例如 1MB）。
3. 用 `process_trace` 在整条 trace 上运行模拟，得到对象缺失率和字节缺失率。
4. 也可以通过 `start_req` 和 `max_req` 只处理 trace 的一部分，做局部模拟。

这套流程适用于大多数缓存算法和 trace 类型，既容易上手，也便于自定义实验。

### 按 trace 比例设置缓存大小

在比较规模差异很大的多条 trace 时，使用绝对字节数会很不方便。此时可以把 `cache_size` 设为 `(0, 1]` 区间内的 `float`，它会被解释为 trace 工作集的一个比例，但这要求同时把 `reader` 传给缓存：

```python
cache = lcs.S3FIFO(
    cache_size=0.1,  # trace 工作集大小（字节）的 10%
    reader=reader,   # cache_size 为 float 时必须提供
)
```

`int` 始终表示绝对字节数，所以 `1024` 表示 1 KiB，而 `1024.0` 超出取值范围，会抛出 `ValueError`。

## Trace 分析

下面这个例子演示了 `TraceAnalyzer` 的用法。

??? code
    ```python
    import libcachesim as lcs

    # 第 1 步：从 S3 存储桶获取一条 trace
    URI = "s3://cache-datasets/cache_dataset_oracleGeneral/2007_msr/msr_hm_0.oracleGeneral.zst"
    reader = lcs.TraceReader(
        trace = URI,
        trace_type = lcs.TraceType.ORACLE_GENERAL_TRACE,
        reader_init_params = lcs.ReaderInitParam(ignore_obj_size=False)
    )

    analysis_option = lcs.AnalysisOption(
            req_rate=True,  # 保留基本的请求速率分析
            access_pattern=False,  # 关闭访问模式分析
            size=True,  # 保留大小分析
            reuse=False,  # 小数据集上关闭复用分析
            popularity=False,  # 小数据集（少于 200 个对象）上关闭流行度分析
            ttl=False,  # 关闭 TTL 分析
            popularity_decay=False,  # 关闭流行度衰减分析
            lifetime=False,  # 关闭生命周期分析
            create_future_reuse_ccdf=False,  # 关闭实验性功能
            prob_at_age=False,  # 关闭实验性功能
            size_change=False,  # 关闭大小变化分析
        )

    analysis_param = lcs.AnalysisParam()

    analyzer = lcs.TraceAnalyzer(
        reader, "example_analysis", analysis_option=analysis_option, analysis_param=analysis_param
    )

    analyzer.run()
    ```

上面的代码演示了如何用 `libcachesim` 进行 trace 分析，流程如下：

1. 用 `TraceReader` 打开 trace 文件，指定 trace 类型和所需的 reader 初始化参数。以 `s3://` 开头的 URI 会自动从 S3 存储桶下载 trace 文件。
2. 用 `AnalysisOption` 配置分析项，开启或关闭特定分析（如请求速率、对象大小等）。
3. 可选地用 `AnalysisParam` 设置额外的分析参数。
4. 用 reader、输出目录以及选定的选项和参数创建 `TraceAnalyzer` 对象。
5. 调用 `analyzer.run()` 运行分析。

运行结束后，你就可以查看分析结果，例如汇总统计（`stat`）或详细结果（如 `example_analysis.size`）。

## 插件系统

libCacheSim 还允许用户开发自己的缓存淘汰算法，并通过插件系统进行测试。

下面是通过插件系统实现 `LRU` 的例子。

??? code
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

    reader = SyntheticReader(num_objects=1000, num_of_req=10000, obj_size=1)
    req_miss_ratio, byte_miss_ratio = plugin_lru_cache.process_trace(reader)
    ref_req_miss_ratio, ref_byte_miss_ratio = LRU(128).process_trace(reader)
    print(f"plugin req miss ratio {req_miss_ratio}, ref req miss ratio {ref_req_miss_ratio}")
    print(f"plugin byte miss ratio {byte_miss_ratio}, ref byte miss ratio {ref_byte_miss_ratio}")
    ```

只要为缓存的初始化、命中、缺失、淘汰、移除和清理定义好自定义 hook 函数，用户就能轻松地对自己的缓存淘汰算法做原型验证和测试。

## 下一步

- [Trace Reader](../examples/reader.md)——打开本地和 S3 上的 trace、切片与遍历
- [缓存模拟](../examples/simulation.md)——所有淘汰算法与准入策略及其参数
- [Trace 分析](../examples/analysis.md)——用 `TraceAnalyzer` 刻画负载特征
- [插件系统](../examples/plugins.md)——自定义缓存与准入策略的 hook 签名
- [API 参考](../api.md)——完整的对外接口
