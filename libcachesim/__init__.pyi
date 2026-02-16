from __future__ import annotations
from typing import Optional, Callable, Any
from collections.abc import Iterator

from .libcachesim_python import ReqOp, TraceType, SamplerType
from .protocols import ReaderProtocol

class Request:
    clock_time: int
    hv: int
    obj_id: int
    obj_size: int
    ttl: int
    op: ReqOp
    valid: bool
    next_access_vtime: int

    def __init__(
        self,
        obj_size: int = 1,
        op: ReqOp = ReqOp.READ,
        valid: bool = True,
        obj_id: int = 0,
        clock_time: int = 0,
        hv: int = 0,
        next_access_vtime: int = -2,
        ttl: int = 0,
    ): ...
    def __init__(self): ...

class CacheObject:
    obj_id: int
    obj_size: int

class CommonCacheParams:
    cache_size: int
    default_ttl: int
    hashpower: int
    consider_obj_metadata: bool

class ReaderInitParam:
    ignore_obj_size: bool
    ignore_size_zero_req: bool
    obj_id_is_num: bool
    obj_id_is_num_set: bool
    cap_at_n_req: int
    time_field: int
    obj_id_field: int
    obj_size_field: int
    op_field: int
    ttl_field: int
    cnt_field: int
    tenant_field: int
    next_access_vtime_field: int
    n_feature_fields: int
    block_size: int
    has_header: bool
    has_header_set: bool
    delimiter: str
    trace_start_offset: int
    binary_fmt_str: str
    def __init__(
        self,
        binary_fmt_str: str = "",
        ignore_obj_size: bool = False,
        ignore_size_zero_req: bool = True,
        obj_id_is_num: bool = True,
        obj_id_is_num_set: bool = False,
        cap_at_n_req: int = -1,
        block_size: int = -1,
        has_header: bool = False,
        has_header_set: bool = False,
        delimiter: str = ",",
        trace_start_offset: int = 0,
        sampler: Optional[Any] = None,
    ): ...

class AnalysisParam:
    access_pattern_sample_ratio_inv: int
    track_n_popular: int
    track_n_hit: int
    time_window: int
    warmup_time: int
    def __init__(
        self,
        access_pattern_sample_ratio_inv: int = 10,
        track_n_popular: int = 10,
        track_n_hit: int = 5,
        time_window: int = 60,
        warmup_time: int = 0,
    ): ...

class AnalysisOption:
    req_rate: bool
    access_pattern: bool
    size: bool
    reuse: bool
    popularity: bool
    ttl: bool
    popularity_decay: bool
    lifetime: bool
    create_future_reuse_ccdf: bool
    prob_at_age: bool
    size_change: bool
    def __init__(
        self,
        req_rate: bool = True,
        access_pattern: bool = True,
        size: bool = True,
        reuse: bool = True,
        popularity: bool = True,
        ttl: bool = False,
        popularity_decay: bool = False,
        lifetime: bool = False,
        create_future_reuse_ccdf: bool = False,
        prob_at_age: bool = False,
        size_change: bool = False,
    ): ...

class Cache:
    cache_size: int
    default_ttl: int
    obj_md_size: int
    n_req: int
    cache_name: str
    init_params: CommonCacheParams

    def __init__(self, init_params: CommonCacheParams, cache_specific_params: str = ""): ...
    def get(self, req: Request) -> bool: ...
    def find(self, req: Request, update_cache: bool = True) -> CacheObject: ...
    def can_insert(self, req: Request) -> bool: ...
    def insert(self, req: Request) -> CacheObject: ...
    def need_eviction(self, req: Request) -> bool: ...
    def evict(self, req: Request) -> CacheObject: ...
    def remove(self, obj_id: int) -> bool: ...
    def to_evict(self, req: Request) -> CacheObject: ...
    def get_occupied_byte(self) -> int: ...
    def get_n_obj(self) -> int: ...
    def print_cache(self) -> str: ...

class CacheBase:
    """Base class for all cache implementations"""
    def __init__(self, _cache: Cache): ...
    def get(self, req: Request) -> bool: ...
    def find(self, req: Request, update_cache: bool = True) -> CacheObject: ...
    def can_insert(self, req: Request) -> bool: ...
    def insert(self, req: Request) -> CacheObject: ...
    def need_eviction(self, req: Request) -> bool: ...
    def evict(self, req: Request) -> CacheObject: ...
    def remove(self, obj_id: int) -> bool: ...
    def to_evict(self, req: Request) -> CacheObject: ...
    def get_occupied_byte(self) -> int: ...
    def get_n_obj(self) -> int: ...
    def print_cache(self) -> str: ...
    def process_trace(self, reader: ReaderProtocol, start_req: int = 0, max_req: int = -1) -> tuple[float, float]: ...
    @property
    def cache_size(self) -> int: ...
    @property
    def cache_name(self) -> str: ...

