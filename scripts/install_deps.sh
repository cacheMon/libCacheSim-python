#!/bin/bash

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

# Elevation helper.
#
# This script is both a developer convenience and cibuildwheel's `before-all`
# (see [tool.cibuildwheel] in pyproject.toml), where it runs as root inside the
# manylinux container with no sudo available. Running as root leaves SUDO empty,
# so every command below is byte-for-byte what it was before this helper existed.
SUDO=""
if [[ ${EUID} -ne 0 ]]; then
	if command -v sudo >/dev/null 2>&1; then
		SUDO="sudo"
	else
		log_error "This script needs root privileges, but neither root nor sudo is available."
		exit 1
	fi
fi

# Install and configure g++ version
install_gcc() {
	log_info "Installing and configuring g++ version..."
	
	# Install gcc-c++ and devtoolset if available
	if yum search devtoolset 2>/dev/null | grep -q devtoolset; then
		log_info "Installing devtoolset for newer g++ version..."
		yum install -y centos-release-scl
		yum install -y devtoolset-11-gcc-c++
		
		# Set environment variables globally for this script
		export CC=/opt/rh/devtoolset-11/root/usr/bin/gcc
		export CXX=/opt/rh/devtoolset-11/root/usr/bin/g++
		export PATH=/opt/rh/devtoolset-11/root/usr/bin:$PATH
		export LD_LIBRARY_PATH=/opt/rh/devtoolset-11/root/usr/lib64:/opt/rh/devtoolset-11/root/usr/lib:$LD_LIBRARY_PATH
		
		# Create symlinks to make it the default
		ln -sf /opt/rh/devtoolset-11/root/usr/bin/gcc /usr/local/bin/gcc
		ln -sf /opt/rh/devtoolset-11/root/usr/bin/g++ /usr/local/bin/g++
		ln -sf /opt/rh/devtoolset-11/root/usr/bin/gcc /usr/local/bin/cc
		ln -sf /opt/rh/devtoolset-11/root/usr/bin/g++ /usr/local/bin/c++
		
		# Add to PATH permanently
		echo 'export PATH=/opt/rh/devtoolset-11/root/usr/bin:$PATH' >> /etc/environment
		echo 'export LD_LIBRARY_PATH=/opt/rh/devtoolset-11/root/usr/lib64:/opt/rh/devtoolset-11/root/usr/lib:$LD_LIBRARY_PATH' >> /etc/environment
		
		log_info "Using g++ from devtoolset-11: $(g++ --version | head -n1)"
	else
		log_info "Using system g++: $(g++ --version | head -n1)"
	fi
}

# Install CMake
install_cmake() {
	log_info "Installing CMake..."
	local cmake_version="3.31.0"
	local cmake_dir="${HOME}/software/cmake"

	pushd /tmp/ >/dev/null
	if [[ ! -f "cmake-${cmake_version}-linux-x86_64.sh" ]]; then
		wget "https://github.com/Kitware/CMake/releases/download/v${cmake_version}/cmake-${cmake_version}-linux-x86_64.sh"
	fi

	mkdir -p "${cmake_dir}" 2>/dev/null || true
	bash "cmake-${cmake_version}-linux-x86_64.sh" --skip-license --prefix="${cmake_dir}"

	# Add to shell config files if not already present
	for shell_rc in "${HOME}/.bashrc" "${HOME}/.zshrc"; do
		# trunk-ignore(shellcheck/SC2016)
		if [[ -f ${shell_rc} ]] && ! grep -q 'PATH=$HOME/software/cmake/bin:$PATH' "${shell_rc}"; then
			# trunk-ignore(shellcheck/SC2016)
			echo 'export PATH=$HOME/software/cmake/bin:$PATH' >>"${shell_rc}"
		fi
	done

	# Source the updated PATH
	export PATH="${cmake_dir}/bin:${PATH}"
	popd >/dev/null
}

