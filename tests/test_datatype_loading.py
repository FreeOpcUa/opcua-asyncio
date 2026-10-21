from collections.abc import AsyncIterator
from struct import pack
from typing import Any

import pytest

from asyncua import Client, Node, Server, ua
from asyncua.common.structures104 import load_enums, new_enum, new_struct, new_struct_field
from asyncua.ua.ua_binary import extensionobject_from_binary, extensionobject_to_binary

from .conftest import find_free_port

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def datatype_server(restore_ua_registry: Any) -> AsyncIterator[tuple[Server, str, dict[str, Node]]]:
    server = Server()
    await server.init()
    url = f"opc.tcp://127.0.0.1:{find_free_port()}"
    server.set_endpoint(url)
    idx = await server.register_namespace("urn:asyncua:test:datatype-loading")
    nodes = {}
    nodes["ReloadEnum"] = await new_enum(
        server, ua.NodeId("ReloadEnum", idx), ua.QualifiedName("ReloadEnum", idx), ["Idle", "Running"]
    )
    nodes["ReloadFlags"] = await new_enum(
        server, ua.NodeId("ReloadFlags", idx), ua.QualifiedName("ReloadFlags", idx), ["Read", "Write"], option_set=True
    )
    nodes["ReloadInner"], _ = await new_struct(
        server,
        ua.NodeId("ReloadInner", idx),
        ua.QualifiedName("ReloadInner", idx),
        [new_struct_field("Count", ua.VariantType.Int32)],
    )
    nodes["ReloadStruct"], encodings = await new_struct(
        server,
        ua.NodeId("ReloadStruct", idx),
        ua.QualifiedName("ReloadStruct", idx),
        [
            new_struct_field("Mode", nodes["ReloadEnum"]),
            new_struct_field("Flags", nodes["ReloadFlags"]),
            new_struct_field("Inner", nodes["ReloadInner"]),
        ],
    )
    value = ua.ExtensionObject(TypeId=encodings[0].nodeid, Body=pack("<iIi", 1, 3, 42))
    variable = await server.nodes.objects.add_variable(idx, "ReloadValue", value, datatype=nodes["ReloadStruct"].nodeid)
    await variable.set_writable()
    nodes["Value"] = variable
    async with server:
        yield server, url, nodes


def check_class(value: Any, expected: type) -> None:
    assert type(value) is expected


async def check_loaded_value(client: Client, nodes: dict[str, Node], classes: dict[str, type]) -> Any:
    value = await client.get_node(nodes["Value"].nodeid).read_value()
    check_class(value, classes["ReloadStruct"])
    check_class(value.Mode, classes["ReloadEnum"])
    assert value.Mode.name == "Running"
    check_class(value.Flags, classes["ReloadFlags"])
    assert value.Flags == getattr(classes["ReloadFlags"], "Read") | getattr(classes["ReloadFlags"], "Write")
    check_class(value.Inner, classes["ReloadInner"])
    assert value.Inner.Count == 42
    for name in ("ReloadEnum", "ReloadFlags", "ReloadInner", "ReloadStruct"):
        cls = classes[name]
        assert getattr(ua, name) is cls
        assert ua.get_type(nodes[name].nodeid) is cls
        if name in ("ReloadInner", "ReloadStruct"):
            definition = await nodes[name].read_data_type_definition()
            assert isinstance(definition, ua.StructureDefinition)
            assert ua.extension_objects_by_typeid[definition.DefaultEncodingId] is cls
            assert ua.typeid_by_extension_objects[cls] == definition.DefaultEncodingId
            assert ua.datatype_by_extension_object[cls] == nodes[name].nodeid
        else:
            assert ua.enums_datatypes[cls] == nodes[name].nodeid
    return value


@pytest.mark.parametrize("overwrite_existing", [False, True])
@pytest.mark.parametrize("reconnect", [False, True])
async def test_repeated_datatype_loading(
    datatype_server: tuple[Server, str, dict[str, Node]], overwrite_existing: bool, reconnect: bool
) -> None:
    _, url, nodes = datatype_server
    names = nodes.keys() - {"Value"}
    client = Client(url)
    async with client:
        first = await client.load_data_type_definitions()
        assert names <= first.keys()
        old_value = await check_loaded_value(client, nodes, first)
        if reconnect:
            await client.disconnect()
            await client.connect()
        second = await client.load_data_type_definitions(overwrite_existing=overwrite_existing)
        if overwrite_existing:
            assert names <= second.keys()
            assert all(second[name] is not first[name] for name in names)
            current = second
        else:
            assert second == {}
            current = first
        await check_loaded_value(client, nodes, current)
        encoded = extensionobject_to_binary(old_value)
        decoded = extensionobject_from_binary(ua.utils.Buffer(encoded))
        check_class(decoded, current["ReloadStruct"])
        assert decoded.Inner.Count == 42
        await client.get_node(nodes["Value"].nodeid).write_value(old_value)
        await check_loaded_value(client, nodes, current)
        assert await client.load_data_type_definitions() == {}
        await check_loaded_value(client, nodes, current)


