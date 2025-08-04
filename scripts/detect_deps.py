"""
Detect dependencies for the project

- pybind11
- xgboost
- lightgbm
"""

import sys
import subprocess


def fix_pybind11():
    """Fix pybind11 installation"""
    print("Checking pybind11 installation...")
    try:
        import pybind11

        print("✓ pybind11 is installed")
        # Check CMake config
        try:
            cmake_dir = pybind11.get_cmake_dir()
            print(f"✓ pybind11 CMake directory: {cmake_dir}")
            return True
        except Exception as e:
            print(f"✗ pybind11 CMake config issue: {e}")
    except ImportError:
        print("✗ pybind11 is not installed")
    print("Reinstalling pybind11...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--force-reinstall", "pybind11"], check=True)
        print("✓ pybind11 reinstalled successfully")
        import pybind11

        cmake_dir = pybind11.get_cmake_dir()
        print(f"✓ pybind11 CMake directory: {cmake_dir}")
        return True
    except Exception as e:
        print(f"✗ pybind11 installation failed: {e}")
        return False


def fix_xgboost():
    """Fix xgboost installation"""
    print("Checking xgboost installation...")
    try:
        import xgboost

        print("✓ xgboost is installed")
        # Try to find CMake directory (if available)
        cmake_dir = getattr(xgboost, "cmake_dir", None)
        if cmake_dir:
            print(f"✓ xgboost CMake directory: {cmake_dir}")
        else:
            # Try common install locations
            import os

            possible_dirs = [
                os.path.join(xgboost.__path__[0], "cmake"),
                os.path.join(xgboost.__path__[0], "..", "cmake"),
                "/usr/local/lib/cmake/xgboost",
                "/usr/local/share/cmake/xgboost",
                "/opt/homebrew/lib/cmake/xgboost",
            ]
            found = False
            for d in possible_dirs:
                if os.path.isdir(d):
                    print(f"✓ xgboost CMake directory: {os.path.abspath(d)}")
                    found = True
                    break
            if not found:
                print("✗ xgboost CMake directory not found (not required for Python usage, only for C++ linkage)")
        return True
    except ImportError:
        print("✗ xgboost is not installed")
    print("Reinstalling xgboost...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--force-reinstall", "xgboost"], check=True)
        print("✓ xgboost reinstalled successfully")
        import xgboost

        print("✓ xgboost is installed after reinstall")
        # Repeat CMake dir check after reinstall
        cmake_dir = getattr(xgboost, "cmake_dir", None)
        if cmake_dir:
            print(f"✓ xgboost CMake directory: {cmake_dir}")
        else:
            import os

            possible_dirs = [
                os.path.join(xgboost.__path__[0], "cmake"),
                os.path.join(xgboost.__path__[0], "..", "cmake"),
                "/usr/local/lib/cmake/xgboost",
                "/usr/local/share/cmake/xgboost",
                "/opt/homebrew/lib/cmake/xgboost",
            ]
            found = False
            for d in possible_dirs:
                if os.path.isdir(d):
                    print(f"✓ xgboost CMake directory: {os.path.abspath(d)}")
                    found = True
                    break
            if not found:
                print("✗ xgboost CMake directory not found (not required for Python usage, only for C++ linkage)")
        return True
    except Exception as e:
        print(f"✗ xgboost installation failed: {e}")
        return False


def fix_lightgbm():
    """Fix lightgbm installation"""
    print("Checking lightgbm installation...")
    try:
        import lightgbm

        print("✓ lightgbm is installed")
        # Try to find CMake directory (if available)
        cmake_dir = getattr(lightgbm, "cmake_dir", None)
        if cmake_dir:
            print(f"✓ lightgbm CMake directory: {cmake_dir}")
        else:
            import os

            possible_dirs = [
                os.path.join(lightgbm.__path__[0], "cmake"),
                os.path.join(lightgbm.__path__[0], "..", "cmake"),
                "/usr/local/lib/cmake/LightGBM",
                "/usr/local/share/cmake/LightGBM",
                "/opt/homebrew/lib/cmake/LightGBM",
            ]
            found = False
            for d in possible_dirs:
                if os.path.isdir(d):
                    print(f"✓ lightgbm CMake directory: {os.path.abspath(d)}")
                    found = True
                    break
            if not found:
                print("✗ lightgbm CMake directory not found (not required for Python usage, only for C++ linkage)")
        return True
    except ImportError:
        print("✗ lightgbm is not installed")
    print("Reinstalling lightgbm...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--force-reinstall", "lightgbm"], check=True)
        print("✓ lightgbm reinstalled successfully")
        import lightgbm

        print("✓ lightgbm is installed after reinstall")
        # Repeat CMake dir check after reinstall
        cmake_dir = getattr(lightgbm, "cmake_dir", None)
        if cmake_dir:
            print(f"✓ lightgbm CMake directory: {cmake_dir}")
        else:
            import os

            possible_dirs = [
                os.path.join(lightgbm.__path__[0], "cmake"),
                os.path.join(lightgbm.__path__[0], "..", "cmake"),
                "/usr/local/lib/cmake/LightGBM",
                "/usr/local/share/cmake/LightGBM",
                "/opt/homebrew/lib/cmake/LightGBM",
            ]
            found = False
            for d in possible_dirs:
                if os.path.isdir(d):
                    print(f"✓ lightgbm CMake directory: {os.path.abspath(d)}")
                    found = True
                    break
            if not found:
                print("✗ lightgbm CMake directory not found (not required for Python usage, only for C++ linkage)")
        return True
    except Exception as e:
        print(f"✗ lightgbm installation failed: {e}")
        return False


def detect_dependencies():
    """Detect dependencies for the project"""
    print("Detecting dependencies...")
    print(f"Python version: {sys.version}")
    print(f"Python path: {sys.executable}")
    fix_pybind11()
    fix_xgboost()
    fix_lightgbm()


if __name__ == "__main__":
    detect_dependencies()
