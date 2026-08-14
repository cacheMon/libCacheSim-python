# Trace Reader

我们提供了统一的 trace reader，用于打开不同格式的 trace 文件并读取其中的请求。

## 基本用法

`TraceReader` 类是这一功能的核心。创建 `TraceReader` 实例时，就会打开一个 trace 文件以便读取请求。

`TraceReader` 接受三个参数：

- `trace: str | TraceReader`：trace 路径或另一个 trace 实例。trace 路径可以是本机上的文件路径（例如 ~/data/trace.oracleGeneral.zst），也可以是 S3 URI（例如 s3://cache-datasets/cache_dataset_oracleGeneral/2007_msr/msr_hm_0.oracleGeneral.zst）。
- `trace_type: TraceType`（可选）：若不指定，将根据文件名推断。
- `reader_init_params: ReaderInitParam`（可选）：若不指定，将使用默认参数初始化 reader。

下面是通过 S3 URI 加载一条 trace 的例子。

```python
import libcachesim as lcs

# 打开一条托管在 S3 上的 trace（更多 trace 见 https://github.com/cacheMon/cache_dataset）
URI = "s3://cache-datasets/cache_dataset_oracleGeneral/2007_msr/msr_hm_0.oracleGeneral.zst"
reader = lcs.TraceReader(
    trace = URI,
    trace_type = lcs.TraceType.ORACLE_GENERAL_TRACE,
    reader_init_params = lcs.ReaderInitParam(ignore_obj_size=False)
)
```

然后就可以遍历整条 trace。

```python
for req in reader:
    print(req.obj_id, req.obj_size)
```

## Reader 切片

`TraceReader` 支持切片和按下标访问。

```python
# 读取前 100 条请求
for req in reader[:100]:
    print(req.obj_id, req.obj_size)
```

```python
# 读取前 100 条之后的 100 条请求
for req in reader[100:200]:
    print(req.obj_id, req.obj_size)
```

```python
# 读取最后 100 条请求
for req in reader[-100:]:
    print(req.obj_id, req.obj_size)
```
