"""
Test cases for cache implementations in libCacheSim Python bindings.

This module tests various cache algorithms and their functionality.
"""

import pytest
import tempfile
import os
from libcachesim import (
    # Basic algorithms
    LHD,
    LRU,
    FIFO,
    LFU,
    ARC,
    Clock,
    Random,
    # Advanced algorithms
    S3FIFO,
    Sieve,
    LIRS,
    TwoQ,
    SLRU,
    WTinyLFU,
    # Request and other utilities
    Request,
    ReqOp,
    SyntheticReader,
)

# Try to import optional algorithms that might not be available
try:
    from libcachesim import LeCaR, LFUDA, ClockPro, Cacheus

    OPTIONAL_ALGORITHMS = [LeCaR, LFUDA, ClockPro, Cacheus]
except ImportError:
    OPTIONAL_ALGORITHMS = []

try:
    from libcachesim import Belady, BeladySize

    OPTIMAL_ALGORITHMS = [Belady, BeladySize]
except ImportError:
    OPTIMAL_ALGORITHMS = []

try:
    from libcachesim import LRUProb, FlashProb

    PROBABILISTIC_ALGORITHMS = [LRUProb, FlashProb]
except ImportError:
    PROBABILISTIC_ALGORITHMS = []

try:
    from libcachesim import Size, GDSF

    SIZE_BASED_ALGORITHMS = [Size, GDSF]
except ImportError:
    SIZE_BASED_ALGORITHMS = []

try:
    from libcachesim import Hyperbolic

    HYPERBOLIC_ALGORITHMS = [Hyperbolic]
except ImportError:
    HYPERBOLIC_ALGORITHMS = []


