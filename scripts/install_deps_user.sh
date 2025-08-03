#!/bin/bash

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
USER_PREFIX="${HOME}/local"
USER_BIN="${USER_PREFIX}/bin"
USER_LIB="${USER_PREFIX}/lib"
USER_INCLUDE="${USER_PREFIX}/include"

# Detect system package manager
detect_package_manager() {
    if command -v apt-get >/dev/null 2>&1; then
        echo "apt"
    elif command -v yum >/dev/null 2>&1; then
        echo "yum"
    elif command -v dnf >/dev/null 2>&1; then
        echo "dnf"
    elif command -v pacman >/dev/null 2>&1; then
        echo "pacman"
    else
        echo "unknown"
    fi
}

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Setup user directories
setup_directories() {
    log_step "Setting up user directories..."
    mkdir -p "${USER_PREFIX}"/{bin,lib,include,share}
    mkdir -p "${HOME}/src"
    
    # Update environment variables
    export PATH="${USER_BIN}:${PATH}"
    export LD_LIBRARY_PATH="${USER_LIB}:${USER_PREFIX}/lib64:${LD_LIBRARY_PATH:-}"
    export PKG_CONFIG_PATH="${USER_LIB}/pkgconfig:${PKG_CONFIG_PATH:-}"
    export CPPFLAGS="-I${USER_INCLUDE} ${CPPFLAGS:-}"
    export LDFLAGS="-L${USER_LIB} -L${USER_PREFIX}/lib64 ${LDFLAGS:-}"
    export CMAKE_PREFIX_PATH="${USER_LIB}/cmake:${CMAKE_PREFIX_PATH:-}"
    
    log_info "User prefix: ${USER_PREFIX}"
}

# Add environment setup to shell config
setup_environment() {
    log_step "Setting up environment variables..."
    
    local env_setup="
# User-installed dependencies
export PATH=\"${USER_BIN}:\$PATH\"
export LD_LIBRARY_PATH=\"${USER_LIB}:${USER_PREFIX}/lib64:\${LD_LIBRARY_PATH:-}\"
export PKG_CONFIG_PATH=\"${USER_LIB}/pkgconfig:\${PKG_CONFIG_PATH:-}\"
export CPPFLAGS=\"-I${USER_INCLUDE} \${CPPFLAGS:-}\"
export LDFLAGS=\"-L${USER_LIB} -L${USER_PREFIX}/lib64 \${LDFLAGS:-}\"
export CMAKE_PREFIX_PATH=\"${USER_LIB}/cmake:\${CMAKE_PREFIX_PATH:-}\"
"
    
    for shell_rc in "${HOME}/.bashrc" "${HOME}/.zshrc" "${HOME}/.profile"; do
        if [[ -f "${shell_rc}" ]] && ! grep -q "User-installed dependencies" "${shell_rc}"; then
            echo "${env_setup}" >> "${shell_rc}"
            log_info "Added environment setup to ${shell_rc}"
        fi
    done
}

# Download and extract function
download_and_extract() {
    local url="$1"
    local filename="$2"
    
    log_info "Downloading ${filename}..."
    if [[ ! -f "${filename}" ]]; then
        wget -O "${filename}" "${url}" || curl -L -o "${filename}" "${url}"
    fi
    
    log_info "Extracting ${filename}..."
    if [[ "${filename}" == *.tar.gz ]] || [[ "${filename}" == *.tgz ]]; then
        tar -xzf "${filename}"
    elif [[ "${filename}" == *.tar.bz2 ]]; then
        tar -xjf "${filename}"
    elif [[ "${filename}" == *.tar.xz ]]; then
        tar -xJf "${filename}"
    elif [[ "${filename}" == *.zip ]]; then
        unzip -q "${filename}"
    fi
}

# Install CMake
install_cmake() {
    log_step "Installing CMake..."
    local cmake_version="3.31.0"
    local cmake_dir="${HOME}/src/cmake"
    
    pushd "${HOME}/src" >/dev/null
    
    if [[ ! -d "${cmake_dir}" ]]; then
        download_and_extract \
            "https://github.com/Kitware/CMake/releases/download/v${cmake_version}/cmake-${cmake_version}-linux-x86_64.tar.gz" \
            "cmake-${cmake_version}-linux-x86_64.tar.gz"
        
        mv "cmake-${cmake_version}-linux-x86_64" "${cmake_dir}"
    fi
    
    # Create symlinks
    ln -sf "${cmake_dir}/bin/cmake" "${USER_BIN}/cmake"
    ln -sf "${cmake_dir}/bin/ctest" "${USER_BIN}/ctest"
    ln -sf "${cmake_dir}/bin/cpack" "${USER_BIN}/cpack"
    
    popd >/dev/null
    log_info "CMake installed: $(cmake --version | head -n1)"
}

