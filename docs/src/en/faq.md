# Frequently Asked Questions

1.  How to resolve when pip install fails?

    See [installation](https://cachemon.github.io/libCacheSim-python/getting_started/installation/).

2.  Get an error message like "cannot find Python package" when building.

    The reason is that when building a Python binding package, we need the header and other necessary modules.
    
    If you can install software directly,

    ```shell
    [sudo] apt install python3-dev
    ```
    If not, please install Python somewhere and set environment variables to help the building system find them.
    
    ```shell
    export CMAKE_ARGS="-DPython3_ROOT_DIR=${Python3_ROOT_DIR} -DPython3_INCLUDE_DIR=${Python3_INCLUDE_DIR} -DPython3_EXECUTABLE=${Python3_EXECUTABLE}"
    ```
