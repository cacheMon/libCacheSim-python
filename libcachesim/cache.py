from abc import ABC
from typing import Callable, Optional
from .libcachesim_python import (
    CommonCacheParams,
    Request,
    CacheObject,
    Cache,
    # Core cache algorithms
    LHD_init,
    LRU_init,
    FIFO_init,
    LFU_init,
    ARC_init,
    Clock_init,
    Random_init,
    LIRS_init,
    TwoQ_init,
    SLRU_init,
    # Advanced algorithms
    S3FIFO_init,
    Sieve_init,
    WTinyLFU_init,
    LeCaR_init,
    LFUDA_init,
    ClockPro_init,
    Cacheus_init,
    # Optimal algorithms
    Belady_init,
    BeladySize_init,
    # Probabilistic algorithms
    LRU_Prob_init,
    flashProb_init,
    # Size-based algorithms
    Size_init,
    GDSF_init,
    # Hyperbolic algorithms
    Hyperbolic_init,
    # Plugin cache
    pypluginCache_init,
    # Process trace function
    c_process_trace,
)

from .protocols import ReaderProtocol


class CacheBase(ABC):
    """Base class for all cache implementations"""

    _cache: Cache  # Internal C++ cache object

    def __init__(self, _cache: Cache):
        self._cache = _cache

    def get(self, req: Request) -> bool:
        return self._cache.get(req)

    def find(self, req: Request, update_cache: bool = True) -> Optional[CacheObject]:
        return self._cache.find(req, update_cache)

    def can_insert(self, req: Request) -> bool:
        return self._cache.can_insert(req)

    def insert(self, req: Request) -> CacheObject:
        return self._cache.insert(req)

    def need_eviction(self, req: Request) -> bool:
        return self._cache.need_eviction(req)

    def evict(self, req: Request) -> CacheObject:
        return self._cache.evict(req)

    def remove(self, obj_id: int) -> bool:
        return self._cache.remove(obj_id)

    def to_evict(self, req: Request) -> CacheObject:
        return self._cache.to_evict(req)

    def get_occupied_byte(self) -> int:
        return self._cache.get_occupied_byte()

    def get_n_obj(self) -> int:
        return self._cache.get_n_obj()
    
    def set_cache_size(self, new_size: int) -> None:
        self._cache.set_cache_size(new_size)

    def print_cache(self) -> str:
        return self._cache.print_cache()

    def process_trace(self, reader: ReaderProtocol, start_req: int = 0, max_req: int = -1) -> tuple[float, float]:
        """Process trace with this cache and return miss ratios"""
        if hasattr(reader, "c_reader") and reader.c_reader:
            # C++ reader with _reader attribute
            if hasattr(reader, "_reader"):
                return c_process_trace(self._cache, reader._reader, start_req, max_req)
            else:
                raise ValueError("C++ reader missing _reader attribute")
        else:
            # Python reader - use Python implementation
            return self._process_trace_python(reader, start_req, max_req)

    def _process_trace_python(
        self, reader: ReaderProtocol, start_req: int = 0, max_req: int = -1
    ) -> tuple[float, float]:
        """Python fallback for processing traces"""
        reader.reset()
        if start_req > 0:
            reader.skip_n_req(start_req)

        n_req = 0
        n_hit = 0
        bytes_req = 0
        bytes_hit = 0

        for req in reader:
            if not req.valid:
                break

            n_req += 1
            bytes_req += req.obj_size

            if self.get(req):
                n_hit += 1
                bytes_hit += req.obj_size

            if max_req > 0 and n_req >= max_req:
                break

        obj_miss_ratio = 1.0 - (n_hit / n_req) if n_req > 0 else 0.0
        byte_miss_ratio = 1.0 - (bytes_hit / bytes_req) if bytes_req > 0 else 0.0
        return obj_miss_ratio, byte_miss_ratio

    # Properties
    @property
    def cache_size(self) -> int:
        return self._cache.cache_size

    @property
    def cache_name(self) -> str:
        return self._cache.cache_name


def _create_common_params(
    cache_size: int, default_ttl: int = 86400 * 300, hashpower: int = 24, consider_obj_metadata: bool = False
) -> CommonCacheParams:
    """Helper to create common cache parameters"""
    return CommonCacheParams(
        cache_size=cache_size,
        default_ttl=default_ttl,
        hashpower=hashpower,
        consider_obj_metadata=consider_obj_metadata,
    )


