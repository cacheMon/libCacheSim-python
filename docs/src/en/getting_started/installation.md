# Installation

## Requirements

| | |
|---|---|
| **OS** | Linux / macOS |
| **Python** | 3.10 -- 3.13 |
| **Architecture** | x86_64 / aarch64 |

Windows is not supported.

## Install from PyPI

Pre-built wheels are published to [PyPI](https://pypi.org/project/libcachesim/), so in most
cases no compiler is needed:

```bash
pip install libcachesim
```

We recommend [uv](https://docs.astral.sh/uv/) to create and manage the environment:

```bash
uv venv --python 3.12 --seed
source .venv/bin/activate
uv pip install libcachesim
```

Verify the installation:

```bash
python -c "import libcachesim; print(libcachesim.__version__)"
```

## Optional eviction algorithms

Three algorithms depend on third-party machine-learning libraries and are therefore guarded by
CMake options, all of which default to `OFF`:

| Algorithm | CMake option | Depends on |
|---|---|---|
| [`LRB`](../examples/simulation.md#lrb) | `ENABLE_LRB` | LightGBM |
| [`ThreeLCache`](../examples/simulation.md#threelcache) | `ENABLE_3L_CACHE` | LightGBM |
| [`GLCache`](../examples/simulation.md#glcache) | `ENABLE_GLCACHE` | XGBoost |

!!! note
    The wheels released on PyPI are built with all three enabled. You only need the steps below
    if no wheel matches your platform and pip falls back to building from source, or if you are
    building from a source checkout yourself.

Install the third-party dependencies first:

```bash
git clone https://github.com/cacheMon/libCacheSim-python.git
cd libCacheSim-python
bash scripts/install_deps.sh

# If you cannot install system packages (e.g., no sudo access)
bash scripts/install_deps_user.sh
```

Then reinstall, passing the options through `CMAKE_ARGS`. Add `--no-cache-dir` to force a
rebuild rather than reusing a cached wheel:

```bash
# Enable one algorithm
CMAKE_ARGS="-DENABLE_LRB=ON" pip install libcachesim --no-cache-dir

# Or enable all three
CMAKE_ARGS="-DENABLE_LRB=ON -DENABLE_3L_CACHE=ON -DENABLE_GLCACHE=ON" \
    pip install libcachesim --no-cache-dir
```

!!! important
    Because the options default to `OFF`, a plain source build silently **omits** these three
    algorithms — constructing `LRB`, `ThreeLCache`, or `GLCache` then fails at runtime.
    Conversely, turning an option `ON` without its dependency installed makes CMake fail during
    configuration (`LIGHTGBM_PATH not found`, or a missing `xgboost` package). Run the
    dependency script first.

## Install from source

The C library [libCacheSim](https://github.com/1a1a11a/libCacheSim) is vendored as a git
submodule, so the checkout must be recursive:

```bash
git clone https://github.com/cacheMon/libCacheSim-python.git
cd libCacheSim-python
git submodule update --init --recursive
pip install .
```

`scripts/install.sh` wraps the whole flow — it updates the submodule, installs the package in
editable mode, checks that the import works, and runs the test suite:

```bash
bash scripts/install.sh

# Same, but with all optional algorithms enabled
bash scripts/install.sh --all
```

Building the extension requires a C++17 compiler, CMake ≥ 3.15, and Ninja. The build is driven
by [scikit-build-core](https://scikit-build-core.readthedocs.io/), which configures and builds
the bundled C library before compiling the [pybind11](https://pybind11.readthedocs.io/)
bindings.

## Troubleshooting

Two failures are common enough to have their own entries in the
[FAQ](../faq.md):

- `pip install` fails to find a suitable wheel and the source build errors out.
- The build reports `cannot find Python package` — Python's development headers are missing, or
  Python lives in a non-standard location.

For anything else, please
[open an issue](https://github.com/cacheMon/libCacheSim-python/issues/new/choose).