# Core cache algorithms
class LHD(CacheBase):
    def __init__(
        self, cache_size: int | float, default_ttl: int = 25920000, hashpower: int = 24, consider_obj_metadata: bool = False, admissioner: Optional["AdmissionerBase"] = None, reader: Optional[ReaderProtocol] = None
    ): ...

class LRU(CacheBase):
    def __init__(
        self, cache_size: int | float, default_ttl: int = 25920000, hashpower: int = 24, consider_obj_metadata: bool = False, admissioner: Optional["AdmissionerBase"] = None, reader: Optional[ReaderProtocol] = None
    ): ...

class FIFO(CacheBase):
    def __init__(
        self, cache_size: int | float, default_ttl: int = 25920000, hashpower: int = 24, consider_obj_metadata: bool = False, admissioner: Optional["AdmissionerBase"] = None, reader: Optional[ReaderProtocol] = None
    ): ...

class LFU(CacheBase):
    def __init__(
        self, cache_size: int | float, default_ttl: int = 25920000, hashpower: int = 24, consider_obj_metadata: bool = False, admissioner: Optional["AdmissionerBase"] = None, reader: Optional[ReaderProtocol] = None
    ): ...

class ARC(CacheBase):
    def __init__(
        self, cache_size: int | float, default_ttl: int = 25920000, hashpower: int = 24, consider_obj_metadata: bool = False, admissioner: Optional["AdmissionerBase"] = None, reader: Optional[ReaderProtocol] = None
    ): ...

class Clock(CacheBase):
    def __init__(
        self, cache_size: int | float, default_ttl: int = 25920000, hashpower: int = 24, consider_obj_metadata: bool = False, init_freq: int = 0, n_bit_counter: int = 1, admissioner: Optional["AdmissionerBase"] = None, reader: Optional[ReaderProtocol] = None
    ): ...

class Random(CacheBase):
    def __init__(
        self, cache_size: int | float, default_ttl: int = 25920000, hashpower: int = 24, consider_obj_metadata: bool = False, admissioner: Optional["AdmissionerBase"] = None, reader: Optional[ReaderProtocol] = None
    ): ...

# Advanced algorithms
class S3FIFO(CacheBase):
    def __init__(
        self, cache_size: int | float, default_ttl: int = 25920000, hashpower: int = 24, consider_obj_metadata: bool = False, small_size_ratio: float = 0.1, ghost_size_ratio: float = 0.9, move_to_main_threshold: int = 2, admissioner: Optional["AdmissionerBase"] = None, reader: Optional[ReaderProtocol] = None
    ): ...

class Sieve(CacheBase):
    def __init__(
        self, cache_size: int | float, default_ttl: int = 25920000, hashpower: int = 24, consider_obj_metadata: bool = False, admissioner: Optional["AdmissionerBase"] = None, reader: Optional[ReaderProtocol] = None
    ): ...

class LIRS(CacheBase):
    def __init__(
        self, cache_size: int | float, default_ttl: int = 25920000, hashpower: int = 24, consider_obj_metadata: bool = False, admissioner: Optional["AdmissionerBase"] = None, reader: Optional[ReaderProtocol] = None
    ): ...

class TwoQ(CacheBase):
    def __init__(
        self, cache_size: int | float, default_ttl: int = 25920000, hashpower: int = 24, consider_obj_metadata: bool = False, a_in_size_ratio: float = 0.25, a_out_size_ratio: float = 0.5, admissioner: Optional["AdmissionerBase"] = None, reader: Optional[ReaderProtocol] = None
    ): ...

class SLRU(CacheBase):
    def __init__(
        self, cache_size: int | float, default_ttl: int = 25920000, hashpower: int = 24, consider_obj_metadata: bool = False, admissioner: Optional["AdmissionerBase"] = None, reader: Optional[ReaderProtocol] = None
    ): ...

