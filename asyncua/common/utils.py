"""
Helper function and classes that do not rely on asyncua library.
Helper function and classes depending on ua object are in ua_utils.py
"""

import os
import logging
import sys
from dataclasses import Field, fields
from typing import get_type_hints, Dict, Tuple, Any, Optional
from ..ua.uaerrors import UaError

_logger = logging.getLogger(__name__)


class ServiceError(UaError):
    def __init__(self, code):
        super().__init__('UA Service Error')
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
        return bytes(self._data[self._cur_pos:])

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

    @property
    def cur_pos(self):
        return self._cur_pos

    def rewind(self, cur_pos=0):
        """
        rewind the buffer
        """
        self._cur_pos = cur_pos
        self._size = len(self._data) - cur_pos


def create_nonce(size=32):
    return os.urandom(size)


def fields_with_resolved_types(
    class_or_instance: Any,
    globalns: Optional[Dict[str, Any]] = None,
    localns: Optional[Dict[str, Any]] = None,
    include_extras: bool = False,
) -> Tuple[Field, ...]:
    """Return a tuple describing the fields of this dataclass.

    Accepts a dataclass or an instance of one. Tuple elements are of
    type Field. ForwardRefs and string types will be resolved.
    """

    fields_ = fields(class_or_instance)
    if sys.version_info.major == 3 and sys.version_info.minor <= 8:
        resolved_fieldtypes = get_type_hints(
            class_or_instance,
            globalns=globalns,
            localns=localns
        )
    else:
        resolved_fieldtypes = get_type_hints(
            class_or_instance,
            globalns=globalns,
            localns=localns,
            include_extras=include_extras
        )
    for field in fields_:
        try:
            field.type = resolved_fieldtypes[field.name]
        except KeyError:
            _logger.info(f"could not resolve fieldtype for field={field} of class_or_instance={class_or_instance}")
            pass

    return fields_
