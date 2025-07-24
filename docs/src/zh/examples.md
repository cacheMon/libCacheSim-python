# 示例和教程

本页提供使用 libCacheSim Python 绑定的实际示例和深入教程。

## 基础示例

### 简单缓存模拟

最基本的缓存模拟示例：

```python
import libcachesim as lcs

# 创建一个1MB大小的LRU缓存
cache = lcs.LRU(cache_size=1024*1024)

# 模拟一些请求
requests = [
    (1, 100),  # 对象1，大小100字节
    (2, 200),  # 对象2，大小200字节
    (1, 100),  # 对象1，再次访问（命中）
    (3, 150),  # 对象3，大小150字节
]

for obj_id, size in requests:
    hit = cache.get(obj_id, size)
    print(f"对象 {obj_id}: {'命中' if hit else '缺失'}")

# 获取统计信息
print(f"命中率: {cache.get_hit_ratio():.2%}")
```

### 跟踪文件处理

从CSV文件读取和处理跟踪：

```python
import libcachesim as lcs

# 配置跟踪读取器
reader_params = lcs.ReaderInitParam()
reader_params.has_header = True
reader_params.delimiter = ","
reader_params.time_field = 1
reader_params.obj_id_field = 2
reader_params.obj_size_field = 3

# 创建跟踪读取器
reader = lcs.TraceReader("workload.csv", lcs.TraceType.CSV_TRACE, reader_params)

# 创建缓存
cache = lcs.LRU(cache_size=1024*1024)

# 处理跟踪
request_count = 0
for request in reader:
    hit = cache.get(request.obj_id, request.obj_size)
    request_count += 1
    
    if request_count % 10000 == 0:
        print(f"处理了 {request_count} 个请求，命中率: {cache.get_hit_ratio():.2%}")

print(f"最终命中率: {cache.get_hit_ratio():.2%}")
```

## 合成工作负载生成

### Zipf分布请求

生成具有Zipf分布的合成工作负载：

```python
import libcachesim as lcs

# 创建Zipf分布的合成读取器
reader = lcs.SyntheticReader(
    num_objects=10000,
    num_requests=100000,
    distribution="zipf",
    alpha=1.0,  # Zipf偏斜参数
    obj_size=4096,
    seed=42  # 为了可重现性
)

# 创建缓存
cache = lcs.LRU(cache_size=10*1024*1024)  # 10MB

# 运行模拟
for request in reader:
    cache.get(request.obj_id, request.obj_size)

print(f"Zipf工作负载 (α=1.0) 命中率: {cache.get_hit_ratio():.2%}")

# 尝试不同的偏斜参数
for alpha in [0.5, 1.0, 1.5, 2.0]:
    reader = lcs.SyntheticReader(
        num_objects=10000,
        num_requests=50000,
        distribution="zipf",
        alpha=alpha,
        obj_size=4096,
        seed=42
    )
    
    cache = lcs.LRU(cache_size=5*1024*1024)
    for request in reader:
        cache.get(request.obj_id, request.obj_size)
    
    print(f"α={alpha}: 命中率 {cache.get_hit_ratio():.2%}")
```

### 均匀分布请求

```python
import libcachesim as lcs

# 创建均匀分布的合成读取器
reader = lcs.SyntheticReader(
    num_objects=5000,
    num_requests=50000,
    distribution="uniform",
    obj_size=4096,
    seed=42
)

cache = lcs.LRU(cache_size=5*1024*1024)
for request in reader:
    cache.get(request.obj_id, request.obj_size)

print(f"均匀工作负载命中率: {cache.get_hit_ratio():.2%}")
```

## 缓存算法比较

### 多算法评估

比较不同缓存算法的性能：

```python
import libcachesim as lcs

# 创建合成工作负载
reader = lcs.SyntheticReader(
    num_objects=10000,
    num_requests=100000,
    distribution="zipf",
    alpha=1.2,
    obj_size=4096,
    seed=42
)

# 保存请求以便重用
requests = list(reader)

# 测试的算法
algorithms = {
    'LRU': lcs.LRU,
    'LFU': lcs.LFU,
    'FIFO': lcs.FIFO,
    'ARC': lcs.ARC,
    'S3FIFO': lcs.S3FIFO,
    'Sieve': lcs.Sieve,
}

cache_size = 10*1024*1024  # 10MB

results = {}
for name, algorithm in algorithms.items():
    cache = algorithm(cache_size)
    
    for request in requests:
        cache.get(request.obj_id, request.obj_size)
    
    results[name] = cache.get_hit_ratio()
    print(f"{name:8}: {cache.get_hit_ratio():.2%}")

# 找到最佳算法
best_algo = max(results, key=results.get)
print(f"\n最佳算法: {best_algo} ({results[best_algo]:.2%})")
```