# Install Ninja build system
install_ninja() {
    log_step "Installing Ninja..."
    local ninja_version="1.11.1"
    
    pushd "${HOME}/src" >/dev/null
    
    if [[ ! -f "${USER_BIN}/ninja" ]]; then
        download_and_extract \
            "https://github.com/ninja-build/ninja/releases/download/v${ninja_version}/ninja-linux.zip" \
            "ninja-linux.zip"
        
        chmod +x ninja
        mv ninja "${USER_BIN}/"
    fi
    
    popd >/dev/null
    log_info "Ninja installed: $(ninja --version)"
}

# Install Zstd
install_zstd() {
    log_step "Installing Zstd..."
    local zstd_version="1.5.5"
    
    pushd "${HOME}/src" >/dev/null
    
    if [[ ! -f "${USER_LIB}/libzstd.so" ]]; then
        download_and_extract \
            "https://github.com/facebook/zstd/releases/download/v${zstd_version}/zstd-${zstd_version}.tar.gz" \
            "zstd-${zstd_version}.tar.gz"
        
        pushd "zstd-${zstd_version}" >/dev/null
        make -j$(nproc)
        make install PREFIX="${USER_PREFIX}"
        
        # Create pkg-config file for Zstd
        mkdir -p "${USER_LIB}/pkgconfig"
        cat > "${USER_LIB}/pkgconfig/libzstd.pc" << EOF
prefix=${USER_PREFIX}
exec_prefix=\${prefix}
libdir=\${exec_prefix}/lib
includedir=\${prefix}/include

Name: libzstd
Description: fast compression library
URL: https://facebook.github.io/zstd/
Version: ${zstd_version}
Libs: -L\${libdir} -lzstd
Cflags: -I\${includedir}
EOF
        
        popd >/dev/null
    fi
    
    popd >/dev/null
    log_info "Zstd installed successfully"
}

# Install Google Perftools (tcmalloc)
install_perftools() {
    log_step "Installing Google Perftools..."
    local perftools_version="2.13"
    
    pushd "${HOME}/src" >/dev/null
    
    if [[ ! -f "${USER_LIB}/libtcmalloc.so" ]]; then
        download_and_extract \
            "https://github.com/gperftools/gperftools/releases/download/gperftools-${perftools_version}/gperftools-${perftools_version}.tar.gz" \
            "gperftools-${perftools_version}.tar.gz"
        
        pushd "gperftools-${perftools_version}" >/dev/null
        ./configure --prefix="${USER_PREFIX}"
        make -j$(nproc)
        make install
        
        # Create pkg-config file for tcmalloc
        mkdir -p "${USER_LIB}/pkgconfig"
        cat > "${USER_LIB}/pkgconfig/libtcmalloc.pc" << EOF
prefix=${USER_PREFIX}
exec_prefix=\${prefix}
libdir=\${exec_prefix}/lib
includedir=\${prefix}/include

Name: libtcmalloc
Description: Google's fast malloc library
URL: https://github.com/gperftools/gperftools
Version: ${perftools_version}
Libs: -L\${libdir} -ltcmalloc
Cflags: -I\${includedir}
EOF
        
        popd >/dev/null
    fi
    
    popd >/dev/null
    log_info "Google Perftools installed successfully"
}

# Install XGBoost
install_xgboost() {
    log_step "Installing XGBoost..."
    
    pushd "${HOME}/src" >/dev/null
    
    if [[ ! -d "xgboost" ]]; then
        git clone --recursive https://github.com/dmlc/xgboost.git
    fi
    
    pushd xgboost >/dev/null
    git pull origin master
    git submodule update --init --recursive
    
    mkdir -p build
    pushd build >/dev/null
    cmake -G Ninja -DCMAKE_INSTALL_PREFIX="${USER_PREFIX}" ..
    ninja
    ninja install
    popd >/dev/null
    popd >/dev/null
    
    popd >/dev/null
    log_info "XGBoost installed successfully"
}

