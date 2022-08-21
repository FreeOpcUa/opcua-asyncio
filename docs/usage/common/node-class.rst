==============
The Node Class
==============

The :class:`asyncua.common.node.Node` class is a central part used on the server and client.
On the server side nodes are created and configured as well as read and written. On the client
side we can browser through the nodes and access and manipulate their values. Nodes should not
be confused with :class:`~asyncua.ua.uatypes.NodeId`: The later only reference nodes but are not
nodes themself! The :class:`~asyncua.ua.uatypes.NodeId` is further discussed in the :ref:`usage/common/nodeid-class:the nodeid class`
section.

The Node class exposes a wide range of the OPC-UA protocol for easy access, however, to fully
optimize your code you will need to use lower level functions. Beside that, for many usecases
the Node class might be the right thing to use for simpler usecases and makes it certainly
easier to get started with OPC-UA.


Creating / Accessing Nodes
==========================

.. note:: In this section we **don't** talk about creating new variables / objects / methods
    on the server side. We just go through the ways how we can create a Node object in python.

The most straight forward way to instanciate a new node is by using the constructor:

.. code-block:: python

    >>> from asyncua import Node
    >>> Node(None, 'ns=2;i=3')
    Node(NodeId(Identifier=3, NamespaceIndex=2, NodeIdType=<NodeIdType.Numeric: 2>))

The constructor takes two arguments: a server, in the example `None` and a nodeid. Ignore
the fact that the server in our example is None, this would lead to errors later on, but 
it is possible to create a Node without a server assigned. The provided nodeid is converted
to a :class:`~asyncua.ua.uatypes.NodeId`.

In most cases there is no need to create a node manually: Both, the server and the client,
offer a :code:`get_node` method to create a new Node. These functions automatically set the
server property on the node and should be prefered to direct node creation.

If we already have a node instance (for example the :code:`client.nodes.root` node) whe can
browse through the hierarchy of nodes using the :meth:`~asyncua.common.node.Node.get_child`,
:meth:`~asyncua.common.node.Node.get_children`, :meth:`~asyncua.common.node.Node.get_parent`
and other browse functions.
