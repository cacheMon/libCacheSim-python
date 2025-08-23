# libCacheSim-python

libCacheSim-python is a high-performance Python binding for the libCacheSim library, providing cache simulation and analysis capabilities. It uses CMake, pybind11, and scikit-build-core for building Python extensions around a C++ core library.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

### Prerequisites and System Dependencies
- Install system dependencies: `sudo bash src/libCacheSim/scripts/install_dependency.sh` -- takes 66 seconds. NEVER CANCEL.
- Install Python build dependencies: `sudo apt install -y python3-numpy python3-pytest pybind11-dev`
- **CRITICAL**: Git submodules are required: `git submodule update --init --recursive` -- takes 2.4 seconds.

### Build Process (Manual CMake - RECOMMENDED)
**NEVER CANCEL builds** - CMake configuration + build takes 20-35 seconds total. Set timeout to 120+ seconds.

1. **Standard build (Debug)**:
   ```bash
   mkdir build && cd build
   cmake .. -G Ninja
   ninja
   ```
   - Configuration: ~2.4 seconds
   - Build: ~3 seconds
   - Total: ~6 seconds

2. **Optimized build (Release)**:
   ```bash
   mkdir build && cd build
   cmake .. -G Ninja -DCMAKE_BUILD_TYPE=Release
   ninja
   ```
   - Configuration: ~17 seconds (includes libCacheSim build with 175 targets)
   - Build: ~18 seconds (includes LTO optimization)
   - Total: ~35 seconds

3. **Test the build**:
   ```bash
   export PYTHONPATH=$(pwd)/build:$PYTHONPATH
   python3 -c "import libcachesim_python as lcs; print('✓ Import successful')"
   ```

### Python Package Installation (pip install -e .)
**WARNING**: pip install may experience network timeouts in CI environments. This is NORMAL.
- If `pip install -e .` fails with network timeouts, use the manual CMake build approach above.
- pip installation typically takes 30-60 seconds when network is stable.
- Use longer timeouts (120+ seconds) and retry if needed.

### Testing
- **Manual validation** (always works):
  ```bash
  export PYTHONPATH=$(pwd)/build:$PYTHONPATH
  python3 -c "
  import libcachesim_python as lcs
  common_params = lcs.CommonCacheParams(cache_size=1024)
  cache = lcs.LRU_init(common_params)
  req = lcs.Request()
  req.obj_id = 1
  req.obj_size = 10
  req.op = lcs.OP_GET
  cache.get(req)
  print(f'Cache has {cache.get_n_obj()} objects')
  "
  ```

- **pytest** (if available):
  ```bash
  python3 -m pytest tests/ -v -m "not optional"
  ```
  - NOTE: System pytest is version 7.4.4, but pyproject.toml requires 8.0+
  - Use manual validation instead if pytest version conflicts occur

### Performance Validation
- **Debug build**: ~65,000 requests/second
- **Release build**: ~571,000 requests/second  
- Test with: `python3 -c "import time; import libcachesim_python as lcs; start=time.time(); common_params=lcs.CommonCacheParams(cache_size=10000); cache=lcs.LRU_init(common_params); [cache.get(lcs.Request(obj_id=i%1000, obj_size=10, op=lcs.OP_GET)) for i in range(100000)]; print(f'Rate: {100000/(time.time()-start):.0f} req/s')"`

## Critical Build Issues & Solutions

### Network Timeouts
**COMMON**: pip install may timeout due to PyPI network issues.
- **Solution**: Use manual CMake build instead of pip install
- **NOT a code issue** - this is an infrastructure limitation

### pybind11 Compatibility
**FIXED**: If you see `py::set_error` compilation errors:
- This was already fixed in src/exception.cpp (lines 24, 26)
- The fix changed `py::set_error(exc, msg)` to `exc(msg)` for pybind11 2.10+ compatibility

