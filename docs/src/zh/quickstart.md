# 快速开始指南

本指南将帮助您开始使用 libCacheSim Python 绑定。

## 安装

### 从 PyPI 安装（推荐）

```bash
pip install libcachesim
```

### 从源码安装

```bash
git clone https://github.com/cacheMon/libCacheSim-python.git
cd libCacheSim-python
git submodule update --init --recursive
pip install -e .
```

## 基本用法

### 1. 创建缓存

```python
import libcachesim as lcs

# 创建不同类型的缓存
lru_cache = lcs.LRU(cache_size=1024*1024)  # 1MB LRU 缓存
lfu_cache = lcs.LFU(cache_size=1024*1024)  # 1MB LFU 缓存
fifo_cache = lcs.FIFO(cache_size=1024*1024)  # 1MB FIFO 缓存
```

### 2. 使用合成跟踪

```python
# 生成 Zipf 分布的请求
reader = lcs.SyntheticReader(
    num_of_req=10000,
    obj_size=1024,
    dist="zipf",
    alpha=1.0,
    num_objects=1000,
    seed=42
)

# 模拟缓存行为
cache = lcs.LRU(cache_size=50*1024)
hit_count = 0

for req in reader:
    if cache.get(req):
        hit_count += 1

print(f"命中率: {hit_count/reader.get_num_of_req():.4f}")
```

### 3. 读取真实跟踪

```python
# 读取 CSV 跟踪
reader = lcs.TraceReader(
    trace="path/to/trace.csv",
    trace_type=lcs.TraceType.CSV_TRACE,
    has_header=True,
    delimiter=",",
    obj_id_is_num=True
)

# 处理请求
cache = lcs.LRU(cache_size=1024*1024)
for req in reader:
    result = cache.get(req)
    # 处理结果...
```

### 4. 缓存性能分析

```python
# 运行综合分析
analyzer = lcs.TraceAnalyzer(reader, "output_prefix")
analyzer.run()

# 这会生成各种分析文件：
# - 命中率曲线
# - 访问模式分析
# - 时间局部性分析
# - 等等...
```

## 可用的缓存算法

libCacheSim 支持众多缓存算法：

### 基础算法
- **LRU**: 最近最少使用
- **LFU**: 最不经常使用
- **FIFO**: 先进先出
- **Clock**: 时钟算法
- **Random**: 随机替换

### 高级算法
- **ARC**: 自适应替换缓存
- **S3FIFO**: 简单、快速、公平的 FIFO
- **Sieve**: Sieve 驱逐算法
- **TinyLFU**: 带准入控制的 Tiny LFU
- **TwoQ**: 双队列算法
- **LRB**: 学习松弛 Belady

### 实验性算法
- **3LCache**: 三级缓存
- **等等...**

## 跟踪格式

支持的跟踪格式包括：

- **CSV**: 逗号分隔值
- **Binary**: 自定义二进制格式
- **OracleGeneral**: Oracle 通用格式
- **Vscsi**: VMware vSCSI 格式
- **等等...**

## 高级功能

### 自定义缓存策略

您可以使用 Python 钩子实现自定义缓存策略：

```python
from collections import OrderedDict

def create_custom_lru():
    def init_hook(cache_size):
        return OrderedDict()
    
    def hit_hook(cache_dict, obj_id, obj_size):
        cache_dict.move_to_end(obj_id)
    
    def miss_hook(cache_dict, obj_id, obj_size):
        cache_dict[obj_id] = obj_size
    
    def eviction_hook(cache_dict, obj_id, obj_size):
        if cache_dict:
            cache_dict.popitem(last=False)
    
    return lcs.PythonHookCache(
        cache_size=1024*1024,
        init_hook=init_hook,
        hit_hook=hit_hook,
        miss_hook=miss_hook,
        eviction_hook=eviction_hook
    )

custom_cache = create_custom_lru()
```

### 跟踪采样

```python
# 空间采样 10% 的请求
reader = lcs.TraceReader(
    trace="large_trace.csv",
    trace_type=lcs.TraceType.CSV_TRACE,
    sampling_ratio=0.1,
    sampling_type=lcs.SamplerType.SPATIAL_SAMPLER
)
```

### 多线程分析

```python
# 使用多线程进行分析
analyzer = lcs.TraceAnalyzer(reader, "output", n_threads=4)
analyzer.run()
```

## 下一步

- 探索 [API 参考](api.md) 获取详细文档
- 查看[使用示例](examples.md)了解更复杂的用例
- 访问我们的 [GitHub 仓库](https://github.com/cacheMon/libCacheSim-python) 获取源码和问题报告
