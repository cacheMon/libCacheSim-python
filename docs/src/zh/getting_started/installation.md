# 安装

## 环境要求

| | |
|---|---|
| **操作系统** | Linux / macOS |
| **Python** | 3.10 -- 3.13 |
| **架构** | x86_64 / aarch64 |

不支持 Windows。

## 从 PyPI 安装

我们已将预编译的 wheel 发布到 [PyPI](https://pypi.org/project/libcachesim/)，因此大多数情况下无需编译器：

```bash
pip install libcachesim
```

推荐使用 [uv](https://docs.astral.sh/uv/) 创建和管理环境：

```bash
uv venv --python 3.12 --seed
source .venv/bin/activate
uv pip install libcachesim
```

验证安装结果：

```bash
python -c "import libcachesim; print(libcachesim.__version__)"
```

## 可选的淘汰算法 {#optional-eviction-algorithms}

有三个算法依赖第三方机器学习库，因此由 CMake 选项控制，且默认全部为 `OFF`：

| 算法 | CMake 选项 | 依赖 |
|---|---|---|
| [`LRB`](../examples/simulation.md#lrb) | `ENABLE_LRB` | LightGBM |
| [`ThreeLCache`](../examples/simulation.md#threelcache) | `ENABLE_3L_CACHE` | LightGBM |
| [`GLCache`](../examples/simulation.md#glcache) | `ENABLE_GLCACHE` | XGBoost |

!!! note
    发布到 PyPI 的 wheel 已启用全部三个算法。只有当没有匹配你平台的 wheel、pip 回退到从源码构建，或者你自己从源码检出进行构建时，才需要执行下面的步骤。

首先安装第三方依赖：

```bash
git clone https://github.com/cacheMon/libCacheSim-python.git
cd libCacheSim-python
bash scripts/install_deps.sh

# 如果你无法安装系统软件包（例如没有 sudo 权限）
bash scripts/install_deps_user.sh
```

然后通过 `CMAKE_ARGS` 传入选项重新安装。加上 `--no-cache-dir` 可以强制重新构建，而不是复用缓存的 wheel：

```bash
# 启用单个算法
CMAKE_ARGS="-DENABLE_LRB=ON" pip install libcachesim --no-cache-dir

# 或者三个全部启用
CMAKE_ARGS="-DENABLE_LRB=ON -DENABLE_3L_CACHE=ON -DENABLE_GLCACHE=ON" \
    pip install libcachesim --no-cache-dir
```

!!! important
    由于这些选项默认为 `OFF`，普通的源码构建会**静默地略过**这三个算法——此时构造 `LRB`、`ThreeLCache` 或 `GLCache` 会在运行时失败。反过来，如果在未安装依赖的情况下把选项打开，CMake 会在配置阶段直接报错（`LIGHTGBM_PATH not found`，或提示缺少 `xgboost` 包）。请先运行依赖安装脚本。

## 从源码安装

C 语言库 [libCacheSim](https://github.com/1a1a11a/libCacheSim) 以 git 子模块的形式引入，因此检出时必须递归拉取：

```bash
git clone https://github.com/cacheMon/libCacheSim-python.git
cd libCacheSim-python
git submodule update --init --recursive
pip install .
```

`scripts/install.sh` 封装了整个流程——它会更新子模块、以可编辑模式安装本包、检查导入是否正常，并运行测试套件：

```bash
bash scripts/install.sh

# 同上，但启用全部可选算法
bash scripts/install.sh --all
```

构建扩展需要支持 C++17 的编译器、CMake ≥ 3.15 以及 Ninja。构建过程由 [scikit-build-core](https://scikit-build-core.readthedocs.io/) 驱动，它会先配置并构建内置的 C 库，再编译 [pybind11](https://pybind11.readthedocs.io/) 绑定。

## 疑难排查

有两类失败足够常见，已在[常见问题](../faq.md)中单列条目：

- `pip install` 找不到合适的 wheel，并且源码构建报错。
- 构建时提示 `cannot find Python package`——缺少 Python 的开发头文件，或者 Python 安装在非标准位置。

其他问题请[提交 issue](https://github.com/cacheMon/libCacheSim-python/issues/new/choose)。
