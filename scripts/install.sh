git submodule update --init --recursive
# Sync submodules
git submodule update --recursive --remote


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