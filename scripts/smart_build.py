#!/usr/bin/env python3
"""
Smart build script
Automatically handles version compatibility and dependency detection
"""

import subprocess
import sys
import os
import platform

def get_macos_deployment_target():
    """Get appropriate macOS deployment target"""
    if sys.platform != "darwin":
        return None
    
    try:
        result = subprocess.run(["sw_vers", "-productVersion"], 
                              capture_output=True, text=True, check=True)
        macos_version = result.stdout.strip()
        major_version = macos_version.split('.')[0]
        
        # Set deployment target to current version
        deployment_target = f"{major_version}.0"
        print(f"Detected macOS version: {macos_version}, set deployment target: {deployment_target}")
        return deployment_target
    except Exception as e:
        print(f"Failed to detect macOS version, using default: {e}")
        return "14.0"

def check_dependency(module_name):
    """Check if a Python module is installed"""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False

def fix_pybind11():
    """Fix pybind11 installation"""
    print("Checking pybind11...")
    subprocess.run([sys.executable, "scripts/fix_pybind11.py"], check=True)

def build_with_flags():
    """Build according to dependencies"""
    # Fix pybind11
    fix_pybind11()
    
    # Check ML dependencies
    xgboost_available = check_dependency("xgboost")
    lightgbm_available = check_dependency("lightgbm")
    
    print(f"XGBoost available: {xgboost_available}")
    print(f"LightGBM available: {lightgbm_available}")
    
    # Build CMake args
    cmake_args = ["-G", "Ninja"]
    
    # Add pybind11 path
    try:
        import pybind11
        pybind11_dir = pybind11.get_cmake_dir()
        cmake_args.extend([f"-Dpybind11_DIR={pybind11_dir}"])
        print(f"Set pybind11 path: {pybind11_dir}")
    except Exception as e:
        print(f"Warning: failed to set pybind11 path: {e}")
    
    # Enable GLCache if XGBoost is available
    if xgboost_available:
        cmake_args.extend(["-DENABLE_GLCACHE=ON"])
        print("Enable GLCache (requires XGBoost)")
    
    # Enable LRB and 3LCache if LightGBM is available
    if lightgbm_available:
        cmake_args.extend(["-DENABLE_LRB=ON", "-DENABLE_3L_CACHE=ON"])
        print("Enable LRB and 3LCache (requires LightGBM)")
    
    # Set macOS deployment target
    deployment_target = get_macos_deployment_target()
    if deployment_target:
        cmake_args.extend([f"-DCMAKE_OSX_DEPLOYMENT_TARGET={deployment_target}"])
    
    # Build commands
    build_dir = "src/libCacheSim/build"
    source_dir = "."
    
    # Clean build directory
    if os.path.exists(build_dir):
        print("Cleaning build directory...")
        subprocess.run(["rm", "-rf", build_dir], check=True)
    
    # Run CMake configure
    cmake_cmd = ["cmake", "-S", source_dir, "-B", build_dir] + cmake_args
    print(f"Running: {' '.join(cmake_cmd)}")
    subprocess.run(cmake_cmd, check=True)
    
    # Run build
    build_cmd = ["cmake", "--build", build_dir]
    print(f"Running: {' '.join(build_cmd)}")
    subprocess.run(build_cmd, check=True)
    
    print("✓ Build completed!")

def main():
    print("=== libCacheSim Smart Build ===")
    print(f"Platform: {platform.platform()}")
    print(f"Python: {sys.version}")
    print()
    
    try:
        build_with_flags()
    except subprocess.CalledProcessError as e:
        print(f"✗ Build failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Build exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 