cmake_minimum_required(VERSION 3.15...3.27)
project(libCacheSim-python)

# Project metadata
set(DESCRIPTION "The libCacheSim Python Package")
set(PROJECT_WEB "https://docs.libcachesim.com/python")

# Build type configuration
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Debug CACHE STRING "Debug" FORCE)
endif()
message(STATUS "CMAKE_BUILD_TYPE: ${CMAKE_BUILD_TYPE}")

# Options
option(ENABLE_GLCACHE "Enable group-learned cache" OFF)
option(ENABLE_LRB "Enable LRB" OFF)
option(ENABLE_3L_CACHE "Enable 3LCache" OFF)

# C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# =============================================================================
# Compiler Flags Configuration
# =============================================================================

# Base flags for all compilers
set(BASE_C_FLAGS "-fPIC -fno-strict-overflow -fno-strict-aliasing")
set(BASE_CXX_FLAGS "-fPIC -fno-strict-overflow -fno-strict-aliasing")

# Compiler-specific flags
if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    set(COMPILER_SPECIFIC_FLAGS "-Wno-cast-user-defined -Wno-array-bounds -Wno-type-limits")
elseif(CMAKE_CXX_COMPILER_ID STREQUAL "Clang")
    set(COMPILER_SPECIFIC_FLAGS "-Wno-array-bounds")
else()
    set(COMPILER_SPECIFIC_FLAGS "")
endif()

# Apply flags
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${BASE_C_FLAGS}")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${BASE_CXX_FLAGS} ${COMPILER_SPECIFIC_FLAGS}")

# =============================================================================
# Git Submodule Management
# =============================================================================

function(initialize_submodules)
    find_package(Git QUIET)
    if(GIT_FOUND AND EXISTS "${PROJECT_SOURCE_DIR}/.git")
        if(NOT EXISTS "${PROJECT_SOURCE_DIR}/src/libCacheSim/CMakeLists.txt")
            message(STATUS "Initializing git submodules...")
            execute_process(
                COMMAND ${GIT_EXECUTABLE} submodule update --init --recursive
                WORKING_DIRECTORY ${PROJECT_SOURCE_DIR}
                RESULT_VARIABLE GIT_SUBMOD_RESULT
            )
            if(NOT GIT_SUBMOD_RESULT EQUAL "0")
                message(FATAL_ERROR "git submodule update --init --recursive failed with ${GIT_SUBMOD_RESULT}")
            endif()
        endif()
    endif()
endfunction()

initialize_submodules()

# =============================================================================
# libCacheSim Build Configuration
# =============================================================================

set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${CMAKE_CURRENT_SOURCE_DIR}/src/libCacheSim/cmake/Modules/")
set(LIBCACHESIM_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/src/libCacheSim")
set(LIBCACHESIM_BUILD_DIR "${CMAKE_CURRENT_SOURCE_DIR}/src/libCacheSim/build")

if(NOT EXISTS "${LIBCACHESIM_SOURCE_DIR}/CMakeLists.txt")
    message(FATAL_ERROR "libCacheSim submodule not found. Please run 'git submodule update --init --recursive'")
endif()

function(build_libcachesim)
    message(STATUS "Building libCacheSim...")
    
    # Prepare CMake arguments for subproject
    set(CMAKE_ARGS
        "-DCMAKE_C_FLAGS=${BASE_C_FLAGS}"
        "-DCMAKE_CXX_FLAGS=${BASE_CXX_FLAGS} ${COMPILER_SPECIFIC_FLAGS}"
        "-DCMAKE_CXX_FLAGS_DEBUG=-g ${BASE_CXX_FLAGS} ${COMPILER_SPECIFIC_FLAGS}"
        "-DCMAKE_CXX_FLAGS_RELEASE=-O3 ${BASE_CXX_FLAGS} ${COMPILER_SPECIFIC_FLAGS}"
        "-DCMAKE_CXX_FLAGS_RELWITHDEBINFO=-O2 -g -DNDEBUG ${BASE_CXX_FLAGS} ${COMPILER_SPECIFIC_FLAGS}"
    )
    
    # Configure libCacheSim
    execute_process(
        COMMAND ${CMAKE_COMMAND} 
            -S ${LIBCACHESIM_SOURCE_DIR} 
            -B ${LIBCACHESIM_BUILD_DIR} 
            -G Ninja 
            -DENABLE_LRB=${ENABLE_LRB} 
            -DENABLE_GLCACHE=${ENABLE_GLCACHE} 
            -DENABLE_3L_CACHE=${ENABLE_3L_CACHE} 
            -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE} 
            ${CMAKE_ARGS}
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
        RESULT_VARIABLE CMAKE_CONFIG_RESULT
    )
    if(NOT CMAKE_CONFIG_RESULT EQUAL "0")
        message(FATAL_ERROR "Failed to configure libCacheSim")
    endif()
    
    # Build libCacheSim
    execute_process(
        COMMAND ${CMAKE_COMMAND} --build ${LIBCACHESIM_BUILD_DIR}
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
        RESULT_VARIABLE CMAKE_BUILD_RESULT
    )
    if(NOT CMAKE_BUILD_RESULT EQUAL "0")
        message(FATAL_ERROR "Failed to build libCacheSim")
    endif()
