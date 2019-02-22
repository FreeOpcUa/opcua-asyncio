import time

import pytest

from opcua.sync import Client


@pytest.fixture
def server():
    pass


@pytest.fixture
def client():
    c = Client("opc.tcp://localhost:4840/freeopcua/server")
    c.connect()
    yield c
    c.disconnect()


def test_sync1(client):
    print(client.nodes.root)
    time.sleep(2)
