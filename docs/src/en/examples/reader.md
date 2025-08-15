# Trace Reader

We support a unified trace reader to open trace files in different format and read the requests.

## Basic usage

`TraceReader` class is the core of this functionality. When we create an instance of `TraceReader`, we open a trace file for read requests.

`TraceReader` accepts three arguments:
- `trace: str | TraceReader`: A trace path or other trace instance. The trace path can be a file path on your local machine (e.g., ~/data/trace.oracleGeneral.zst) or an S3 URI (e.g., s3://cache-datasets/cache_dataset_oracleGeneral/2007_msr/msr_hm_0.oracleGeneral.zst).
- `trace_type: TraceType` (optional): If not given, it will be infered according to the file name.
- `reader_init_params: ReaderInitParam` (optional): If not given, will use default params for reader initialization.

Here is an example to load one trace via an S3 URI.

```python
import libcachesim as lcs

# Open a trace hosted on S3 (find more via https://github.com/cacheMon/cache_dataset)
URI = "s3://cache-datasets/cache_dataset_oracleGeneral/2007_msr/msr_hm_0.oracleGeneral.zst"
reader = lcs.TraceReader(
    trace = URI,
    trace_type = lcs.TraceType.ORACLE_GENERAL_TRACE,
    reader_init_params = lcs.ReaderInitParam(ignore_obj_size=False)
)
```

Then we can walk through the trace.

```python
for req in reader:
    print(req.obj_id, req.obj_size)
```

## Reader slicing

`TraceReader` support slicing and index access.

```python
# Read the first 100 reqs
for req in reader[:100]:
    print(req.obj_id, req.obj_size)
```

```python
# Read 100 reqs after the first 100 reqs 
for req in reader[100:200]:
    print(req.obj_id, req.obj_size)
```

```python
# Read last 100 reqs
for req in reader[-100:]:
    print(req.obj_id, req.obj_size)
```