"""
Helper function and classes that do not rely on asyncua library.
Helper function and classes depending on ua object are in ua_utils.py
"""

import os
import logging
from ..ua.uaerrors import UaError

_logger = logging.getLogger(__name__)


class ServiceError(UaError):
    def __init__(self, code):
        super(ServiceError, self).__init__('UA Service Error')
        self.code = code


class NotEnoughData(UaError):
    pass


class SocketClosedException(UaError):
    pass


class Buffer:
    """
    Alternative to io.BytesIO making debug easier
    and added a few convenience methods.
    """

    def __init__(self, data, start_pos=0, size=-1):
        self._data = data
        self._cur_pos = start_pos
        if size == -1:
            size = len(data) - start_pos
        self._size = size

    def __str__(self):
        return f"Buffer(size:{self._size}, data:{self._data[self._cur_pos:self._cur_pos + self._size]})"
    __repr__ = __str__

    def __len__(self):
        return self._size

    def __bool__(self):
        return self._size > 0

    def __bytes__(self):
        """Return remains of buffer as bytes."""
        return self._data[self._cur_pos:]

    def read(self, size):
        """
        read and pop number of bytes for buffer
        """
        if size > self._size:
            raise NotEnoughData(f"Not enough data left in buffer, request for {size}, we have {self._size}")
        self._size -= size
        pos = self._cur_pos
        self._cur_pos += size
        return self._data[pos:self._cur_pos]

    def copy(self, size=-1):
        """
        return a shadow copy, optionally only copy 'size' bytes
        """
        if size == -1 or size > self._size:
            size = self._size
        return Buffer(self._data, self._cur_pos, size)

    def skip(self, size):
        """
        skip size bytes in buffer
        """
        if size > self._size:
            raise NotEnoughData(f"Not enough data left in buffer, request for {size}, we have {self._size}")
        self._size -= size
        self._cur_pos += size


def create_nonce(size=32):
    return os.urandom(size)
