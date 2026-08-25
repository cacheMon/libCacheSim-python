# 缓存模拟

## 基本用法

缓存类是缓存模拟的核心。创建一个缓存实例（例如 `LRU`、`S3FIFO`）时，我们可以配置缓存大小以及该算法特有的参数，比如晋升阈值。

```py
import libcachesim as lcs

# 初始化缓存
cache = lcs.S3FIFO(
    cache_size=1024 * 1024,
    # 算法特有参数
    small_size_ratio=0.2,
    ghost_size_ratio=0.8,
    move_to_main_threshold=2,
)
```

准入策略是可选的——如果不提供，缓存会直接按替换策略接纳所有对象。通过 `admissioner` 参数，可以在缓存前面放置一个准入器（例如 `BloomFilterAdmissioner`）。

```py
import libcachesim as lcs

# 初始化准入器
admissioner = lcs.BloomFilterAdmissioner()

# 第 2 步：初始化缓存
cache = lcs.S3FIFO(
    cache_size=1024 * 1024,
    # 算法特有参数
    small_size_ratio=0.2,
    ghost_size_ratio=0.8,
    move_to_main_threshold=2,
    # 可选地提供准入器
    admissioner=admissioner,
)
```

然后就可以借助 trace reader 用真实世界的负载运行缓存模拟（关于 `TraceReader` 的更多用法见 [Trace Reader](reader.md)）：

```py
# 高效处理整条 trace（C++ 后端）
req_miss_ratio, byte_miss_ratio = cache.process_trace(reader)
print(f"Request miss ratio: {req_miss_ratio:.4f}, Byte miss ratio: {byte_miss_ratio:.4f}")
```

`process_trace` 还接受另外两个参数，用于把回放限制在 trace 的一部分上：

```py
# 跳过前 10000 条请求，然后处理接下来的 1000 条
req_miss_ratio, byte_miss_ratio = cache.process_trace(reader, start_req=10_000, max_req=1_000)
```

- `start_req: int` —— 第一条待处理请求的下标（默认：`0`）
- `max_req: int` —— 最多处理多少条请求；`-1` 表示整条 trace（默认：`-1`）

!!! note
    `process_trace` 会在回放前把 reader 倒回起点，所以你不需要自己调用 `reset()`。但*缓存*本身会跨多次调用保留状态——每测一种配置就新建一个缓存，而不要复用已经被上一轮预热过的缓存。

## 按比例设置缓存大小 {#cache-size-as-a-ratio}

`cache_size` 既接受绝对字节数（`int`），也接受 trace 工作集的一个比例（`float`）。float 必须落在 `(0, 1]` 区间内，并且需要提供 `reader` 参数，因为要用它来调用 `reader.get_working_set_size()`：

```py
# trace 总工作集大小（字节）的 10%
cache = lcs.S3FIFO(
    cache_size=0.1,
    reader=reader,  # cache_size 为 float 时必须提供
)
```

传入 float 却不给 `reader`，或者 float 超出 `(0, 1]`，都会抛出 `ValueError`。注意 `1024` 和 `1024.0` 因此含义截然不同——前者是 1 KiB，后者会被拒绝。

## 逐请求操作 {#working-with-individual-requests}

`process_trace` 把整个回放过程放在 C++ 后端执行，是速度最快的方式。当你需要逐条请求进行观察或干预时，`CacheBase` 也暴露了底层操作：

```py
for req in reader:
    hit = cache.get(req)  # 查找，缺失时插入（必要时触发淘汰）
    if not hit:
        print(f"miss on {req.obj_id}, cache now holds {cache.get_n_obj()} objects")
```

| 方法 | 说明 |
|---|---|
| `get(req)` | 完整的请求路径：查找 `req`，缺失时插入，必要时淘汰。命中返回 `True`。 |
| `find(req, update_cache=True)` | 查找对象，但缺失时不插入。设 `update_cache=False` 可做无副作用的探测。 |
| `can_insert(req)` | 该对象是否会被准入。 |
| `insert(req)` | 直接插入对象，不检查空间。 |
| `need_eviction(req)` | 插入 `req` 是否需要先淘汰。 |
| `to_evict(req)` | 返回下一个将被淘汰的对象，但并不真的淘汰它。 |
| `evict(req)` | 按策略淘汰一个对象。 |
| `remove(obj_id)` | 移除指定对象。若该对象不在缓存中则返回 `False`。 |
| `get_occupied_byte()` | 当前已占用的字节数。 |
| `get_n_obj()` | 当前缓存中的对象个数。 |
| `set_cache_size(new_size)` | 原地调整缓存大小。 |
| `print_cache()` | 返回描述当前缓存状态的字符串，调试时很有用。 |

