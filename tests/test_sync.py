from concurrent.futures import Future

import pytest

from asyncua.sync import Client, Server, ThreadLoop, SyncNode, call_method_full, XmlExporter, new_enum, new_struct, new_struct_field
from asyncua import ua, uamethod


@uamethod
def divide(parent, x, y):
    return x / y


@pytest.fixture
def tloop():
    with ThreadLoop() as tl:
        tl.loop.set_debug(True)
        yield tl


@pytest.fixture
def server(tloop):
    s = Server(tloop=tloop)
    s.disable_clock(True)
    s.set_endpoint('opc.tcp://0.0.0.0:8840/freeopcua/server/')
    uri = "http://examples.freeopcua.github.io"
    ns_idx = s.register_namespace(uri)
    myobj = s.nodes.objects.add_object(ns_idx, "MyObject")
    myobj.add_variable(ns_idx, "MyVariable", 6.7)
    myobj.add_variable(ns_idx, "MySin", 0, ua.VariantType.Float)
    s.nodes.objects.add_method(ns_idx, "Divide", divide, [ua.VariantType.Float, ua.VariantType.Float], [ua.VariantType.Float])
    with s:
        yield s


@pytest.fixture
def client(tloop, server):
    c = Client("opc.tcp://admin@localhost:8840/freeopcua/server", tloop=tloop)
    with c:
        yield c


@pytest.fixture
def client_no_tloop(server):
    with Client("opc.tcp://admin@localhost:8840/freeopcua/server") as c:
        yield c


@pytest.fixture
def idx(client):
    uri = "http://examples.freeopcua.github.io"
    i = client.get_namespace_index(uri)
    return i


def test_sync_client(client, idx):
    client.load_type_definitions()
    myvar = client.nodes.root.get_child(["0:Objects", f"{idx}:MyObject", f"{idx}:MyVariable"])
    assert myvar.read_value() == 6.7


def test_sync_client_get_node(client):
    node = client.get_node(85)
    assert node == client.nodes.objects
    nodes = node.get_children()
    assert len(nodes) > 2
    assert nodes[0] == client.nodes.server
    assert isinstance(nodes[0], SyncNode)


def test_sync_server_get_node(server):
    node = server.get_node(85)
    assert node == server.nodes.objects
    nodes = node.get_children()
    assert len(nodes) > 2
    assert nodes[0] == server.nodes.server
    assert isinstance(nodes[0], SyncNode)


class MySubHandler:

    def __init__(self):
        self.future = Future()

    def reset(self):
        self.future = Future()

    def datachange_notification(self, node, val, data):
        self.future.set_result((node, val))

    def event_notification(self, event):
        self.future.set_result(event)


def test_sync_tloop_sub(client_no_tloop):
    test_sync_sub(client_no_tloop)


def test_sync_sub(client):
    myhandler = MySubHandler()
    sub = client.create_subscription(1, myhandler)
    var = client.nodes.objects.add_variable(3, 'SubVar', 0.1)
    sub.subscribe_data_change(var)
    n, v = myhandler.future.result()
    assert v == 0.1
    assert n == var
    myhandler.reset()
    var.write_value(0.123)
    n, v = myhandler.future.result()
    assert v == 0.123
    sub.delete()


def test_sync_meth(client, idx):
    res = client.nodes.objects.call_method(f"{idx}:Divide", 4, 2)
    assert res == 2
    with pytest.raises(ua.UaError):
        res = client.nodes.objects.call_method(f"{idx}:Divide", 4, 0)


def test_sync_client_no_tl(client_no_tloop, idx):
    test_sync_meth(client_no_tloop, idx)


def test_sync_call_meth(client, idx):
    methodid = client.nodes.objects.get_child(f"{idx}:Divide")
    res = call_method_full(client.tloop, client.nodes.objects, methodid, 4, 2)
    assert res.OutputArguments[0] == 2


def test_sync_xml_export(server):
    exp = XmlExporter(server)
    exp.build_etree([server.nodes.objects])
    exp.write_xml("toto_test_export.xml")


def test_create_enum_sync(server):
    idx = 4
    new_enum(server, idx, "MyCustEnum", [
        "titi",
        "toto",
        "tutu",
    ])

    server.load_data_type_definitions()

    var = server.nodes.objects.add_variable(idx, "my_enum", ua.MyCustEnum.toto)
    val = var.read_value()
    assert val == 1


def test_create_enum_sync_client(client):
    idx = 4
    new_enum(client, idx, "MyCustEnum2", [
        "titi",
        "toto",
        "tutu",
    ])

    client.load_data_type_definitions()

    var = client.nodes.objects.add_variable(idx, "my_enum", ua.MyCustEnum2.toto)
    val = var.read_value()
    assert val == 1


def test_create_struct_sync(server):
    idx = 4

    new_struct(server, idx, "MyMyStruct", [
        new_struct_field("MyBool", ua.VariantType.Boolean),
        new_struct_field("MyUInt32", ua.VariantType.UInt32, array=True),
    ])

    server.load_data_type_definitions()
    mystruct = ua.MyMyStruct()
    mystruct.MyUInt32 = [78, 79]
    var = server.nodes.objects.add_variable(idx, "my_struct", mystruct)
    val = var.read_value()
    assert val.MyUInt32 == [78, 79]


def test_create_struct_sync_client(client):
    idx = 4

    new_struct(client, idx, "MyMyStruct", [
        new_struct_field("MyBool", ua.VariantType.Boolean),
        new_struct_field("MyUInt32", ua.VariantType.UInt32, array=True),
    ])

    client.load_data_type_definitions()
    mystruct = ua.MyMyStruct()
    mystruct.MyUInt32 = [78, 79]
    var = client.nodes.objects.add_variable(idx, "my_struct", mystruct)
    val = var.read_value()
    assert val.MyUInt32 == [78, 79]
