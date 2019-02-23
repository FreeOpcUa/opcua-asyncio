

def make_node(server, nodeid):
    """
    Node factory
    Needed no break cyclical import of `Node`
    """
    from .node import Node
    return Node(server, nodeid)
