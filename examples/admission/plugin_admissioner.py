from libcachesim import PluginAdmissioner, SyntheticReader, LRU
import random

'''
A toy example where we admit ten percent of all requests
at random. The admit rate is tracked and printed in the
free hook to serve as a final sanity check.
'''


class AdmissionerStats:
    admitted_requests: int = 0
    total_requests: int = 0


def init_hook():
    return AdmissionerStats()


def admit_hook(data, request):
    admit = random.randint(1, 10) == 5
    if admit:
        data.admitted_requests += 1
    data.total_requests += 1
    return admit


def clone_hook():
    pass


def update_hook(data, request, cs):
    pass


def free_hook(data):
    print(f'Admit rate: {100 * data.admitted_requests / data.total_requests}%')


custom_admissioner = PluginAdmissioner(
    "AdmitTenPercent",
    init_hook,
    admit_hook,
    clone_hook,
    update_hook,
    free_hook,
)
lru_cache = LRU(
    cache_size=1024,
    admissioner=custom_admissioner
)

reader = SyntheticReader(
    num_of_req=100_000,
    num_objects=10_000,
    obj_size=100,
    alpha=0.8,
    dist="zipf",
)

for req in reader:
    lru_cache.get(req)

# Invokes free_hook, percentage should be ~10%
del lru_cache
