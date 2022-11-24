========================
Installation & CLI Tools
========================

Package Installation
====================

The opcua-asyncio package is available `PyPi <https://pypi.org/project/asyncua/>`_ as :code:`asyncua` package.
To install the package execute

.. code-block:: console

    pip install asyncua

As the package is still under very active development you might also consider to install the package from the
source repository

.. code-block:: console

    pip install git+https://github.com/FreeOpcUa/opcua-asyncio.git#egg=asyncua
    # or, if git is not available
    pip install https://github.com/FreeOpcUa/opcua-asyncio/archive/refs/heads/master.zip#egg=asyncua

Once the installation is completed, the package is ready to be used. To verify the installation,
or the report the version if you create a bugreport, the following code can be run in a python interpreter:

.. code-block:: python
 
    import asyncua
    print(asyncua.__version__)


Command Line Tools
==================

Alongside the package some utility command line tools are installed: 

:code:`uabrowse`: 
    Browse OPC-UA node and print result

:code:`uacall`: 
    Call method of a node

:code:`uaclient`:
    Connect to server and start python shell. root and objects nodes are available. Node specificed in command line is available as mynode variable.

:code:`uadiscover`:
    Performs OPC UA discovery and prints information on servers and endpoints.

:code:`uageneratestructs`:
    Generate a Python module from the xml structure definition (.bsd), the node argument is typically a children of i=93.

:code:`uahistoryread`:
    Read history of a node.

:code:`uals`:
    Browse OPC-UA node and print result.

:code:`uaread` / :code:`uawrite`:
    Read / Write attribute of a node, by default reads value of a node.

:code:`uaserver`:
    Run an example OPC-UA server. By importing xml definition and using uawrite command line, it is even possible to expose real data using this server.

:code:`uasubscribe`:
    Subscribe to a node and print results

These command line tools can be used from within the environment in which the package was installed. To get more information run:

.. code-block:: console

    <ua-tool> --help
    # For example
    uaread --help


More Tools for Development
==========================

.. todo:: Create a list of additional tools which are nice to have during development
    Possible Tools:

    - opcua-client (https://github.com/FreeOpcUa/opcua-client-gui)
    - UaModeler (https://www.unified-automation.com/products/development-tools/uamodeler.html)
