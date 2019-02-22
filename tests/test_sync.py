import time

import pytest

from opcua.sync import Client, start_thread_loop, stop_thread_loop


@pytest.fixture
def server():
    pass


@pytest.fixture
def tloop():
    t_loop = start_thread_loop()
    yield t_loop
    stop_thread_loop()


@pytest.fixture
def client(tloop):
    c = Client("opc.tcp://localhost:4840/freeopcua/server")
    c.connect()
    yield c
    c.disconnect()


def test_sync1(client):
    print(client.nodes.root)
    time.sleep(2)
