# 开发者指南

本页面向的是*开发* libCacheSim Python 本身的人，而非它的使用者。如果你只是想使用这个库，请从[安装指南](getting_started/installation.md)开始。

## 仓库结构

```
libCacheSim-python/
├── libcachesim/          # Python 包
│   ├── __init__.py       # 对外 API（__all__）
│   ├── __init__.pyi      # 编译扩展的类型存根
│   ├── cache.py          # 缓存包装类
│   ├── admissioner.py    # 准入策略包装类
│   ├── trace_reader.py   # TraceReader，支持 S3
│   ├── synthetic_reader.py
│   ├── trace_analyzer.py
│   ├── protocols.py      # ReaderProtocol
│   └── util.py           # trace 转换辅助函数
├── src/                  # pybind11 绑定（C++）
│   ├── export_cache.cpp
│   ├── export_reader.cpp
│   ├── export_analyzer.cpp
│   ├── export_admissioner.cpp
│   └── libCacheSim/      # git 子模块：C 语言库
├── tests/
├── examples/
├── scripts/
└── docs/
```

整体结构是：C 库负责实际计算，`src/*.cpp` 通过 pybind11 将其暴露出来，`libcachesim/*.py` 再把它封装成符合 Python 习惯的 API。

## 环境搭建

C 库是一个 git 子模块，因此检出时必须递归拉取：

```bash
git clone https://github.com/cacheMon/libCacheSim-python.git
cd libCacheSim-python
git submodule update --init --recursive
pip install -e ".[dev]"
```

`dev` 附加依赖会引入 `pytest`、`ruff`、`mypy` 和 `pre-commit`。

`scripts/install.sh` 自动化了其中大部分工作：更新子模块、以可编辑模式安装、验证导入，并运行测试。注意它安装的是普通的 `-e .` 外加 `pytest`，**并非**完整的 `dev` 附加依赖——如果需要 `ruff`、`mypy` 和 `pre-commit`，仍要执行上面的命令。加上 `--all` 可启用可选的学习型算法：

```bash
# --all 只是打开 CMake 选项；请先安装 LightGBM/XGBoost，
# 否则配置阶段会因 LIGHTGBM_PATH not found 而失败
bash scripts/install_deps.sh        # 无 sudo 权限时用 install_deps_user.sh
bash scripts/install.sh --all
```

### 构建系统

