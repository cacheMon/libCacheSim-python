import libcachesim as lcs

# Step 1: Get one trace from S3 bucket
URI = "cache_dataset_oracleGeneral/2007_msr/msr_hm_0.oracleGeneral.zst"
dl = lcs.DataLoader()
dl.load(URI)

# Step 2: Open trace and process efficiently
reader = lcs.TraceReader(
    trace = dl.get_cache_path(URI),
    trace_type = lcs.TraceType.ORACLE_GENERAL_TRACE,
    reader_init_params = lcs.ReaderInitParam(ignore_obj_size=False)
)

# Step 3: Initialize cache
cache = lcs.S3FIFO(cache_size=1024*1024)

# Step 4: Process entire trace efficiently (C++ backend)
obj_miss_ratio, byte_miss_ratio = cache.process_trace(reader)
print(f"Object miss ratio: {obj_miss_ratio:.4f}, Byte miss ratio: {byte_miss_ratio:.4f}")

# Step 4.1: Process with limited number of requests
cache = lcs.S3FIFO(cache_size=1024*1024)
obj_miss_ratio, byte_miss_ratio = cache.process_trace(
    reader,
    start_req=0,
    max_req=1000
)
print(f"Object miss ratio: {obj_miss_ratio:.4f}, Byte miss ratio: {byte_miss_ratio:.4f}")