endfunction()

build_libcachesim()

# =============================================================================
# Logging Configuration
# =============================================================================

function(configure_logging)
    string(TOLOWER "${LOG_LEVEL}" LOG_LEVEL_LOWER)
    string(TOLOWER "${CMAKE_BUILD_TYPE}" CMAKE_BUILD_TYPE_LOWER)
    
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
endfunction()

configure_logging()

# =============================================================================
# Dependency Management
# =============================================================================

# Find required packages
find_package(Python3 REQUIRED COMPONENTS Interpreter Development.Module)
find_package(pybind11 CONFIG REQUIRED)
find_package(PkgConfig REQUIRED)

# Initialize dependency lists
set(required_libs "")
set(optional_libs "")

# GLib dependency
pkg_check_modules(GLib REQUIRED glib-2.0)
include_directories(${GLib_INCLUDE_DIRS})
link_directories(${GLib_LIBRARY_DIRS})
list(APPEND required_libs ${GLib_LIBRARIES})

# ZSTD dependency
find_package(ZSTD REQUIRED)
message(STATUS "ZSTD_INCLUDE_DIR: ${ZSTD_INCLUDE_DIR}, ZSTD_LIBRARIES: ${ZSTD_LIBRARIES}")
if("${ZSTD_LIBRARIES}" STREQUAL "")
    message(FATAL_ERROR "zstd not found")
endif()
include_directories(${ZSTD_INCLUDE_DIR})
link_directories(${ZSTD_LIBRARY_DIRS})
list(APPEND required_libs ${ZSTD_LIBRARIES})

# Optional dependencies based on features
if(ENABLE_GLCACHE)
    find_package(xgboost REQUIRED)
    include_directories(${XGBOOST_INCLUDE_DIR})
    list(APPEND optional_libs xgboost::xgboost)
    add_compile_definitions(ENABLE_GLCACHE=1)
    message(STATUS "XGBOOST_INCLUDE_DIR: ${XGBOOST_INCLUDE_DIR}")
endif()

# LightGBM for LRB and 3L_CACHE
set(LIGHTGBM_FEATURES ENABLE_LRB ENABLE_3L_CACHE)
set(LIGHTGBM_NEEDED FALSE)

foreach(FEATURE ${LIGHTGBM_FEATURES})
    if(${FEATURE})
        set(LIGHTGBM_NEEDED TRUE)
        add_compile_definitions(${FEATURE}=1)
    endif()
endforeach()

if(LIGHTGBM_NEEDED)
    if(NOT DEFINED LIGHTGBM_PATH)
        find_path(LIGHTGBM_PATH LightGBM)
    endif()
    if(NOT LIGHTGBM_PATH)
        message(FATAL_ERROR "LIGHTGBM_PATH not found")
    endif()
    
    if(NOT DEFINED LIGHTGBM_LIB)
        find_library(LIGHTGBM_LIB _lightgbm)
    endif()
    if(NOT LIGHTGBM_LIB)
        message(FATAL_ERROR "LIGHTGBM_LIB not found")
    endif()
    
    include_directories(${LIGHTGBM_PATH})
    list(APPEND optional_libs ${LIGHTGBM_LIB})
