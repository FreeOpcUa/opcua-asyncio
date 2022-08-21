================
The NodeId Class
================

The :class:`asyncua.ua.uatypes.NodeId` class is used as a reference to :class:`~asyncua.common.node.Node`'s
and is used on the server and client side to access nodes. The two classes 
:class:`~asyncua.ua.uatypes.NodeId` and :class:`~asyncua.common.node.Node` should not
be confused: The NodeId is a reference to the actual Node and does not provide direct
access to the Node. To learn more about the Node class, head over to :ref:`usage/common/node-class:the node class`.


A NodeId contains two main informations which allow a unique mapping in the opc-ua address space:
The :attr:`~asyncua.ua.uatypes.NodeId.Identifier` and the :attr:`~asyncua.ua.uatypes.NodeId.NamespaceIndex`.
In addition there is the :attr:`~asyncua.ua.uatypes.NodeId.NodeIdType` attribute which is used
to specify which opc-ua type is used for the Identifier.


Creating NodeId's
=================

As allready mentioned above, the NodeId class supports different types for the Identifier.
The type is handled automatically on class instanciation and there is usually no need
to set the type manually. Creating new NodeIds usually looks like this:

.. code-block:: python

    >>> from asyncua import ua
    >>> ua.NodeId(1, 2)  # Integer Identifier
    NodeId(Identifier=1, NamespaceIndex=2, NodeIdType=<NodeIdType.FourByte: 1>)
    >>> ua.NodeId('Test', 2)  # String Identifier
    NodeId(Identifier='Test', NamespaceIndex=2, NodeIdType=<NodeIdType.String: 3>)
    >>> ua.NodeId(b'Test', 2)  # Bytes Identifier
    NodeId(Identifier=b'Test', NamespaceIndex=2, NodeIdType=<NodeIdType.ByteString: 5>)

A NodeId can also be built from a single string:

.. code-block:: python

    >>> ua.NodeId.from_string('ns=2;i=4')
    NodeId(Identifier=4, NamespaceIndex=2, NodeIdType=<NodeIdType.Numeric: 2>)
    >>> ua.NodeId.from_string('ns=2;s=Test')
    NodeId(Identifier='Test', NamespaceIndex=2, NodeIdType=<NodeIdType.String: 3>)

The input string must be in the format :code:`<key>=<val>;[<key>=<val>]`, or in words:
it must be a list of key-value pairs, separated by semicolons.
The following keys are supported:

ns
    The ns key will map to the Namespace of the NodeId
i, s, g, b
    These keys will map to the Identifier of the NodeId. The character specifies the 
    type: Numeric, String, Guid or Bytes.
srv, nsu:
    If one of this keys is set, a :class:`~asyncua.ua.uatypes.ExpandedNodeId` will be returned
    and the ServerIndex and NamespaceUri will be set.
