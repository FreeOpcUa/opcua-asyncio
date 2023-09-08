from __future__ import annotations

import asyncua
from asyncua import ua
from asyncua.common.session_interface import AbstractSession


def make_node(session: AbstractSession, nodeid: ua.NodeId) -> asyncua.Node:
    """
    Node factory
    Needed no break cyclical import of `Node`
    """
    from .node import Node
    return Node(session, nodeid)
