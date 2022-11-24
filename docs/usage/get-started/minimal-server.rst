=======================
A Minimal OPC-UA Server
=======================

Let's start exploring the :code:`asyncua` package by building a minimal runnable server.
Most of the hard work will be hidden behind the scene and we only need to implement the
application specific code.

The complete code will look like the code below. In the next sections we will look at
the different parts of the code, so don't be overhelmed by the code snippet!

.. literalinclude:: ../../../examples/server-minimal.py
    :caption: server-minimal.py
    :linenos:

Before we even look at the code in detail, let's try out what our server can do.
Start the server in a terminal with :code:`python server-minimal.py` and open a new console.
In the new console you now can use the CLI tools (see :ref:`usage/get-started/installation:command line tools`) provided by the package to explore
the server. The following session gives you an idea how the tools can be used.

.. code-block:: console

    $ uals --url=opc.tcp://127.0.0.1:4840  # List root node
    Browsing node i=84 at opc.tcp://127.0.0.1:4840
    DisplayName                                NodeId   BrowseName    Value

    LocalizedText(Locale=None, Text='Objects') i=85     0:Objects
    LocalizedText(Locale=None, Text='Types')   i=86     0:Types
    LocalizedText(Locale=None, Text='Views')   i=87     0:Views

    $ uals --url=opc.tcp://127.0.0.1:4840 --nodeid i=85 # List 0:Objects
    Browsing node i=85 at opc.tcp://127.0.0.1:4840

    DisplayName                                     NodeId               BrowseName         Value

    LocalizedText(Locale=None, Text='Server')       i=2253               0:Server
    LocalizedText(Locale=None, Text='Aliases')      i=23470              0:Aliases
    LocalizedText(Locale=None, Text='MyObject')     ns=2;i=1             2:MyObject
    LocalizedText(Locale=None, Text='ServerMethod') ns=2;s=ServerMethod  2:ServerMethod

    $ # In the last two lines we can see our own MyObject and ServerMethod
    $ # Lets read a value!
    $ uaread --url=opc.tcp://127.0.0.1:4840 --nodeid "ns=2;i=2"  # By NodeId
    7.599999999999997
    $ uaread --url=opc.tcp://127.0.0.1:4840 --path "0:Objects,2:MyObject,2:MyVariable" # By BrowsePath
    12.199999999999996
    
Seems like our server is working and we can browse through the nodes, read values, ...
So let's start working through the code!

Imports, Basic Setup & Configuration
====================================

In the first few lines the relevant packages, classes and methods are imported. 
While the :mod:`logging` module is optional (just remove all calls to the logging module),
:mod:`asyncio` is required to actually run our main function. From the :mod:`asyncua`
package we need the :class:`~asyncua.server.server.Server`, the :mod:`asyncua.ua`
module and the :meth:`~asyncua.common.methods.uamethod` decorator.

Ignore the :code:`@uamethod ...` part for the moment and jump straight into the
:code:`async def main()` function:

.. literalinclude:: ../../../examples/server-minimal.py
    :caption: server-minimal.py, Line 13 - 22
    :lines: 13-22

.. todo:: The :meth:`~asyncua.server.server.Server.init` and :meth:`~asyncua.server.server.Server.set_endpoint`
    methods have no docstrings but are referenced in the next section.

Here the server is created and initialized (:meth:`~asyncua.server.server.Server.init`).
The endpoint is configured (:meth:`~asyncua.server.server.Server.set_endpoint`) and a custom namespace
is registered (:meth:`~asyncua.server.server.Server.register_namespace`). It's recommended (:emphasis:`required??`)
that all custom objects, variables and methods live in a separate namespace. We store its index as :code:`idx`.
We'll need it later to add our custom objects to the namespace.

Creating Objects and Variables
==============================

.. literalinclude:: ../../../examples/server-minimal.py
    :caption: server-minimal.py, Line 26 - 29
    :lines: 26-29

In the next lines, the custom object "MyObject" is created and a variable is added to this object.
Note that by default all variables are read-only, so we need to be explicit and make it writable.
The :meth:`~asyncua.common.node.Node.add_object` / :meth:`~asyncua.common.node.Node.add_variable` calls
are actually just calling :meth:`~asyncua.common.manage_nodes.create_object`, respectively 
:meth:`~asyncua.common.manage_nodes.create_variable` internally. You can find more information on
how nodes and variables are created in the API docs of these methods.

Adding Methods
==============

With the code we have written so far, we would already have a server which can be run and
exposes some custom data. But to complete the example, we also add a method which is callable
by clients:

.. literalinclude:: ../../../examples/server-minimal.py
    :caption: server-minimal.py, Line 8 - 11
    :lines: 8 - 11 

.. literalinclude:: ../../../examples/server-minimal.py
    :caption: server-minimal.py, Line 30 - 36
    :lines: 30 - 36

To do this, a function, decorated with the :meth:`~asyncua.common.methods.uamethod` decorator,
is created and, similar to the objects and variables, registered on the server. It would
also be possible to register a undecorated function on the server, but in this case the
coversion from and to UA Variant types would be up to us.

Starting the Server
===================

.. literalinclude:: ../../../examples/server-minimal.py
    :caption: server-minimal.py, Line 37 -
    :lines: 37 -

Using the server as a context manager with :code:`async with server: ...` allows us to 
hide starting and shutting down the server nicely. In order to keep the server alive
a endless loop must be present. In this example the loop is also used to periodically
update the variable in our custom object.

Now that we have a working server, let's go on and write :ref:`usage/get-started/minimal-client:a minimal opc-ua client`!