## 跟踪采样

### 空间采样

使用采样减少大型跟踪的大小：

```python
import libcachesim as lcs

# 设置采样参数
sampler = lcs.Sampler(
    sample_ratio=0.1,  # 采样10%的请求
    type=lcs.SamplerType.SPATIAL_SAMPLER
)

reader_params = lcs.ReaderInitParam()
reader_params.has_header = True
reader_params.sampler = sampler

# 读取采样跟踪
reader = lcs.TraceReader("large_trace.csv", lcs.TraceType.CSV_TRACE, reader_params)

cache = lcs.LRU(cache_size=1024*1024)
request_count = 0

for request in reader:
    cache.get(request.obj_id, request.obj_size)
    request_count += 1

print(f"处理了 {request_count} 个采样请求")
print(f"采样命中率: {cache.get_hit_ratio():.2%}")
```

### 时间采样

```python
import libcachesim as lcs

# 时间采样配置
sampler = lcs.Sampler(
    sample_ratio=0.05,  # 采样5%
    type=lcs.SamplerType.TEMPORAL_SAMPLER
)

reader_params = lcs.ReaderInitParam()
reader_params.sampler = sampler

reader = lcs.TraceReader("timestamped_trace.csv", lcs.TraceType.CSV_TRACE, reader_params)

# 运行模拟...
```

## 跟踪分析

### 基本跟踪统计

分析跟踪特征：

```python
import libcachesim as lcs

# 创建跟踪分析器
analyzer = lcs.TraceAnalyzer("workload.csv", lcs.TraceType.CSV_TRACE)

# 分析基本统计
print("跟踪分析:")
print(f"总请求数: {analyzer.get_num_requests():,}")
print(f"唯一对象数: {analyzer.get_num_objects():,}")
print(f"平均对象大小: {analyzer.get_average_obj_size():.2f} 字节")
print(f"总数据大小: {analyzer.get_total_size():,} 字节")

# 分析重用距离
reuse_distances = analyzer.get_reuse_distance()
print(f"平均重用距离: {sum(reuse_distances)/len(reuse_distances):.2f}")
```

### 流行度分析

```python
import libcachesim as lcs
import matplotlib.pyplot as plt

# 创建分析器
analyzer = lcs.TraceAnalyzer("workload.csv", lcs.TraceType.CSV_TRACE)

# 获取对象流行度
popularity = analyzer.get_popularity()

# 绘制流行度分布
plt.figure(figsize=(10, 6))
plt.loglog(range(1, len(popularity)+1), sorted(popularity, reverse=True))
plt.xlabel('对象排名')
plt.ylabel('访问频率')
plt.title('对象流行度分布')
plt.grid(True)
plt.show()
```

## 高级场景

### 缓存层次结构

模拟多级缓存层次结构：

```python
import libcachesim as lcs

class CacheHierarchy:
    def __init__(self, l1_size, l2_size):
        self.l1_cache = lcs.LRU(l1_size)  # L1缓存
        self.l2_cache = lcs.LRU(l2_size)  # L2缓存
        self.l1_hits = 0
        self.l2_hits = 0
        self.misses = 0
    
    def get(self, obj_id, obj_size):
        # 首先检查L1
        if self.l1_cache.get(obj_id, obj_size):
            self.l1_hits += 1
            return True
        
        # 然后检查L2
        if self.l2_cache.get(obj_id, obj_size):
            self.l2_hits += 1
            # 将对象提升到L1
            self.l1_cache.get(obj_id, obj_size)
            return True
        
        # 完全缺失
        self.misses += 1
        # 将对象加载到两个级别
        self.l1_cache.get(obj_id, obj_size)
        self.l2_cache.get(obj_id, obj_size)
        return False
    
    def get_stats(self):
        total = self.l1_hits + self.l2_hits + self.misses
        return {
            'l1_hit_ratio': self.l1_hits / total,
            'l2_hit_ratio': self.l2_hits / total,
            'overall_hit_ratio': (self.l1_hits + self.l2_hits) / total
        }

# 使用缓存层次结构
hierarchy = CacheHierarchy(l1_size=1024*1024, l2_size=10*1024*1024)

reader = lcs.SyntheticReader(
    num_objects=50000,
    num_requests=100000,
    distribution="zipf",
    alpha=1.0,
    obj_size=4096,
    seed=42
)

for request in reader:
    hierarchy.get(request.obj_id, request.obj_size)

stats = hierarchy.get_stats()
print(f"L1命中率: {stats['l1_hit_ratio']:.2%}")
print(f"L2命中率: {stats['l2_hit_ratio']:.2%}")
print(f"总命中率: {stats['overall_hit_ratio']:.2%}")
```

