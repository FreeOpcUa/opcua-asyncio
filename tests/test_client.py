import logging
import pytest

from asyncua import Client
from asyncua import ua
from asyncua import Node

_logger = logging.getLogger(__name__)
pytestmark = pytest.mark.asyncio


async def test_service_fault(server, admin_client):
    request = ua.ReadRequest()
    request.TypeId = ua.FourByteNodeId(999)  # bad type!
    with pytest.raises(ua.UaStatusCodeError):
        await admin_client.uaclient.protocol.send_request(request)


async def test_objects_anonymous(server, client):
    objects = client.nodes.objects
    with pytest.raises(ua.UaStatusCodeError):
        await objects.write_attribute(ua.AttributeIds.WriteMask, ua.DataValue(999))
    with pytest.raises(ua.UaStatusCodeError):
        await objects.add_folder(3, "MyFolder")


async def test_folder_anonymous(server, admin_client, client):
    objects = admin_client.nodes.objects
    f = await objects.add_folder(3, "MyFolderRO")
    f_ro = client.get_node(f.nodeid)
    assert f == f_ro
    with pytest.raises(ua.UaStatusCodeError):
        await f_ro.add_folder(3, "MyFolder2")
    await server.delete_nodes([f, f_ro])


async def test_variable_anonymous(server, admin_client, client):
    objects = admin_client.nodes.objects
    v = await objects.add_variable(3, "MyROVariable", 6)
    await v.write_value(4)  # this should work
    v_ro = client.get_node(v.nodeid)
    with pytest.raises(ua.UaStatusCodeError):
        await v_ro.write_value(2)
    assert await v_ro.read_value() == 4
    await v.set_writable(True)
    await v_ro.write_value(2)  # now it should work
    assert await v_ro.read_value() == 2
    await v.set_writable(False)
    with pytest.raises(ua.UaStatusCodeError):
        await v_ro.write_value(9)
    assert await v_ro.read_value() == 2


async def test_context_manager(server):
    """Context manager calls connect() and disconnect()"""
    state = [0]

    async def increment_state(*args, **kwargs):
        state[0] += 1

    # create client and replace instance methods with dummy methods
    client = Client("opc.tcp://dummy_address:10000")
    client.connect = increment_state.__get__(client)
    client.disconnect = increment_state.__get__(client)

    assert state[0] == 0
    async with client:
        # test if client connected
        assert state[0] == 1
    # test if client disconnected
    assert state[0] == 2


async def test_enumstrings_getvalue(server, client):
    """
    The real exception is server side, but is detected by using a client.
    All due the server trace is also visible on the console.
    The client only 'sees' an TimeoutError
    """
    nenumstrings = client.get_node(ua.ObjectIds.AxisScaleEnumeration_EnumStrings)
    await nenumstrings.read_value()


async def test_custom_enum_struct(server, client):
    await client.load_type_definitions()
    ns = await client.get_namespace_index("http://yourorganisation.org/struct_enum_example/")
    myvar = client.get_node(ua.NodeId(6009, ns))
    val = await myvar.read_value()
    assert 242 == val.IntVal1
    assert ua.ExampleEnum.EnumVal2 == val.EnumVal


async def test_multiple_read_and_write_value(server, client):
    f = await server.nodes.objects.add_folder(3, "Multiple_read_write_test")
    v1 = await f.add_variable(3, "a", 1)
    await v1.set_writable()
    v2 = await f.add_variable(3, "b", 2)
    await v2.set_writable()
    v3 = await f.add_variable(3, "c", 3)
    await v3.set_writable()
    v_ro = await f.add_variable(3, "ro", 3)

    vals = await client.read_values([v1, v2, v3])
    assert vals == [1, 2, 3]
    rets = await client.write_values([v1, v2, v3], [4, 5, 6])
    assert rets == [
        ua.StatusCode(value=ua.StatusCodes.Good),
        ua.StatusCode(value=ua.StatusCodes.Good),
        ua.StatusCode(value=ua.StatusCodes.Good),
    ]
    vals = await client.read_values([v1, v2, v3])
    assert vals == [4, 5, 6]
    with pytest.raises(ua.uaerrors.BadUserAccessDenied):
        await client.write_values([v1, v2, v_ro], [4, 5, 6])
    rets = await client.write_values([v1, v2, v_ro], [4, 5, 6], raise_on_partial_error=False)
    assert rets == [
        ua.StatusCode(value=ua.StatusCodes.Good),
        ua.StatusCode(ua.StatusCodes.Good),
        ua.StatusCode(ua.StatusCodes.BadUserAccessDenied),
    ]