# Install LightGBM
install_lightgbm() {
    log_step "Installing LightGBM..."
    
    pushd "${HOME}/src" >/dev/null
    
    if [[ ! -d "LightGBM" ]]; then
        git clone --recursive https://github.com/microsoft/LightGBM.git
    fi
    
    pushd LightGBM >/dev/null
    git pull origin master
    git submodule update --init --recursive
    
    mkdir -p build
    pushd build >/dev/null
    cmake -G Ninja -DCMAKE_INSTALL_PREFIX="${USER_PREFIX}" ..
    ninja
    ninja install
    popd >/dev/null
    popd >/dev/null
    
    popd >/dev/null
    log_info "LightGBM installed successfully"
}

# Create CMake configuration files
create_cmake_configs() {
    log_step "Creating CMake configuration files..."
    
    # Create CMake config for Zstd
    mkdir -p "${USER_LIB}/cmake/zstd"
    cat > "${USER_LIB}/cmake/zstd/zstdConfig.cmake" << EOF
set(ZSTD_FOUND TRUE)
set(ZSTD_INCLUDE_DIRS "${USER_INCLUDE}")
set(ZSTD_LIBRARIES "${USER_LIB}/libzstd.so")
set(ZSTD_LIBRARY "${USER_LIB}/libzstd.so")
EOF

    # Create CMake config for tcmalloc
    mkdir -p "${USER_LIB}/cmake/tcmalloc"
    cat > "${USER_LIB}/cmake/tcmalloc/tcmallocConfig.cmake" << EOF
set(TCMALLOC_FOUND TRUE)
set(TCMALLOC_INCLUDE_DIRS "${USER_INCLUDE}")
set(TCMALLOC_LIBRARIES "${USER_LIB}/libtcmalloc.so")
set(TCMALLOC_LIBRARY "${USER_LIB}/libtcmalloc.so")
EOF

    # Create CMake config for XGBoost
    mkdir -p "${USER_LIB}/cmake/xgboost"
    cat > "${USER_LIB}/cmake/xgboost/xgboostConfig.cmake" << EOF
set(XGBOOST_FOUND TRUE)
set(XGBOOST_INCLUDE_DIRS "${USER_INCLUDE}")
if(EXISTS "${USER_PREFIX}/lib64/libxgboost.so")
    set(XGBOOST_LIBRARIES "${USER_PREFIX}/lib64/libxgboost.so")
    set(XGBOOST_LIBRARY "${USER_PREFIX}/lib64/libxgboost.so")
else()
    set(XGBOOST_LIBRARIES "${USER_LIB}/libxgboost.so")
    set(XGBOOST_LIBRARY "${USER_LIB}/libxgboost.so")
endif()
EOF

    # Create CMake config for LightGBM
    mkdir -p "${USER_LIB}/cmake/lightgbm"
    cat > "${USER_LIB}/cmake/lightgbm/lightgbmConfig.cmake" << EOF
set(LIGHTGBM_FOUND TRUE)
set(LIGHTGBM_INCLUDE_DIRS "${USER_INCLUDE}")
if(EXISTS "${USER_PREFIX}/lib64/lib_lightgbm.so")
    set(LIGHTGBM_LIBRARIES "${USER_PREFIX}/lib64/lib_lightgbm.so")
    set(LIGHTGBM_LIBRARY "${USER_PREFIX}/lib64/lib_lightgbm.so")
else()
    set(LIGHTGBM_LIBRARIES "${USER_LIB}/lib_lightgbm.so")
    set(LIGHTGBM_LIBRARY "${USER_LIB}/lib_lightgbm.so")
endif()
EOF

    log_info "CMake configuration files created"
}

# Verify installations
verify_installations() {
    log_step "Verifying installations..."
    
    local errors=0
    
    # Check Zstd
    if [[ ! -f "${USER_LIB}/libzstd.so" ]]; then
        log_error "Zstd library not found: ${USER_LIB}/libzstd.so"
        ((errors++))
    else
        log_info "✓ Zstd library found"
    fi
    
    # Check tcmalloc
    if [[ ! -f "${USER_LIB}/libtcmalloc.so" ]]; then
        log_error "tcmalloc library not found: ${USER_LIB}/libtcmalloc.so"
        ((errors++))
    else
        log_info "✓ tcmalloc library found"
    fi
    
    # Check XGBoost
    if [[ ! -f "${USER_LIB}/libxgboost.so" ]] && [[ ! -f "${USER_PREFIX}/lib64/libxgboost.so" ]]; then
        log_warn "XGBoost library not found: ${USER_LIB}/libxgboost.so or ${USER_PREFIX}/lib64/libxgboost.so"
    else
        log_info "✓ XGBoost library found"
    fi
    
    # Check LightGBM
    if [[ ! -f "${USER_LIB}/lib_lightgbm.so" ]]; then
        log_warn "LightGBM library not found: ${USER_LIB}/lib_lightgbm.so"
    else
        log_info "✓ LightGBM library found"
    fi
    
    if [[ $errors -gt 0 ]]; then
        log_error "Installation verification failed with $errors error(s)"
        return 1
    else
        log_info "All core libraries verified successfully"
    fi
}

