# libCacheSim Python 绑定

欢迎使用 libCacheSim Python 绑定！这是一个高性能的缓存模拟库，提供了 Python 接口。

## 概述

libCacheSim 是一个高性能的缓存模拟框架，支持各种缓存算法和跟踪格式。Python 绑定为缓存模拟、分析和研究提供了易于使用的接口。

## 主要特性

- **高性能**: 基于优化的 C++ libCacheSim 库构建
- **多种缓存算法**: 支持 LRU、LFU、FIFO、ARC、Clock、S3FIFO、Sieve 等多种算法
- **跟踪支持**: 读取各种跟踪格式（CSV、二进制、OracleGeneral 等）
- **合成跟踪**: 生成 Zipf 和均匀分布的合成工作负载
- **分析工具**: 内置跟踪分析和缓存性能评估
- **易于集成**: 简单的 Python API，适用于研究和生产环境

## 快速示例

```python
import libcachesim as lcs

# 创建缓存
cache = lcs.LRU(cache_size=1024*1024)  # 1MB 缓存

# 生成合成跟踪
reader = lcs.SyntheticReader(
    num_of_req=10000,
    obj_size=1024,
    dist="zipf",
    alpha=1.0
)

# 模拟缓存行为
hit_count = 0
for req in reader:
    if cache.get(req):
        hit_count += 1

hit_ratio = hit_count / reader.get_num_of_req()
print(f"命中率: {hit_ratio:.4f}")
```

## 安装

```bash
pip install libcachesim
```

或从源码安装：

```bash
git clone https://github.com/cacheMon/libCacheSim-python.git
cd libCacheSim-python
pip install -e .
```

## 快速开始

查看我们的[快速开始指南](quickstart.md)开始使用 libCacheSim Python 绑定，或浏览 [API 参考](api.md)获取详细文档。

## 贡献

我们欢迎贡献！请查看我们的 [GitHub 仓库](https://github.com/cacheMon/libCacheSim-python)了解更多信息。

## 许可证

本项目采用 GPL-3.0 许可证。
