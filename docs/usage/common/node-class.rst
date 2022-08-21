==============
The Node Class
==============

The :class:`asyncua.common.node.Node` class is a central part used on the server and client.
On the server side nodes are created and configured as well as read and written. On the client
side we can browser through the nodes and access and manipulate their values. Nodes should not
be confused with :class:`~asyncua.ua.uatypes.NodeId`: The later only reference nodes but are not
nodes themself! The :class:`~asyncua.ua.uatypes.NodeId` is further discussed in the :ref:`usage/common/nodeid-class:the nodeid class`
section.

