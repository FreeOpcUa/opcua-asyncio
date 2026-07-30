=====================
Synchronous Interface
=====================

You don't like to work with ``asyncio`` and ``async`` / ``await`` or you need to integrate
the package in code which is not using ``asyncio``? The :mod:`asyncua.sync` module provides
a convenient wrapper around the client and server and provides synchronous versions of
the node and subscription classes. This allows direct usage of the package, using the same
interface as for ``async`` code, without writing custom wrappers.

Client lifecycle
================

Disconnecting a sync Client keeps its ThreadLoop running so that the Client can connect
again later. Close the Client explicitly when it is no longer needed:

.. code-block:: python

   from asyncua.sync import Client

   client = Client("opc.tcp://localhost:4840")
   try:
       client.connect()
       value = client.nodes.server_state.read_value()
       client.disconnect()

       client.connect()
       value = client.nodes.server_state.read_value()
       client.disconnect()
   finally:
       client.close()

A ThreadLoop supplied by the caller is never stopped by the Client.
