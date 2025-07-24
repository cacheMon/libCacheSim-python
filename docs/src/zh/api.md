# API 参考

本页面提供 libCacheSim Python 绑定的详细 API 文档。

## 核心类

### 缓存类

所有缓存类都继承自基础缓存接口，并提供以下方法：

```python
class Cache:
    """基础缓存接口。"""
    
    def get(self, obj_id: int, obj_size: int = 1) -> bool:
        """从缓存请求对象。
        
        参数:
            obj_id: 对象标识符
            obj_size: 对象大小（字节）
            
        返回:
            如果缓存命中返回 True，缓存缺失返回 False
        """
    
    def get_hit_ratio(self) -> float:
        """获取当前缓存命中率。"""
    
    def get_miss_ratio(self) -> float:
        """获取当前缓存缺失率。"""
        
    def get_num_hits(self) -> int:
        """获取缓存命中总数。"""
        
    def get_num_misses(self) -> int:
        """获取缓存缺失总数。"""
```

### 可用的缓存算法

```python
# 基础算法
def LRU(cache_size: int) -> Cache: ...
def LFU(cache_size: int) -> Cache: ...
def FIFO(cache_size: int) -> Cache: ...
def Clock(cache_size: int) -> Cache: ...
def Random(cache_size: int) -> Cache: ...

# 高级算法  
def ARC(cache_size: int) -> Cache: ...
def S3FIFO(cache_size: int) -> Cache: ...
def Sieve(cache_size: int) -> Cache: ...
def TinyLFU(cache_size: int) -> Cache: ...
def TwoQ(cache_size: int) -> Cache: ...
```

### TraceReader

```python
class TraceReader:
    """读取各种格式的跟踪文件。"""
    
    def __init__(self, trace_path: str, trace_type: TraceType, 
                 reader_params: ReaderInitParam = None):
        """初始化跟踪读取器。
        
        参数:
            trace_path: 跟踪文件路径
            trace_type: 跟踪格式类型
            reader_params: 可选的读取器配置
        """
    
    def __iter__(self):
        """迭代跟踪中的请求。"""
        
    def reset(self):
        """重置读取器到跟踪开始。"""
        
    def skip(self, n: int):
        """跳过 n 个请求。"""
        
    def clone(self):
        """创建读取器的副本。"""
```

### SyntheticReader  

```python
class SyntheticReader:
    """生成合成工作负载。"""
    
    def __init__(self, num_objects: int, num_requests: int,
                 distribution: str = "zipf", alpha: float = 1.0,
                 obj_size: int = 1, seed: int = None):
        """初始化合成读取器。
        
        参数:
            num_objects: 唯一对象数量
            num_requests: 要生成的总请求数
            distribution: 分布类型（"zipf"，"uniform"）
            alpha: Zipf 偏斜参数
            obj_size: 对象大小（字节）
            seed: 用于可重现性的随机种子
        """
```

### TraceAnalyzer

```python
class TraceAnalyzer:
    """分析跟踪特征。"""
    
    def __init__(self, trace_path: str, trace_type: TraceType,
                 reader_params: ReaderInitParam = None):
        """初始化跟踪分析器。"""
        
    def get_num_requests(self) -> int:
        """获取总请求数。"""
        
    def get_num_objects(self) -> int:
        """获取唯一对象数。"""
        
    def get_working_set_size(self) -> int:
        """获取工作集大小。"""
```

## 枚举和常量

### TraceType

```python
class TraceType:
    """支持的跟踪文件格式。"""
    CSV_TRACE = "csv"
    BINARY_TRACE = "binary"  
    ORACLE_GENERAL_TRACE = "oracle"
    PLAIN_TXT_TRACE = "txt"
```

### SamplerType

```python
class SamplerType:
    """采样策略。"""
    SPATIAL_SAMPLER = "spatial"
    TEMPORAL_SAMPLER = "temporal"
```

### ReqOp

```python
class ReqOp:
    """请求操作类型。"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
```

## 数据结构

### Request

```python
class Request:
    """表示缓存请求。"""
    
    def __init__(self):
        self.obj_id: int = 0
        self.obj_size: int = 1
        self.timestamp: int = 0
        self.op: str = "read"
```

### ReaderInitParam

```python
class ReaderInitParam:
    """跟踪读取器的配置参数。"""
    
    def __init__(self):
        self.has_header: bool = False
        self.delimiter: str = ","
        self.obj_id_is_num: bool = True
        self.ignore_obj_size: bool = False
        self.ignore_size_zero_req: bool = True
        self.cap_at_n_req: int = -1
        self.block_size: int = 4096
        self.trace_start_offset: int = 0
        
        # 字段映射（从1开始索引）
        self.time_field: int = 1
        self.obj_id_field: int = 2
        self.obj_size_field: int = 3
        self.op_field: int = 4
        
        self.sampler: Sampler = None
```

### Sampler

