"""Wrapper of Reader with S3 support."""
from __future__ import annotations

import logging
from typing import overload, Union, Optional, Any
from collections.abc import Iterator
from urllib.parse import urlparse

from .protocols import ReaderProtocol
from .libcachesim_python import (
    TraceType,
    TraceFormat,
    Request,
    ReaderInitParam,
    Reader,
    Sampler,
    ReadDirection,
    cal_working_set_size,
)
from ._s3_cache import get_data_loader

logger = logging.getLogger(__name__)


class TraceReaderSliceIterator:
    """Iterator for sliced TraceReader."""

    def __init__(self, reader: "TraceReader", start: int, stop: int, step: int):
        # Clone the reader to avoid side effects on the original
        self.reader = reader.clone()
        self.start = start
        self.stop = stop
        self.step = step
        self.current = start
        
        # Initialize position: reset and skip to start position once
        self.reader.reset()
        if start > 0:
            self._skip_to_start_position(start)
        
    def __iter__(self) -> Iterator[Request]:
        return self
        
    def __next__(self) -> Request:
        if self.current >= self.stop:
            raise StopIteration
            
        # Read the current request
        try:
            req = self.reader.read_one_req()
        except RuntimeError:
            raise StopIteration
        
        # Advance to next position based on step
        if self.step > 1:
            self._skip_requests(self.step - 1)
        
        self.current += self.step
        return req
    
    def _skip_to_start_position(self, position: int) -> None:
        """Skip to the start position efficiently."""
        if not self.reader._reader.is_zstd_file:
            # Try using skip_n_req for non-zstd files
            skipped = self.reader.skip_n_req(position)
            if skipped != position:
                # If we couldn't skip the expected number, simulate the rest
                remaining = position - skipped
                self._simulate_skip(remaining)
        else:
            # For zstd files, always simulate
            self._simulate_skip(position)
    
    def _skip_requests(self, n: int) -> None:
        """Skip n requests efficiently."""
        if not self.reader._reader.is_zstd_file:
            # Try using skip_n_req for non-zstd files
            skipped = self.reader.skip_n_req(n)
            if skipped != n:
                # If we couldn't skip all, we're likely at EOF
                self.current = self.stop  # Mark as done
        else:
            # For zstd files, simulate
            self._simulate_skip(n)
    
    def _simulate_skip(self, n: int) -> None:
        """Simulate skip by reading requests one by one."""
        for _ in range(n):
            try:
                self.reader.read_one_req()
            except RuntimeError:
                # If we can't read more, we're at EOF
                self.current = self.stop  # Mark as done
                break


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

        # Handle S3 URIs
        if isinstance(trace, str) and trace.startswith("s3://"):
            trace = self._resolve_s3_path(trace)

        if reader_init_params is None:
            reader_init_params = ReaderInitParam()

        if not isinstance(reader_init_params, ReaderInitParam):
            raise TypeError("reader_init_params must be an instance of ReaderInitParam")

        self._reader = Reader(trace, trace_type, reader_init_params)

    def _validate_s3_uri(self, s3_uri: str) -> tuple[str, str]:
        """
        Validate and parse S3 URI.

        Args:
            s3_uri: S3 URI like "s3://bucket/key"

        Returns:
            Tuple of (bucket, key)

        Raises:
            ValueError: If URI is invalid
        """
        parsed = urlparse(s3_uri)

        if parsed.scheme != "s3":
            raise ValueError(f"Invalid S3 URI scheme. Expected 's3', got '{parsed.scheme}': {s3_uri}")

        if not parsed.netloc:
            raise ValueError(f"Missing bucket name in S3 URI: {s3_uri}")

        bucket = parsed.netloc
        key = parsed.path.lstrip("/")

        if not key:
            raise ValueError(f"Missing key (object path) in S3 URI: {s3_uri}")

        # Check for path traversal in the key part only
        if ".." in key:
            raise ValueError(f"S3 key contains path traversal patterns: {key}")

        # Check for double slashes in the key part (after s3://)
        if "//" in key:
            raise ValueError(f"S3 key contains double slashes: {key}")

        # Check for backslashes (not valid in URLs)
        if "\\" in s3_uri:
            raise ValueError(f"S3 URI contains backslashes: {s3_uri}")

        return bucket, key

    def _resolve_s3_path(self, s3_path: str) -> str:
        """
        Resolve S3 path to local cached file path.

        Args:
            s3_path: S3 URI like "s3://bucket/key"

        Returns:
            Local file path
        """
        try:
            bucket, key = self._validate_s3_uri(s3_path)
        except ValueError as e:
            raise ValueError(f"Invalid S3 URI: {e}")

        # Get data loader for this bucket
        try:
            loader = get_data_loader(bucket)
        except ValueError as e:
            raise ValueError(f"Invalid bucket name '{bucket}': {e}")

        logger.info(f"Resolving S3 path: {s3_path}")
        try:
            return loader.get_cached_path(key)
        except ValueError as e:
            raise ValueError(f"Invalid S3 key '{key}': {e}")

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
        ret = self._reader.read_one_req(req)  # return 0 if success
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

    def get_working_set_size(self) -> tuple[int, int]:
        return cal_working_set_size(self._reader)

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

    def __getitem__(self, key: Union[int, slice]) -> Union[Request, TraceReaderSliceIterator]:
        if isinstance(key, slice):
            # Handle slice
            total_len = self._reader.get_num_of_req()
            start, stop, step = key.indices(total_len)
            return TraceReaderSliceIterator(self, start, stop, step)
        elif isinstance(key, int):
            # Handle single index
            total_len = self._reader.get_num_of_req()
            if key < 0:
                key += total_len
            if key < 0 or key >= total_len:
                raise IndexError("Index out of range")
            
            self._reader.reset()
            
            # Try to skip to the target position
            if key > 0:
                if not self._reader.is_zstd_file:
                    # For non-zstd files, try skip_n_req and check return value
                    skipped = self._reader.skip_n_req(key)
                    if skipped != key:
                        # If we couldn't skip the expected number, simulate the rest
                        remaining = key - skipped
                        self._simulate_skip_single(remaining)
                else:
                    # For zstd files, always simulate
                    self._simulate_skip_single(key)
            
            # Read the target request
            req = Request()
            ret = self._reader.read_one_req(req)
            if ret != 0:
                raise IndexError(f"Cannot read request at index {key}")
            return req
        else:
            raise TypeError("TraceReader indices must be integers or slices")
    
    def _simulate_skip_single(self, n: int) -> None:
        """Simulate skip by reading requests one by one for single index access."""
        for i in range(n):
            req = Request()
            ret = self._reader.read_one_req(req)
            if ret != 0:
                raise IndexError(f"Cannot skip to position, reached EOF at {i}")
    
    # Note: Removed old inefficient methods _can_use_skip_n_req and _simulate_skip_and_read_single
    # The new implementation is more efficient and handles skip_n_req return values properly
