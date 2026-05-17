import pytest
import libcachesim as lcs
import threading
import time

S3_URI = "s3://cache-datasets/cache_dataset_oracleGeneral/2007_msr/msr_hm_0.oracleGeneral.zst"

def run_heavy_simulation(name):
    # Create a large synthetic trace
    reader = lcs.TraceReader(trace=S3_URI)
    cache = lcs.LRU(cache_size=1024*1024)

    print(f"Thread {name} starting simulation...")
    start = time.time()
    # Call C++ core logic
    lcs.Util.process_trace(cache, reader)
    end = time.time()
    print(f"Thread {name} completed in {end - start:.2f}s")

def test_gil_release():
    """
    Test to verify that the GIL is released during heavy C++ processing.
    We run two threads that perform heavy simulations and measure total time.
    If the total time is close to the single-thread time, it indicates GIL release.
    If the total time is close to double the single-thread time, it indicates GIL is still held.
    """
    # --- Experiment start ---

    # test single-thread time for reference
    start_single = time.time()
    run_heavy_simulation("Single")
    end_single = time.time()
    single_thread_time = end_single - start_single
    print(f"\nSingle-thread time: {single_thread_time:.2f}s")

    start_total = time.time()

    t1 = threading.Thread(target=run_heavy_simulation, args=("A",))
    t2 = threading.Thread(target=run_heavy_simulation, args=("B",))

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    end_total = time.time()
    print(f"\nTotal elapsed time: {end_total - start_total:.2f}s")

    assert single_thread_time * 1.5 > (end_total - start_total), "GIL release test failed: Total time should be close to single-thread time if GIL is released."
