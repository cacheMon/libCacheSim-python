"""Wrapper of Reader"""

import logging
from typing import overload, Union, Optional
from collections.abc import Iterator

from .protocols import ReaderProtocol

from .libcachesim_python import TraceType, SamplerType, Request, ReaderInitParam, Reader, Sampler, ReadDirection


class TraceReader(ReaderProtocol):
    _reader: Reader

    # Mark this as a C++ reader for c_process_trace compatibility
    c_reader: bool = True

    @overload
    def __init__(self, trace: Reader) -> None: ...

    def __init__(
        self,
        trace: Union[Reader, str],
        trace_type: TraceType = TraceType.UNKNOWN_TRACE,
        reader_init_params: Optional[ReaderInitParam] = None,
    ):
        if isinstance(trace, Reader):
            self._reader = trace
            return

        if reader_init_params is None:
            reader_init_params = ReaderInitParam()

        if not isinstance(reader_init_params, ReaderInitParam):
            raise TypeError("reader_init_params must be an instance of ReaderInitParam")

        self._reader = Reader(trace, trace_type, reader_init_params)

    @property
    def n_read_req(self) -> int:
        return self._reader.n_read_req

    @property
    def n_total_req(self) -> int:
        return self._reader.n_total_req

    @property
    def trace_path(self) -> str:
        return self._reader.trace_path

    @property
    def file_size(self) -> int:
        return self._reader.file_size

    @property
    def init_params(self) -> ReaderInitParam:
        return self._reader.init_params

    @property
    def trace_type(self) -> TraceType:
        return self._reader.trace_type

    @property
    def trace_format(self) -> str:
        return self._reader.trace_format

    @property
    def ver(self) -> int:
        return self._reader.ver

    @property
    def cloned(self) -> bool:
        return self._reader.cloned

    @property
    def cap_at_n_req(self) -> int:
        return self._reader.cap_at_n_req

    @property
    def trace_start_offset(self) -> int:
        return self._reader.trace_start_offset

    @property
    def mapped_file(self) -> bool:
        return self._reader.mapped_file

    @property
    def mmap_offset(self) -> int:
        return self._reader.mmap_offset

    @property
    def is_zstd_file(self) -> bool:
        return self._reader.is_zstd_file

    @property
    def item_size(self) -> int:
        return self._reader.item_size

    @property
    def line_buf(self) -> str:
        return self._reader.line_buf

    @property
    def line_buf_size(self) -> int:
        return self._reader.line_buf_size

    @property
    def csv_delimiter(self) -> str:
        return self._reader.csv_delimiter

    @property
    def csv_has_header(self) -> bool:
        return self._reader.csv_has_header

    @property
    def obj_id_is_num(self) -> bool:
        return self._reader.obj_id_is_num

    @property
    def obj_id_is_num_set(self) -> bool:
        return self._reader.obj_id_is_num_set

    @property
    def ignore_size_zero_req(self) -> bool:
        return self._reader.ignore_size_zero_req

    @property
    def ignore_obj_size(self) -> bool:
        return self._reader.ignore_obj_size

    @property
    def block_size(self) -> int:
        return self._reader.block_size

    @ignore_size_zero_req.setter
    def ignore_size_zero_req(self, value: bool) -> None:
        self._reader.ignore_size_zero_req = value

    @ignore_obj_size.setter
    def ignore_obj_size(self, value: bool) -> None:
        self._reader.ignore_obj_size = value

    @block_size.setter
    def block_size(self, value: int) -> None:
        self._reader.block_size = value

    @property
    def n_req_left(self) -> int:
        return self._reader.n_req_left

    @property
    def last_req_clock_time(self) -> int:
        return self._reader.last_req_clock_time

    @property
    def lcs_ver(self) -> int:
        return self._reader.lcs_ver

    @property
    def sampler(self) -> Sampler:
        return self._reader.sampler

    @property
    def read_direction(self) -> ReadDirection:
        return self._reader.read_direction

    def get_num_of_req(self) -> int:
        return self._reader.get_num_of_req()

    def read_one_req(self) -> Request:
        req = Request()
        ret = self._reader.read_one_req(req) # return 0 if success
        if ret != 0:
            raise RuntimeError("Failed to read one request")
        return req

    def reset(self) -> None:
        self._reader.reset()

    def close(self) -> None:
        self._reader.close()

    def clone(self) -> "TraceReader":
        return TraceReader(self._reader.clone())

    def read_first_req(self, req: Request) -> Request:
        return self._reader.read_first_req(req)

    def read_last_req(self, req: Request) -> Request:
        return self._reader.read_last_req(req)

    def skip_n_req(self, n: int) -> int:
        return self._reader.skip_n_req(n)

    def read_one_req_above(self) -> Request:
        return self._reader.read_one_req_above()

    def go_back_one_req(self) -> None:
        self._reader.go_back_one_req()

    def set_read_pos(self, pos: float) -> None:
        self._reader.set_read_pos(pos)

    def __iter__(self) -> Iterator[Request]:
        self._reader.reset()
        return self

    def __len__(self) -> int:
        return self._reader.get_num_of_req()

    def __next__(self) -> Request:
        req = Request()
        ret = self._reader.read_one_req(req)
        if ret != 0:
            raise StopIteration
        return req

    def __getitem__(self, index: int) -> Request:
        if index < 0 or index >= self._reader.get_num_of_req():
            raise IndexError("Index out of range")
        self._reader.reset()
        self._reader.skip_n_req(index)
        req = Request()
        return self._reader.read_one_req(req)