# Check system dependencies
check_system_dependencies() {
    log_step "Checking system dependencies..."
    
    local pkg_manager=$(detect_package_manager)
    log_info "Detected package manager: ${pkg_manager}"
    
    # Check for essential build tools
    local missing_tools=()
    
    if ! command -v gcc >/dev/null 2>&1; then
        missing_tools+=("gcc")
    fi
    
    if ! command -v make >/dev/null 2>&1; then
        missing_tools+=("make")
    fi
    
    if ! command -v wget >/dev/null 2>&1 && ! command -v curl >/dev/null 2>&1; then
        missing_tools+=("wget or curl")
    fi
    
    if ! command -v git >/dev/null 2>&1; then
        missing_tools+=("git")
    fi
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log_warn "Missing system dependencies: ${missing_tools[*]}"
        log_info "Please install them using your system package manager:"
        
        case "${pkg_manager}" in
            "apt")
                log_info "  sudo apt update && sudo apt install build-essential wget git"
                ;;
            "yum")
                log_info "  sudo yum groupinstall 'Development Tools' && sudo yum install wget git"
                ;;
            "dnf")
                log_info "  sudo dnf groupinstall 'Development Tools' && sudo dnf install wget git"
                ;;
            "pacman")
                log_info "  sudo pacman -S base-devel wget git"
                ;;
            *)
                log_warn "Unknown package manager. Please install: ${missing_tools[*]}"
                ;;
        esac
        
        log_warn "Continuing with installation, but some tools may fail..."
    else
        log_info "All essential build tools are available"
    fi
}

# Main installation function
main() {
    log_info "Starting user-level dependency installation..."
    log_warn "This script will install dependencies to ${USER_PREFIX}"
    log_warn "Make sure to source your shell config after installation!"
    
    # Check system dependencies first
    check_system_dependencies
    
    setup_directories
    setup_environment
    
    # Install build tools
    install_cmake
    install_ninja
    
    # Install libraries
    install_zstd
    install_perftools
    
    # Install ML libraries (optional, comment out if not needed)
    if command -v git >/dev/null 2>&1; then
        install_xgboost
        install_lightgbm
    else
        log_warn "Git not available, skipping XGBoost and LightGBM"
    fi
    
    # Create CMake configuration files
    create_cmake_configs
    
    # Verify installations
    verify_installations
    
    log_info "Installation completed!"
    log_info "Please run: source ~/.bashrc (or your shell config file)"
    log_info "Or start a new terminal session to use the installed dependencies."
    
    echo
    log_info "Installed tools:"
    echo "  - CMake: ${USER_BIN}/cmake"
    echo "  - Ninja: ${USER_BIN}/ninja" 
    echo "  - XGBoost: ${USER_LIB}/libxgboost.so"
    echo "  - LightGBM: ${USER_LIB}/lib_lightgbm.so"
    echo "  - Libraries in: ${USER_LIB}"
    echo "  - Headers in: ${USER_INCLUDE}"
    
    echo
    log_info "To build libCacheSim with these dependencies, use:"
    echo "  mkdir build && cd build"
    echo "  cmake -DCMAKE_PREFIX_PATH=\"${USER_LIB}/cmake\" .."
    echo "  make -j$(nproc)"
    echo
    log_info "Or set these environment variables before building:"
    echo "  export CMAKE_PREFIX_PATH=\"${USER_LIB}/cmake:\$CMAKE_PREFIX_PATH\""
    echo "  export PKG_CONFIG_PATH=\"${USER_LIB}/pkgconfig:\$PKG_CONFIG_PATH\""
    echo "  export LD_LIBRARY_PATH=\"${USER_LIB}:${USER_PREFIX}/lib64:\$LD_LIBRARY_PATH\""
}

# Run main function
main "$@"
