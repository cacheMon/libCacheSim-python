from collections import OrderedDict
from libcachesim import PluginCache, CommonCacheParams, Request, SyntheticReader, LRU


class StandaloneLRU:
    def __init__(self):
        self.cache_data = OrderedDict()

    def cache_hit(self, obj_id):
        if obj_id in self.cache_data:
            obj_size = self.cache_data.pop(obj_id)
            self.cache_data[obj_id] = obj_size

    def cache_miss(self, obj_id, obj_size):
        self.cache_data[obj_id] = obj_size

    def cache_eviction(self):
        evicted_id, _ = self.cache_data.popitem(last=False)
        return evicted_id

    def cache_remove(self, obj_id):
        if obj_id in self.cache_data:
            del self.cache_data[obj_id]


def cache_init_hook(common_cache_params: CommonCacheParams):
    return StandaloneLRU()


def cache_hit_hook(cache, request: Request):
    cache.cache_hit(request.obj_id)


def cache_miss_hook(cache, request: Request):
    cache.cache_miss(request.obj_id, request.obj_size)


def cache_eviction_hook(cache, request: Request):
    return cache.cache_eviction()


def cache_remove_hook(cache, obj_id):
    cache.cache_remove(obj_id)


def cache_free_hook(cache):
    cache.cache_data.clear()


plugin_lru_cache = PluginCache(
    cache_size=1024,
    cache_init_hook=cache_init_hook,
    cache_hit_hook=cache_hit_hook,
    cache_miss_hook=cache_miss_hook,
    cache_eviction_hook=cache_eviction_hook,
    cache_remove_hook=cache_remove_hook,
    cache_free_hook=cache_free_hook,
    cache_name="CustomizedLRU",
)

ref_lru_cache = LRU(cache_size=1024)

reader = SyntheticReader(
    num_of_req=100000,
    num_objects=10000,
    obj_size=100,
    seed=42,
    alpha=0.8,
    dist="zipf",
)

for req in reader:
    plugin_hit = plugin_lru_cache.get(req)
    ref_hit = ref_lru_cache.get(req)
    assert plugin_hit == ref_hit, f"Cache hit mismatch: {plugin_hit} != {ref_hit}"

print("All requests processed successfully. Plugin cache matches reference LRU cache.")
