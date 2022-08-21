=======================
A Minimal OPC-UA Client
=======================

In this section we will build a client which reads / writes data from the server
created in the last section and calls the method which the server provides.
Running the client code will require a running server of course, so open a new
terminal and run :code:`python server-minimal.py` to start the server.

Like in the server section, we will first look at the complete code of the client
before diving into the details:

.. literalinclude:: ../../../examples/client-minimal.py
    :caption: client-minimal.py
    :linenos:


Connecting to the server
========================

To connect to the server a new :class:`~asyncua.client.client.Client` instance is created.
The client supports the same async context manager construct as we have already seen in
the server, which can be used to handle the opening / closing of the connection for us.

Getting the namespace
=====================
As all our custom objects life in a custom namespace, we need to get the namespace
index to address our objects. This is done with the :meth:`~asyncua.client.client.Client.get_namespace_index`
method. If you are connecting to a unknown server and want to find out which namespaces
are available the :meth:`~asyncua.client.client.Client.get_namespace_array` method can be used to
fetch a list of all namespaces of the server. 

Read / Write Variables
======================

To read or write a variable of an object, we first need to get the :class:`~asyncua.common.node.Node`
of the variable. The :meth:`~asyncua.common.node.Node.get_child` method of the root node 
(which is just a regular node) is used to transform the known path to a Node.

.. note:: Using :meth:`~asyncua.common.node.Node.get_child` will perform a server request
    in the background to resolve the path to a node. Extensive usage of this method can
    create a lot of network traffic which is not strictly required if the node id is knwon.
    If you know the node id it's better to use the :meth:`~asyncua.client.client.Client.get_node`
    method of the client. For example :code:`client.get_node("ns=2;i=2")` or
    :code:`client.get_node(ua.NodeId(2, 2))` could be used in the example. 
    Note that the call is not :code:`async`!

Once we have our node object, the variable value can directly be read or written using
the :meth:`~asyncua.common.node.Node.read_value` and :meth:`~asyncua.common.node.Node.write_value`
methods. The read method automatically transforms the opc-ua type to a python type but the
:meth:`~asyncua.common.node.Node.read_data_value` method can be used if the original type of
the variable is of interest. The write interface is built flexible and a :class:`~asyncua.ua.uatypes.Variant`
is also accepted to specify the exact type to be used.

Calling Methods
===============

The method interface is similar to the interface of variables. In the example the special
node :code:`client.nodes.objects`, wich is in fact just a shortcut to the :code:`0:Objects`
node, is used to call the `2:ServerMethod` on it. The :meth:`~asyncua.common.node.Node.call_method`
must be called on the parent node of the actuall method node.