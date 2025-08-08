#!/bin/bash
set -euo pipefail

function usage() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -h, --help    Show this help message"
    echo "  -b, --build-wheels   Build the Python wheels"
    echo "  -a, --all   Install with optional dependencies for development"
    exit 1
}
# Parse command line arguments
BUILD_WHEELS=0
CMAKE_ARGS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            ;;
        -b|--build-wheels)
            BUILD_WHEELS=1
            shift
            ;;
        -a|--all)
            CMAKE_ARGS="-DENABLE_LRB=ON -DENABLE_GLCACHE=ON -DENABLE_3L_CACHE=ON"
            BUILD_WHEELS=0
            shift
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# For submodule update
git submodule update --init --recursive
git submodule update --recursive --remote
if [ $? -ne 0 ]; then
  echo "Error: git submodule update failed"
  exit 1
fi

python scripts/sync_version.py
CMAKE_ARGS=$CMAKE_ARGS python -m pip install -e . -vvv

# Test that the import works
echo "Testing import..."
python -c "import libcachesim"

# Run tests
python -m pip install pytest
python -m pytest tests
if [[ "$CMAKE_ARGS" == *"-DENABLE_LRB=ON"* && "$CMAKE_ARGS" == *"-DENABLE_GLCACHE=ON"* && "$CMAKE_ARGS" == *"-DENABLE_3L_CACHE=ON"* ]]; then
    echo "Running tests for optional eviction algos..."
    python -m pytest tests -m "optional"
fi

# Build wheels if requested
if [[ $BUILD_WHEELS -eq 1 ]]; then
    echo "--- Building Python wheels for distribution ---"

    # --- Environment and dependency checks ---
    echo "Checking dependencies: python3, pip, docker, cibuildwheel..."

    if ! command -v python3 &> /dev/null; then
        echo "Error: python3 is not installed. Please install it and run this script again."
        exit 1
    fi

    if ! python3 -m pip --version &> /dev/null; then
        echo "Error: pip for python3 is not available. Please install it."
        exit 1
    fi

    if ! command -v docker &> /dev/null; then
        echo "Error: docker is not installed. Please install it and ensure the docker daemon is running."
        exit 1
    fi

    # Check if user can run docker without sudo, otherwise use sudo
    SUDO_CMD=""
    if ! docker ps &> /dev/null; then
        echo "Warning: Current user cannot run docker. Trying with sudo."
        if sudo docker ps &> /dev/null; then
            SUDO_CMD="sudo"
        else
            echo "Error: Failed to run docker, even with sudo. Please check your docker installation and permissions."
            exit 1
        fi
    fi

    if ! python3 -m cibuildwheel --version &> /dev/null; then
        echo "cibuildwheel not found, installing..."
        python3 -m pip install cibuildwheel
    fi

    echo "Dependency check completed."

    # --- Run cibuildwheel ---
    # The project to build is specified as an argument.
    # cibuildwheel should be run from the repository root.
    # The output directory will be 'wheelhouse/' by default.
    echo "Starting the wheel build process for Linux..."
    ${SUDO_CMD} python3 -m cibuildwheel --platform linux .

    echo "Build process completed successfully. Wheels are in the 'wheelhouse' directory."
fi