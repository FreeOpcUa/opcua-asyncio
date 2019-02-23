"""
Helper function and classes that do not rely on asyncua library.
Helper function and classes depending on ua object are in ua_utils.py
"""

import os
import logging
from ..ua.uaerrors import UaError

_logger = logging.getLogger(__name__)
__all__ = ["ServiceError", "NotEnoughData", "SocketClosedException", "Buffer", "create_nonce"]


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
    alternative to io.BytesIO making debug easier
    and added a few convenience methods
    """

    def __init__(self, data, start_pos=0, size=-1):
        self._data = data
        self._cur_pos = start_pos
        if size == -1:
            size = len(data) - start_pos
        self._size = size

    def __str__(self):
        return "Buffer(size:{0}, data:{1})".format(
            self._size,
            self._data[self._cur_pos:self._cur_pos + self._size])
    __repr__ = __str__

    def __len__(self):
        return self._size

    def read(self, size):
        """
        read and pop number of bytes for buffer
        """
        if size > self._size:
            raise NotEnoughData("Not enough data left in buffer, request for {0}, we have {1}".format(size, self))
        # self.logger.debug("Request for %s bytes, from %s", size, self)
        self._size -= size
        pos = self._cur_pos
        self._cur_pos += size
        data = self._data[pos:self._cur_pos]
        # self.logger.debug("Returning: %s ", data)
        return data

    def copy(self, size=-1):
        """
        return a shadow copy, optionnaly only copy 'size' bytes
        """
        if size == -1 or size > self._size:
            size = self._size
        return Buffer(self._data, self._cur_pos, size)

    def skip(self, size):
        """
        skip size bytes in buffer
        """
        if size > self._size:
            raise NotEnoughData("Not enough data left in buffer, request for {0}, we have {1}".format(size, self))
        self._size -= size
        self._cur_pos += size


def create_nonce(size=32):
    return os.urandom(size)
