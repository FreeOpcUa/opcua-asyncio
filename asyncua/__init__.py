"""
Pure Python OPC-UA library
"""

import sys
from importlib import metadata

__version__ = metadata.version("asyncua")

from .common import Node, uamethod
from .client import Client
from .server import Server
