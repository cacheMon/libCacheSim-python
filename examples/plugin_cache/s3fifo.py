# An example of plugin for s3fifo
from collections import OrderedDict
from libcachesim import PluginCache, CommonCacheParams, Request, S3FIFO, SyntheticReader

# NOTE(haocheng): we only support ignore object size for now
class StandaloneS3FIFO:
    def __init__(self,
                 small_size_ratio: float = 0.1,
                 ghost_size_ratio: float = 0.9,
                 move_to_main_threshold: int = 2,
                 cache_size: int = 1024):
        # S3-FIFO uses three queues with OrderedDict for O(1) operations
        self.small_fifo = OrderedDict()
        self.main_fifo = OrderedDict()
        self.ghost_fifo = OrderedDict()
        
        # Size limits
        self.small_max_size = int(small_size_ratio * cache_size)
        self.main_max_size = int(cache_size - small_size_ratio * cache_size)
        self.ghost_max_size = int(ghost_size_ratio * cache_size)
        
        # Frequency tracking
        self.small_freq = {}
        self.main_freq = {}
        self.ghost_freq = {}
        
        # Other parameters
        self.max_freq = 3
        self.move_to_main_threshold = move_to_main_threshold

    def cache_hit(self, obj_id):
        """
        Cache hit can happen in two cases:
        1. Small FIFO cache hit (small_fifo)
        2. Main FIFO cache hit (main_fifo)
        """
        if obj_id in self.main_fifo:
            self.main_freq[obj_id] += 1
        elif obj_id in self.small_fifo:
            self.small_freq[obj_id] += 1
        else:
            print(f"Cache hit for obj_id {obj_id} but not found in any queue")
            print(f"small_fifo: {list(self.small_fifo.keys())}")
            print(f"main_fifo: {list(self.main_fifo.keys())}")
            print(f"ghost_fifo: {list(self.ghost_fifo.keys())}")
            assert False, "Cache hit should happen in small_fifo or main_fifo"
    
    def cache_miss(self, obj_id, obj_size=1):
        """
        Cache miss can happen in three cases:
        1. Miss in small and main but hit in ghost
        2. Miss all three queues
        """
        if obj_id in self.ghost_fifo:
            del self.ghost_fifo[obj_id]
            del self.ghost_freq[obj_id]
            self.insert_to_main(obj_id)
        else:
            # Miss all three queues
            cond = (obj_id not in self.small_fifo) and (obj_id not in self.main_fifo)
            assert cond, "Should not be in small_fifo or main_fifo"

            # Then we need to insert to small fifo queue
            self.insert_to_small(obj_id)

    def insert_to_small(self, obj_id):
        if len(self.small_fifo) >= self.small_max_size:
            self.cache_evict_small()
        self.small_fifo[obj_id] = None  # OrderedDict value doesn't matter
        self.small_freq[obj_id] = 0

    def insert_to_main(self, obj_id):
        if len(self.main_fifo) >= self.main_max_size:
            self.cache_evict_main()
        self.main_fifo[obj_id] = None
        self.main_freq[obj_id] = 0
    
    def insert_to_ghost(self, obj_id, original_freq=0):
        if len(self.ghost_fifo) >= self.ghost_max_size:
            # Remove oldest item
            oldest_id = next(iter(self.ghost_fifo))
            del self.ghost_fifo[oldest_id]
            del self.ghost_freq[oldest_id]
        self.ghost_fifo[obj_id] = None
        self.ghost_freq[obj_id] = original_freq
    
    def cache_evict_small(self):
        has_evicted = False
        evicted_id = None
        while not has_evicted and len(self.small_fifo) > 0:
            obj_to_evict = next(iter(self.small_fifo))  # Get first item
            if self.small_freq[obj_to_evict] >= self.move_to_main_threshold:
                # Move to main fifo cache (not real evict, just move)
                del self.small_fifo[obj_to_evict]
                del self.small_freq[obj_to_evict]
                self.insert_to_main(obj_to_evict)
            else:
                evicted_id = obj_to_evict
                # Insert to ghost fifo cache (real evict)
                del self.small_fifo[obj_to_evict]
                del self.small_freq[obj_to_evict]
                self.insert_to_ghost(obj_to_evict)
                has_evicted = True
        return evicted_id
    
    def cache_evict_main(self):
        has_evicted = False
        evicted_id = None
        while not has_evicted and len(self.main_fifo) > 0:
            obj_to_evict = next(iter(self.main_fifo))  # Get first item
            freq = self.main_freq[obj_to_evict]
            if freq >= 1:
                # Reinsert with decremented frequency
                del self.main_fifo[obj_to_evict]
                del self.main_freq[obj_to_evict]
                self.insert_to_main(obj_to_evict)
                self.main_freq[obj_to_evict] = min(freq, self.max_freq) - 1
            else:
                evicted_id = obj_to_evict
                # Real eviction
                del self.main_fifo[obj_to_evict]
                del self.main_freq[obj_to_evict]
                has_evicted = True
        return evicted_id

    def cache_evict(self):
        evicted_id = None
        # if main is full or small is empty, evict main
        if len(self.main_fifo) >= self.main_max_size or len(self.small_fifo) == 0:
            evicted_id = self.cache_evict_main()
        # if small is not empty, evict small
        else:
            evicted_id = self.cache_evict_small()
        if evicted_id is None:
            assert False, "Should not be None"
        return evicted_id

    def cache_remove(self, obj_id):
        removed = False
        if obj_id in self.small_fifo:
            del self.small_fifo[obj_id]
            del self.small_freq[obj_id]
            removed = True
        elif obj_id in self.ghost_fifo:
            del self.ghost_fifo[obj_id]
            del self.ghost_freq[obj_id]
            removed = True
        elif obj_id in self.main_fifo:
            del self.main_fifo[obj_id]
            del self.main_freq[obj_id]
            removed = True
        return removed
    
def cache_init_hook(common_cache_params: CommonCacheParams):
    return StandaloneS3FIFO(cache_size=common_cache_params.cache_size)

def cache_hit_hook(cache, request: Request):
    cache.cache_hit(request.obj_id)

def cache_miss_hook(cache, request: Request):
    cache.cache_miss(request.obj_id, request.obj_size)

def cache_eviction_hook(cache, request: Request):
    # NOTE(haocheng): never called
    pass

def cache_remove_hook(cache, obj_id):
    cache.cache_remove(obj_id)

def cache_free_hook(cache):
    cache.small_fifo.clear()
    cache.small_freq.clear()
    cache.ghost_fifo.clear()
    cache.ghost_freq.clear()
    cache.main_fifo.clear()
    cache.main_freq.clear()

cache = PluginCache(
    cache_size=1024*1024,
    cache_init_hook=cache_init_hook,
    cache_hit_hook=cache_hit_hook,
    cache_miss_hook=cache_miss_hook,
    cache_eviction_hook=cache_eviction_hook,
    cache_remove_hook=cache_remove_hook,
    cache_free_hook=cache_free_hook,
    cache_name="S3FIFO")

ref_s3fifo = S3FIFO(cache_size=1024)

reader = SyntheticReader(
    num_of_req=1000000,
    num_objects=100,
    obj_size=1,
    seed=42,
    alpha=0.8,
    dist="zipf",
)

for req in reader:
    plugin_hit = cache.get(req)
    ref_hit = ref_s3fifo.get(req)
    assert plugin_hit == ref_hit, f"Cache hit mismatch: {plugin_hit} != {ref_hit}"

print("All requests processed successfully. Plugin cache matches reference S3FIFO cache.")