endif()

# =============================================================================
# libCacheSim Library Target
# =============================================================================

set(MAIN_PROJECT_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/src/libCacheSim")
set(MAIN_PROJECT_BUILD_DIR "${LIBCACHESIM_BUILD_DIR}")
set(MAIN_PROJECT_LIB_PATH "${MAIN_PROJECT_BUILD_DIR}/liblibCacheSim.a")

if(NOT EXISTS "${MAIN_PROJECT_LIB_PATH}")
    message(FATAL_ERROR "Pre-built libCacheSim library not found at ${MAIN_PROJECT_LIB_PATH}. Please build the main project first.")
endif()

message(STATUS "Found pre-built libCacheSim library at ${MAIN_PROJECT_LIB_PATH}")

# Import the main library as an imported target
add_library(libCacheSim_main STATIC IMPORTED)
set_target_properties(libCacheSim_main PROPERTIES
    IMPORTED_LOCATION "${MAIN_PROJECT_LIB_PATH}"
    INTERFACE_INCLUDE_DIRECTORIES 
        "${MAIN_PROJECT_SOURCE_DIR}/libCacheSim/include;${MAIN_PROJECT_SOURCE_DIR}/libCacheSim/utils/include;${MAIN_PROJECT_SOURCE_DIR}/libCacheSim"
)

# =============================================================================
# Python Module Configuration
# =============================================================================

include_directories(src)
include_directories(${MAIN_PROJECT_SOURCE_DIR}/libCacheSim/bin)

# Define source files
set(PYTHON_MODULE_SOURCES
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
)

# Create Python module
pybind11_add_module(libcachesim_python ${PYTHON_MODULE_SOURCES} WITH_SOABI)

# Configure target properties
set_target_properties(libcachesim_python PROPERTIES
    POSITION_INDEPENDENT_CODE ON
    INSTALL_RPATH_USE_LINK_PATH TRUE
    BUILD_WITH_INSTALL_RPATH TRUE
    INSTALL_RPATH "$ORIGIN"
)

target_compile_definitions(libcachesim_python PRIVATE VERSION_INFO=${PROJECT_VERSION})

# =============================================================================
# Platform-Specific Configuration
# =============================================================================

function(configure_platform_specific_linking target)
    if(CMAKE_SYSTEM_NAME STREQUAL "Linux")
        target_link_options(${target} PRIVATE -Wl,--no-as-needed)
        target_link_libraries(${target} PRIVATE dl)
    elseif(CMAKE_SYSTEM_NAME STREQUAL "Darwin")
        # Find argp library on macOS
        find_library(ARGP_LIBRARY argp PATHS /opt/homebrew/lib /usr/local/lib)
        if(ARGP_LIBRARY)
            target_link_libraries(${target} PRIVATE ${ARGP_LIBRARY})
        endif()
        
        # Find and link intl library
        find_library(INTL_LIBRARY intl PATHS /opt/homebrew/lib /usr/local/lib)
        if(INTL_LIBRARY)
            target_link_libraries(${target} PRIVATE ${INTL_LIBRARY})
        endif()
    else()
        # Other platforms - try to link dl if available
        find_library(DL_LIBRARY dl)
        if(DL_LIBRARY)
            target_link_libraries(${target} PRIVATE ${DL_LIBRARY})
        endif()
    endif()
endfunction()

# Link libraries
target_link_libraries(libcachesim_python PRIVATE
    libCacheSim_main
    pybind11::headers
    pybind11::module
    ${required_libs}
    ${optional_libs}
)

configure_platform_specific_linking(libcachesim_python)

# =============================================================================
# Installation
# =============================================================================

install(TARGETS libcachesim_python LIBRARY DESTINATION libcachesim)