# ------------------------------------------------------------------------------------------------
# Core cache algorithms
# ------------------------------------------------------------------------------------------------
class LHD(CacheBase):
    """Least Hit Density cache (no special parameters)"""

    def __init__(
        self, cache_size: int, default_ttl: int = 86400 * 300, hashpower: int = 24, consider_obj_metadata: bool = False
    ):
        super().__init__(
            _cache=LHD_init(_create_common_params(cache_size, default_ttl, hashpower, consider_obj_metadata))
        )


class LRU(CacheBase):
    """Least Recently Used cache (no special parameters)"""

    def __init__(
        self, cache_size: int, default_ttl: int = 86400 * 300, hashpower: int = 24, consider_obj_metadata: bool = False
    ):
        super().__init__(
            _cache=LRU_init(_create_common_params(cache_size, default_ttl, hashpower, consider_obj_metadata))
        )


class FIFO(CacheBase):
    """First In First Out cache (no special parameters)"""

    def __init__(
        self, cache_size: int, default_ttl: int = 86400 * 300, hashpower: int = 24, consider_obj_metadata: bool = False
    ):
        super().__init__(
            _cache=FIFO_init(_create_common_params(cache_size, default_ttl, hashpower, consider_obj_metadata))
        )


class LFU(CacheBase):
    """Least Frequently Used cache (no special parameters)"""

    def __init__(
        self, cache_size: int, default_ttl: int = 86400 * 300, hashpower: int = 24, consider_obj_metadata: bool = False
    ):
        super().__init__(
            _cache=LFU_init(_create_common_params(cache_size, default_ttl, hashpower, consider_obj_metadata))
        )


class ARC(CacheBase):
    """Adaptive Replacement Cache (no special parameters)"""

    def __init__(
        self, cache_size: int, default_ttl: int = 86400 * 300, hashpower: int = 24, consider_obj_metadata: bool = False
    ):
        super().__init__(
            _cache=ARC_init(_create_common_params(cache_size, default_ttl, hashpower, consider_obj_metadata))
        )


class Clock(CacheBase):
    """Clock replacement algorithm

    Special parameters:
    init_freq: initial frequency of the object (default: 0)
    n_bit_counter: number of bits for the counter (default: 1)
    """

    def __init__(
        self,
        cache_size: int,
        default_ttl: int = 86400 * 300,
        hashpower: int = 24,
        consider_obj_metadata: bool = False,
        init_freq: int = 0,
        n_bit_counter: int = 1,
    ):
        cache_specific_params = f"init-freq={init_freq}, n-bit-counter={n_bit_counter}"
        super().__init__(
            _cache=Clock_init(
                _create_common_params(cache_size, default_ttl, hashpower, consider_obj_metadata), cache_specific_params
            )
        )


class Random(CacheBase):
    """Random replacement cache (no special parameters)"""

    def __init__(
        self, cache_size: int, default_ttl: int = 86400 * 300, hashpower: int = 24, consider_obj_metadata: bool = False
    ):
        super().__init__(
            _cache=Random_init(_create_common_params(cache_size, default_ttl, hashpower, consider_obj_metadata))
        )


# Advanced algorithms
class S3FIFO(CacheBase):
    """S3-FIFO cache algorithm

    Special parameters:
    small_size_ratio: ratio of small cache size to total cache size (default: 0.1)
    ghost_size_ratio: ratio of ghost cache size to total cache size (default: 0.9)
    move_to_main_threshold: threshold for moving objects from ghost to main cache (default: 2)
    """

    def __init__(
        self,
        cache_size: int,
        default_ttl: int = 86400 * 300,
        hashpower: int = 24,
        consider_obj_metadata: bool = False,
        small_size_ratio: float = 0.1,
        ghost_size_ratio: float = 0.9,
        move_to_main_threshold: int = 2,
    ):
        cache_specific_params = f"small-size-ratio={small_size_ratio}, ghost-size-ratio={ghost_size_ratio}, move-to-main-threshold={move_to_main_threshold}"
        super().__init__(
            _cache=S3FIFO_init(
                _create_common_params(cache_size, default_ttl, hashpower, consider_obj_metadata), cache_specific_params
            )
        )


class Sieve(CacheBase):
    """Sieve cache algorithm (no special parameters)"""

    def __init__(
        self, cache_size: int, default_ttl: int = 86400 * 300, hashpower: int = 24, consider_obj_metadata: bool = False
    ):
        super().__init__(
            _cache=Sieve_init(_create_common_params(cache_size, default_ttl, hashpower, consider_obj_metadata))
        )


