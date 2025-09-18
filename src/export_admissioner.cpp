// libcachesim_python - libCacheSim Python bindings
// Copyright 2025 The libcachesim Authors.  All rights reserved.
//
// Use of this source code is governed by a GPL-3.0
// license that can be found in the LICENSE file or at
// https://github.com/1a1a11a/libcachesim/blob/develop/LICENSE

#include <pybind11/functional.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "../libCacheSim/include/libCacheSim/admissionAlgo.h"
#include "export.h"

namespace libcachesim {

namespace py = pybind11;

void export_admissioner(py::module &m) {
  py::class_<admissioner_t>(m, "Admissioner")
      .def(py::init<>())
      .def_readwrite("params", &admissioner_t::params)

      .def_property(
          "admissioner_name",
          [](const admissioner_t &self) {
            return std::string(self.admissioner_name);
          },
          [](admissioner_t &self, const std::string &val) {
            strncpy(self.admissioner_name, val.c_str(), CACHE_NAME_LEN);
            self.admissioner_name[CACHE_NAME_LEN - 1] = '\0';
          })

      .def_property(
          "init_params",
          [](const admissioner_t &self) {
            return self.init_params ? std::string(self.init_params)
                                    : std::string{};
          },
          [](admissioner_t &self, const std::string &val) {
            if (self.init_params) free(self.init_params);
            self.init_params = strdup(val.c_str());
          })

      .def("admit",
           [](admissioner_t &self, uintptr_t req_ptr) {
             if (!self.admit)
               throw std::runtime_error("admit function pointer is NULL");
             request_t *req = reinterpret_cast<request_t *>(req_ptr);
             return self.admit(&self, req);
           })

      .def("clone",
           [](admissioner_t &self) {
             if (!self.clone)
               throw std::runtime_error("clone function pointer is NULL");
             return self.clone(&self);
           })

      .def("update",
           [](admissioner_t &self, uintptr_t req_ptr, uint64_t cache_size) {
             if (!self.update)
               throw std::runtime_error("update function pointer is NULL");
             request_t *req = reinterpret_cast<request_t *>(req_ptr);
             self.update(&self, req, cache_size);
           })

      .def("free", [](admissioner_t &self) {
        if (!self.free)
          throw std::runtime_error("free function pointer is NULL");
        self.free(&self);
      });
}

}  // namespace libcachesim
