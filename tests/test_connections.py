# coding: utf-8
import asyncio
import pytest
import struct
from asyncua import Client, Server, ua
from asyncua.ua.uaerrors import BadMaxConnectionsReached
from .conftest import port_num, find_free_port

pytestmark = pytest.mark.asyncio


async def test_max_connections_1(opc):
    opc.server.iserver.isession.__class__.max_connections = 1
    port = opc.server.endpoint.port
    if port == port_num:
        # if client we already have one connection
        with pytest.raises(BadMaxConnectionsReached):
            async with Client(f'opc.tcp://127.0.0.1:{port}'):
                pass
    else:
        async with Client(f'opc.tcp://127.0.0.1:{port}'):
            with pytest.raises(BadMaxConnectionsReached):
                async with Client(f'opc.tcp://127.0.0.1:{port}'):
                    pass
    opc.server.iserver.isession.__class__.max_connections = 1000


async def test_dos_server(opc):
    # See issue 1013 a crafted packet triggered dos
    port = opc.server.endpoint.port
    async with Client(f'opc.tcp://127.0.0.1:{port}') as c:
        # craft invalid packet that trigger dos
        message_type, chunk_type, packet_size = [ua.MessageType.SecureOpen, b'E', 0]
        c.uaclient.protocol.transport.write(struct.pack("<3scI", message_type, chunk_type, packet_size))
        # sleep to give the server time to handle the message because we bypass the asyncio
        await asyncio.sleep(1.0)
        with pytest.raises(ConnectionError):
            # now try to read a value to see if server is still alive
            server_time_node = c.get_node(ua.NodeId(ua.ObjectIds.Server_ServerStatus_CurrentTime))
            await server_time_node.read_value()


async def test_safe_disconnect():
    c = Client(url="opc.tcp://example:4840")
    await c.disconnect()
    # second disconnect should be noop
    await c.disconnect()


async def test_client_connection_lost():
    # Test the disconnect behavoir
    port = find_free_port()
    srv = Server()
    await srv.init()
    srv.set_endpoint(f'opc.tcp://127.0.0.1:{port}')
    await srv.start()
    async with Client(f'opc.tcp://127.0.0.1:{port}', timeout=0.5, watchdog_intervall=1) as cl:
        await srv.stop()
        await asyncio.sleep(2)
        with pytest.raises(ConnectionError):
            # check if connection is alive
            await cl.check_connection()
        # check if exception is correct rethrown on second call
        with pytest.raises(ConnectionError):
            await cl.check_connection()
        # check if a exception is thrown when a normal function is called
        with pytest.raises(ConnectionError):
            await cl.get_namespace_array()