class LIRS(CacheBase):
    """Low Inter-reference Recency Set (no special parameters)"""

    def __init__(
        self, cache_size: int, default_ttl: int = 86400 * 300, hashpower: int = 24, consider_obj_metadata: bool = False
    ):
        super().__init__(
            _cache=LIRS_init(_create_common_params(cache_size, default_ttl, hashpower, consider_obj_metadata))
        )

    def insert(self, req: Request) -> Optional[CacheObject]:
        return super().insert(req)


class TwoQ(CacheBase):
    """2Q replacement algorithm

    Special parameters:
    a_in_size_ratio: ratio of Ain queue size to total cache size (default: 0.25)
    a_out_size_ratio: ratio of Aout queue size to total cache size (default: 0.5)
    """

    def __init__(
        self,
        cache_size: int,
        default_ttl: int = 86400 * 300,
        hashpower: int = 24,
        consider_obj_metadata: bool = False,
        a_in_size_ratio: float = 0.25,
        a_out_size_ratio: float = 0.5,
    ):
        cache_specific_params = f"Ain-size-ratio={a_in_size_ratio}, Aout-size-ratio={a_out_size_ratio}"
        super().__init__(
            _cache=TwoQ_init(
                _create_common_params(cache_size, default_ttl, hashpower, consider_obj_metadata), cache_specific_params
            )
        )


class SLRU(CacheBase):
    """Segmented LRU (no special parameters)"""

    def __init__(
        self, cache_size: int, default_ttl: int = 86400 * 300, hashpower: int = 24, consider_obj_metadata: bool = False
    ):
        super().__init__(
            _cache=SLRU_init(_create_common_params(cache_size, default_ttl, hashpower, consider_obj_metadata))
        )


class WTinyLFU(CacheBase):
    """Window TinyLFU

    Special parameters:
    main_cache: the type of the main cache (default: "SLRU")
    window_size: ratio of the window size to the main cache size (default: 0.01)
    """

    def __init__(
        self,
        cache_size: int,
        default_ttl: int = 86400 * 300,
        hashpower: int = 24,
        consider_obj_metadata: bool = False,
        main_cache: str = "SLRU",
        window_size: float = 0.01,
    ):
        cache_specific_params = f"main-cache={main_cache}, window-size={window_size}"
        super().__init__(
            _cache=WTinyLFU_init(
                _create_common_params(cache_size, default_ttl, hashpower, consider_obj_metadata), cache_specific_params
            )
        )


class LeCaR(CacheBase):
    """Learning Cache Replacement

    Special parameters:
    update_weight (bool): whether to update the weight (default: True)
    lru_weight (float): the initial weight (probability) of the LRU (default: 0.5), 1 - lru_weight = lfu_weight, i.e, the probability of the LRU being selected
    """

    def __init__(
        self,
        cache_size: int,
        default_ttl: int = 86400 * 300,
        hashpower: int = 24,
        consider_obj_metadata: bool = False,
        update_weight: bool = True,
        lru_weight: float = 0.5,
    ):
        cache_specific_params = f"update-weight={int(update_weight)}, lru-weight={lru_weight}"
        super().__init__(
            _cache=LeCaR_init(
                _create_common_params(cache_size, default_ttl, hashpower, consider_obj_metadata), cache_specific_params
            )
        )


class LFUDA(CacheBase):
    """LFU with Dynamic Aging (no special parameters)"""

    def __init__(
        self, cache_size: int, default_ttl: int = 86400 * 300, hashpower: int = 24, consider_obj_metadata: bool = False
    ):
        super().__init__(
            _cache=LFUDA_init(_create_common_params(cache_size, default_ttl, hashpower, consider_obj_metadata))
        )


class ClockPro(CacheBase):
    """Clock-Pro replacement algorithm

    Special parameters:
    init_ref: initial reference count (default: 0)
    init_ratio_cold: initial ratio of cold pages (default: 1)
    """

    def __init__(
        self,
        cache_size: int,
        default_ttl: int = 86400 * 300,
        hashpower: int = 24,
        consider_obj_metadata: bool = False,
        init_ref: int = 0,
        init_ratio_cold: float = 0.5,
    ):
        cache_specific_params = f"init-ref={init_ref}, init-ratio-cold={init_ratio_cold}"
        super().__init__(
            _cache=ClockPro_init(
                _create_common_params(cache_size, default_ttl, hashpower, consider_obj_metadata), cache_specific_params
            )
        )


