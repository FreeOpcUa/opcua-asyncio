===============
Client Overview
===============

Creating a client
=================

There is not much to it: Create a :class:`asyncua.client.client.Client` and your
ready to go. The url is usually something like ``opc.tcp:\\<server>:4840``, but you
might check your server documentation to make sure your server runs actually on this port.

Connecting to a server
======================

.. todo:: Show different examples, with / without security, ...


Learn more about the server
===========================

.. todo:: Things to show here: Namespaces, loading data type definitions, ...

Browsing and accessing nodes
============================

.. todo:: Usage of shortcut objects (root, objects, ...)


Managing additional sessions
===========================

Use ``UaClient.create_session_object(parameters)`` to create an additional
session on an open secure channel, then activate it with its own credentials.
``sessions`` lists owned sessions; ``get_session(id)`` and
``close_session_object(id)`` use the server-assigned SessionId.
``disconnect()`` closes all owned sessions and the connection.

The server must support multiple sessions per channel. Callers manage channel
renewal and keep each session active; additional sessions are not automatically
recovered.
