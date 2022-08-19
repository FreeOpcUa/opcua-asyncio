# coding: utf-8
import pytest

from asyncua import Client
from asyncua.ua.uaerrors import BadMaxConnectionsReached

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


async def test_safe_disconnect():
    c = Client(url="opc.tcp://example:4840")
    await c.disconnect()
    # second disconnect should be noop
    await c.disconnect()
