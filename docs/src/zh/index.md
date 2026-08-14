# 欢迎使用 libCacheSim Python

!!! note
    为方便起见，下文将 *libCacheSim Python 包*（本仓库）简称为 *libCacheSim*，将其底层的 *C 语言库* 称为 *libCacheSim lib*。

<figure markdown="span">
  ![](../assets/logos/logo.jpg){ align="center" alt="libCacheSim Light" class="logo-light" width="60%" }
</figure>

<p style="text-align:center">
一个用于构建和运行缓存模拟的高性能库
</strong>
</p>

<p style="text-align:center">
<script async defer src="https://buttons.github.io/buttons.js"></script>
<a class="github-button" href="https://github.com/cacheMon/libCacheSim-python" data-show-count="true" data-size="large" aria-label="Star">Star</a>
<a class="github-button" href="https://github.com/cacheMon/libCacheSim-python/subscription" data-show-count="true" data-icon="octicon-eye" data-size="large" aria-label="Watch">Watch</a>
<a class="github-button" href="https://github.com/cacheMon/libCacheSim-python/fork" data-show-count="true" data-icon="octicon-repo-forked" data-size="large" aria-label="Fork">Fork</a>
</p>

libCacheSim 是 [libCacheSim lib](https://github.com/1a1a11a/libCacheSim) 的 Python 绑定，简单易用，可用于构建和运行缓存模拟。

得益于[底层的 libCacheSim lib](https://github.com/1a1a11a/libCacheSim)，libCacheSim 速度很快：

- 高性能——真实 trace 回放可达每秒 2000 万条以上请求。
- 高内存效率——内存占用小且可预测。
- 开箱即用的并行能力——利用多核 CPU 加速 trace 分析与缓存模拟。

libCacheSim 同时灵活易用：

- 与[开源缓存数据集](https://github.com/cacheMon/cache_dataset)无缝集成，该数据集在 S3 上托管了数千条 trace。
- 基于[底层 libCacheSim lib](https://github.com/1a1a11a/libCacheSim) 的高吞吐模拟。
- 可细粒度控制缓存请求及其他内部数据。
- 无需任何编译即可开发自定义的插件缓存。