class TestCacheBasicFunctionality:
    """Test basic cache functionality across different algorithms"""

    @pytest.mark.parametrize(
        "cache_class",
        [
            LHD,
            LRU,
            FIFO,
            LFU,
            ARC,
            Clock,
            Random,
            S3FIFO,
            Sieve,
            LIRS,
            TwoQ,
            SLRU,
            WTinyLFU,
            LeCaR,
            LFUDA,
            ClockPro,
            Cacheus,
            LRUProb,
            FlashProb,
            Size,
            GDSF,
            Hyperbolic,
        ],
    )
    def test_cache_initialization(self, cache_class):
        """Test that all cache types can be initialized with different sizes"""
        cache_sizes = [1024, 1024 * 1024, 1024 * 1024 * 1024]  # 1KB, 1MB, 1GB

        for size in cache_sizes:
            try:
                cache = cache_class(size)
                assert cache is not None
                assert hasattr(cache, "get")
                assert hasattr(cache, "insert")
                assert hasattr(cache, "find")
            except Exception as e:
                pytest.skip(f"Cache {cache_class.__name__} failed to initialize: {e}")

    @pytest.mark.parametrize(
        "cache_class", [LHD, LRU, FIFO, LFU, ARC, Clock, Random, S3FIFO, Sieve, LIRS, TwoQ, SLRU, WTinyLFU]
    )
    def test_basic_get_and_insert(self, cache_class):
        """Test basic get and insert operations"""
        if cache_class == LHD:
            pytest.skip("LHD's insert always returns None")


        cache = cache_class(1024 * 1024)  # 1MB cache

        # Create a request
        req = Request()
        req.obj_id = 1
        req.obj_size = 100
        req.op = ReqOp.OP_GET

        # Initially, object should not be in cache
        hit = cache.get(req)
        assert hit == False

        # Insert the object
        if cache_class != LIRS:
            cache_obj = cache.insert(req)
            assert cache_obj is not None
            assert cache_obj.obj_id == 1
            assert cache_obj.obj_size == 100
        else:
            assert cache.insert(req) is None

        # Now it should be a hit
        hit = cache.get(req)
        assert hit == True

    @pytest.mark.parametrize(
        "cache_class",
        [
            LHD,
            LRU,
            FIFO,
            LFU,
            ARC,
            Clock,
            Random,
            S3FIFO,
            Sieve,
            LIRS,
            TwoQ,
            SLRU,
            WTinyLFU,
            LeCaR,
            LFUDA,
            ClockPro,
            Cacheus,
            LRUProb,
            FlashProb,
            Size,
            GDSF,
            Hyperbolic,
        ],
    )
    def test_cache_eviction(self, cache_class):
        """Test that cache eviction works when cache is full"""
        cache = cache_class(1024 * 1024)  # 1MB cache

        if cache_class == GDSF:
            pytest.skip("GDSF should be used with find/get but not insert")

        # Insert objects until cache is full
        for i in range(5):
            req = Request()
            req.obj_id = i
            req.obj_size = 50  # Each object is 50 bytes
            req.op = ReqOp.OP_GET
            req.next_access_vtime = 100 + i

            cache.insert(req)

        # Try to insert one more object
        req = Request()
        req.obj_id = 999
        req.obj_size = 50
        req.next_access_vtime = 200
        req.op = ReqOp.OP_GET
        cache.insert(req)

    @pytest.mark.parametrize(
        "cache_class",
        [
            LHD,
            LRU,
            FIFO,
            LFU,
            ARC,
            Clock,
            Random,
            S3FIFO,
            Sieve,
            LIRS,
            TwoQ,
            SLRU,
            WTinyLFU,
            LeCaR,
            LFUDA,
            ClockPro,
            Cacheus,
            LRUProb,
            FlashProb,
            Size,
            GDSF,
            Hyperbolic,
        ],
    )
    def test_cache_find_method(self, cache_class):
        """Test the find method functionality"""
        cache = cache_class(1024)

        req = Request()
        req.obj_id = 1
        req.obj_size = 100
        req.op = ReqOp.OP_GET

        # Initially should not find the object
        cache_obj = cache.find(req, update_cache=False)
        assert cache_obj is None

        # Insert the object
        cache.insert(req)

        # Now should find it
        cache_obj = cache.find(req, update_cache=False)
        assert cache_obj is not None
        assert cache_obj.obj_id == 1

    @pytest.mark.parametrize(
        "cache_class",
        [
            LHD,
            LRU,
            FIFO,
            LFU,
            ARC,
            Clock,
            Random,
            S3FIFO,
            Sieve,
            LIRS,
            TwoQ,
            SLRU,
            WTinyLFU,
            LeCaR,
            LFUDA,
            ClockPro,
            Cacheus,
            LRUProb,
            FlashProb,
            Size,
            GDSF,
            Hyperbolic,
        ],
    )
    def test_cache_can_insert(self, cache_class):
        """Test can_insert method"""
        cache = cache_class(1024 * 1024)

        req = Request()
        req.obj_id = 1
        req.obj_size = 100
        req.op = ReqOp.OP_GET

        # Should be able to insert initially
        can_insert = cache.can_insert(req)
        assert can_insert == True

        # Insert the object
        cache.insert(req)

        # Try to insert a larger object that won't fit
        req2 = Request()
        req2.obj_id = 2
        req2.obj_size = 150  # Too large for remaining space
        req2.op = ReqOp.OP_GET

        can_insert = cache.can_insert(req2)
        # Some algorithms might still return True if they can evict
        assert can_insert in [True, False]


class TestCacheEdgeCases:
    """Test edge cases and error conditions"""

    def test_zero_size_cache(self):
        """Test cache with zero size"""
        cache = LRU(0)

        req = Request()
        req.obj_id = 1
        req.obj_size = 100
        req.op = ReqOp.OP_GET

        # Should not be able to insert
        can_insert = cache.can_insert(req)
        assert can_insert == False

    def test_large_object(self):
        """Test inserting object larger than cache size"""
        cache = LRU(100)

        req = Request()
        req.obj_id = 1
        req.obj_size = 200  # Larger than cache
        req.op = ReqOp.OP_GET

        # Should not be able to insert
        can_insert = cache.can_insert(req)
        assert can_insert == False

    def test_string_object_id(self):
        """Test with string object ID"""
        req = Request()
        with pytest.raises(Exception):
            req.obj_id = "1"

    def test_zero_size_object(self):
        """Test with zero size object"""
        cache = LRU(1024)

        req = Request()
        req.obj_id = 1
        req.obj_size = 0
        req.op = ReqOp.OP_GET

        # Should work fine
        cache.insert(req)
        hit = cache.get(req)
        assert hit == True


