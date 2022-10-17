=====================
Synchronous Interface
=====================

You don't like to work with ``asyncio`` and ``async`` / ``await`` or you need to integrate
the package in code wich is not using ``asyncio``? The :mod:`asyncua.sync` module provides
a convinient wrapper around the client and server and provides synchronous versions of
the node and subscription classes. This allows direct usage of the package, using the same
interface as for ``async`` code, without writing custom wrappers.