class Cacheus(CacheBase):
    """Cacheus algorithm (no special parameters)"""

    def __init__(
        self, cache_size: int, default_ttl: int = 86400 * 300, hashpower: int = 24, consider_obj_metadata: bool = False
    ):
        super().__init__(
            _cache=Cacheus_init(_create_common_params(cache_size, default_ttl, hashpower, consider_obj_metadata))
        )


# Optimal algorithms
class Belady(CacheBase):
    """Belady's optimal algorithm (no special parameters)"""

    def __init__(
        self, cache_size: int, default_ttl: int = 86400 * 300, hashpower: int = 24, consider_obj_metadata: bool = False
    ):
        super().__init__(
            _cache=Belady_init(_create_common_params(cache_size, default_ttl, hashpower, consider_obj_metadata))
        )


class BeladySize(CacheBase):
    """Belady's optimal algorithm with size consideration

    Special parameters:
    n_samples: number of samples for the size consideration (default: 128)
    """

    def __init__(
        self,
        cache_size: int,
        default_ttl: int = 86400 * 300,
        hashpower: int = 24,
        consider_obj_metadata: bool = False,
        n_samples: int = 128,
    ):
        cache_specific_params = f"n-samples={n_samples}"
        super().__init__(
            _cache=BeladySize_init(
                _create_common_params(cache_size, default_ttl, hashpower, consider_obj_metadata), cache_specific_params
            )
        )


class LRUProb(CacheBase):
    """LRU with Probabilistic Replacement

    Special parameters:
    prob: probability of promoting an object to the head of the queue (default: 0.5)
    """

    def __init__(
        self,
        cache_size: int,
        default_ttl: int = 86400 * 300,
        hashpower: int = 24,
        consider_obj_metadata: bool = False,
        prob: float = 0.5,
    ):
        cache_specific_params = f"prob={prob}"
        super().__init__(
            _cache=LRU_Prob_init(
                _create_common_params(cache_size, default_ttl, hashpower, consider_obj_metadata), cache_specific_params
            )
        )


class FlashProb(CacheBase):
    """FlashProb replacement algorithm

    Special parameters:
    ram_size_ratio: ratio of the RAM size to the total cache size (default: 0.05)
    disk_admit_prob: probability of admitting a disk page to the RAM (default: 0.2)
    ram_cache: the type of the RAM cache (default: "LRU")
    disk_cache: the type of the disk cache (default: "FIFO")
    """

    def __init__(
        self,
        cache_size: int,
        default_ttl: int = 86400 * 300,
        hashpower: int = 24,
        consider_obj_metadata: bool = False,
        ram_size_ratio: float = 0.05,
        disk_admit_prob: float = 0.2,
        ram_cache: str = "LRU",
        disk_cache: str = "FIFO",
    ):
        cache_specific_params = f"ram-size-ratio={ram_size_ratio}, disk-admit-prob={disk_admit_prob}, ram-cache={ram_cache}, disk-cache={disk_cache}"
        super().__init__(
            _cache=flashProb_init(
                _create_common_params(cache_size, default_ttl, hashpower, consider_obj_metadata), cache_specific_params
            )
        )


class Size(CacheBase):
    """Size-based replacement algorithm (no special parameters)"""

    def __init__(
        self, cache_size: int, default_ttl: int = 86400 * 300, hashpower: int = 24, consider_obj_metadata: bool = False
    ):
        super().__init__(
            _cache=Size_init(_create_common_params(cache_size, default_ttl, hashpower, consider_obj_metadata))
        )


class GDSF(CacheBase):
    """GDSF replacement algorithm (no special parameters)"""

    def __init__(
        self, cache_size: int, default_ttl: int = 86400 * 300, hashpower: int = 24, consider_obj_metadata: bool = False
    ):
        super().__init__(
            _cache=GDSF_init(_create_common_params(cache_size, default_ttl, hashpower, consider_obj_metadata))
        )


class Hyperbolic(CacheBase):
    """Hyperbolic replacement algorithm (no special parameters)"""

    def __init__(
        self, cache_size: int, default_ttl: int = 86400 * 300, hashpower: int = 24, consider_obj_metadata: bool = False
    ):
        super().__init__(
            _cache=Hyperbolic_init(_create_common_params(cache_size, default_ttl, hashpower, consider_obj_metadata))
        )


