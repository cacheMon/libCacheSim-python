cmake_minimum_required(VERSION 3.15...3.27)
project(libCacheSim-python)
set(DESCRIPTION "The libCacheSim Python Package")
set(PROJECT_WEB "http://cachemon.github.io/libCacheSim-python")

# Auto-initialize submodules if not already done
find_package(Git QUIET)
if(GIT_FOUND AND EXISTS "${PROJECT_SOURCE_DIR}/.git")
    # Check if submodule is initialized
    if(NOT EXISTS "${PROJECT_SOURCE_DIR}/src/libCacheSim/CMakeLists.txt")
        message(STATUS "Initializing git submodules...")
        execute_process(COMMAND ${GIT_EXECUTABLE} submodule update --init --recursive
                        WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}
                        RESULT_VARIABLE GIT_SUBMOD_RESULT)
        if(NOT GIT_SUBMOD_RESULT EQUAL "0")
            message(FATAL_ERROR "git submodule update --init --recursive failed with ${GIT_SUBMOD_RESULT}")
        endif()
    endif()
endif()

# Auto-build libCacheSim if needed
set(LIBCACHESIM_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/src/libCacheSim")
if(NOT EXISTS "${LIBCACHESIM_SOURCE_DIR}/CMakeLists.txt")
    message(FATAL_ERROR "libCacheSim submodule not found. Please run 'git submodule update --init --recursive'")
endif()

# Build libCacheSim first
set(LIBCACHESIM_BUILD_DIR "${CMAKE_CURRENT_SOURCE_DIR}/src/libCacheSim/build")
if(NOT EXISTS "${LIBCACHESIM_BUILD_DIR}/export_vars.cmake")
    message(STATUS "Building libCacheSim...")
    execute_process(
        COMMAND ${CMAKE_COMMAND} -S ${LIBCACHESIM_SOURCE_DIR} -B ${LIBCACHESIM_BUILD_DIR} -G Ninja
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
        RESULT_VARIABLE CMAKE_CONFIG_RESULT
    )
    if(NOT CMAKE_CONFIG_RESULT EQUAL "0")
        message(FATAL_ERROR "Failed to configure libCacheSim")
    endif()
    
    execute_process(
        COMMAND ${CMAKE_COMMAND} --build ${LIBCACHESIM_BUILD_DIR}
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
        RESULT_VARIABLE CMAKE_BUILD_RESULT
    )
    if(NOT CMAKE_BUILD_RESULT EQUAL "0")
        message(FATAL_ERROR "Failed to build libCacheSim")
    endif()
endif()

# Note(haocheng): now we still utilize the exported cache from 
# the main project, which should be deprecated soon 

# Include exported variables from cache
if(DEFINED LIBCB_BUILD_DIR)
    set(MAIN_PROJECT_BUILD_DIR "${LIBCB_BUILD_DIR}")
    message(STATUS "Using provided LIBCB_BUILD_DIR: ${LIBCB_BUILD_DIR}")
else()
    set(MAIN_PROJECT_BUILD_DIR "${CMAKE_CURRENT_SOURCE_DIR}/src/libCacheSim/build")
endif()
set(EXPORT_FILE "${MAIN_PROJECT_BUILD_DIR}/export_vars.cmake")

if(EXISTS "${EXPORT_FILE}")
    include("${EXPORT_FILE}")
    message(STATUS "Loaded variables from export_vars.cmake")
else()
    message(FATAL_ERROR "export_vars.cmake not found at ${EXPORT_FILE}. Please build the main project first (e.g. cd .. && cmake -G Ninja -B build)")
endif()

# Force enable -fPIC
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -fPIC")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fPIC")

project(libCacheSim-python VERSION "${LIBCACHESIM_VERSION}")

if(LOG_LEVEL_LOWER STREQUAL "default")
    if(CMAKE_BUILD_TYPE_LOWER MATCHES "debug")
        add_compile_definitions(LOGLEVEL=6)
    else()
        add_compile_definitions(LOGLEVEL=7)
    endif()
elseif(LOG_LEVEL_LOWER STREQUAL "verbose")
    add_compile_definitions(LOGLEVEL=5)
elseif(LOG_LEVEL_LOWER STREQUAL "debug")
    add_compile_definitions(LOGLEVEL=6)
elseif(LOG_LEVEL_LOWER STREQUAL "info")
    add_compile_definitions(LOGLEVEL=7)
elseif(LOG_LEVEL_LOWER STREQUAL "warn")
    add_compile_definitions(LOGLEVEL=8)
elseif(LOG_LEVEL_LOWER STREQUAL "error")
    add_compile_definitions(LOGLEVEL=9)
else()
    add_compile_definitions(LOGLEVEL=7)