async def test_two_clients_share_loaded_datatypes(datatype_server: tuple[Server, str, dict[str, Node]]) -> None:
    _, url, nodes = datatype_server
    async with Client(url) as first_client, Client(url) as second_client:
        first = await first_client.load_data_type_definitions()
        assert await second_client.load_data_type_definitions() == {}
        await check_loaded_value(first_client, nodes, first)
        await check_loaded_value(second_client, nodes, first)
        second = await second_client.load_data_type_definitions(overwrite_existing=True)
        assert nodes.keys() - {"Value"} <= second.keys()
        await check_loaded_value(first_client, nodes, second)
        await check_loaded_value(second_client, nodes, second)


@pytest.mark.parametrize("option_set", [False, True])
async def test_load_enums_overwrite_existing(
    datatype_server: tuple[Server, str, dict[str, Node]], option_set: bool
) -> None:
    _, url, nodes = datatype_server
    name = "ReloadFlags" if option_set else "ReloadEnum"
    async with Client(url) as client:
        base_node = client.nodes.option_set_type if option_set else client.nodes.enum_data_type
        first = await load_enums(client, base_node, option_set=option_set)
        assert name in first
        assert await load_enums(client, base_node, option_set=option_set) == {}
        second = await load_enums(client, base_node, option_set=option_set, overwrite_existing=True)
        assert name in second
        assert second[name] is not first[name]
        assert getattr(ua, name) is second[name]
        assert ua.get_type(nodes[name].nodeid) is second[name]


async def test_reload_changed_datatype_definitions(datatype_server: tuple[Server, str, dict[str, Node]]) -> None:
    _, url, nodes = datatype_server
    async with Client(url) as client:
        first = await client.load_data_type_definitions()
        await check_loaded_value(client, nodes, first)
        for name, member_value in (("ReloadEnum", 7), ("ReloadFlags", 3)):
            definition = await nodes[name].read_data_type_definition()
            assert isinstance(definition, ua.EnumDefinition)
            definition.Fields[1].Value = member_value
            await nodes[name].write_data_type_definition(definition)
        definition = await nodes["ReloadInner"].read_data_type_definition()
        assert isinstance(definition, ua.StructureDefinition)
        definition.Fields = [new_struct_field("Count", ua.VariantType.UInt64)]
        await nodes["ReloadInner"].write_data_type_definition(definition)
        assert await client.load_data_type_definitions() == {}
        await check_loaded_value(client, nodes, first)
        second = await client.load_data_type_definitions(overwrite_existing=True)
        assert nodes.keys() - {"Value"} <= second.keys()
        definition = await nodes["ReloadStruct"].read_data_type_definition()
        assert isinstance(definition, ua.StructureDefinition)
        await nodes["Value"].write_value(
            ua.ExtensionObject(TypeId=definition.DefaultEncodingId, Body=pack("<iIQ", 7, 9, 2**40))
        )
        value = await client.get_node(nodes["Value"].nodeid).read_value()
        check_class(value, second["ReloadStruct"])
        check_class(value.Mode, second["ReloadEnum"])
        assert value.Mode is getattr(second["ReloadEnum"], "Running")
        assert value.Mode.value == 7
        check_class(value.Flags, second["ReloadFlags"])
        assert value.Flags == getattr(second["ReloadFlags"], "Read") | getattr(second["ReloadFlags"], "Write")
        assert value.Flags.value == 9
        check_class(value.Inner, second["ReloadInner"])
        assert value.Inner.Count == 2**40


async def test_overwrite_self_referencing_structure(datatype_server: tuple[Server, str, dict[str, Node]]) -> None:
    server, url, nodes = datatype_server
    idx = nodes["ReloadStruct"].nodeid.NamespaceIndex
    nodeid = ua.NodeId("ReloadRecursive", idx)
    dtype, encodings = await new_struct(
        server, nodeid, ua.QualifiedName("ReloadRecursive", idx), [new_struct_field("Children", nodeid, array=True)]
    )
    variable = await server.nodes.objects.add_variable(
        idx,
        "RecursiveValue",
        ua.ExtensionObject(TypeId=encodings[0].nodeid, Body=pack("<ii", 1, 0)),
        datatype=dtype.nodeid,
    )
    async with Client(url) as client:
        first = await client.load_data_type_definitions()
        second = await client.load_data_type_definitions(overwrite_existing=True)
        assert second["ReloadRecursive"] is not first["ReloadRecursive"]
        value = await client.get_node(variable.nodeid).read_value()
        check_class(value, second["ReloadRecursive"])
        check_class(value.Children[0], second["ReloadRecursive"])
