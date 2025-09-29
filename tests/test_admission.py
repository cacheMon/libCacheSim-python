"""
Test cases for cache admission in libCacheSim Python bindings.

This module tests the PluginAdmissioner and existing admission policies
"""

import pytest
from libcachesim import (
    SizeAdmissioner,
    ProbAdmissioner,
    SizeProbabilisticAdmissioner,
    BloomFilterAdmissioner,
    PluginAdmissioner,
    LRU
)
from libcachesim.libcachesim_python import (
    Request,
    ReqOp
)


class TestSizeAdmissioner:
    """test existing size admissioner policy"""

    def test_default_configuration(self):
        int64_max = (2 ** 63) - 1
        cache = LRU(
            # Cache size must be large enough to fit the object
            cache_size=int64_max,
            admissioner=SizeAdmissioner()
        )

        # We should be able to admit an item which lies underneath
        # the default threshold of INT64_MAX
        req = Request()
        req.obj_id = 0
        req.obj_size = int64_max - 1
        req.op = ReqOp.OP_GET
        assert cache.can_insert(req)

        # Anything equating to the default threshold should fail
        req = Request()
        req.obj_id = 0
        req.obj_size = int64_max
        req.op = ReqOp.OP_GET
        assert not cache.can_insert(req)

    @pytest.mark.parametrize("thresh", [0, 100, 250, 500, 750, 1000])
    def test_custom_configuration(self, thresh):
        cache = LRU(
            cache_size=1000,
            admissioner=SizeAdmissioner(size_threshold=thresh)
        )
        admits = 0

        # Create 1000 requests of unique sizes and test to see and
        # use `cache_can_insert_default` to run the admissioner
        for i in range(1000):
            req = Request()
            req.obj_id = i
            req.obj_size = i
            req.op = ReqOp.OP_GET
            if cache.can_insert(req):
                admits += 1

        # All items admitted should lie within the size threshold
        assert admits == thresh


class TestProbAdmissioner:
    """test existing probabilistic admissioner policy"""

    # Note: The `ProbAdmissioner` does not accept zero as a valid
    # probability, hence we do not test a `admit_nothing` scenario
    def test_admit_all(self):
        cache = LRU(
            # Cache size must be large enough to fit the object
            cache_size=1000,
            admissioner=ProbAdmissioner(prob=1.0)
        )

        # Probability threshold is one, so everything should be
        # admitted unconditionally
        for obj_id in range(1000):
            req = Request()
            req.obj_id = obj_id
            req.obj_size = 1
            req.op = ReqOp.OP_GET
            assert cache.can_insert(req)

    @pytest.mark.parametrize("prob", [0.0001, 0.1, 0.5, 0.9, 0.9999])
    def test_admit_amount(self, prob):
        cache = LRU(
            # Cache size must be large enough to fit the object
            cache_size=1000,
            admissioner=ProbAdmissioner(prob=prob)
        )
        total_requests, admits = 1000, 0

        # Probability threshold is one, so everything should be
        # admitted unconditionally
        for obj_id in range(total_requests):
            req = Request()
            req.obj_id = obj_id
            req.obj_size = 1
            req.op = ReqOp.OP_GET
            if cache.can_insert(req):
                admits += 1

        # This value is not deterministic, hence just perform a
        # basic sanity check to make sure it lies between 0 and 1
        admit_rate = admits / total_requests
        assert 0 <= admit_rate and admit_rate <= 1


class TestSizeProbabilisticAdmissioner:

    @pytest.mark.parametrize("exponent", [0.0001, 0.1, 0.5, 0.9, 0.9999])
    def test_admit_amount(self, exponent):
        cache = LRU(
            # Cache size must be large enough to fit the object
            cache_size=1000,
            admissioner=SizeProbabilisticAdmissioner(exponent=exponent)
        )
        total_requests, admits = 1000, 0

        # Probability threshold is one, so everything should be
        # admitted unconditionally
        for obj_id in range(total_requests):
            req = Request()
            req.obj_id = obj_id
            req.obj_size = 1
            req.op = ReqOp.OP_GET
            if cache.can_insert(req):
                admits += 1

        # This value is not deterministic, hence just perform a
        # basic sanity check to make sure it lies between 0 and 1
        admit_rate = admits / total_requests
        assert 0 <= admit_rate and admit_rate <= 1


class TestBloomFilter:
    """test existing bloomfilter admissioner policy"""

    @pytest.mark.parametrize("visits", [0, 1, 2, 3])
    def test_multi_pass(self, visits):
        cache = LRU(
            cache_size=1000,
            admissioner=BloomFilterAdmissioner()
        )
        admits = 0

        # Here, we try to "see" each item a certain number of times
        # to increment it's "seen_times" count in the bloom filter
        # hash table.
        for _ in range(visits):
            for obj_id in range(1000):
                req = Request()
                req.obj_id = obj_id
                req.obj_size = 1
                req.op = ReqOp.OP_GET
                if cache.can_insert(req):
                    cache.insert(req)

        # Next, we check to see if the items were admitted to cache
        for obj_id in range(1000):
            req = Request()
            req.obj_id = obj_id
            req.obj_size = 1
            req.op = ReqOp.OP_GET
            if cache.get(req):
                admits += 1

        # Only if each item is visited more than once should we see
        # that it was admitted to the cache
        expected = 1000 if visits > 1 else 0
        assert admits == expected


# TODO: Tests crash if we do not explicitly delete the cache object
class TestPluginAdmissioner:
    """test PluginAdmissioner using custom simplistic policies"""

    def test_admit_all(self):
        pa = PluginAdmissioner(
            "testAdmissioner",
            lambda: None,
            # Accept all items
            lambda data, req: True,
            lambda: None,
            lambda data, req: None,
            lambda data: None,
        )
        cache = LRU(cache_size=1000, admissioner=pa)

        # Here, we test a basic custom admission policy which
        # should simply accept every single request
        for size in range(1000):
            req = Request()
            req.obj_id = 0
            req.obj_size = size
            req.op = ReqOp.OP_GET
            assert cache.can_insert(req)
        del cache

    def test_admit_nothing(self):
        pa = PluginAdmissioner(
            "testAdmissioner",
            lambda: None,
            # Reject all items
            lambda data, req: False,
            lambda: None,
            lambda data, req: None,
            lambda data: None,
        )
        cache = LRU(cache_size=1000, admissioner=pa)

        # Here, we test a basic custom admission policy which
        # should simply reject every single request
        for size in range(1000):
            req = Request()
            req.obj_id = 0
            req.obj_size = size
            req.op = ReqOp.OP_GET
            assert not cache.can_insert(req)
        del cache

    @pytest.mark.parametrize("thresh", [0, 100, 250, 500, 750, 1000])
    def test_custom_size(self, thresh):
        pa = PluginAdmissioner(
            "testAdmissioner",
            lambda: None,
            # Equivalent to the size admissioner
            lambda data, req: req.obj_size < thresh,
            lambda: None,
            lambda data, req: None,
            lambda data: None,
        )
        cache, admits = LRU(cache_size=1000, admissioner=pa), 0

        # Here, we test a custom implementation of the existing
        # size policy which admits everything under a static size
        # threshold
        for size in range(1000):
            req = Request()
            req.obj_id = 0
            req.obj_size = size
            req.op = ReqOp.OP_GET
            if cache.can_insert(req):
                admits += 1

        # Same correctness criteria as `TestSizeAdmissioner`
        assert admits == thresh
        del cache
