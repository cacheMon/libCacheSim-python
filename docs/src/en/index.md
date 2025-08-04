# Welcome to libCacheSim Python

!!! note
    For convenience, we refer to the *libCacheSim Python Package* (this repo) as *libCacheSim* and the *C library* as *libCacheSim lib* in the following documentation.

<figure markdown="span">
  ![](../assets/logos/logo.jpg){ align="center" alt="libCacheSim Light" class="logo-light" width="60%" }
</figure>

<p style="text-align:center">
A high-performance library for building and running cache simulations
</strong>
</p>

<p style="text-align:center">
<script async defer src="https://buttons.github.io/buttons.js"></script>
<a class="github-button" href="https://github.com/cacheMon/libCacheSim-python" data-show-count="true" data-size="large" aria-label="Star">Star</a>
<a class="github-button" href="https://github.com/cacheMon/libCacheSim-python/subscription" data-show-count="true" data-icon="octicon-eye" data-size="large" aria-label="Watch">Watch</a>
<a class="github-button" href="https://github.com/cacheMon/libCacheSim-python/fork" data-show-count="true" data-icon="octicon-repo-forked" data-size="large" aria-label="Fork">Fork</a>
</p>

libCacheSim is an easy-to-use python binding of [libCachesim lib](https://github.com/1a1a11a/libCacheSim) for building and running cache simulations.

libCacheSim is fast with the features from [underlying libCacheSim lib](https://github.com/1a1a11a/libCacheSim):

- High performance - over 20M requests/sec for a realistic trace replay.
- High memory efficiency - predictable and small memory footprint.
- Parallelism out-of-the-box - uses the many CPU cores to speed up trace analysis and cache simulations.

libCacheSim is flexible and easy to use with:

- Seamless integration with [open-source cache dataset](https://github.com/cacheMon/cache_dataset) consisting of thousands traces hosted on S3.
- High-throughput simulation with the [underlying libCacheSim lib](https://github.com/1a1a11a/libCacheSim)
- Detailed cache requests and other internal data control
- Customized plugin cache development without any compilation