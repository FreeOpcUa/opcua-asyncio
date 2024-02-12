from concurrent.futures import Future
from pathlib import Path
import tempfile

import pytest

from asyncua.client import Client as AsyncClient
from asyncua.client.ua_client import UaClient
from asyncua.sync import (
    Client,
    Server,
    ThreadLoop,
    SyncNode,
    call_method_full,
    XmlExporter,
    new_enum,
    new_struct,
    new_struct_field,
    sync_async_client_method,
    sync_uaclient_method,
)
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


def test_sync_uaclient_method(client, idx):
    client.load_type_definitions()
    myvar = client.nodes.root.get_child(["0:Objects", f"{idx}:MyObject", f"{idx}:MyVariable"])
    read_attributes = sync_uaclient_method(UaClient.read_attributes)(client)
    results = read_attributes([myvar.nodeid], attr=ua.AttributeIds.Value)
    assert len(results) == 1
    assert results[0].Value.Value == 6.7


def test_sync_async_client_method(client, idx):
    client.load_type_definitions()
    myvar = client.nodes.root.get_child(["0:Objects", f"{idx}:MyObject", f"{idx}:MyVariable"])
    read_attributes = sync_async_client_method(AsyncClient.read_attributes)(client)
    results = read_attributes([myvar], attr=ua.AttributeIds.Value)
    assert len(results) == 1
    assert results[0].Value.Value == 6.7


def test_sync_client_get_node(client, idx):
    node = client.get_node(85)
    assert node == client.nodes.objects
    nodes = node.get_children()
    assert len(nodes) > 2
    assert nodes[0] == client.nodes.server
    assert isinstance(nodes[0], SyncNode)

    results = node.get_children_by_path([[f"{idx}:MyObject", f"{idx}:MyVariable"]])
    assert len(results) == 1
    vars = results[0]
    assert len(vars) == 1
    assert vars[0].read_value() == 6.7


def test_sync_delete_nodes(client):
    obj = client.nodes.objects
    var = obj.add_variable(2, "VarToDelete", 9.1)
    childs = obj.get_children()
    assert var in childs
    nodes, statuses = client.delete_nodes([var])
    assert len(nodes) == len(statuses) == 1
    assert isinstance(nodes[0], SyncNode)
    assert nodes[0] == var
    assert statuses[0].is_good()


async def test_sync_import_xml(client):
    nodes = client.import_xml("tests/custom_struct.xml")
    assert all([isinstance(node, ua.NodeId) for node in nodes])


def test_sync_read_attributes(client: Client, idx):
    client.load_type_definitions()
    myvar = client.nodes.root.get_child(
        ["0:Objects", f"{idx}:MyObject", f"{idx}:MyVariable"]
    )
    assert isinstance(myvar, SyncNode)
    results = client.read_attributes([myvar], attr=ua.AttributeIds.Value)
    assert len(results) == 1
    assert results[0].Value.Value == 6.7


def test_sync_read_values(client: Client, idx):
    client.load_type_definitions()
    myvar = client.nodes.root.get_child(
        ["0:Objects", f"{idx}:MyObject", f"{idx}:MyVariable"]
    )
    assert isinstance(myvar, SyncNode)
    results = client.read_values([myvar])
    assert len(results) == 1
    assert results[0] == 6.7


def test_sync_write_values(client: Client):
    myvar = client.nodes.objects.add_variable(3, "a", 1)
    myvar.set_writable()
    assert isinstance(myvar, SyncNode)
    rets = client.write_values([myvar], [4])
    assert rets == [ua.StatusCode(value=ua.StatusCodes.Good)]
    assert myvar.read_value() == 4


def test_sync_client_browse_nodes(client: Client, idx):
    nodes = [
        client.get_node("ns=0;i=2267"),
        client.get_node("ns=0;i=2259"),
    ]
    results = client.browse_nodes(nodes)
    assert len(results) == 2
    assert isinstance(results, list)
    assert results[0][0] == nodes[0]
    assert results[1][0] == nodes[1]
    assert isinstance(results[0][0], SyncNode)
    assert isinstance(results[1][0], SyncNode)
    assert isinstance(results[0][1], ua.BrowseResult)
    assert isinstance(results[1][1], ua.BrowseResult)


def test_sync_server_get_node(server, idx):
    node = server.get_node(85)
    assert node == server.nodes.objects
    nodes = node.get_children()
    assert len(nodes) > 2
    assert nodes[0] == server.nodes.server
    assert isinstance(nodes[0], SyncNode)

    results = node.get_children_by_path([[f"{idx}:MyObject", f"{idx}:MyVariable"]])
    assert len(results) == 1
    vars = results[0]
    assert len(vars) == 1
    assert vars[0].read_value() == 6.7


@pytest.mark.xfail(
        raises=AttributeError, reason="asyncua introduced a regression, likely when we switched to pathlib", strict=True
    )
async def test_sync_server_creating_shelf_files_works(tloop: ThreadLoop, tmp_path: Path) -> None:
    shelf_file_path: Path = tmp_path / "shelf_file"

    Server(tloop=tloop, shelf_file=shelf_file_path)


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
    with tempfile.TemporaryDirectory() as tmpdir:
        exp.write_xml(Path(tmpdir) / "toto_test_export.xml")


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
