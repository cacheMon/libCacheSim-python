from libcachesim import BloomFilterAdmissioner, SyntheticReader, LRU

BloomFilter = BloomFilterAdmissioner()
lru_without_admission = LRU(
    cache_size=1024,
    # admissioner=BloomFilter
)
lru_with_admission = LRU(
    cache_size=1024,
    admissioner=BloomFilter
)

reader = SyntheticReader(
    num_of_req=100_000,
    num_objects=10_000,
    obj_size=100,
    alpha=0.8,
    dist="zipf",
)

without_admission_hits = 0
with_admission_hits = 0

for req in reader:
    if lru_without_admission.get(req):
        without_admission_hits += 1
    if lru_with_admission.get(req):
        with_admission_hits += 1

print(f'Obtained {without_admission_hits} without using cache admission')
print(f'Obtained {with_admission_hits} using cache admission')
