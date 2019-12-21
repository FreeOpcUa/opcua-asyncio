
import logging
import pytest

from asyncua import Client
from asyncua import ua

_logger = logging.getLogger(__name__)
pytestmark = pytest.mark.asyncio


async def test_service_fault(server, admin_client):
    request = ua.ReadRequest()
    request.TypeId = ua.FourByteNodeId(999)  # bad type!
    with pytest.raises(ua.UaStatusCodeError):
        await admin_client.uaclient.protocol.send_request(request)


async def test_objects_anonymous(server, client):
    objects = client.get_objects_node()
    with pytest.raises(ua.UaStatusCodeError):
        await objects.set_attribute(ua.AttributeIds.WriteMask, ua.DataValue(999))
    with pytest.raises(ua.UaStatusCodeError):
        await objects.add_folder(3, 'MyFolder')


async def test_folder_anonymous(server, admin_client, client):
    objects = admin_client.get_objects_node()
    f = await objects.add_folder(3, 'MyFolderRO')
    f_ro = client.get_node(f.nodeid)
    assert f == f_ro
    with pytest.raises(ua.UaStatusCodeError):
        await f_ro.add_folder(3, 'MyFolder2')


async def test_variable_anonymous(server, admin_client, client):
    objects = admin_client.get_objects_node()
    v = await objects.add_variable(3, 'MyROVariable', 6)
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
    client = Client('opc.tcp://dummy_address:10000')
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
    value = ua.Variant(await nenumstrings.read_value())


async def test_custom_enum_struct(server, client):
    await client.load_type_definitions()
    ns = await client.get_namespace_index('http://yourorganisation.org/struct_enum_example/')
    myvar = client.get_node(ua.NodeId(6009, ns))
    val = await myvar.read_value()
    assert 242 == val.IntVal1
    assert ua.ExampleEnum.EnumVal2 == val.EnumVal


async def test_multiple_read_and_write_value(server, client):
    f = await server.nodes.objects.add_folder(3, 'Multiple_read_write_test')
    v1 = await f.add_variable(3, "a", 1)
    await v1.set_writable()
    v2 = await f.add_variable(3, "b", 2)
    await v2.set_writable()
    v3 = await f.add_variable(3, "c", 3)
    await v3.set_writable()
    v_ro = await f.add_variable(3, "ro", 3)

    vals = await client.read_values([v1, v2, v3])
    assert vals == [1, 2, 3]
    await client.write_values([v1, v2, v3], [4, 5, 6])
    vals = await client.read_values([v1, v2, v3])
    assert vals == [4, 5, 6]
    with pytest.raises(ua.uaerrors.BadUserAccessDenied):
        await client.write_values([v1, v2, v_ro], [4, 5, 6])


