git submodule update --init --recursive

# Build the main libCacheSim C++ library first
echo "Building main libCacheSim library..."
pushd src/libCacheSim
bash scripts/install_dependency.sh
rm -rf build
cmake -G Ninja -B build
ninja -C build
popd

# Now build and install the Python binding
echo "Building Python binding..."
echo "Sync python version..."
python scripts/sync_version.py
python -m pip install -e . -vvv

# Test that the import works
echo "Testing import..."
python -c "import libcachesim"

# Run tests
python -m pip install pytest
python -m pytest tests