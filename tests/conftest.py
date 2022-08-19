import asyncio
import pytest
import operator
import os
import socket
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Process, Condition, Event
from collections import namedtuple
from asyncio import get_event_loop_policy, sleep
from contextlib import closing

from asyncua import Client
from asyncua import Server, ua
from asyncua.client.ua_client import UASocketProtocol
from asyncua.client.ha.ha_client import HaClient, HaConfig, HaMode
from asyncua.server.history import HistoryDict
from asyncua.server.history_sql import HistorySQLite

from .test_common import add_server_methods
from .util_enum_struct import add_server_custom_enum_struct





RETRY = 20
SLEEP = 0.4
PORTS_USED = set()
Opc = namedtuple('opc', ['opc', 'server'])

def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        port = s.getsockname()[1]
        if port not in PORTS_USED:
            PORTS_USED.add(port)
            return port
        else:
            return find_free_port()

port_num = find_free_port()
port_num1 = find_free_port()
port_discovery = find_free_port()


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


@pytest.fixture(scope='module')
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    loop = get_event_loop_policy().new_event_loop()
    loop.set_debug(True)
    yield loop
    loop.close()


class ServerProcess(Process):
    def __init__(self):
        super().__init__()
        self.url = f"opc.tcp://127.0.0.1:{port_num}"
        self.cond = Condition()
        self.stop_ev = Event()

    async def run_server(self, url):
        srv = Server()
        srv.set_endpoint(url)
        await srv.init()
        await add_server_methods(srv)
        await add_server_custom_enum_struct(srv)
        async with srv:
            with self.cond:
                self.cond.notify_all()
            while not self.stop_ev.is_set():
                await asyncio.sleep(1)
        await srv.stop()

    def stop(self):
        self.stop_ev.set()

    async def wait_for_start(self):
        with ThreadPoolExecutor() as pool:
            result = await asyncio.get_running_loop().run_in_executor(pool, self.wait_for_start_sync)

    def wait_for_start_sync(self):
        with self.cond:
            self.cond.wait()

    def run(self):
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.run_server(self.url))


@pytest.fixture(scope='module')
async def running_server(request):
    """
    Spawn a server in a separate process
    which can handle OPCUA requests
    """
    process = ServerProcess()
    process.start()
    await process.wait_for_start()
    yield process.url
    process.stop()
    process.join()


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

@pytest.fixture(scope="session")
def client_key_and_cert(request):
    base_dir = os.path.dirname(os.path.dirname(__file__))
    cert_dir = os.path.join(base_dir, "examples/certificates") + os.sep
    key = f"{cert_dir}peer-private-key-example-1.pem"
    cert = f"{cert_dir}peer-certificate-example-1.der"
    return key, cert


@pytest.fixture(scope="session")
def server_key_and_cert(request):
    base_dir = os.path.dirname(os.path.dirname(__file__))
    cert_dir = os.path.join(base_dir, "examples") + os.sep
    key = f"{cert_dir}private-key-example.pem"
    cert = f"{cert_dir}certificate-example.der"
    return key, cert


@pytest.fixture(scope="function")
def ha_config():
    """
    Factory method to return a HaConfig
    """

    def _ha_config(srv_port1, srv_port2, ha_mode=HaMode.WARM):
        return HaConfig(
            ha_mode,
            keepalive_timer=1,
            manager_timer=1,
            reconciliator_timer=1,
            urls=[
                f"opc.tcp://127.0.0.1:{srv_port1}",
                f"opc.tcp://127.0.0.1:{srv_port2}",
            ],
            session_timeout=30,
        )

    return _ha_config


@pytest.fixture(scope="module")
async def ha_servers(server_key_and_cert):
    # start our own server
    srvs = []
    key, cert = server_key_and_cert

    async def create_srv(port, key, cert):
        srv = Server()
        srvs.append(srv)
        await srv.init()
        await srv.set_application_uri("urn:freeopcua:python:discovery")
        srv.set_endpoint(f"opc.tcp://127.0.0.1:{port}")
        srv.set_security_policy(
            [
                ua.SecurityPolicyType.NoSecurity,
                ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt,
            ]
        )
        await srv.load_certificate(cert)
        await srv.load_private_key(key)
        await srv.start()
        # default the service level to 255 once started
        slevel = srv.get_node(ua.NodeId(ua.ObjectIds.Server_ServiceLevel))
        await slevel.write_value(ua.Variant(255, ua.VariantType.Byte))
        return srv

    port_1 = find_free_port()
    port_2 = find_free_port()
    srv1 = await create_srv(port_1, key, cert)
    srv2 = await create_srv(port_2, key, cert)
    yield srv1, srv2
    # stop the servers
    for srv in srvs:
        await srv.stop()
    PORTS_USED.remove(port_1)
    PORTS_USED.remove(port_2)


