# Developer Guide

This page is for people working *on* libCacheSim Python, rather than with it. If you only want
to use the library, start with [Installation](getting_started/installation.md).

## Repository layout

```
libCacheSim-python/
├── libcachesim/          # The Python package
│   ├── __init__.py       # Public API surface (__all__)
│   ├── __init__.pyi      # Type stubs for the compiled extension
│   ├── cache.py          # Cache wrapper classes
│   ├── admissioner.py    # Admission policy wrappers
│   ├── trace_reader.py   # TraceReader, with S3 support
│   ├── synthetic_reader.py
│   ├── trace_analyzer.py
│   ├── protocols.py      # ReaderProtocol
│   └── util.py           # Trace conversion helpers
├── src/                  # pybind11 bindings (C++)
│   ├── export_cache.cpp
│   ├── export_reader.cpp
│   ├── export_analyzer.cpp
│   ├── export_admissioner.cpp
│   └── libCacheSim/      # git submodule: the C library
├── tests/
├── examples/
├── scripts/
└── docs/
```

The general shape is: the C library does the work, `src/*.cpp` exposes it through pybind11, and
`libcachesim/*.py` wraps that in an ergonomic Python API.

## Getting set up

The C library is a git submodule, so the checkout must be recursive:

```bash
git clone https://github.com/cacheMon/libCacheSim-python.git
cd libCacheSim-python
git submodule update --init --recursive
pip install -e ".[dev]"
```

The `dev` extra brings in `pytest`, `ruff`, `mypy`, and `pre-commit`.

`scripts/install.sh` does all of the above and then runs the tests. Pass `--all` to enable the
optional learned algorithms:

```bash
bash scripts/install.sh --all
```

### Build system

Builds go through [scikit-build-core](https://scikit-build-core.readthedocs.io/), configured in
`pyproject.toml`. It configures and builds the bundled C library first, then compiles the
bindings with Ninja. Optional features are toggled with `CMAKE_ARGS`:

```bash
CMAKE_ARGS="-DENABLE_LRB=ON -DENABLE_3L_CACHE=ON -DENABLE_GLCACHE=ON" pip install -e .
```

Note that `pyproject.toml` sets `build-dir = "build"`, so incremental rebuilds reuse previous
output. If a rebuild picks up stale artefacts, remove `build/` and `src/libCacheSim/build/`.

## Testing

```bash
python -m pytest tests/
```

!!! important
    `pyproject.toml` sets `addopts = [..., "-m", "not optional"]`, so a plain `pytest` run
    **skips** the tests for the optional learned algorithms. To run those, you need a build with
    the corresponding CMake flags and an explicit marker selection:

    ```bash
    python -m pytest tests/ -m optional
    ```

The suite also sets `filterwarnings = ["error", ...]`, so a new warning will fail the build.

Several tests download traces from the public S3 bucket, so they need network access on first
run; subsequent runs use the local cache.

## Code style

There is no `pre-commit` configuration checked in, so run the tools directly:

```bash
# Lint and auto-fix Python
ruff check libcachesim/ tests/ examples/
ruff format libcachesim/

# Type-check
mypy libcachesim/

# Format C++ (uses the checked-in .clang-format)
clang-format -i src/*.cpp src/*.h
```

`ruff` is configured in `pyproject.toml` with a 120-character line length and the `E`, `F`,
`UP`, `B`, `SIM`, and `G` rule sets.

## Adding a cache algorithm

Adding an algorithm that already exists in the C library takes five steps:

1. **Bind it.** In `src/export_cache.cpp`, expose the algorithm's `*_init` function following
   the pattern used by the existing ones.
2. **Wrap it.** In `libcachesim/cache.py`, add a class deriving from `CacheBase`. Build the
   common parameters with the existing `_create_common_params(...)` helper — this is also what
   gives every cache the fractional `cache_size` behaviour for free — and pass any
   algorithm-specific settings as a `cache_specific_params` string:

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

   Note that the C library's parameter names are hyphenated (`my-param`) even though the Python
   keyword is underscored.
3. **Export it.** Add the class to both the import block and `__all__` in
   `libcachesim/__init__.py`, and add a stub to `libcachesim/__init__.pyi`.
4. **Test it.** Add a case to `tests/test_cache.py`. If the algorithm depends on an optional
   build flag, mark it `@pytest.mark.optional`.
5. **Document it.** Add a section to `docs/src/en/examples/simulation.md` and a row to the table
   in `docs/src/en/api.md`.

If the algorithm needs a third-party library, guard the import as `ThreeLCache` and `GLCache`
do — a `try`/`except ImportError` that re-raises with the `CMAKE_ARGS` incantation the user
needs.

## Documentation

The site is built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) plus
`mkdocs-static-i18n`. Sources live in `docs/src/<locale>/`, and the locale folders must mirror
each other: a page at `en/examples/reader.md` is translated by a file at
`zh/examples/reader.md`. A file at any other path is simply never rendered. Missing
translations fall back to English, so partial translation is fine.

To build and preview locally:

```bash
bash scripts/build_docs.sh --serve   # http://127.0.0.1:8000
```

Or directly:

```bash
pip install -r docs/requirements.txt
cd docs && mkdocs build --clean --strict
```

Always build with `--strict` before opening a PR — that is what CI runs, and it turns broken
internal links into build failures.

Prefer relative links between pages (`../faq.md`) over absolute URLs to the published site, so
that links keep working in local builds and under the locale fallback.

## Continuous integration

| Workflow | Trigger | What it does |
|---|---|---|
| `.github/workflows/build.yml` | changes under `src/`, `libcachesim/`, `tests/` | Builds and tests on Ubuntu and macOS (Intel and Apple Silicon) across Python 3.10–3.13, and separately builds the docs |
| `.github/workflows/docs.yml` | changes under `docs/` | Builds with `--strict` and deploys to GitHub Pages on `main` |
| `.github/workflows/pypi-release.yml` | published release, or manual dispatch | Builds wheels with cibuildwheel and publishes to PyPI |

Note that `build.yml` only triggers on changes to code paths, and `docs.yml` only on `docs/`, so
a docs-only PR will not run the test suite and vice versa.

## Releasing

Releases are cut by publishing a GitHub release, which triggers `pypi-release.yml`.

Wheels are built by [cibuildwheel](https://cibuildwheel.pypa.io/) using the configuration in
`pyproject.toml`, which builds manylinux and macOS wheels for every supported CPython version
with **all three** optional algorithms enabled, and verifies each wheel by importing it and
running both the default and `optional` test selections.

`scripts/sync_version.py` keeps the version in `pyproject.toml` in step with
`src/libCacheSim/version.txt` from the submodule.

## Contributing

Bug reports and feature requests belong in
[GitHub issues](https://github.com/cacheMon/libCacheSim-python/issues/new/choose). For changes
to the simulation core itself rather than the bindings, the right repository is
[1a1a11a/libCacheSim](https://github.com/1a1a11a/libCacheSim).
