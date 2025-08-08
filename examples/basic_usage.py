import libcachesim as lcs

# Step 1: Open a trace hosted on S3 (find more via https://github.com/cacheMon/cache_dataset)
URI = "s3://cache-datasets/cache_dataset_oracleGeneral/2007_msr/msr_hm_0.oracleGeneral.zst"
reader = lcs.TraceReader(
    trace=URI,
    trace_type=lcs.TraceType.ORACLE_GENERAL_TRACE,
    reader_init_params=lcs.ReaderInitParam(ignore_obj_size=False),
)

# Step 2: Initialize cache
cache = lcs.S3FIFO(
    cache_size=1024 * 1024,
    # Cache specific parameters
    small_size_ratio=0.2,
    ghost_size_ratio=0.8,
    move_to_main_threshold=2,
)

# Step 3: Process entire trace efficiently (C++ backend)
req_miss_ratio, byte_miss_ratio = cache.process_trace(reader)
print(f"Request miss ratio: {req_miss_ratio:.4f}, Byte miss ratio: {byte_miss_ratio:.4f}")

# Step 3.1: Process the first 1000 requests
cache = lcs.S3FIFO(
    cache_size=1024 * 1024,
    # Cache specific parameters
    small_size_ratio=0.2,
    ghost_size_ratio=0.8,
    move_to_main_threshold=2,
)
req_miss_ratio, byte_miss_ratio = cache.process_trace(reader, start_req=0, max_req=1000)
print(f"Request miss ratio: {req_miss_ratio:.4f}, Byte miss ratio: {byte_miss_ratio:.4f}")