class WTinyLFU(CacheBase):
    def __init__(
        self, cache_size: int | float, default_ttl: int = 25920000, hashpower: int = 24, consider_obj_metadata: bool = False, main_cache: str = "SLRU", window_size: float = 0.01, admissioner: Optional["AdmissionerBase"] = None, reader: Optional[ReaderProtocol] = None
    ): ...

class LeCaR(CacheBase):
    def __init__(
        self, cache_size: int | float, default_ttl: int = 25920000, hashpower: int = 24, consider_obj_metadata: bool = False, update_weight: bool = True, lru_weight: float = 0.5, admissioner: Optional["AdmissionerBase"] = None, reader: Optional[ReaderProtocol] = None
    ): ...

class LFUDA(CacheBase):
    def __init__(
        self, cache_size: int | float, default_ttl: int = 25920000, hashpower: int = 24, consider_obj_metadata: bool = False, admissioner: Optional["AdmissionerBase"] = None, reader: Optional[ReaderProtocol] = None
    ): ...

class ClockPro(CacheBase):
    def __init__(
        self, cache_size: int | float, default_ttl: int = 25920000, hashpower: int = 24, consider_obj_metadata: bool = False, init_ref: int = 0, init_ratio_cold: float = 0.5, admissioner: Optional["AdmissionerBase"] = None, reader: Optional[ReaderProtocol] = None
    ): ...

class Cacheus(CacheBase):
    def __init__(
        self, cache_size: int | float, default_ttl: int = 25920000, hashpower: int = 24, consider_obj_metadata: bool = False, admissioner: Optional["AdmissionerBase"] = None, reader: Optional[ReaderProtocol] = None
    ): ...

# Optimal algorithms
class Belady(CacheBase):
    def __init__(
        self, cache_size: int | float, default_ttl: int = 25920000, hashpower: int = 24, consider_obj_metadata: bool = False, admissioner: Optional["AdmissionerBase"] = None, reader: Optional[ReaderProtocol] = None
    ): ...

class BeladySize(CacheBase):
    def __init__(
        self, cache_size: int | float, default_ttl: int = 25920000, hashpower: int = 24, consider_obj_metadata: bool = False, n_samples: int = 128, admissioner: Optional["AdmissionerBase"] = None, reader: Optional[ReaderProtocol] = None
    ): ...

# Probabilistic algorithms
class LRUProb(CacheBase):
    def __init__(
        self, cache_size: int | float, default_ttl: int = 25920000, hashpower: int = 24, consider_obj_metadata: bool = False, prob: float = 0.5, admissioner: Optional["AdmissionerBase"] = None, reader: Optional[ReaderProtocol] = None
    ): ...

class FlashProb(CacheBase):
    def __init__(
        self, cache_size: int | float, default_ttl: int = 25920000, hashpower: int = 24, consider_obj_metadata: bool = False, ram_size_ratio: float = 0.05, disk_admit_prob: float = 0.2, ram_cache: str = "LRU", disk_cache: str = "FIFO", admissioner: Optional["AdmissionerBase"] = None, reader: Optional[ReaderProtocol] = None
    ): ...

# Size-based algorithms
class Size(CacheBase):
    def __init__(
        self, cache_size: int | float, default_ttl: int = 25920000, hashpower: int = 24, consider_obj_metadata: bool = False, admissioner: Optional["AdmissionerBase"] = None, reader: Optional[ReaderProtocol] = None
    ): ...

class GDSF(CacheBase):
    def __init__(
        self, cache_size: int | float, default_ttl: int = 25920000, hashpower: int = 24, consider_obj_metadata: bool = False, admissioner: Optional["AdmissionerBase"] = None, reader: Optional[ReaderProtocol] = None
    ): ...

# Hyperbolic algorithms
class Hyperbolic(CacheBase):
    def __init__(
        self, cache_size: int | float, default_ttl: int = 25920000, hashpower: int = 24, consider_obj_metadata: bool = False, admissioner: Optional["AdmissionerBase"] = None, reader: Optional[ReaderProtocol] = None
    ): ...

# Extra deps
class ThreeLCache(CacheBase):
    def __init__(
        self, cache_size: int | float, default_ttl: int = 25920000, hashpower: int = 24, consider_obj_metadata: bool = False, objective: str = "byte-miss-ratio", admissioner: Optional["AdmissionerBase"] = None, reader: Optional[ReaderProtocol] = None
    ): ...