@pytest.fixture(scope="module")
async def srv_variables(ha_servers):
    """
    This fixture returns client like ha_client
    server within the module scope.
    """
    clts = []
    # add the variables to the client
    node_to_var = {}
    for srv in ha_servers:
        for var in ("V1", "V2"):
            url = f"{srv.endpoint.scheme}://admin@{srv.endpoint.netloc}"
            c = Client(url, timeout=10)
            clts.append(c)
            await c.connect()
            values = [1, 2, 3]
            o = c.nodes.objects
            node = await o.add_variable(3, f"SubscriptionVariable{var}", values)
            node_to_var[node] = values
    yield node_to_var
    # disconnect admin@clients used to write the custom variables
    for c in clts:
        await c.disconnect()


@pytest.fixture(scope="function")
async def ha_client(ha_config, ha_servers):
    """
    This fixture returns everytime a new
    HaClient but configured with the same
    server within the module scope.
    """
    srv1, srv2 = ha_servers
    srv1_port = srv1.endpoint.port
    srv2_port = srv2.endpoint.port

    ha_config = ha_config(srv1_port, srv2_port)
    ha_client = HaClient(ha_config)
    yield ha_client
    if ha_client.is_running:
        await ha_client.stop()


async def wait_clients_socket(ha_client, state):
    for client in ha_client.get_clients():
        for _ in range(RETRY):
            if state == UASocketProtocol.CLOSED and not client.uaclient.protocol:
                break
            if client.uaclient.protocol and client.uaclient.protocol.state == state:
                # for connection OPEN, also wait for the session to be established
                # otherwise we can encounter failure on disconnect
                if state == UASocketProtocol.OPEN:
                    if client._renew_channel_task:
                        break
                else:
                    break
            await sleep(SLEEP)
        assert (not client.uaclient.protocol and state == UASocketProtocol.CLOSED) or client.uaclient.protocol.state == state


async def wait_sub_in_real_map(ha_client, sub, negation=False):
    reconciliator = ha_client.reconciliator
    oper = operator.not_ if negation else operator.truth
    for client in ha_client.get_clients():
        url = client.server_url.geturl()
        for _ in range(RETRY):
            if oper(
                reconciliator.real_map.get(url) and reconciliator.real_map[url].get(sub)
            ):
                break
            await sleep(SLEEP)
        assert oper(reconciliator.real_map[url].get(sub))


async def wait_node_in_real_map(ha_client, sub, node_str, negation=False):
    oper = operator.not_ if negation else operator.truth
    reconciliator = ha_client.reconciliator
    for client in ha_client.get_clients():
        url = client.server_url.geturl()
        vs = None
        for _ in range(RETRY):
            # virtual subscription must already exist,
            if reconciliator.real_map.get(url):
                vs = reconciliator.real_map[url][sub]
                if oper(node_str in vs.nodes):
                    break
            await sleep(SLEEP)
        assert oper(node_str in vs.nodes)


async def wait_mode_in_real_map(ha_client, client, sub, mode, value):
    reconciliator = ha_client.reconciliator
    await wait_sub_in_real_map(ha_client, sub)
    url = client.server_url.geturl()
    vsub = reconciliator.real_map[url][sub]
    option = None
    for _ in range(RETRY):
        option = getattr(vsub, mode)
        if option == value:
            break
        await sleep(SLEEP)
    assert option == value


async def wait_for_status_change(ha_client, client, status):
    # wait for the KeepAlive task to update its client status
    srv_info = ha_client.clients[client]
    for _ in range(RETRY):
        if srv_info.status == status:
            break
        await sleep(SLEEP)
    assert srv_info.status == status