构建通过 [scikit-build-core](https://scikit-build-core.readthedocs.io/) 完成，配置写在 `pyproject.toml` 中。它会先配置并构建内置的 C 库，再用 Ninja 编译绑定层。可选特性通过 `CMAKE_ARGS` 开关：

```bash
CMAKE_ARGS="-DENABLE_LRB=ON -DENABLE_3L_CACHE=ON -DENABLE_GLCACHE=ON" pip install -e .
```

注意 `pyproject.toml` 设置了 `build-dir = "build"`，因此增量重建会复用此前的产物。如果重建时读到了陈旧的中间产物，请删除 `build/` 和 `src/libCacheSim/build/`。

## 测试

```bash
python -m pytest tests/
```

!!! important
    `pyproject.toml` 中设置了 `addopts = [..., "-m", "not optional"]`，因此直接运行 `pytest` 会**跳过**可选学习型算法的测试。要运行这些测试，需要用对应的 CMake 选项构建，并显式指定 marker：

    ```bash
    python -m pytest tests/ -m optional
    ```

测试套件还设置了 `filterwarnings = ["error", ...]`，因此新出现的警告会直接导致构建失败。

有几个测试会从公开的 S3 存储桶下载 trace，因此首次运行需要网络；后续运行会使用本地缓存。

## 代码风格

仓库中并未提交 `pre-commit` 配置，因此请直接运行相关工具：

```bash
# 检查并自动修复 Python 代码
ruff check libcachesim/ tests/ examples/
ruff format libcachesim/

# 类型检查
mypy libcachesim/

# 格式化 C++（使用仓库中的 .clang-format）
clang-format -i src/*.cpp src/*.h
```

`ruff` 在 `pyproject.toml` 中配置，行宽为 120，启用了 `E`、`F`、`UP`、`B`、`SIM` 和 `G` 规则集。

## 新增一个缓存算法

若该算法在 C 库中已经存在，接入它需要五步：

1. **绑定。** 在 `src/export_cache.cpp` 中，参照已有算法的写法暴露该算法的 `*_init` 函数。
2. **封装。** 在 `libcachesim/cache.py` 中新增一个继承自 `CacheBase` 的类。用已有的 `_create_common_params(...)` 辅助函数来构造公共参数——这也是每个缓存能够免费获得按比例设置 `cache_size` 能力的原因——并把算法特有的设置以 `cache_specific_params` 字符串传入：

   ```python
   class MyAlgo(CacheBase):
       """My algorithm

       Special parameters:
       my_param: what it controls (default: 0.5)
       """

       def __init__(
           self,
           cache_size: int | float,
           default_ttl: int = 86400 * 300,
           hashpower: int = 24,
           consider_obj_metadata: bool = False,
           my_param: float = 0.5,
           admissioner: AdmissionerBase = None,
           reader: ReaderProtocol = None,
       ):
           cache_specific_params = f"my-param={my_param}"
           super().__init__(
               _cache=MyAlgo_init(
                   _create_common_params(
                       cache_size, default_ttl, hashpower, consider_obj_metadata, reader
                   ),
                   cache_specific_params,
               ),
               admissioner=admissioner,
           )
   ```

   注意 C 库的参数名使用连字符（`my-param`），而 Python 关键字参数使用下划线。
3. **导出。** 把该类同时加入 `libcachesim/__init__.py` 的 import 块和 `__all__`，并在 `libcachesim/__init__.pyi` 中补上存根。
4. **测试。** 在 `tests/test_cache.py` 中增加用例。如果该算法依赖可选的编译选项，请标记 `@pytest.mark.optional`。
5. **写文档。** 在 `docs/src/en/examples/simulation.md` 中新增一节，并在 `docs/src/en/api.md` 的表格中增加一行。

如果该算法依赖第三方库，请像 `ThreeLCache` 和 `GLCache` 那样保护 import——用 `try`/`except ImportError` 捕获后重新抛出，并在消息中给出用户需要的 `CMAKE_ARGS` 写法。

## 文档

站点使用 [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) 加 `mkdocs-static-i18n` 构建。源文件位于 `docs/src/<locale>/`，各语言目录必须彼此镜像：`en/examples/reader.md` 这个页面的译文必须位于 `zh/examples/reader.md`。放在其他路径的文件根本不会被渲染。缺失的译文会回退到英文，因此部分翻译也是可以接受的。

本地构建与预览：

```bash
bash scripts/build_docs.sh --serve   # http://127.0.0.1:8000
```

或者直接运行：

```bash
pip install -r docs/requirements.txt
cd docs && mkdocs build --clean --strict
```

提 PR 之前请务必用 `--strict` 构建一次——CI 跑的就是这个命令，它会把失效的站内链接变成构建失败。

页面之间请优先使用相对链接（`../faq.md`），而不是指向已发布站点的绝对 URL，这样在本地构建和语言回退时链接仍然有效。

翻译中文页面时，如果某个标题会被其他页面以锚点链接引用，请用 `attr_list` 显式固定锚点 ID，例如 `## 按比例设置缓存大小 {#cache-size-as-a-ratio}`，这样跨页链接在两种语言下都能正常工作。

## 持续集成

| 工作流 | 触发条件 | 作用 |
|---|---|---|
| `.github/workflows/build.yml` | `src/`、`libcachesim/`、`tests/` 下的改动 | 在 Ubuntu 和 macOS（Apple Silicon）上针对 Python 3.11–3.14 构建并测试，同时单独构建文档 |
| `.github/workflows/docs.yml` | `docs/` 下的改动 | 以 `--strict` 构建，并在 `main` 分支上部署到 GitHub Pages |
| `.github/workflows/pypi-release.yml` | 发布 release，或手动触发 | 用 cibuildwheel 构建 wheel 并发布到 PyPI |

注意 `build.yml` 只在代码路径变动时触发，而 `docs.yml` 只在 `docs/` 变动时触发，因此仅改文档的 PR 不会运行测试套件，反之亦然。

## 发布

发布流程由创建 GitHub release 触发，进而运行 `pypi-release.yml`。

wheel 由 [cibuildwheel](https://cibuildwheel.pypa.io/) 按 `pyproject.toml` 中的配置构建，会为所有受支持的 CPython 版本构建 manylinux 和 macOS wheel，并启用**全部三个**可选算法，同时通过导入 wheel 并分别运行默认测试和 `optional` 测试来做校验。

`scripts/sync_version.py` 负责让 `pyproject.toml` 中的版本号与子模块中的 `src/libCacheSim/version.txt` 保持一致。

## 参与贡献

Bug 报告和功能需求请提交到 [GitHub issues](https://github.com/cacheMon/libCacheSim-python/issues/new/choose)。如果改动涉及的是模拟内核本身而非绑定层，正确的仓库是 [1a1a11a/libCacheSim](https://github.com/1a1a11a/libCacheSim)。
