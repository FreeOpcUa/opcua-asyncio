import asyncio
import pytest
from collections import namedtuple
from opcua import Client
from opcua import Server
from .test_common import add_server_methods
from .util_enum_struct import add_server_custom_enum_struct

port_num = 48540
port_num1 = 48510
port_discovery = 48550

Opc = namedtuple('opc', ['opc', 'server'])


def pytest_generate_tests(metafunc):
    if 'opc' in metafunc.fixturenames:
        metafunc.parametrize('opc', ['client', 'server'], indirect=True)


@pytest.yield_fixture(scope='module')
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='module')
async def server():
    # start our own server
    srv = Server()
    await srv.init()
    srv.set_endpoint(f'opc.tcp://127.0.0.1:{port_num}')
    await add_server_methods(srv)
    await add_server_custom_enum_struct(srv)
    await srv.start()
    yield srv
    # stop the server
    await srv.stop()


@pytest.fixture(scope='module')
async def discovery_server():
    # start our own server
    srv = Server()
    await srv.init()
    await srv.set_application_uri('urn:freeopcua:python:discovery')
    srv.set_endpoint(f'opc.tcp://127.0.0.1:{port_discovery}')
    await srv.start()
    yield srv
    # stop the server
    await srv.stop()


@pytest.fixture(scope='module')
async def admin_client():
    # start admin client
    # long timeout since travis (automated testing) can be really slow
    clt = Client(f'opc.tcp://admin@127.0.0.1:{port_num}', timeout=10)
    await clt.connect()
    yield clt
    await clt.disconnect()


@pytest.fixture(scope='module')
async def client():
    # start anonymous client
    ro_clt = Client(f'opc.tcp://127.0.0.1:{port_num}')
    await ro_clt.connect()
    yield ro_clt
    await ro_clt.disconnect()


@pytest.fixture(scope='module')
async def opc(request):
    """
    Fixture for tests that should run for both `Server` and `Client`
    :param request:
    :return:
    """
    if request.param == 'client':
        srv = Server()
        await srv.init()
        srv.set_endpoint(f'opc.tcp://127.0.0.1:{port_num}')
        await add_server_methods(srv)
        await srv.start()
        # start client
        # long timeout since travis (automated testing) can be really slow
        clt = Client(f'opc.tcp://admin@127.0.0.1:{port_num}', timeout=10)
        await clt.connect()
        yield Opc(clt, srv)
        await clt.disconnect()
        await srv.stop()
    elif request.param == 'server':
        # start our own server
        # start our own server
        srv = Server()
        await srv.init()
        srv.set_endpoint(f'opc.tcp://127.0.0.1:{port_num1}')
        await add_server_methods(srv)
        await srv.start()
        yield Opc(srv, srv)
        # stop the server
        await srv.stop()
    else:
        raise ValueError("invalid internal test config")
