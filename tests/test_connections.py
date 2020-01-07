# coding: utf-8

import asyncio

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
        client_2 = Client(f'opc.tcp://127.0.0.1:{port}')
        with pytest.raises(BadMaxConnectionsReached):
            await client_2.connect()
            await client_2.disconnect()
    else:
        client_1 = Client(f'opc.tcp://127.0.0.1:{port}')
        await client_1.connect()
        client_2 = Client(f'opc.tcp://127.0.0.1:{port}')
        with pytest.raises(BadMaxConnectionsReached):
            await client_2.connect()
            await client_2.disconnect()
        await client_1.disconnect()
    opc.server.iserver.isession.__class__.max_connections = 1000