### Optional Features (Advanced Algorithms)
Optional cache algorithms (LRB, GLCache, 3LCache) require additional dependencies:
- **XGBoost** and **LightGBM** libraries
- Install with: `bash scripts/install_deps.sh` or `bash scripts/install_deps_user.sh`
- Build with: `cmake -DENABLE_LRB=ON -DENABLE_GLCACHE=ON -DENABLE_3L_CACHE=ON`
- **Skip optional features** for basic development - they are not required

## Development Workflow

### Standard Development Process
1. **Initialize**: `git submodule update --init --recursive`
2. **Install system deps**: `sudo bash src/libCacheSim/scripts/install_dependency.sh`
3. **Build**: `mkdir build && cd build && cmake .. -G Ninja && ninja`
4. **Test**: `export PYTHONPATH=$(pwd)/build:$PYTHONPATH && python3 -c "import libcachesim_python"`
5. **Validate changes**: Run manual performance test

### After Making Code Changes
1. **Rebuild**: `ninja` (from build directory) -- takes 2-3 seconds
2. **Test import**: `python3 -c "import libcachesim_python"`
3. **Run validation scenarios**: Test cache algorithms manually
4. **Performance check**: Verify >500k requests/second in Release mode

### Common Validation Scenarios
Always test these scenarios after making changes:
1. **Basic cache creation**: LRU, FIFO, LFU, ARC, S3FIFO
2. **Request processing**: Insert/get operations with different object sizes
3. **Performance**: Ensure >500k requests/second (Release build)
4. **Memory usage**: Verify reasonable memory consumption

## Code Navigation

### Key Directories
- `src/`: Python binding source code (C++)
- `src/libCacheSim/`: Git submodule containing the core C++ library
- `tests/`: Python test suite
- `examples/`: Usage examples
- `benchmark/`: Performance benchmarks
- `scripts/`: Build and installation scripts

### Core Source Files
- `src/export.cpp`: Main pybind11 module definition
- `src/export_cache.cpp`: Cache algorithm exports
- `src/export_reader.cpp`: Trace reader exports
- `src/exception.cpp`: Exception handling (recently fixed for pybind11 compatibility)
- `CMakeLists.txt`: Build configuration
- `pyproject.toml`: Python package configuration

### Native Tools
The build also produces native C++ binaries in `src/libCacheSim/build/bin/`:
- `cachesim`: Command-line cache simulator
- `traceAnalyzer`: Trace analysis tool
- `MRC`: Miss ratio curve generation
- Use: `./cachesim trace_path csv LRU 100MB`

## Timing Expectations

### Build Times (NEVER CANCEL - set timeouts 120+ seconds)
- Git submodule init: 2.4 seconds
- System dependency install: 66 seconds
- CMake configuration (Debug): 2.4 seconds
- CMake configuration (Release): 17 seconds (includes full libCacheSim build)
- Build (Debug): 3 seconds
- Build (Release): 18 seconds (includes LTO)
- **Total fresh build**: 75-110 seconds depending on build type

### Test Times
- Manual validation: <1 second
- Performance test (100k requests): 0.2 seconds
- pytest (when working): 10-30 seconds

### Network Dependencies
- pip install: 30-300 seconds (may timeout, use manual build instead)
- Git submodule clone: 2-5 seconds

## Troubleshooting

### Build Failures
- **pybind11 not found**: `sudo apt install pybind11-dev`
- **Network timeouts**: Use manual CMake build instead of pip install
- **Missing submodules**: `git submodule update --init --recursive`
- **XGBoost/LightGBM missing**: Disable optional features or install via `scripts/install_deps.sh`

### Import Failures
- **Module not found**: `export PYTHONPATH=$(pwd)/build:$PYTHONPATH`
- **Symbol errors**: Rebuild with `ninja` from build directory
- **Version mismatch**: Check pybind11 version compatibility

### Performance Issues
- **Slow performance**: Use Release build (`cmake -DCMAKE_BUILD_TYPE=Release`)
- **Memory leaks**: Check exception handling and object lifecycle

Always use the manual CMake build approach for reliable development - the pip install method may fail due to network issues beyond your control.