# Install Zstd from source
install_zstd() {
	log_info "Installing Zstd from source..."
	local zstd_version="1.5.0"
	
	pushd /tmp/ >/dev/null
	if [[ ! -f "zstd-${zstd_version}.tar.gz" ]]; then
		wget "https://github.com/facebook/zstd/releases/download/v${zstd_version}/zstd-${zstd_version}.tar.gz"
		tar xf "zstd-${zstd_version}.tar.gz"
	fi
	pushd "zstd-${zstd_version}/build/cmake/" >/dev/null
	mkdir -p _build
	pushd _build >/dev/null
	cmake -G Ninja ..
	ninja
	${SUDO} ninja install
	popd >/dev/null
	popd >/dev/null
	popd >/dev/null
}

# Install XGBoost from source
install_xgboost() {
	log_info "Installing XGBoost from source..."
	pushd /tmp/ >/dev/null
	if [[ ! -d "xgboost" ]]; then
		git clone --recursive https://github.com/dmlc/xgboost
	fi
	pushd xgboost >/dev/null
	mkdir -p build
	pushd build >/dev/null
	cmake -G Ninja ..
	ninja
	${SUDO} ninja install
	popd >/dev/null
	popd >/dev/null
	popd >/dev/null
}

# Install LightGBM from source
install_lightgbm() {
	log_info "Installing LightGBM from source..."
	pushd /tmp/ >/dev/null
	if [[ ! -d "LightGBM" ]]; then
		git clone --recursive https://github.com/microsoft/LightGBM
	fi
	pushd LightGBM >/dev/null
	mkdir -p build
	pushd build >/dev/null
	cmake -G Ninja ..
	ninja
	${SUDO} ninja install
	popd >/dev/null
	popd >/dev/null
	popd >/dev/null
}

# Detect OS and install dependencies.
#
# Dispatch on the available package manager rather than on $OSTYPE alone, so that
# this covers the same platforms as upstream's
# src/libCacheSim/scripts/install_dependency.sh (Debian/Ubuntu/WSL, macOS,
# CentOS/RHEL). macOS is matched first; the manylinux images used for the release
# wheels ship yum/dnf but no apt-get, so they still take the yum branch below.
if [[ "$OSTYPE" == "darwin"* ]]; then
	log_info "Detected macOS system, installing dependencies via brew..."

	# Install basic dependencies via Homebrew
	brew install glib gperftools argp-standalone xxhash llvm wget cmake ninja zstd xgboost lightgbm pkgconf

elif command -v apt-get >/dev/null 2>&1; then
	log_info "Detected Debian/Ubuntu system, installing dependencies via apt..."

	${SUDO} apt-get update
	# CMakeLists.txt requires pkg-config, GLib 2.0 and Zstandard; the rest mirrors
	# upstream's setup_ubuntu. Unlike the yum branch there is no need to build CMake
	# or Zstd from source, since apt ships cmake >= 3.15 and libzstd-dev.
	${SUDO} apt-get install -y --no-install-recommends \
		build-essential pkg-config git wget cmake ninja-build \
		libglib2.0-dev libzstd-dev \
		libgoogle-perftools-dev google-perftools xxhash libunwind-dev

	# Needed by the optional learned algorithms (ENABLE_GLCACHE / ENABLE_3L_CACHE /
	# ENABLE_LRB); no distro packages provide the CMake config files these need.
	install_xgboost
	install_lightgbm

elif command -v yum >/dev/null 2>&1 || command -v dnf >/dev/null 2>&1; then
	log_info "Detected CentOS/RHEL system, installing dependencies via yum..."

	# Enable EPEL repository
	yum install -y epel-release
	
	# Enable PowerTools/CRB repository
	if yum repolist | grep -q powertools; then
		yum-config-manager --set-enabled powertools
	elif yum repolist | grep -q crb; then
		yum-config-manager --set-enabled crb
	fi
	
	# Install development tools
	yum groupinstall -y "Development Tools"
	yum install -y glib2-devel google-perftools-devel
	yum install -y ninja-build git wget
	
	# Install and configure g++ version
	install_gcc
	
	# Install CMake
	install_cmake
	
	# Install dependencies from source
	install_zstd
	install_xgboost
	install_lightgbm

else
	log_error "Unsupported operating system: $OSTYPE (no brew, apt-get, yum or dnf found)"
	exit 1
fi

log_info "Dependencies installation completed!"
