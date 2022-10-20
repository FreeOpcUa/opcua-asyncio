

def make_node(session, nodeid):
    """
    Node factory
    Needed no break cyclical import of `Node`
    """
    from .node import Node
    return Node(session, nodeid)
