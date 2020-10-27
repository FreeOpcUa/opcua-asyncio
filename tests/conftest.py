import asyncio
import pytest
from collections import namedtuple
from asyncua import ua, Client, Server
from asyncua.server.history import HistoryDict
from asyncua.server.history_sql import HistorySQLite

from .test_common import add_server_methods
from .util_enum_struct import add_server_custom_enum_struct
from threading import Thread

port_num = 48540
port_num1 = 48510
port_discovery = 48550

Opc = namedtuple('opc', ['opc', 'server'])


def pytest_generate_tests(metafunc):
    mark = metafunc.definition.get_closest_marker('parametrize')
    # override the opc parameters when explicilty provided
    if getattr(mark, "args", None) and "opc" in mark.args:
        pass
    elif "opc" in metafunc.fixturenames:
        metafunc.parametrize('opc', ['client', 'server'], indirect=True)
    elif 'history' in metafunc.fixturenames:
        metafunc.parametrize('history', ['dict', 'sqlite'], indirect=True)
    elif 'history_server' in metafunc.fixturenames:
        metafunc.parametrize('history_server', ['dict', 'sqlite'], indirect=True)


@pytest.yield_fixture(scope='module')
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    loop.set_debug(True)
    yield loop
    loop.close()


@pytest.fixture(scope='module')
async def running_server(request):
    """
    Spawn a server in a separate thread
    which can handle OPCUA requests
    """

    def wrapper(url):
        async def server(url):
            srv = Server()
            srv.set_endpoint(url)
            await srv.init()
            await add_server_methods(srv)
            await add_server_custom_enum_struct(srv)
            async with srv:
                while t.do_run:
                    await asyncio.sleep(1)
            await srv.stop()
        loop = asyncio.new_event_loop()
        loop.run_until_complete(server(url))

    url = f"opc.tcp://127.0.0.1:{port_num}"
    t = Thread(target=wrapper, args=(url,))
    t.do_run = True
    t.start()
    await asyncio.sleep(3)
    yield url

    def fin():
        t.do_run = False
        t.join()
    request.addfinalizer(fin)


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


@pytest.fixture()
async def history(request):
    if request.param == 'dict':
        h = HistoryDict()
        await h.init()
        yield h
        await h.stop()
    elif request.param == 'sqlite':
        h = HistorySQLite(':memory:')
        await h.init()
        yield h
        await h.stop()


class HistoryServer:
    def __init__(self):
        self.srv = Server()
        self.srv_node = None
        self.ev_values = None
        self.var = None
        self.values = None


async def create_srv_events(history_server: HistoryServer):
    history_server.ev_values = [i for i in range(20)]
    srv_evgen = await history_server.srv.get_event_generator()
    history_server.srv_node = history_server.srv.get_node(ua.ObjectIds.Server)
    await history_server.srv.historize_node_event(history_server.srv_node, period=None)
    for i in history_server.ev_values:
        srv_evgen.event.Severity = history_server.ev_values[i]
        await srv_evgen.trigger(message="test message")
        await asyncio.sleep(.1)
    await asyncio.sleep(2)


async def create_var(history_server: HistoryServer):
    o = history_server.srv.nodes.objects
    history_server.values = [i for i in range(20)]
    history_server.var = await o.add_variable(3, "history_var", 0)
    await history_server.srv.historize_node_data_change(history_server.var, period=None, count=0)
    for i in history_server.values:
        await history_server.var.write_value(i)
    await asyncio.sleep(1)


async def create_history_server(sqlite=False) -> HistoryServer:
    history_server = HistoryServer()
    await history_server.srv.init()
    history_server.srv.set_endpoint(f'opc.tcp://127.0.0.1:{port_num if not sqlite else port_num1}')
    await history_server.srv.start()
    if sqlite:
        history = HistorySQLite(":memory:")
        await history.init()
        history_server.srv.iserver.history_manager.set_storage(history)
    await create_var(history_server)
    await create_srv_events(history_server)
    return history_server


@pytest.fixture(scope='module')
async def history_server(request):
    if request.param == 'dict':
        srv = await create_history_server()
        yield srv
        await srv.srv.stop()
    elif request.param == 'sqlite':
        srv = await create_history_server(sqlite=True)
        yield srv
        await srv.srv.stop()
