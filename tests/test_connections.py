# coding: utf-8
import pytest
import asyncio
from asyncua import Client, ua
from asyncua.ua.uaerrors import BadMaxConnectionsReached
import struct
from .conftest import port_num

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


async def test_oom_server(opc):
    port = opc.server.endpoint.port
    async with Client(f'opc.tcp://127.0.0.1:{port}') as c:
        # craft invalid packet that trigger oom
        message_type, chunk_type, packet_size = [ua.MessageType.SecureOpen, b'E', 0]
        c.uaclient.protocol.transport.write(struct.pack("<3scI", message_type, chunk_type, packet_size))
        # sleep to give the server time to handle the message because we bypass the asyncio
        await asyncio.sleep(1.0)
        # now try to read a value to see if server is still alive
        server_time_node = c.get_node(ua.NodeId(ua.ObjectIds.Server_ServerStatus_CurrentTime))
        await server_time_node.read_value()


async def test_safe_disconnect():
    c = Client(url="opc.tcp://example:4840")
    await c.disconnect()
    # second disconnect should be noop
    await c.disconnect()
