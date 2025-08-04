# An example of plugin for s3fifo

# NOTE(haocheng): the one shows that with plugin system, we can make cache as lego blocks
# Happy caching!

import libcachesim as lcs
from collections import OrderedDict
from collections import deque
from libcachesim import PluginCache, CommonCacheParams, Request, S3FIFO, FIFO, SyntheticReader


# NOTE(haocheng): we only support ignore object size for now
class StandaloneS3FIFO:
    def __init__(
        self,
        small_size_ratio: float = 0.1,
        ghost_size_ratio: float = 0.9,
        move_to_main_threshold: int = 2,
        cache_size: int = 1024,
    ):
        self.cache_size = cache_size
        small_fifo_size = int(small_size_ratio * cache_size)
        main_fifo_size = cache_size - small_fifo_size
        ghost_fifo_size = int(ghost_size_ratio * cache_size)

        self.small_set = set()
        self.main_set = set()
        self.ghost_set = deque(maxlen=ghost_fifo_size)

        self.small_fifo = FIFO(small_fifo_size)
        self.main_fifo = FIFO(main_fifo_size)
        self.ghost_fifo = FIFO(ghost_fifo_size)

        # Frequency tracking
        self.freq = {}

        # Other parameters
        self.max_freq = 3
        self.move_to_main_threshold = move_to_main_threshold

        self.has_evicted = False  # Mark if we start to evict, only after full we will start eviction
        self.hit_on_ghost = False

    def cache_hit(self, req: Request):
        hit_small = False
        hit_main = False
        if self.small_fifo.find(req, update_cache=False):
            self.freq[req.obj_id] += 1

        if self.main_fifo.find(req, update_cache=False):
            self.freq[req.obj_id] += 1

    def cache_miss(self, req: Request):
        if not self.hit_on_ghost:
            obj = self.ghost_fifo.find(req, update_cache=False)
            if obj is not None:
                self.hit_on_ghost = True
                # remove from ghost set
                self.ghost_fifo.remove(req.obj_id)
                self.ghost_set.remove(req.obj_id)

        # NOTE(haocheng): first we need to know this miss object has record in ghost or not
        if not self.hit_on_ghost:
            if req.obj_size >= self.small_fifo.cache_size:
                # If object is too large, we do not process it
                return

            # If is initialization state, we need to insert to small fifo,
            # then we can insert to main fifo
            if not self.has_evicted and self.small_fifo.get_occupied_byte() >= self.small_fifo.cache_size:
                obj = self.main_fifo.insert(req)
                self.main_set.add(obj.obj_id)
            else:
                obj = self.small_fifo.insert(req)
                self.small_set.add(obj.obj_id)
        else:
            obj = self.main_fifo.insert(req)
            self.main_set.add(req.obj_id)
            self.hit_on_ghost = False
        self.freq[obj.obj_id] = 0

    def cache_evict_small(self, req: Request):
        has_evicted = False
        evicted_id = None
        real_evicted_id = None
        while not has_evicted and self.small_fifo.get_occupied_byte() > 0:
            obj_to_evict = self.small_fifo.to_evict(req)
            evicted_id = obj_to_evict.obj_id  # Store the ID before any operations
            if self.freq[obj_to_evict.obj_id] >= self.move_to_main_threshold:
                new_req = Request(obj_id=evicted_id, obj_size=1)
                self.main_fifo.insert(new_req)
                self.main_set.add(evicted_id)
                # Reset frequency
                self.freq[evicted_id] = 0
            else:
                new_req = Request(obj_id=evicted_id, obj_size=1)
                self.ghost_fifo.get(new_req)
                self.ghost_set.append(evicted_id)
                has_evicted = True
                real_evicted_id = evicted_id
            flag = self.small_fifo.remove(evicted_id)
            self.small_set.remove(evicted_id)
            assert flag, "Should be able to remove"
        return real_evicted_id

    def cache_evict_main(self, req: Request):
        has_evicted = False
        evicted_id = None
        while not has_evicted and self.main_fifo.get_occupied_byte() > 0:
            obj_to_evict = self.main_fifo.to_evict(req)
            assert obj_to_evict is not None
            evicted_id = obj_to_evict.obj_id  # Store the ID before any operations
            freq = self.freq[evicted_id]
            if freq >= 1:
                # Reinsert with decremented frequency
                self.main_fifo.remove(evicted_id)
                self.main_set.remove(evicted_id)
                new_req = Request(obj_id=evicted_id, obj_size=1)
                self.main_fifo.insert(new_req)
                self.main_set.add(evicted_id)
                self.freq[evicted_id] = min(freq, self.max_freq) - 1
            else:
                flag = self.main_fifo.remove(evicted_id)
                self.main_set.remove(evicted_id)
                has_evicted = True
            # print(f"Evicted {evicted_id}")
        return evicted_id

    def cache_evict(self, req: Request):
        if not self.hit_on_ghost:
            obj = self.ghost_fifo.find(req, update_cache=False)
            if obj is not None:
                self.hit_on_ghost = True
                # remove from ghost set
                self.ghost_fifo.remove(req.obj_id)
                self.ghost_set.remove(req.obj_id)

        self.has_evicted = True
        cond = self.main_fifo.get_occupied_byte() > self.main_fifo.cache_size
        if cond or (self.small_fifo.get_occupied_byte() == 0):
            obj_id = self.cache_evict_main(req)
        else:
            obj_id = self.cache_evict_small(req)

        if obj_id is not None:
            del self.freq[obj_id]

        return obj_id

    def cache_remove(self, obj_id):
        removed = False
        removed |= self.small_fifo.remove(obj_id)
        removed |= self.ghost_fifo.remove(obj_id)
        removed |= self.main_fifo.remove(obj_id)
        return removed