endif()

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find python and pybind11
find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)
find_package(pybind11 CONFIG REQUIRED)

# Include directories for dependencies
include_directories(${GLib_INCLUDE_DIRS})
include_directories(${GLib_CONFIG_INCLUDE_DIR})
include_directories(${XGBOOST_INCLUDE_DIR})
include_directories(${LIGHTGBM_PATH})
include_directories(${ZSTD_INCLUDE_DIR})
include_directories(${MAIN_PROJECT_SOURCE_DIR}/libCacheSim/bin)

# Find the main libCacheSim library
set(MAIN_PROJECT_BUILD_DIR "${MAIN_PROJECT_BUILD_DIR}")
set(MAIN_PROJECT_LIB_PATH "${MAIN_PROJECT_BUILD_DIR}/liblibCacheSim.a")

if(EXISTS "${MAIN_PROJECT_LIB_PATH}")
    message(STATUS "Found pre-built libCacheSim library at ${MAIN_PROJECT_LIB_PATH}")

    # Import the main library as an imported target
    add_library(libCacheSim_main STATIC IMPORTED)
    set_target_properties(libCacheSim_main PROPERTIES
        IMPORTED_LOCATION "${MAIN_PROJECT_LIB_PATH}"
        INTERFACE_INCLUDE_DIRECTORIES "${MAIN_PROJECT_SOURCE_DIR}/libCacheSim/include;${MAIN_PROJECT_SOURCE_DIR}/libCacheSim/utils/include;${MAIN_PROJECT_SOURCE_DIR}/libCacheSim"
    )
    link_directories(${GLib_LIBRARY_DIRS})
    link_directories(${ZSTD_LIBRARY_DIRS})
    set(LIBCACHESIM_TARGET libCacheSim_main)

else()
    message(FATAL_ERROR "Pre-built libCacheSim library not found. Please build the main project first: cd .. && cmake -G Ninja -B build && ninja -C build")
endif()

include_directories(src)

python_add_library(libcachesim_python MODULE
    src/export.cpp
    src/export_cache.cpp
    src/export_reader.cpp
    src/export_analyzer.cpp
    src/export_misc.cpp
    src/exception.cpp
    ${MAIN_PROJECT_SOURCE_DIR}/libCacheSim/bin/cli_reader_utils.c
    ${MAIN_PROJECT_SOURCE_DIR}/libCacheSim/bin/traceUtils/traceConvLCS.cpp
    ${MAIN_PROJECT_SOURCE_DIR}/libCacheSim/bin/traceUtils/traceConvOracleGeneral.cpp
    ${MAIN_PROJECT_SOURCE_DIR}/libCacheSim/bin/traceUtils/utils.cpp
    WITH_SOABI
)

set_target_properties(libcachesim_python PROPERTIES
    POSITION_INDEPENDENT_CODE ON
    INSTALL_RPATH_USE_LINK_PATH TRUE
    BUILD_WITH_INSTALL_RPATH TRUE
    INSTALL_RPATH "$ORIGIN"
)

target_compile_definitions(libcachesim_python PRIVATE VERSION_INFO=${PROJECT_VERSION})

target_link_libraries(libcachesim_python PRIVATE
    ${LIBCACHESIM_TARGET}
    pybind11::headers
    pybind11::module
    ${GLib_LIBRARIES}
    ${ZSTD_LIBRARIES}
)

# Add platform-specific link options and libraries
if(CMAKE_SYSTEM_NAME STREQUAL "Linux")
    # GNU ld option, only available on Linux
    target_link_options(libcachesim_python PRIVATE -Wl,--no-as-needed)
    target_link_libraries(libcachesim_python PRIVATE dl)
elseif(CMAKE_SYSTEM_NAME STREQUAL "Darwin")
    # macOS doesn't need --no-as-needed
    # dl functions are part of the system library on macOS
    # No need to explicitly link dl

    # Find argp library on macOS
    find_library(ARGP_LIBRARY argp PATHS /opt/homebrew/lib /usr/local/lib)
    if(ARGP_LIBRARY)
        target_link_libraries(libcachesim_python PRIVATE ${ARGP_LIBRARY})
    endif()

    # Find and link other dependencies that might be needed
    find_library(INTL_LIBRARY intl PATHS /opt/homebrew/lib /usr/local/lib)
    if(INTL_LIBRARY)
        target_link_libraries(libcachesim_python PRIVATE ${INTL_LIBRARY})
    endif()
else()
    # Other platforms - try to link dl if available
    find_library(DL_LIBRARY dl)
    if(DL_LIBRARY)
        target_link_libraries(libcachesim_python PRIVATE ${DL_LIBRARY})
    endif()
endif()

# install to wheel directory
install(TARGETS libcachesim_python LIBRARY DESTINATION libcachesim)
