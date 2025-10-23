// libcachesim_python - libCacheSim Python bindings
// Copyright 2025 The libcachesim Authors.  All rights reserved.
//
// Use of this source code is governed by a GPL-3.0
// license that can be found in the LICENSE file or at
// https://github.com/1a1a11a/libcachesim/blob/develop/LICENSE

#include "exception.h"

#include <pybind11/pybind11.h>

namespace libcachesim {

namespace py = pybind11;

void register_exception(py::module& m) {
  static py::exception<CacheException> exc_cache(m, "CacheException");
  static py::exception<ReaderException> exc_reader(m, "ReaderException");

  // Single exception translator with catch blocks ordered from most-specific to least-specific
  py::register_exception_translator([](std::exception_ptr p) {
    try {
      if (p) std::rethrow_exception(p);
    } catch (const CacheException& e) {
      // Custom exception: CacheException
      py::set_error(exc_cache, e.what());
    } catch (const ReaderException& e) {
      // Custom exception: ReaderException
      py::set_error(exc_reader, e.what());
    } catch (const std::bad_alloc& e) {
      // Memory allocation error
      PyErr_SetString(PyExc_MemoryError, e.what());
    } catch (const std::invalid_argument& e) {
      // Invalid argument error
      PyErr_SetString(PyExc_ValueError, e.what());
    } catch (const std::out_of_range& e) {
      // Out of range error
      PyErr_SetString(PyExc_IndexError, e.what());
    } catch (const std::domain_error& e) {
      // Domain error
      PyErr_SetString(PyExc_ValueError,
                      ("Domain error: " + std::string(e.what())).c_str());
    } catch (const std::overflow_error& e) {
      // Overflow error
      PyErr_SetString(PyExc_OverflowError, e.what());
    } catch (const std::range_error& e) {
      // Range error
      PyErr_SetString(PyExc_ValueError,
                      ("Range error: " + std::string(e.what())).c_str());
    } catch (const std::runtime_error& e) {
      // Generic runtime error
      PyErr_SetString(PyExc_RuntimeError, e.what());
    } catch (const std::exception& e) {
      // Catch-all for any other std::exception
      PyErr_SetString(PyExc_RuntimeError,
                      ("C++ exception: " + std::string(e.what())).c_str());
    }
  });
}

}  // namespace libcachesim
