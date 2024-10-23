"""
Pure Python OPC-UA library
"""

import sys

if sys.version_info >= (3, 8):
    from importlib import metadata
else:
    import importlib_metadata as metadata

__version__ = metadata.version("asyncua")

from .common import Node, uamethod
from .client import Client
from .server import Server
