# Trace 分析

除了模拟缓存之外，libCacheSim 还能直接刻画负载特征：请求速率、对象大小分布、复用距离、流行度等。这些都通过 `TraceAnalyzer` 完成，它是底层 libCacheSim lib 中分析器的一层轻量封装。

## 基本用法

`TraceAnalyzer` 接受一个 reader、一个输出路径前缀，以及两个可选的配置对象：

```python
import libcachesim as lcs

# 第 1 步：打开一条 trace（详见 Trace Reader 页面）
URI = "s3://cache-datasets/cache_dataset_oracleGeneral/2007_msr/msr_hm_0.oracleGeneral.zst"
reader = lcs.TraceReader(
    trace=URI,
    trace_type=lcs.TraceType.ORACLE_GENERAL_TRACE,
    reader_init_params=lcs.ReaderInitParam(ignore_obj_size=False),
)

# 第 2 步：运行分析
analyzer = lcs.TraceAnalyzer(reader, "example_analysis")
analyzer.run()
```

构造参数如下：

- `reader: ReaderProtocol`——待分析的 trace。
- `output_path: str`——生成的结果文件的前缀。
- `analysis_option: AnalysisOption`（可选）——要运行哪些分析。默认为 `AnalysisOption()`。
- `analysis_param: AnalysisParam`（可选）——这些分析的调节参数。默认为 `AnalysisParam()`。

!!! important
    分析器完全运行在 C++ 后端，因此只接受由 C 实现的 reader——实际上就是 [`TraceReader`](reader.md)。传入 `SyntheticReader` 会抛出 `ReaderException: Only C/C++ reader is supported`。若要分析合成负载，请先用 `Util.convert_to_oracleGeneral` 将其写出，再用 `TraceReader` 重新打开。

## 选择分析项 {#selecting-analyses}

`AnalysisOption` 的每个字段对应一项分析，其中五项默认开启：

| 选项 | 默认值 | 含义 |
|---|---|---|
| `req_rate` | `True` | 请求速率与对象速率随时间的变化 |
| `access_pattern` | `True` | 单个对象随时间的访问模式 |
| `size` | `True` | 对象大小分布，分别按请求和按对象统计 |
| `reuse` | `True` | 复用时间 / 复用距离分布 |
| `popularity` | `True` | 对象流行度分布（Zipf 拟合） |
| `ttl` | `False` | TTL 分布（仅对带 TTL 的 trace 有意义） |
| `popularity_decay` | `False` | 对象流行度如何随时间衰减 |
| `lifetime` | `False` | 对象生命周期分布 |
| `create_future_reuse_ccdf` | `False` | 实验性——未来复用的 CCDF |
| `prob_at_age` | `False` | 实验性——访问概率随年龄的变化 |
| `size_change` | `False` | 对象大小在多次访问间的变化情况 |

各项分析彼此独立，因此在大 trace 上关掉不需要的分析可以显著加快运行速度：

```python
analysis_option = lcs.AnalysisOption(
    req_rate=True,       # 保留基本的请求速率分析
    access_pattern=False,
    size=True,           # 保留大小分析
    reuse=False,
    popularity=False,
    ttl=False,
    popularity_decay=False,
    lifetime=False,
    create_future_reuse_ccdf=False,
    prob_at_age=False,
    size_change=False,
)

analyzer = lcs.TraceAnalyzer(reader, "example_analysis", analysis_option=analysis_option)
analyzer.run()
```

## 调节分析行为

`AnalysisParam` 控制已启用分析的具体行为：

| 参数 | 默认值 | 含义 |
|---|---|---|
| `access_pattern_sample_ratio_inv` | `10` | 访问模式分析的采样率倒数——取值为 `n` 时大约保留 `1/n` 的数据 |
| `track_n_popular` | `10` | 统计并报告请求数的最流行对象个数 |
| `track_n_hit` | `5` | 追踪多少个 "X-hit wonder" 分桶，即恰好被访问 1 次、2 次……直到 `track_n_hit` 次的对象数量 |
| `time_window` | `60` | 时间序列输出所用分桶的宽度，单位为秒 |
| `warmup_time` | `0` | 开始统计前跳过的 trace 秒数 |

```python
analysis_param = lcs.AnalysisParam(
    track_n_popular=4,
    track_n_hit=4,
    time_window=300,
)

analyzer = lcs.TraceAnalyzer(
    reader, "example_analysis",
    analysis_option=analysis_option,
    analysis_param=analysis_param,
)
analyzer.run()
```

!!! warning
    有两个约束很容易踩坑：

    - `warmup_time` 必须是 `time_window` 的整数倍，否则分析器会直接报错，因为流行度衰减的计算依赖这一关系。
    - 流行度分析和复用分析需要足够大的工作集才能给出有意义的结果。在很小的 trace 上——只有寥寥几个不同对象时——请把 `track_n_popular` 和 `track_n_hit` 设为不超过对象总数，或者干脆关闭 `popularity` 和 `reuse`。

## 分析结果

`run()` 会写出纯文本的结果文件，它们都以 `output_path` 为前缀。每项启用的分析至少产出一个文件——大小分析写出 `example_analysis.size`，某些分析还会额外输出按时间窗口划分的变体，例如 `example_analysis.sizeWindow_w60_req`。

```python
with open("example_analysis.size") as f:
    print(f.read())
```

本次运行的汇总信息——trace 路径、请求数与对象数、强制缺失率、平均对象大小、平均访问频率、时间跨度，以及 X-hit wonder 和流行度直方图——会写入**当前工作目录**下名为 `stat` 的文件。注意该路径是固定的，并非由 `output_path` 推导而来，而且分析器是以*追加*方式写入，因此多次运行的结果会累积在同一个文件里。

用完之后，可以调用 `cleanup()` 释放分析器的内部状态：

```python
analyzer.cleanup()
```

## 工作集大小

对于最常用的那个统计量——trace 一共触及了多少数据——你根本不需要分析器。`TraceReader` 直接就能给出：

```python
n_obj, n_byte = reader.get_working_set_size()
print(f"{n_obj} unique objects, {n_byte} bytes")
```

按比例设置的 `cache_size` 也正是以此为基准计算的，参见[缓存模拟](simulation.md#cache-size-as-a-ratio)。
