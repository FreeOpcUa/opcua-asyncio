# coding: utf-8
import asyncio
import pytest

from asyncua import Client, Server
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
            await cl.get_namespace_array()