### 缓存预热

在评估前预热缓存：

```python
import libcachesim as lcs

reader = lcs.SyntheticReader(
    num_objects=10000,
    num_requests=200000,
    distribution="zipf",
    alpha=1.0,
    obj_size=4096,
    seed=42
)

cache = lcs.LRU(cache_size=5*1024*1024)

# 分为预热和评估阶段
warmup_requests = 50000
eval_requests = 0

for i, request in enumerate(reader):
    hit = cache.get(request.obj_id, request.obj_size)
    
    if i < warmup_requests:
        # 预热阶段 - 不计算统计
        continue
    else:
        # 评估阶段
        eval_requests += 1

print(f"预热后命中率: {cache.get_hit_ratio():.2%}")
print(f"评估请求数: {eval_requests}")
```

### 动态缓存大小

随时间变化缓存大小：

```python
import libcachesim as lcs

reader = lcs.SyntheticReader(
    num_objects=10000,
    num_requests=100000,
    distribution="zipf",
    alpha=1.0,
    obj_size=4096,
    seed=42
)

# 从小缓存开始
initial_size = 1024*1024  # 1MB
max_size = 10*1024*1024   # 10MB
growth_interval = 10000   # 每10000个请求增长

cache = lcs.LRU(initial_size)
current_size = initial_size

for i, request in enumerate(reader):
    # 定期增加缓存大小
    if i > 0 and i % growth_interval == 0 and current_size < max_size:
        current_size = min(current_size * 2, max_size)
        # 注意：这里需要创建新缓存，因为现有缓存大小无法动态更改
        new_cache = lcs.LRU(current_size)
        cache = new_cache
        print(f"在请求 {i} 处将缓存大小增加到 {current_size/1024/1024:.1f}MB")
    
    cache.get(request.obj_id, request.obj_size)

print(f"最终命中率: {cache.get_hit_ratio():.2%}")
```

## 性能优化技巧

### 批量处理

```python
import libcachesim as lcs

# 处理大型跟踪时批量处理请求
def process_trace_in_batches(filename, cache, batch_size=10000):
    reader = lcs.TraceReader(filename, lcs.TraceType.CSV_TRACE)
    
    batch = []
    total_processed = 0
    
    for request in reader:
        batch.append(request)
        
        if len(batch) >= batch_size:
            # 处理批次
            for req in batch:
                cache.get(req.obj_id, req.obj_size)
            
            total_processed += len(batch)
            print(f"处理了 {total_processed} 个请求")
            batch = []
    
    # 处理剩余请求
    for req in batch:
        cache.get(req.obj_id, req.obj_size)
    
    return total_processed + len(batch)

# 使用
cache = lcs.LRU(cache_size=10*1024*1024)
total = process_trace_in_batches("large_trace.csv", cache)
print(f"总共处理了 {total} 个请求")
```

### 内存高效的请求处理

```python
import libcachesim as lcs

def memory_efficient_simulation(filename, cache_size):
    """内存高效的缓存模拟。"""
    
    reader_params = lcs.ReaderInitParam()
    reader_params.cap_at_n_req = 1000000  # 限制内存中的请求数
    
    reader = lcs.TraceReader(filename, lcs.TraceType.CSV_TRACE, reader_params)
    cache = lcs.LRU(cache_size)
    
    request_count = 0
    for request in reader:
        cache.get(request.obj_id, request.obj_size)
        request_count += 1
        
        # 定期报告进度
        if request_count % 100000 == 0:
            print(f"进度: {request_count:,} 请求，命中率: {cache.get_hit_ratio():.2%}")
    
    return cache.get_hit_ratio()

# 使用
hit_ratio = memory_efficient_simulation("workload.csv", 10*1024*1024)
print(f"最终命中率: {hit_ratio:.2%}")
```

这些示例展示了libCacheSim Python绑定的各种使用场景，从基础缓存模拟到高级性能分析和优化技术。根据您的具体需求调整这些示例。
