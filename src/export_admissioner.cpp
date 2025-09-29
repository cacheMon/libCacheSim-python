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

typedef struct __attribute__((visibility("hidden")))
pypluginAdmissioner_params {
  py::object data;  ///< Plugin's internal data structure (python object)
  py::function admissioner_init_hook;
  py::function admissioner_admit_hook;
  py::function admissioner_clone_hook;
  py::function admissioner_update_hook;
  py::function admissioner_free_hook;
  std::string admissioner_name;
} pypluginAdmissioner_params_t;

static bool pypluginAdmissioner_admit(admissioner_t *, const request_t *);
static admissioner_t *pypluginAdmissioner_clone(admissioner_t *);
static void pypluginAdmissioner_free(admissioner_t *);
static void pypluginAdmissioner_update(admissioner_t *, const request_t *,
                                       const uint64_t);

struct PypluginAdmissionerParamsDeleter {
  void operator()(pypluginAdmissioner_params_t *ptr) const {
    if (ptr != nullptr) {
      if (!ptr->admissioner_free_hook.is_none()) {
        try {
          ptr->admissioner_free_hook(ptr->data);
        } catch (...) { }
      }
      delete ptr;
    }
  }
};

admissioner_t *create_plugin_admissioner(std::string admissioner_name,
                                         py::function admissioner_init_hook,
                                         py::function admissioner_admit_hook,
                                         py::function admissioner_clone_hook,
                                         py::function admissioner_update_hook,
                                         py::function admissioner_free_hook) {
  std::unique_ptr<pypluginAdmissioner_params_t,
                  PypluginAdmissionerParamsDeleter>
      params;
  admissioner_t *admissioner = nullptr;
  try {
    admissioner = (admissioner_t *)malloc(sizeof(admissioner_t));
    if (!admissioner) {
      throw std::runtime_error("Failed to initialize admissioner structure");
    }
    memset(admissioner, 0, sizeof(admissioner_t));

    // We will pass a raw pointer for C++ to take ownership of
    admissioner->admit = pypluginAdmissioner_admit;
    admissioner->clone = pypluginAdmissioner_clone;
    admissioner->free = pypluginAdmissioner_free;
    admissioner->update = pypluginAdmissioner_update;

    // Initialize pointers to python hook functions
    params = std::unique_ptr<pypluginAdmissioner_params_t,
                             PypluginAdmissionerParamsDeleter>(
        new pypluginAdmissioner_params_t(), PypluginAdmissionerParamsDeleter());
    params->data = admissioner_init_hook();
    params->admissioner_admit_hook = admissioner_admit_hook;
    params->admissioner_clone_hook = admissioner_clone_hook;
    params->admissioner_update_hook = admissioner_update_hook;
    params->admissioner_free_hook = admissioner_free_hook;
    params->admissioner_name = admissioner_name;

    // Transfer ownership of params to admissioner
    admissioner->params = params.release();
    return admissioner;
  } catch (...) {
    if (admissioner) free(admissioner);
    throw;
  }
}

static bool pypluginAdmissioner_admit(admissioner_t *admissioner,
                                      const request_t *req) {
  pypluginAdmissioner_params_t *params =
      (pypluginAdmissioner_params_t *)admissioner->params;
  return params->admissioner_admit_hook(params->data, req).cast<bool>();
}

static admissioner_t *pypluginAdmissioner_clone(admissioner_t *admissioner) {
  pypluginAdmissioner_params_t *params =
      (pypluginAdmissioner_params_t *)admissioner->params;
  return params->admissioner_clone_hook(params->data).cast<admissioner_t *>();
}

static void pypluginAdmissioner_free(admissioner_t *admissioner) {
  pypluginAdmissioner_params_t *params =
      (pypluginAdmissioner_params_t *)admissioner->params;
  params->admissioner_free_hook(params->data);
}

static void pypluginAdmissioner_update(admissioner_t *admissioner,
                                       const request_t *req,
                                       const uint64_t cache_size) {
  pypluginAdmissioner_params_t *params =
      (pypluginAdmissioner_params_t *)admissioner->params;
  params->admissioner_update_hook(params->data, req, cache_size);
}

template <admissioner_t *(*fn)(const char *)>
void export_admissioner_creator(py::module &m, const std::string &name) {
  m.def(
      name.c_str(),
      [=](py::object params_obj) {
        const char *params = nullptr;
        std::string s;

        // Here, by allowing the passing of None to resolve to NULL, we can
        // allow the default arguments specified in C++ to be used when no
        // arguments are specified through the Python wrapper classes.
        if (!params_obj.is_none()) {
          s = params_obj.cast<std::string>();
          params = s.c_str();
        }

        // Admissioner is exported lower down
        admissioner_t *admissioner = fn(params);
        if (!admissioner)
          throw std::runtime_error("Creator for " + name + " returned NULL");
        return admissioner;
      },
      py::return_value_policy::reference);
}

void export_admissioner(py::module &m) {
  // ***********************************************************************
  // ****                                                               ****
  // ****                 Admissioner struct bindings                   ****
  // ****                                                               ****
  // ***********************************************************************

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
  // ***********************************************************************
  // ****                                                               ****
  // ****             end of admissioner struct bindings                ****
  // ****                                                               ****
  // ***********************************************************************

  // Exposing existing implementations of admission algorithms
  export_admissioner_creator<create_bloomfilter_admissioner>(
      m, "create_bloomfilter_admissioner");
  export_admissioner_creator<create_prob_admissioner>(
      m, "create_prob_admissioner");
  export_admissioner_creator<create_size_admissioner>(
      m, "create_size_admissioner");
  export_admissioner_creator<create_size_probabilistic_admissioner>(
      m, "create_size_probabilistic_admissioner");
  export_admissioner_creator<create_adaptsize_admissioner>(
      m, "create_adaptsize_admissioner");
  m.def("create_plugin_admissioner", &create_plugin_admissioner,
        "admissioner_name"_a, "admissioner_init_hook"_a,
        "admissioner_admit_hook"_a, "admissioner_clone_hook"_a,
        "admissioner_update_hook"_a, "admissioner_free_hook"_a,
        py::return_value_policy::take_ownership);
}

}  // namespace libcachesim