`cache_size` 和 `cache_name` 属性是只读的。

## 缓存算法 {#caches}

下面这些缓存类都继承自 `CacheBase` 并共享同一套接口。除非另有说明，所有缓存类都接受以下公共参数：

- `cache_size: int | float` —— 缓存大小（字节），或工作集的一个比例（见[上文](#cache-size-as-a-ratio)）
- `default_ttl: int`（可选）—— 默认 TTL，单位为秒（默认：`25920000`，即 300 天）
- `hashpower: int`（可选）—— 初始哈希表大小的以 2 为底的对数（默认：`24`）
- `consider_obj_metadata: bool`（可选）—— 每个对象的缓存元数据是否计入缓存大小（默认：`False`）
- `admissioner: AdmissionerBase`（可选）—— 置于缓存之前的准入策略（默认：`None`）
- `reader: ReaderProtocol`（可选）—— 仅当 `cache_size` 为比例时才需要（默认：`None`）

### LHD
**Least Hit Density（最小命中密度）** 根据每个对象的单位空间期望命中数（命中密度）进行淘汰。

- *除公共参数外无额外参数*

### LRU
**Least Recently Used（最近最少使用）** 淘汰最长时间未被访问的对象。

- *除公共参数外无额外参数*

### LRUK
**LRU-K** 淘汰后向 K 距离（backward K-distance）最大的对象，也就是第 K 次最近访问时间最早的那个。访问次数不足 K 次的对象后向 K 距离视为无穷大，会按 FIFO 顺序被优先淘汰，因此仅被访问一次的对象不足以在缓存中站稳脚跟。

- `k: int` —— 每个对象跟踪的最近访问次数（默认：`2`）

### FIFO
**First-In, First-Out（先进先出）** 按进入顺序淘汰对象，不考虑访问频率和时间局部性。

- *除公共参数外无额外参数*

### LFU
**Least Frequently Used（最不经常使用）** 淘汰访问频率最低的对象。

- *除公共参数外无额外参数*

### ARC
**Adaptive Replacement Cache（自适应替换缓存）** 是一种在时间局部性和访问频率之间取得平衡的混合算法。

- *除公共参数外无额外参数*

### Clock
**Clock** 是 `LRU` 的一种低复杂度近似。

- `init_freq: int` —— 新对象的初始频率计数值（默认：`0`）
- `n_bit_counter: int` —— 频率计数器使用的位数（默认：`1`）

### Random
**Random** 随机淘汰对象。

- *除公共参数外无额外参数*

### S3FIFO
**Simple, Scalable FIFO** 把缓存拆分为两部分：一个用于新准入对象的小 FIFO 队列，以及一个用于已证明较热对象的主 FIFO 队列，同时用一个 ghost 队列记录最近被淘汰对象的标识。只被访问一次的对象（one-hit wonder）会很快被挤出小队列，而不会污染主队列。

- `small_size_ratio: float` —— 分配给小队列的缓存比例（默认：`0.1`）
- `ghost_size_ratio: float` —— ghost 队列大小占缓存的比例（默认：`0.9`）
- `move_to_main_threshold: int` —— 对象在小队列中被访问多少次后晋升到主队列（默认：`2`）

### Sieve
**Sieve** 在一个 FIFO 队列上移动指针，淘汰第一个 visited 位未被置位的对象，同时清除途经对象的该位。它在保持 FIFO 简洁性的同时达到接近 LRU 的缺失率，且命中时不做任何晋升操作。

- *除公共参数外无额外参数*

### LIRS
**Low Inter-reference Recency Set** 按对象倒数第二次访问（而非最后一次访问）的近期程度来排序，从而能把真正的热点对象与扫描过程中只被碰过一次的对象区分开。

- *除公共参数外无额外参数*

### TwoQ
**2Q** 把新对象先放入一个 FIFO 队列（`Ain`），只有当对象的标识还在 ghost 队列（`Aout`）中时又被再次访问，才会晋升进入 LRU 主队列。

- `a_in_size_ratio: float` —— `Ain` 队列大小占缓存的比例（默认：`0.25`）
- `a_out_size_ratio: float` —— `Aout` ghost 队列大小占缓存的比例（默认：`0.5`）

### SLRU
**Segmented LRU（分段 LRU）** 把缓存划分为若干有序的 LRU 分段；对象每命中一次就晋升一段，并随着新对象到来逐步向淘汰端降级。

- *除公共参数外无额外参数*

### MQ
**Multi-Queue（多队列）** 把对象分布在一组按访问频率排序的 LRU 队列中：对象被重复访问时逐级晋升，在其生命期（lifetime）内未被访问则逐级降级。淘汰总是从最低的非空队列尾部取出，同时用一个 FIFO 幽灵队列（`Qout`）记录被淘汰对象的频率，使得很快再次被访问的对象能够回到原来的队列。

- `n_queue: int` —— 队列层数，取值需在 `[1, 64]` 内（默认：`8`）
- `lifetime: int` —— 对象未被访问多少个请求后降级一层（默认：`10000`）
- `qout_size_ratio: float` —— `Qout` 幽灵队列大小相对缓存大小的倍数，取值需在 `(0, 64]` 内（默认：`4.0`）

### WTinyLFU
**Window TinyLFU** 在一个较大的主缓存前面放置一个小的 LRU 窗口，并用频率草图（frequency sketch）来判断离开窗口的对象是否值得挤掉主缓存中的淘汰候选者。

- `main_cache: str` —— 主缓存所用的淘汰算法（默认：`"SLRU"`）
- `window_size: float` —— LRU 窗口大小占**总缓存大小**的比例，取值需在 `[0, 1)` 内，主缓存获得剩余部分（默认：`0.01`）

### LeCaR
**Learning Cache Replacement** 同时维护一个 LRU 候选者和一个 LFU 候选者，并用基于后悔最小化（regret minimisation）更新的权重在二者之间做选择，从而能随着负载在偏时间局部性与偏频率之间切换而自适应调整。

- `update_weight: bool` —— 回放过程中是否持续学习权重（默认：`True`）
- `lru_weight: float` —— 选择 LRU 候选者的初始概率；LFU 权重为 `1 - lru_weight`（默认：`0.5`）

### LFUDA
**LFU with Dynamic Aging（带动态老化的 LFU）** 在 `LFU` 基础上，每次访问时给对象优先级加上一个全局年龄值，这样很久以前流行的对象最终会老化淘汰，而不会长期占住缓存。

- *除公共参数外无额外参数*

### ClockPro
**CLOCK-Pro** 用 CLOCK 指针近似 `LIRS`，同时追踪热页和冷页，并为最近被淘汰的冷页设置一个试用期。

- `init_ref: int` —— 新准入对象的初始引用计数（默认：`0`）
- `init_ratio_cold: float` —— 缓存中初始被划为冷页的比例（默认：`0.5`）

### Clock2QPlus
**Clock-2Q+** 是 2Q 的变体，在 Clock 主缓存前面放置一个小的 FIFO 试用队列。幽灵队列记录最近被淘汰的对象标识，自适应的关联窗口（correlation window）则用于调节对象需要在 FIFO 队列中存活多久才值得晋升。

- `fifo_size_ratio: float` —— FIFO 队列大小占缓存的比例（默认：`0.1`）
- `ghost_size_ratio: float` —— 幽灵队列大小占缓存的比例（默认：`0.9`）
- `move_to_main_threshold: int` —— 对象晋升到主缓存前所需的命中次数（默认：`1`）
- `corr_window_ratio: float` —— 关联窗口初始大小占 FIFO 队列的比例（默认：`0.5`）

### Cacheus
**Cacheus** 在 `LeCaR` 的基础上增加了对学习率的轻量自适应以及扫描/抖动检测，使其在 `LeCaR` 表现不佳的负载上退化得更平缓。

- *除公共参数外无额外参数*

### Belady
**Belady's MIN** 是最优的离线策略：它淘汰下一次访问时间最远的对象。该策略无法在线实现，其存在意义是作为可达缺失率的下界。

- *除公共参数外无额外参数*

!!! important
    `Belady` 和 `BeladySize` 会读取 `req.next_access_vtime`，只有 oracle trace 才带有这一字段。请使用 `ORACLE_GENERAL_TRACE` 格式的 trace（如本页各示例所示）；在普通 trace 上该未来访问字段缺失，结果没有意义。

### BeladySize
**Size-aware Belady** 把 `Belady` 扩展到对象大小可变的场景，在一批候选对象的采样中综合考虑下次访问时间和对象大小来选择淘汰目标。

- `n_samples: int` —— 选择淘汰对象时采样的对象个数（默认：`128`）

### LRUProb
**LRU with Probabilistic Promotion（概率晋升的 LRU）** 行为与 `LRU` 类似，但对象只以 `prob` 的概率被移到队首。取值越低，行为越接近 `FIFO`，晋升开销也越小。

- `prob: float` —— 命中时晋升对象的概率（默认：`0.5`）

### FlashProb
**FlashProb** 建模 RAM + 闪存的两级缓存，只以一定概率把从 RAM 淘汰的对象写入闪存层，从而限制闪存设备上的写放大。

- `ram_size_ratio: float` —— RAM 层大小占总缓存的比例（默认：`0.05`）
- `disk_admit_prob: float` —— 对象被准入磁盘层的概率（默认：`0.2`）
- `ram_cache: str` —— RAM 层所用的淘汰算法（默认：`"LRU"`）
- `disk_cache: str` —— 磁盘层所用的淘汰算法（默认：`"FIFO"`）

### Size
**Size** 优先淘汰最大的对象，从而最大化保留的对象数量。在对象大小差异很大的负载上适合作为基线。

- *除公共参数外无额外参数*

### GDSF
**GreedyDual-Size with Frequency** 按频率除以大小对对象排序，并叠加一个全局老化因子，从而偏好体积小且访问频繁的对象。

- *除公共参数外无额外参数*

### Hyperbolic
**Hyperbolic** 每次淘汰时采样若干对象，淘汰其中访问次数除以在缓存中驻留时间最小的那个，从而在不维护全局结构的情况下近似出一个优先级排序。

- *除公共参数外无额外参数*

### ThreeLCache
**3LCache** 是一种学习型策略，它预测每个对象的保留价值，并据此把对象组织在三个层级中。

- `objective: str` —— 学习模型优化的目标指标（默认：`"byte-miss-ratio"`）

!!! warning
    需要以 `-DENABLE_3L_CACHE=ON` 构建。参见[安装指南](../getting_started/installation.md#optional-eviction-algorithms)。在未开启该选项的构建中构造它会抛出 `ImportError`。

### GLCache
**Group-Learned Cache** 把对象分组为 segment，学习预测每个 segment 的未来价值，并通过合并价值最低的 segment 来完成淘汰，而不是逐个对象做决策。

- `segment_size: int` —— 每个 segment 包含的对象数（默认：`100`）
- `n_merge: int` —— 单次淘汰中合并的 segment 数（默认：`2`）
- `type: str` —— 缓存类型，例如学习型变体或某个基线（默认：`"learned"`）
- `rank_intvl: float` —— segment 重新排序的频率，以缓存的比例表示（默认：`0.02`）
- `merge_consecutive_segs: bool` —— 合并是否限定在连续的 segment 之间（默认：`True`）
- `train_source_y: str` —— 训练标签的来源（默认：`"online"`）
- `retrain_intvl: int` —— 模型重训练的间隔秒数（默认：`86400`）

!!! warning
    需要以 `-DENABLE_GLCACHE=ON` 构建。参见[安装指南](../getting_started/installation.md#optional-eviction-algorithms)。在未开启该选项的构建中构造它会抛出 `ImportError`。

### LRB
**Learning Relaxed Belady** 训练一个模型在线近似 Belady 的决策，淘汰那些被预测为下次访问较远的对象。

- `objective: str` —— 学习模型优化的目标指标（默认：`"byte-miss-ratio"`）

!!! warning
    需要以 `-DENABLE_LRB=ON` 构建。参见[安装指南](../getting_started/installation.md#optional-eviction-algorithms)。在未开启该选项的构建中构造它会抛出 `ImportError`。

### PluginCache
**PluginCache** 让你无需编译，仅通过 hook 函数就能用纯 Python 实现淘汰策略。它在[插件系统](plugins.md)中单独介绍。

## 准入策略 {#admission-policies}

### BloomFilterAdmissioner
使用布隆过滤器，根据对象被看到的次数来决定是否准入。

- *无参数*

### ProbAdmissioner
以固定概率准入对象。

- `prob: float`（可选）—— 准入对象的概率（默认：`0.5`）

### SizeAdmissioner
仅在对象大小低于指定阈值时才准入。

- `size_threshold: int`（可选）—— 允许准入的最大对象大小（字节）（默认：`9_223_372_036_854_775_807`，即 `INT64_MAX`）

### SizeProbabilisticAdmissioner
以随对象增大而递减的概率准入对象，从而偏好小对象。

- `exponent: float`（可选）—— 控制过滤大对象力度的指数（默认：`1e-6`）

### AdaptSizeAdmissioner
实现 **AdaptSize**，一种基于反馈、周期性调整大小阈值的策略。

- `max_iteration: int`（可选）—— 参数调优的最大迭代次数（默认：`15`）
- `reconf_interval: int`（可选）—— 重新评估阈值的间隔（以请求数计）（默认：`30_000`）

### PluginAdmissioner
让你通过 hook 函数用 Python 实现准入策略。参见[插件系统](plugins.md#pluginadmissioner)。

## 对比不同算法

由于所有缓存都暴露相同的接口，遍历多个算法非常简单。`process_trace` 会在开始前把 reader 倒回起点，因此同一个 reader 可以直接交给每一轮运行，无需显式调用 `reset()`：

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
