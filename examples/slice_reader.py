import libcachesim as lcs
import logging
logging.basicConfig(level=logging.DEBUG)


URI = "s3://cache-datasets/cache_dataset_oracleGeneral/2007_msr/msr_hm_0.oracleGeneral.zst"
reader = lcs.TraceReader(
    trace = URI,
    trace_type = lcs.TraceType.ORACLE_GENERAL_TRACE,
    reader_init_params = lcs.ReaderInitParam(ignore_obj_size=False)
)

for req in reader[:3]:
    print(req.obj_id, req.obj_size)

for req in reader[1:4]:
    print(req.obj_id, req.obj_size)

reader.reset()
read_n_req = 4
for req in reader:
    if read_n_req <= 0:
        break
    print(req.obj_id, req.obj_size)
    read_n_req -= 1