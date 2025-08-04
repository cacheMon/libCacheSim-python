# Frequently Asked Questions

1.  How to resolve when pip install fails?

    See [installation](https://cachemon.github.io/libCacheSim-python/getting_started/installation/).

2.  Get an error message like "cannot find Python package" when building.

    The reason is that building Python bindings requires Python's development headers and libraries.
    
    If you have administrative privileges, you can use your system's package manager to install the required package. For example:
    *   **Debian/Ubuntu**: `sudo apt install python3-dev`
    *   **RHEL/CentOS/Fedora**: `sudo yum install python3-devel`
    *   **macOS**: Installing Python with Homebrew (`brew install python`) is usually sufficient.

    Alternatively, if you installed Python in a custom location, you must set environment variables to help the build system find it. Remember to replace the placeholders in the command below with your actual paths.
    
    ```shell
    export CMAKE_ARGS="-DPython3_ROOT_DIR=${Python3_ROOT_DIR} -DPython3_INCLUDE_DIR=${Python3_INCLUDE_DIR} -DPython3_EXECUTABLE=${Python3_EXECUTABLE}"
    ```