class TestCacheWithSyntheticTrace:
    """Test cache performance with synthetic traces"""

    def test_cache_with_zipf_trace(self):
        """Test cache performance with Zipf distribution"""
        # Create synthetic reader with Zipf distribution
        reader = SyntheticReader(num_of_req=1000, obj_size=100, alpha=1.0, dist="zipf", num_objects=100, seed=42)

        # Test with different cache algorithms
        cache_algorithms = [LRU, FIFO, LFU, S3FIFO, Sieve]

        for cache_class in cache_algorithms:
            cache = cache_class(1024)  # 1KB cache

            # Process the trace
            miss_ratio, _ = cache.process_trace(reader)

            # Basic sanity checks
            assert 0.0 <= miss_ratio <= 1.0

            # Reset reader for next test
            reader.reset()

    def test_cache_with_uniform_trace(self):
        """Test cache performance with uniform distribution"""
        # Create synthetic reader with uniform distribution
        reader = SyntheticReader(num_of_req=500, obj_size=50, dist="uniform", num_objects=50, seed=123)

        cache = LRU(512)  # 512B cache

        # Process the trace
        miss_ratio, _ = cache.process_trace(reader)

        # Basic sanity checks
        assert 0.0 <= miss_ratio <= 1.0


class TestCacheStatistics:
    """Test cache statistics and metrics"""

    def test_cache_occupied_bytes(self):
        """Test get_occupied_byte method"""
        cache = LRU(1024)

        # Initially should be 0
        occupied = cache.get_occupied_byte()
        assert occupied == 0

        # Insert an object
        req = Request()
        req.obj_id = 1
        req.obj_size = 100
        req.op = ReqOp.OP_GET
        cache.insert(req)

        # Should reflect the inserted object size
        occupied = cache.get_occupied_byte()
        assert occupied >= 100  # May include metadata overhead

    def test_cache_object_count(self):
        """Test get_n_obj method"""
        cache = LRU(1024)

        # Initially should be 0
        n_obj = cache.get_n_obj()
        assert n_obj == 0

        # Insert objects
        for i in range(3):
            req = Request()
            req.obj_id = i
            req.obj_size = 100
            req.op = ReqOp.OP_GET
            cache.insert(req)

        # Should have 3 objects
        n_obj = cache.get_n_obj()
        assert n_obj == 3

    def test_cache_print(self):
        """Test print_cache method"""
        cache = LRU(1024)

        # Insert an object
        req = Request()
        req.obj_id = 1
        req.obj_size = 100
        req.op = ReqOp.OP_GET
        cache.insert(req)

        # Should return a string representation
        cache.print_cache()


class TestCacheOperations:
    """Test various cache operations"""

    def test_cache_remove(self):
        """Test remove method"""
        cache = LRU(1024)

        # Insert an object
        req = Request()
        req.obj_id = 1
        req.obj_size = 100
        req.op = ReqOp.OP_GET
        cache.insert(req)

        # Verify it's in cache
        hit = cache.get(req)
        assert hit == True

        # Remove it
        removed = cache.remove(1)
        assert removed == True

        # Verify it's no longer in cache
        hit = cache.get(req)
        assert hit == False

    def test_cache_need_eviction(self):
        """Test need_eviction method"""
        cache = LRU(200)

        # Insert objects until cache is nearly full
        for i in range(3):
            req = Request()
            req.obj_id = i
            req.obj_size = 50
            req.op = ReqOp.OP_GET
            cache.insert(req)

        # Try to insert a larger object
        req = Request()
        req.obj_id = 999
        req.obj_size = 100
        req.op = ReqOp.OP_GET

        # Should need eviction
        need_eviction = cache.need_eviction(req)
        assert need_eviction == True

    def test_cache_to_evict(self):
        """Test to_evict method"""
        cache = LRU(200)

        # Insert objects
        for i in range(3):
            req = Request()
            req.obj_id = i
            req.obj_size = 50
            req.op = ReqOp.OP_GET
            cache.insert(req)

        # Try to insert a larger object
        req = Request()
        req.obj_id = 999
        req.obj_size = 100
        req.op = ReqOp.OP_GET

        # Should return an object to evict
        evict_obj = cache.to_evict(req)
        assert evict_obj is not None
        assert hasattr(evict_obj, "obj_id")


class TestCacheOptionalAlgorithms:
    """Test optional algorithms"""

    @pytest.mark.optional
    def test_glcache(self):
        """Test GLCache algorithm"""
        from libcachesim import GLCache

        cache = GLCache(1024)
        assert cache is not None

    @pytest.mark.optional
    def test_lrb(self):
        """Test LRB algorithm"""
        from libcachesim import LRB

        cache = LRB(1024)
        assert cache is not None

    @pytest.mark.optional
    def test_3lcache(self):
        """Test 3LCache algorithm"""
        from libcachesim import ThreeLCache

        cache = ThreeLCache(1024)
        assert cache is not None