class GLCache(CacheBase):
    def __init__(
        self, cache_size: int | float, default_ttl: int = 25920000, hashpower: int = 24, consider_obj_metadata: bool = False, segment_size: int = 100, n_merge: int = 2, type: str = "learned", rank_intvl: float = 0.02, merge_consecutive_segs: bool = True, train_source_y: str = "online", retrain_intvl: int = 86400, admissioner: Optional["AdmissionerBase"] = None, reader: Optional[ReaderProtocol] = None
    ): ...

class LRB(CacheBase):
    def __init__(
        self, cache_size: int | float, default_ttl: int = 25920000, hashpower: int = 24, consider_obj_metadata: bool = False, objective: str = "byte-miss-ratio", admissioner: Optional["AdmissionerBase"] = None, reader: Optional[ReaderProtocol] = None
    ): ...

# Plugin cache
class PluginCache(CacheBase):
    def __init__(
        self,
        cache_size: int | float,
        cache_init_hook: Callable,
        cache_hit_hook: Callable,
        cache_miss_hook: Callable,
        cache_eviction_hook: Callable,
        cache_remove_hook: Callable,
        cache_free_hook: Optional[Callable] = None,
        cache_name: str = "PythonHookCache",
        default_ttl: int = 25920000,
        hashpower: int = 24,
        consider_obj_metadata: bool = False,
        admissioner: Optional["AdmissionerBase"] = None,
        reader: Optional[ReaderProtocol] = None,
    ): ...
    def set_hooks(self, init_hook, hit_hook, miss_hook, eviction_hook, remove_hook, free_hook=None): ...

# Readers
class TraceReader(ReaderProtocol):
    c_reader: bool
    def __init__(self, trace: str, trace_type: TraceType = TraceType.UNKNOWN_TRACE, **kwargs): ...

class SyntheticReader(ReaderProtocol):
    c_reader: bool
    def __init__(
        self,
        num_of_req: int,
        obj_size: int = 4000,
        time_span: int = 604800,
        start_obj_id: int = 0,
        seed: int | None = None,
        alpha: float = 1.0,
        dist: str = "zipf",
        num_objects: int | None = None,
    ): ...

# Trace generators
def create_zipf_requests(
    num_objects: int,
    num_requests: int,
    alpha: float = 1.0,
    obj_size: int = 4000,
    time_span: int = 604800,
    start_obj_id: int = 0,
    seed: int | None = None,
) -> Iterator[Request]: ...
def create_uniform_requests(
    num_objects: int,
    num_requests: int,
    obj_size: int = 4000,
    time_span: int = 604800,
    start_obj_id: int = 0,
    seed: int | None = None,
) -> Iterator[Request]: ...

# Analyzer
class TraceAnalyzer:
    def __init__(self, analyzer, reader: ReaderProtocol, output_path: str, analysis_param, analysis_option): ...
    def run(self) -> None: ...
    def cleanup(self) -> None: ...

# Utilities
class Util:
    @staticmethod
    def convert_to_oracleGeneral(reader, ofilepath, output_txt: bool = False, remove_size_change: bool = False): ...
    @staticmethod
    def convert_to_lcs(
        reader, ofilepath, output_txt: bool = False, remove_size_change: bool = False, lcs_ver: int = 1
    ): ...
    @staticmethod
    def process_trace(
        cache: CacheBase, reader: ReaderProtocol, start_req: int = 0, max_req: int = -1
    ) -> tuple[float, float]: ...

# Admissioners
class AdmissionerBase:
    def __init__(self, _admissioner): ...
    def clone(self): ...
    def update(self, req: Request, cache_size: int): ...
    def admit(self, req: Request) -> bool: ...
    def free(self): ...

class BloomFilterAdmissioner(AdmissionerBase):
    def __init__(self): ...

class ProbAdmissioner(AdmissionerBase):
    def __init__(self, prob: Optional[float] = None): ...

class SizeAdmissioner(AdmissionerBase):
    def __init__(self, size_threshold: Optional[int] = None): ...

class SizeProbabilisticAdmissioner(AdmissionerBase):
    def __init__(self, exponent: Optional[float] = None): ...

class AdaptSizeAdmissioner(AdmissionerBase):
    def __init__(self, max_iteration: Optional[int] = None, reconf_interval: Optional[int] = None): ...

class PluginAdmissioner(AdmissionerBase):
    def __init__(
        self,
        admissioner_name: str,
        admissioner_init_hook: Callable,
        admissioner_admit_hook: Callable,
        admissioner_clone_hook: Callable,
        admissioner_update_hook: Callable,
        admissioner_free_hook: Callable,
    ): ...