async def test_read_and_write_status_check(server, client):
    f = await server.nodes.objects.add_folder(3, "read_and_write_status_check")
    v1 = await f.add_variable(3, "a", 1)
    await v1.set_writable()

    testValue = 1
    testStatusCode = ua.StatusCode(ua.StatusCodes.Bad)

    # set value StatusCode to Bad
    variant = ua.Variant(testValue, ua.VariantType.Int64)
    dataValue = ua.DataValue(variant, StatusCode_=testStatusCode)
    await v1.set_value(dataValue)

    # check that reading the value generates an error
    # with raise_on_bad_status set to True as default
    with pytest.raises(ua.UaStatusCodeError):
        val = await v1.read_data_value()

    # check that reading the value does not generate an error
    # with raise_on_bad_status set to False
    val = await v1.read_data_value(False)
    assert val.Value.Value is None, "Value should be Null if StatusCode is Bad"
    assert val.StatusCode_ == testStatusCode, (
        "StatusCode expected " + str(val.StatusCode_) + ", but instead got " + str(testStatusCode)
    )

    # check that reading the value generates an error
    # with raise_on_bad_status set to True
    with pytest.raises(ua.UaStatusCodeError):
        val = await v1.read_data_value(True)


async def test_browse_nodes(server, client):
    nodes = [
        client.get_node("ns=0;i=2267"),
        client.get_node("ns=0;i=2259"),
    ]
    results = await client.browse_nodes(nodes)
    assert len(results) == 2
    assert isinstance(results, list)
    assert results[0][0] == nodes[0]
    assert results[1][0] == nodes[1]
    assert isinstance(results[0][0], Node)
    assert isinstance(results[1][0], Node)
    assert isinstance(results[0][1], ua.BrowseResult)
    assert isinstance(results[1][1], ua.BrowseResult)


async def test_translate_browsepaths(server, client: Client):
    server_node = await client.nodes.objects.get_child("Server")

    relative_paths = ["/0:ServiceLevel", "/0:ServerStatus/0:State"]
    results = await client.translate_browsepaths(server_node.nodeid, relative_paths)
    assert len(results) == 2
    assert isinstance(results, list)
    assert results[0].StatusCode.value == ua.StatusCodes.Good
    assert results[0].Targets[0].TargetId == ua.NodeId.from_string("ns=0;i=2267")
    assert results[1].StatusCode.value == ua.StatusCodes.Good
    assert results[1].Targets[0].TargetId == ua.NodeId.from_string("ns=0;i=2259")
    for result in results:
        assert isinstance(result, ua.BrowsePathResult)

    results2 = await client.translate_browsepaths(server_node.nodeid, ["/0:UnknownPath"])
    assert len(results2) == 1
    assert isinstance(results2, list)
    assert results2[0].StatusCode.value == ua.StatusCodes.BadNoMatch
    assert len(results2[0].Targets) == 0

    with pytest.raises(ua.UaStringParsingError):
        await client.translate_browsepaths(server_node.nodeid, ["/1:<Boiler"])


async def test_strip_credentials_in_url():
    """Check that the credentials are correctly stripped in the server url"""

    client = Client("opc.tcp://user:password@dummy_address:10000")
    assert client.server_url.netloc == "dummy_address:10000"

    client = Client("opc.tcp://user:password@dummy_address:10000")
    client.strip_url_credentials = False
    assert client.server_url.netloc == "user:password@dummy_address:10000"
