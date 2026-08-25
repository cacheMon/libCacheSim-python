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

然后通过 `CMAKE_ARGS` 传入选项重新安装。这些选项只在**源码构建**时生效，因此必须强制走源码构建：仅加 `--no-cache-dir` 是不够的，pip 仍可能提示 `Requirement already satisfied` 或直接安装预编译 wheel，这两种情况下 `CMAKE_ARGS` 都会被静默忽略。请改为从当前 checkout 构建：

```bash
# 启用单个算法
CMAKE_ARGS="-DENABLE_LRB=ON" pip install --force-reinstall .

# 或者三个全部启用
CMAKE_ARGS="-DENABLE_LRB=ON -DENABLE_3L_CACHE=ON -DENABLE_GLCACHE=ON" \
    pip install --force-reinstall .
```

若要从 PyPI 而不是 checkout 构建，还需要禁用 wheel，确保真正执行源码构建：

```bash
CMAKE_ARGS="-DENABLE_LRB=ON" \
    pip install --force-reinstall --no-binary libcachesim libcachesim
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

`scripts/install.sh` 封装了整个流程——它会更新子模块、以可编辑模式安装本包（`pip install -e .`）、检查导入是否正常，并运行测试套件：

```bash
bash scripts/install.sh

# 同上，但启用全部可选算法
bash scripts/install.sh --all
```

!!! warning "`--all` 需要先安装学习型算法的依赖"
    `--all` 只是打开三个 CMake 选项，并**不会**安装 LightGBM 和 XGBoost。在尚未装好它们的机器上，构建会在配置阶段失败，报出类似 `LIGHTGBM_PATH not found` 的错误。请先运行依赖脚本：

    ```bash
    bash scripts/install_deps.sh        # 无 sudo 权限时用 install_deps_user.sh
    bash scripts/install.sh --all
    ```

构建扩展需要支持 C++17 的编译器、CMake ≥ 3.15 以及 Ninja，另外还需要三个在 configure 阶段查找的原生依赖：**pkg-config**、**GLib 2.0** 和 **Zstandard**。这三者都是必需的——`CMakeLists.txt` 中分别以 `find_package(PkgConfig REQUIRED)`、`pkg_check_modules(GLib REQUIRED glib-2.0)` 和 `find_package(ZSTD REQUIRED)` 声明——缺少任意一个都会在编译任何代码之前中断配置，并报出类似 `No package 'glib-2.0' found` 的错误。

上文的依赖脚本会在其支持的平台上安装它们（`install_deps.sh` 面向基于 yum 的发行版和 macOS）。在 Debian/Ubuntu 上，请使用子模块提供的脚本，或直接安装：

```bash
bash src/libCacheSim/scripts/install_dependency.sh

# 或者只装配置构建所需的最小集合
sudo apt install -y pkg-config libglib2.0-dev libzstd-dev
```

构建本身由 [scikit-build-core](https://scikit-build-core.readthedocs.io/) 驱动，它会先配置并构建内置的 C 库，再编译 [pybind11](https://pybind11.readthedocs.io/) 绑定。

## 疑难排查

有两类失败足够常见，已在[常见问题](../faq.md)中单列条目：

- `pip install` 找不到合适的 wheel，并且源码构建报错。
- 构建时提示 `cannot find Python package`——缺少 Python 的开发头文件，或者 Python 安装在非标准位置。

其他问题请[提交 issue](https://github.com/cacheMon/libCacheSim-python/issues/new/choose)。