def cache_init_hook(common_cache_params: CommonCacheParams):
    return StandaloneS3FIFO(cache_size=common_cache_params.cache_size)


def cache_hit_hook(cache, request: Request):
    cache.cache_hit(request)


def cache_miss_hook(cache, request: Request):
    cache.cache_miss(request)


def cache_eviction_hook(cache, request: Request):
    evicted_id = None
    while evicted_id is None:
        evicted_id = cache.cache_evict(request)
    return evicted_id


def cache_remove_hook(cache, obj_id):
    cache.cache_remove(obj_id)


def cache_free_hook(cache):
    pass


cache = PluginCache(
    cache_size=1024,
    cache_init_hook=cache_init_hook,
    cache_hit_hook=cache_hit_hook,
    cache_miss_hook=cache_miss_hook,
    cache_eviction_hook=cache_eviction_hook,
    cache_remove_hook=cache_remove_hook,
    cache_free_hook=cache_free_hook,
    cache_name="S3FIFO",
)

URI = "cache_dataset_oracleGeneral/2007_msr/msr_hm_0.oracleGeneral.zst"
dl = lcs.DataLoader()
dl.load(URI)

# Step 2: Open trace and process efficiently
reader = lcs.TraceReader(
    trace=dl.get_cache_path(URI),
    trace_type=lcs.TraceType.ORACLE_GENERAL_TRACE,
    reader_init_params=lcs.ReaderInitParam(ignore_obj_size=True),
)

ref_s3fifo = S3FIFO(cache_size=1024, small_size_ratio=0.1, ghost_size_ratio=0.9, move_to_main_threshold=2)

# for req in reader:
#     hit = cache.get(req)
#     ref_hit = ref_s3fifo.get(req)
#     assert hit == ref_hit, f"Cache hit mismatch: {hit} != {ref_hit}"

req_miss_ratio, byte_miss_ratio = cache.process_trace(reader)
ref_req_miss_ratio, ref_byte_miss_ratio = ref_s3fifo.process_trace(reader)
print(f"Plugin req miss ratio: {req_miss_ratio}, ref req miss ratio: {ref_req_miss_ratio}")
print(f"Plugin byte miss ratio: {byte_miss_ratio}, ref byte miss ratio: {ref_byte_miss_ratio}")

assert req_miss_ratio == ref_req_miss_ratio
assert byte_miss_ratio == ref_byte_miss_ratio
print("All requests processed successfully. Plugin cache matches reference S3FIFO cache.")
