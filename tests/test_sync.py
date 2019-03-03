import time

import pytest

from asyncua.sync import Client, start_thread_loop, stop_thread_loop, Server
from asyncua import ua


@pytest.fixture
def server():
    s = Server()
    s.set_endpoint('opc.tcp://*:8840/freeopcua/server/')
    uri = "http://examples.freeopcua.github.io"
    idx = s.register_namespace(uri)
    myobj = s.nodes.objects.add_object(idx, "MyObject")
    myvar = myobj.add_variable(idx, "MyVariable", 6.7)
    mysin = myobj.add_variable(idx, "MySin", 0, ua.VariantType.Float)
    s.start()
    yield s
    s.stop()


@pytest.fixture
def tloop():
    t_loop = start_thread_loop()
    yield t_loop
    stop_thread_loop()


@pytest.fixture
def client(tloop, server):
    c = Client("opc.tcp://localhost:8840/freeopcua/server")
    c.connect()
    yield c
    c.disconnect()


def test_sync_client(client):
    client.load_type_definitions()
    uri = "http://examples.freeopcua.github.io"
    idx = client.get_namespace_index(uri)
    myvar = client.nodes.root.get_child(["0:Objects", f"{idx}:MyObject", f"{idx}:MyVariable"])
    assert myvar.get_value() == 6.7


def test_sync_get_node(client):
    node  = client.get_node(85)
    assert node == client.nodes.objects
    nodes = node.get_children()
    assert len(nodes) == 2
    assert nodes[0] == client.nodes.server