# Extra deps
class ThreeLCache(CacheBase):
    """Three-Level Cache

    Special parameters:
    objective: the objective of the ThreeLCache (default: "byte-miss-ratio")
    """

    def __init__(
        self,
        cache_size: int,
        default_ttl: int = 86400 * 300,
        hashpower: int = 24,
        consider_obj_metadata: bool = False,
        objective: str = "byte-miss-ratio",
    ):
        # Try to import ThreeLCache_init
        try:
            from .libcachesim_python import ThreeLCache_init
        except ImportError:
            raise ImportError(
                'ThreeLCache is not installed. Please install it with `CMAKE_ARGS="-DENABLE_3L_CACHE=ON" pip install libcachesim --force-reinstall`'
            )

        cache_specific_params = f"objective={objective}"
        super().__init__(
            _cache=ThreeLCache_init(
                _create_common_params(cache_size, default_ttl, hashpower, consider_obj_metadata), cache_specific_params
            )
        )


class GLCache(CacheBase):
    """GLCache replacement algorithm

    Special parameters:
    segment-size: the size of the segment (default: 100)
    n-merge: the number of merges (default: 2)
    type: the type of the GLCache (default: "learned")
    rank-intvl: the interval for ranking (default: 0.02)
    merge-consecutive-segs: whether to merge consecutive segments (default: True)
    train-source-y: the source of the training data (default: "online")
    retrain-intvl: the interval for retraining (default: 86400)
    """

    def __init__(
        self,
        cache_size: int,
        default_ttl: int = 86400 * 300,
        hashpower: int = 24,
        consider_obj_metadata: bool = False,
        segment_size: int = 100,
        n_merge: int = 2,
        type: str = "learned",
        rank_intvl: float = 0.02,
        merge_consecutive_segs: bool = True,
        train_source_y: str = "online",
        retrain_intvl: int = 86400,
    ):
        # Try to import GLCache_init
        try:
            from .libcachesim_python import GLCache_init
        except ImportError:
            raise ImportError(
                'GLCache is not installed. Please install it with `CMAKE_ARGS="-DENABLE_GLCACHE=ON" pip install libcachesim --force-reinstall`'
            )

        cache_specific_params = f"segment-size={segment_size}, n-merge={n_merge}, type={type}, rank-intvl={rank_intvl}, merge-consecutive-segs={merge_consecutive_segs}, train-source-y={train_source_y}, retrain-intvl={retrain_intvl}"
        super().__init__(
            _cache=GLCache_init(
                _create_common_params(cache_size, default_ttl, hashpower, consider_obj_metadata), cache_specific_params
            )
        )


class LRB(CacheBase):
    """LRB replacement algorithm

    Special parameters:
    objective: the objective of the LRB (default: "byte-miss-ratio")
    """

    def __init__(
        self,
        cache_size: int,
        default_ttl: int = 86400 * 300,
        hashpower: int = 24,
        consider_obj_metadata: bool = False,
        objective: str = "byte-miss-ratio",
    ):
        # Try to import LRB_init
        try:
            from .libcachesim_python import LRB_init
        except ImportError:
            raise ImportError(
                'LRB is not installed. Please install it with `CMAKE_ARGS="-DENABLE_LRB=ON" pip install libcachesim --force-reinstall`'
            )

        cache_specific_params = f"objective={objective}"
        super().__init__(
            _cache=LRB_init(
                _create_common_params(cache_size, default_ttl, hashpower, consider_obj_metadata), cache_specific_params
            )
        )


# Plugin cache for custom Python implementations
class PluginCache(CacheBase):
    """Python plugin cache for custom implementations"""

    def __init__(
        self,
        cache_size: int,
        cache_init_hook: Callable,
        cache_hit_hook: Callable,
        cache_miss_hook: Callable,
        cache_eviction_hook: Callable,
        cache_remove_hook: Callable,
        cache_free_hook: Optional[Callable] = None,
        cache_name: str = "PythonHookCache",
        default_ttl: int = 86400 * 300,
        hashpower: int = 24,
        consider_obj_metadata: bool = False,
    ):
        self.common_cache_params = _create_common_params(cache_size, default_ttl, hashpower, consider_obj_metadata)

        super().__init__(
            _cache=pypluginCache_init(
                self.common_cache_params,
                cache_name,
                cache_init_hook,
                cache_hit_hook,
                cache_miss_hook,
                cache_eviction_hook,
                cache_remove_hook,
                cache_free_hook,
            )
        )
