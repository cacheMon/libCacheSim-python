from abc import ABC
from .libcachesim_python import (
    Admissioner,
    Request,
    create_bloomfilter_admissioner,
    create_prob_admissioner,
    create_size_admissioner,
    create_size_probabilistic_admissioner,
    create_adaptsize_admissioner,
    create_plugin_admissioner,
)


class AdmissionerBase(ABC):
    _admissioner: Admissioner  # Internal C++ admissioner object

    def __init__(self, _admissioner: Admissioner):
        self._admissioner = _admissioner

    def clone(self):
        return self._admissioner.clone()

    def update(self, req: Request, cache_size: int):
        return self._admissioner.update(req, cache_size)

    def admit(self, req: Request):
        return self._admissioner.admit(req)

    def free(self):
        return self._admissioner.free()


class BloomFilterAdmissioner(AdmissionerBase):
    def __init__(self):
        admissioner = create_bloomfilter_admissioner(None)
        super().__init__(admissioner)


class ProbAdmissioner(AdmissionerBase):
    def __init__(self, prob: float = None):
        params = f"prob={prob}" if prob is not None else None
        admissioner = create_prob_admissioner(params)
        super().__init__(admissioner)


class SizeAdmissioner(AdmissionerBase):
    def __init__(self, size_threshold: int = None):
        params = f"size={size_threshold}" if size_threshold is not None else None
        admissioner = create_size_admissioner(params)
        super().__init__(admissioner)


class SizeProbabilisticAdmissioner(AdmissionerBase):
    def __init__(self, exponent: float = None):
        params = f"exponent={exponent}" if exponent is not None else None
        admissioner = create_size_probabilistic_admissioner(params)
        super().__init__(admissioner)


class AdaptSizeAdmissioner(AdmissionerBase):
    def __init__(self, max_iteration: int = None, reconf_interval: int = None):
        params = ",".join(
            f'{arg}={val}' for arg, val in {
                'max-iteration': max_iteration,
                'reconf-interval': reconf_interval,
            }.items() if val is not None
        ) or None

        admissioner = create_adaptsize_admissioner(params)
        super().__init__(admissioner)


class PluginAdmissioner(AdmissionerBase):
    def __init__(self,
                 admissioner_name,
                 admissioner_init_hook,
                 admissioner_admit_hook,
                 admissioner_clone_hook,
                 admissioner_update_hook,
                 admissioner_free_hook):
        admissioner = create_plugin_admissioner(
            admissioner_name,
            admissioner_init_hook,
            admissioner_admit_hook,
            admissioner_clone_hook,
            admissioner_update_hook,
            admissioner_free_hook)
        super().__init__(admissioner)