```python
class Sampler:
    """请求采样配置。"""
    
    def __init__(self, sample_ratio: float = 1.0, 
                 type: str = "spatial"):
        """初始化采样器。
        
        参数:
            sample_ratio: 要采样的请求比例（0.0-1.0）
            type: 采样类型（"spatial" 或 "temporal"）
        """
        self.sample_ratio = sample_ratio
        self.type = type
```

## 工具函数

### 合成跟踪生成

```python
def create_zipf_requests(num_objects, num_requests, alpha, obj_size, seed=None):
    """
    创建 Zipf 分布的合成请求。
    
    参数:
        num_objects (int): 唯一对象数量
        num_requests (int): 要生成的总请求数
        alpha (float): Zipf 偏斜参数（越高越偏斜）
        obj_size (int): 每个对象的大小（字节）
        seed (int, 可选): 随机种子，用于可重现性
        
    返回:
        List[Request]: 生成的请求列表
    """
    
def create_uniform_requests(num_objects, num_requests, obj_size, seed=None):
    """
    创建均匀分布的合成请求。
    
    参数:
        num_objects (int): 唯一对象数量
        num_requests (int): 要生成的总请求数
        obj_size (int): 每个对象的大小（字节）
        seed (int, 可选): 随机种子，用于可重现性
        
    返回:
        List[Request]: 生成的请求列表
    """
```

### 缓存算法

可用的缓存算法及其工厂函数：

```python
# 基础算法
LRU(cache_size: int) -> Cache
LFU(cache_size: int) -> Cache  
FIFO(cache_size: int) -> Cache
Clock(cache_size: int) -> Cache
Random(cache_size: int) -> Cache

# 高级算法
ARC(cache_size: int) -> Cache
S3FIFO(cache_size: int) -> Cache
Sieve(cache_size: int) -> Cache
TinyLFU(cache_size: int) -> Cache
TwoQ(cache_size: int) -> Cache
LRB(cache_size: int) -> Cache

# 实验性算法
cache_3L(cache_size: int) -> Cache
```

### 性能指标

```python
class CacheStats:
    """缓存性能统计。"""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.bytes_written = 0
        self.bytes_read = 0
    
    @property
    def hit_ratio(self) -> float:
        """计算命中率。"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    @property
    def miss_ratio(self) -> float:
        """计算缺失率。"""
        return 1.0 - self.hit_ratio
```

## 错误处理

库使用标准的 Python 异常：

- `ValueError`: 无效参数或配置
- `FileNotFoundError`: 跟踪文件未找到
- `RuntimeError`: 底层 C++ 库的运行时错误
- `MemoryError`: 内存不足条件

错误处理示例：

```python
try:
    reader = lcs.TraceReader("nonexistent.csv", lcs.TraceType.CSV_TRACE)
except FileNotFoundError:
    print("跟踪文件未找到")
except ValueError as e:
    print(f"无效配置: {e}")
```

## 配置选项

### 读取器配置

```python
reader_params = lcs.ReaderInitParam(
    has_header=True,           # CSV 有标题行
    delimiter=",",             # 字段分隔符
    obj_id_is_num=True,       # 对象 ID 是数字
    ignore_obj_size=False,    # 不忽略对象大小
    ignore_size_zero_req=True, # 忽略零大小请求
    cap_at_n_req=1000000,     # 限制请求数量
    block_size=4096,          # 块大小（用于基于块的跟踪）
    trace_start_offset=0,     # 跳过初始请求
)

# 字段映射（从1开始索引）
reader_params.time_field = 1
reader_params.obj_id_field = 2  
reader_params.obj_size_field = 3
reader_params.op_field = 4
```

### 采样配置

```python
sampler = lcs.Sampler(
    sample_ratio=0.1,                    # 采样 10% 的请求
    type=lcs.SamplerType.SPATIAL_SAMPLER # 空间采样
)
reader_params.sampler = sampler
```

## 线程安全

库为大多数用例提供线程安全操作：

- 单个缓存实例内的缓存操作是线程安全的
- 可以并发使用多个读取器
- 分析操作可以利用多线程

对于高并发场景，考虑为每个线程使用单独的缓存实例。

## 内存管理

库自动管理大多数操作的内存：

- 缓存对象处理自己的内存分配
- 跟踪读取器自动管理缓冲
- 请求对象轻量且可重用

对于大规模模拟，监控内存使用并考虑：

- 使用采样减少跟踪大小
- 分块处理跟踪
- 适当限制缓存大小

## 最佳实践

1. **使用适当的缓存大小**: 根据模拟目标确定缓存大小
2. **设置随机种子**: 用于合成跟踪的可重现结果
3. **处理错误**: 始终将文件操作包装在 try-catch 块中
4. **监控内存**: 对于大型跟踪，考虑采样或分块
5. **使用线程**: 为分析任务利用多线程
6. **验证跟踪**: 在模拟前检查跟踪格式和内容
