"""
Run common tests on server side
Tests that can only be run on server side must be defined here
"""
import asyncio
import pytest
import logging
from datetime import timedelta
from enum import EnumMeta

import asyncua
from asyncua import Server, Client, ua, uamethod
from asyncua.common.event_objects import BaseEvent, AuditEvent, AuditChannelEvent, AuditSecurityEvent, AuditOpenSecureChannelEvent
from asyncua.common import ua_utils

pytestmark = pytest.mark.asyncio
_logger = logging.getLogger(__name__)


async def test_discovery(server, discovery_server):
    client = Client(discovery_server.endpoint.geturl())
    async with client:
        servers = await client.find_servers()
        new_app_uri = 'urn:freeopcua:python:server:test_discovery'
        await server.set_application_uri(new_app_uri)
        await server.register_to_discovery(discovery_server.endpoint.geturl(), 0)
        # let server register registration
        await asyncio.sleep(0.5)
        new_servers = await client.find_servers()
        assert len(new_servers) - len(servers) == 1
        assert new_app_uri not in [s.ApplicationUri for s in servers]
        assert new_app_uri in [s.ApplicationUri for s in new_servers]


async def test_unregister_discovery(server, discovery_server):
    client = Client(discovery_server.endpoint.geturl())
    async with client:
        new_app_uri = 'urn:freeopcua:python:server:test_discovery2'
        await server.set_application_uri(new_app_uri)
        # register without automatic renewal
        await server.register_to_discovery(discovery_server.endpoint.geturl(), period=0)
        await asyncio.sleep(0.5)
        # unregister, no automatic renewal to stop
        await server.unregister_from_discovery(discovery_server.endpoint.geturl())
        await asyncio.sleep(0.5)
        # reregister with automatic renewal
        await server.register_to_discovery(discovery_server.endpoint.geturl(), period=60)
        await asyncio.sleep(0.5)
        # unregister, cancel scheduled renewal
        await server.unregister_from_discovery(discovery_server.endpoint.geturl())


async def test_find_servers2(server, discovery_server):
    client = Client(discovery_server.endpoint.geturl())
    async with client:
        servers = await client.find_servers()
        new_app_uri1 = 'urn:freeopcua:python:server:test_discovery1'
        await server.set_application_uri(new_app_uri1)
        await server.register_to_discovery(discovery_server.endpoint.geturl(), period=0)
        new_app_uri2 = 'urn:freeopcua:python:test_discovery2'
        await server.set_application_uri(new_app_uri2)
        await server.register_to_discovery(discovery_server.endpoint.geturl(), period=0)
        await asyncio.sleep(0.1)  # let server register registration
        new_servers = await client.find_servers()
        assert len(new_servers) - len(servers) == 2
        assert new_app_uri1 not in [s.ApplicationUri for s in servers]
        assert new_app_uri2 not in [s.ApplicationUri for s in servers]
        assert new_app_uri1 in [s.ApplicationUri for s in new_servers]
        assert new_app_uri2 in [s.ApplicationUri for s in new_servers]
        # now do a query with filer
        new_servers = await client.find_servers(['urn:freeopcua:python:server'])
        assert len(new_servers) - len(servers) == 0
        assert new_app_uri1 in [s.ApplicationUri for s in new_servers]
        assert new_app_uri2 not in [s.ApplicationUri for s in new_servers]
        # now do a query with filer
        new_servers = await client.find_servers(['urn:freeopcua:python'])
        assert len(new_servers) - len(servers) == 2
        assert new_app_uri1 in [s.ApplicationUri for s in new_servers]
        assert new_app_uri2 in [s.ApplicationUri for s in new_servers]


async def test_register_namespace(server):
    uri = 'http://mycustom.Namespace.com'
    idx1 = await server.register_namespace(uri)
    idx2 = await server.get_namespace_index(uri)
    assert idx1 == idx2


async def test_register_existing_namespace(server):
    uri = 'http://mycustom.Namespace.com'
    idx1 = await server.register_namespace(uri)
    idx2 = await server.register_namespace(uri)
    idx3 = await server.get_namespace_index(uri)
    assert idx1 == idx2
    assert idx1 == idx3


async def test_register_use_namespace(server):
    uri = 'http://my_very_custom.Namespace.com'
    idx = await server.register_namespace(uri)
    root = server.nodes.root
    myvar = await root.add_variable(idx, 'var_in_custom_namespace', [5])
    myid = myvar.nodeid
    assert idx == myid.NamespaceIndex


async def test_server_method(server):
    def func(parent, variant):
        return [ua.Variant(variant.Value * 2, variant.VariantType)]

    o = server.nodes.objects
    v = await o.add_method(3, 'Method1', func, [ua.VariantType.Int64], [ua.VariantType.Int64])
    result = await o.call_method(v, ua.Variant(2.1))
    assert result == 4.2


async def test_historize_variable(server):
    o = server.nodes.objects
    var = await o.add_variable(3, "test_hist", 1.0)
    await server.iserver.enable_history_data_change(var, timedelta(days=1))
    await asyncio.sleep(1)
    await var.write_value(2.0)
    await var.write_value(3.0)
    await server.iserver.disable_history_data_change(var)


async def test_multiple_clients_with_subscriptions(server):
    """
    Tests that multiple clients can subscribe, and when one client disconnects, the other
    still maintains it's subscription
    """
    class SubscriptionHandler:
        def datachange_notification(self, node, val, data):
            pass
    sub_handler = SubscriptionHandler()
    client1 = Client(server.endpoint.geturl())
    client2 = Client(server.endpoint.geturl())

    o = server.nodes.objects
    var = await o.add_variable(3, "some_variable", 1.0)
    async with client1:
        async with client2:
            sub1 = await client1.create_subscription(100, sub_handler)
            sub2 = await client2.create_subscription(100, sub_handler)
            await sub1.subscribe_data_change(var)
            await sub2.subscribe_data_change(var)
            assert sub1.subscription_id in server.iserver.subscription_service.subscriptions
            assert sub2.subscription_id in server.iserver.subscription_service.subscriptions
        # When client2 disconnects, client1 should still keep its subscription.
        assert sub1.subscription_id in server.iserver.subscription_service.subscriptions
        assert sub2.subscription_id not in server.iserver.subscription_service.subscriptions
    assert sub1.subscription_id not in server.iserver.subscription_service.subscriptions
    assert sub2.subscription_id not in server.iserver.subscription_service.subscriptions


async def test_historize_events(server):
    srv_node = server.get_node(ua.ObjectIds.Server)
    assert await srv_node.read_event_notifier() == {ua.EventNotifier.SubscribeToEvents}
    srvevgen = await server.get_event_generator()
    await server.iserver.enable_history_event(srv_node, period=None)
    assert await srv_node.read_event_notifier() == {ua.EventNotifier.SubscribeToEvents, ua.EventNotifier.HistoryRead}
    await srvevgen.trigger(message='Message')
    await server.iserver.disable_history_event(srv_node)


async def test_references_for_added_nodes_method(server):
    objects = server.nodes.objects
    o = await objects.add_object(3, 'MyObject')
    nodes = await objects.get_referenced_nodes(refs=ua.ObjectIds.Organizes, direction=ua.BrowseDirection.Forward,
                                               includesubtypes=False)
    assert o in nodes
    nodes = await o.get_referenced_nodes(refs=ua.ObjectIds.Organizes, direction=ua.BrowseDirection.Inverse,
                                         includesubtypes=False)
    assert objects in nodes
    assert await o.get_parent() == objects
    assert (await o.read_type_definition()).Identifier == ua.ObjectIds.BaseObjectType

    @uamethod
    def callback(parent):
        return

    m = await o.add_method(3, 'MyMethod', callback)
    nodes = await o.get_referenced_nodes(refs=ua.ObjectIds.HasComponent, direction=ua.BrowseDirection.Forward,
                                         includesubtypes=False)
    assert m in nodes
    nodes = await m.get_referenced_nodes(refs=ua.ObjectIds.HasComponent, direction=ua.BrowseDirection.Inverse,
                                         includesubtypes=False)
    assert o in nodes
    assert await m.get_parent() == o
    await server.delete_nodes([o])


async def test_get_event_from_type_node_BaseEvent(server):
    """
    This should work for following BaseEvent tests to work
    (maybe to write it a bit differentlly since they are not independent)
    """
    ev = await asyncua.common.events.get_event_obj_from_type_node(
        asyncua.Node(server.iserver.isession, ua.NodeId(ua.ObjectIds.BaseEventType))
    )
    check_base_event(ev)


async def test_get_event_from_type_node_Inhereted_AuditEvent(server):
    ev = await asyncua.common.events.get_event_obj_from_type_node(
        asyncua.Node(server.iserver.isession, ua.NodeId(ua.ObjectIds.AuditEventType))
    )
    # we did not receive event
    assert ev is not None
    assert isinstance(ev, BaseEvent)
    assert isinstance(ev, AuditEvent)
    assert ev.EventType == ua.NodeId(ua.ObjectIds.AuditEventType)
    assert ev.Severity == 1
    assert ev.ActionTimeStamp is None
    assert ev.Status is False
    assert ev.ServerId is None
    assert ev.ClientAuditEntryId is None
    assert ev.ClientUserId is None


async def test_get_event_from_type_node_MultiInhereted_AuditOpenSecureChannelEvent(server):
    ev = await asyncua.common.events.get_event_obj_from_type_node(
        asyncua.Node(server.iserver.isession, ua.NodeId(ua.ObjectIds.AuditOpenSecureChannelEventType))
    )
    assert ev is not None
    assert isinstance(ev, BaseEvent)
    assert isinstance(ev, AuditEvent)
    assert isinstance(ev, AuditSecurityEvent)
    assert isinstance(ev, AuditChannelEvent)
    assert isinstance(ev, AuditOpenSecureChannelEvent)
    assert ev.EventType == ua.NodeId(ua.ObjectIds.AuditOpenSecureChannelEventType)
    assert ev.Severity == 1
    assert ev.ClientCertificate is None
    assert ev.ClientCertificateThumbprint is None
    assert ev.RequestType is None
    assert ev.SecurityPolicyUri is None
    assert ev.SecurityMode is None
    assert ev.RequestedLifetime is None


async def test_eventgenerator_default(server):
    evgen = await server.get_event_generator()
    await check_eventgenerator_base_event(evgen, server)
    await check_eventgenerator_source_server(evgen, server)


async def test_eventgenerator_BaseEvent_object(server):
    evgen = await server.get_event_generator(BaseEvent())
    await check_eventgenerator_base_event(evgen, server)
    await check_eventgenerator_source_server(evgen, server)


async def test_eventgenerator_BaseEvent_Node(server):
    evgen = await server.get_event_generator(asyncua.Node(server.iserver.isession, ua.NodeId(ua.ObjectIds.BaseEventType)))
    await check_eventgenerator_base_event(evgen, server)
    await check_eventgenerator_source_server(evgen, server)


async def test_eventgenerator_BaseEvent_NodeId(server):
    evgen = await server.get_event_generator(ua.NodeId(ua.ObjectIds.BaseEventType))
    await check_eventgenerator_base_event(evgen, server)
    await check_eventgenerator_source_server(evgen, server)


async def test_eventgenerator_BaseEvent_ObjectIds(server):
    evgen = await server.get_event_generator(ua.ObjectIds.BaseEventType)
    await check_eventgenerator_base_event(evgen, server)
    await check_eventgenerator_source_server(evgen, server)


async def test_eventgenerator_BaseEvent_Identifier(server):
    evgen = await server.get_event_generator(2041)
    await check_eventgenerator_base_event(evgen, server)
    await check_eventgenerator_source_server(evgen, server)


async def test_eventgenerator_sourceServer_Node(server):
    evgen = await server.get_event_generator(emitting_node=asyncua.Node(server.iserver.isession, ua.NodeId(ua.ObjectIds.Server)))
    await check_eventgenerator_base_event(evgen, server)
    await check_eventgenerator_source_server(evgen, server)


async def test_eventgenerator_sourceServer_NodeId(server):
    evgen = await server.get_event_generator(emitting_node=ua.NodeId(ua.ObjectIds.Server))
    await check_eventgenerator_base_event(evgen, server)
    await check_eventgenerator_source_server(evgen, server)


async def test_eventgenerator_sourceServer_ObjectIds(server):
    evgen = await server.get_event_generator(emitting_node=ua.ObjectIds.Server)
    await check_eventgenerator_base_event(evgen, server)
    await check_eventgenerator_source_server(evgen, server)


async def test_eventgenerator_sourceMyObject(server):
    objects = server.nodes.objects
    o = await objects.add_object(3, 'MyObject')
    evgen = await server.get_event_generator(emitting_node=o)
    await check_eventgenerator_base_event(evgen, server)
    await check_event_generator_object(evgen, o)
    await server.delete_nodes([o])


async def test_eventgenerator_source_collision(server):
    objects = server.nodes.objects
    o = await objects.add_object(3, 'MyObject')
    event = BaseEvent(sourcenode=o.nodeid)
    evgen = await server.get_event_generator(event, ua.ObjectIds.Server)
    await check_eventgenerator_base_event(evgen, server)
    await check_event_generator_object(evgen, o, emitting_node=asyncua.Node(server.iserver.isession, ua.ObjectIds.Server))
    await server.delete_nodes([o])


async def test_eventgenerator_inherited_event(server):
    evgen = await server.get_event_generator(ua.ObjectIds.AuditEventType)
    await check_eventgenerator_source_server(evgen, server)
    ev = evgen.event
    assert ev is not None  # we did not receive event
    assert isinstance(ev, BaseEvent)
    assert isinstance(ev, AuditEvent)
    assert ua.NodeId(ua.ObjectIds.AuditEventType) == ev.EventType
    assert 1 == ev.Severity
    assert ev.ActionTimeStamp is None
    assert False is ev.Status
    assert ev.ServerId is None
    assert ev.ClientAuditEntryId is None
    assert ev.ClientUserId is None


async def test_eventgenerator_multi_inherited_event(server):
    evgen = await server.get_event_generator(ua.ObjectIds.AuditOpenSecureChannelEventType)
    await check_eventgenerator_source_server(evgen, server)
    ev = evgen.event
    assert ev is not None  # we did not receive event
    assert isinstance(ev, BaseEvent)
    assert isinstance(ev, AuditEvent)
    assert isinstance(ev, AuditSecurityEvent)
    assert isinstance(ev, AuditChannelEvent)
    assert isinstance(ev, AuditOpenSecureChannelEvent)
    assert ua.NodeId(ua.ObjectIds.AuditOpenSecureChannelEventType) == ev.EventType
    assert 1 == ev.Severity
    assert ev.ClientCertificate is None
    assert ev.ClientCertificateThumbprint is None
    assert ev.RequestType is None
    assert ev.SecurityPolicyUri is None
    assert ev.SecurityMode is None
    assert ev.RequestedLifetime is None


async def test_create_custom_data_type_object_id(server):
    """
    For the custom events all posibilites are tested.
    For other custom types only one test case is done since they are using the same code
    """
    type = await server.create_custom_data_type(2, 'MyDataType', ua.ObjectIds.BaseDataType,
                                                [('PropertyNum', ua.VariantType.Int32),
                                                 ('PropertyString', ua.VariantType.String)])
    await check_custom_type(type, ua.ObjectIds.BaseDataType, server, ua.NodeClass.DataType)


async def test_create_custom_event_type_object_id(server):
    type = await server.create_custom_event_type(2, 'MyEvent', ua.ObjectIds.BaseEventType,
                                                 [('PropertyNum', ua.VariantType.Int32),
                                                  ('PropertyString', ua.VariantType.String)])
    await check_custom_type(type, ua.ObjectIds.BaseEventType, server)
    await server.delete_nodes([type])


async def test_create_custom_object_type_object_id(server):
    def func(parent, variant):
        return [ua.Variant(True, ua.VariantType.Boolean)]

    properties = [('PropertyNum', ua.VariantType.Int32),
                  ('PropertyString', ua.VariantType.String)]
    variables = [('VariableString', ua.VariantType.String),
                 ('MyEnumVar', ua.VariantType.Int32, ua.NodeId(ua.ObjectIds.ApplicationType))]
    methods = [('MyMethod', func, [ua.VariantType.Int64], [ua.VariantType.Boolean])]
    node_type = await server.create_custom_object_type(2, 'MyObjectType', ua.ObjectIds.BaseObjectType, properties,
                                                       variables, methods)
    await check_custom_type(node_type, ua.ObjectIds.BaseObjectType, server)
    variables = await node_type.get_variables()
    assert await node_type.get_child("2:VariableString") in variables
    assert ua.VariantType.String == (
        await(await node_type.get_child("2:VariableString")).read_data_value()).Value.VariantType
    assert await node_type.get_child("2:MyEnumVar") in variables
    assert ua.VariantType.Int32 == (await(await node_type.get_child("2:MyEnumVar")).read_data_value()).Value.VariantType
    assert ua.NodeId(ua.ObjectIds.ApplicationType) == await (await node_type.get_child("2:MyEnumVar")).read_data_type()
    methods = await node_type.get_methods()
    assert await node_type.get_child("2:MyMethod") in methods


async def test_create_custom_variable_type_object_id(server):
    type = await server.create_custom_variable_type(2, 'MyVariableType', ua.ObjectIds.BaseVariableType,
                                                    [('PropertyNum', ua.VariantType.Int32),
                                                     ('PropertyString', ua.VariantType.String)])
    await check_custom_type(type, ua.ObjectIds.BaseVariableType, server)


async def test_create_custom_event_type_node_id(server):
    etype = await server.create_custom_event_type(2, 'MyEvent', ua.NodeId(ua.ObjectIds.BaseEventType),
                                                  [('PropertyNum', ua.VariantType.Int32),
                                                   ('PropertyString', ua.VariantType.String)])
    await check_custom_type(etype, ua.ObjectIds.BaseEventType, server)
    await server.delete_nodes([etype])


async def test_create_custom_event_type_node(server):
    etype = await server.create_custom_event_type(2, 'MyEvent1', asyncua.Node(server.iserver.isession, ua.NodeId(ua.ObjectIds.BaseEventType)),
                                                  [('PropertyNum', ua.VariantType.Int32),
                                                   ('PropertyString', ua.VariantType.String)])
    await check_custom_type(etype, ua.ObjectIds.BaseEventType, server)
    await server.delete_nodes([etype])


async def test_get_event_from_type_node_custom_event(server):
    etype = await server.create_custom_event_type(2, 'MyEvent2', ua.ObjectIds.BaseEventType,
                                                  [('PropertyNum', ua.VariantType.Int32),
                                                   ('PropertyString', ua.VariantType.String)])
    ev = await asyncua.common.events.get_event_obj_from_type_node(etype)
    check_custom_event(ev, etype)
    assert 0 == ev.PropertyNum
    assert ev.PropertyString is None
    await server.delete_nodes([etype])


async def test_eventgenerator_custom_event(server):
    etype = await server.create_custom_event_type(2, 'MyEvent3', ua.ObjectIds.BaseEventType,
                                                  [('PropertyNum', ua.VariantType.Int32),
                                                   ('PropertyString', ua.VariantType.String)])
    evgen = await server.get_event_generator(etype, ua.ObjectIds.Server)
    check_eventgenerator_custom_event(evgen, etype, server)
    await check_eventgenerator_source_server(evgen, server)
    assert 0 == evgen.event.PropertyNum
    assert evgen.event.PropertyString is None
    await server.delete_nodes([etype])


async def test_eventgenerator_custom_event_with_variables(server):
    # Here use generic create_custom_object_type
    # Variables are still missing in create_custom_event_type
    properties = [('PropertyNum', ua.VariantType.Int32),
                  ('PropertyString', ua.VariantType.String)]
    variables = [('VariableString', ua.VariantType.String),
                 ('MyEnumVar', ua.VariantType.Int32, ua.NodeId(ua.ObjectIds.ApplicationType))]
    etype = await server.create_custom_object_type(2, 'MyEvent33', ua.ObjectIds.BaseEventType, properties, variables)
    evgen = await server.get_event_generator(etype, ua.ObjectIds.Server)
    check_eventgenerator_custom_event(evgen, etype, server)
    await check_eventgenerator_source_server(evgen, server)
    assert 0 == evgen.event.PropertyNum
    assert evgen.event.PropertyString is None
    await server.delete_nodes([etype])


async def test_eventgenerator_double_custom_event(server):
    event1 = await server.create_custom_event_type(3, 'MyEvent4', ua.ObjectIds.BaseEventType,
                                                   [('PropertyNum', ua.VariantType.Int32),
                                                    ('PropertyString', ua.VariantType.String)])
    event2 = await server.create_custom_event_type(4, 'MyEvent5', event1, [('PropertyBool', ua.VariantType.Boolean),
                                                                           ('PropertyInt', ua.VariantType.Int32)])
    evgen = await server.get_event_generator(event2, ua.ObjectIds.Server)
    check_eventgenerator_custom_event(evgen, event2, server)
    await check_eventgenerator_source_server(evgen, server)
    # Properties from MyEvent1
    assert 0 == evgen.event.PropertyNum
    assert evgen.event.PropertyString is None
    # Properties from MyEvent2
    assert not evgen.event.PropertyBool
    assert 0 == evgen.event.PropertyInt
    await server.delete_nodes([event1, event2])


async def test_eventgenerator_custom_event_my_object(server):
    objects = server.nodes.objects
    o = await objects.add_object(3, 'MyObject')
    etype = await server.create_custom_event_type(2, 'MyEvent6', ua.ObjectIds.BaseEventType,
                                                  [('PropertyNum', ua.VariantType.Int32),
                                                   ('PropertyString', ua.VariantType.String)])

    evgen = await server.get_event_generator(etype, o)
    check_eventgenerator_custom_event(evgen, etype, server)
    await check_event_generator_object(evgen, o)
    assert 0 == evgen.event.PropertyNum
    assert evgen.event.PropertyString is None
    await server.delete_nodes([o, etype])


async def test_context_manager():
    # Context manager calls start() and stop()
    state = [0]

    async def increment_state(self, *args, **kwargs):
        state[0] += 1

    # create server and replace instance methods with dummy methods
    server = Server()
    server.start = increment_state.__get__(server)
    server.stop = increment_state.__get__(server)
    assert state[0] == 0
    async with server:
        # test if server started
        assert 1 == state[0]
    # test if server stopped
    assert 2 == state[0]


async def test_get_node_by_ns(server):
    def get_ns_of_nodes(nodes):
        ns_list = set()
        for node in nodes:
            ns_list.add(node.nodeid.NamespaceIndex)
        return ns_list

    # incase other testss created nodes in unregistered namespace
    _idx_d = await server.register_namespace('dummy1')  # noqa: F841
    _idx_d = await server.register_namespace('dummy2')  # noqa: F841
    _idx_d = await server.register_namespace('dummy3')  # noqa: F841
    # create the test namespaces and vars
    idx_a = await server.register_namespace('a')
    idx_b = await server.register_namespace('b')
    idx_c = await server.register_namespace('c')
    o = server.nodes.objects
    _myvar2 = await o.add_variable(idx_a, "MyBoolVar2", True)  # noqa: F841
    _myvar3 = await o.add_variable(idx_b, "MyBoolVar3", True)  # noqa: F841
    _myvar4 = await o.add_variable(idx_c, "MyBoolVar4", True)  # noqa: F841
    # the tests
    nodes = await ua_utils.get_nodes_of_namespace(server, namespaces=[idx_a, idx_b, idx_c])
    assert 3 == len(nodes)
    assert {idx_a, idx_b, idx_c} == get_ns_of_nodes(nodes)

    nodes = await ua_utils.get_nodes_of_namespace(server, namespaces=[idx_a])
    assert 1 == len(nodes)
    assert {idx_a} == get_ns_of_nodes(nodes)

    nodes = await ua_utils.get_nodes_of_namespace(server, namespaces=[idx_b])
    assert 1 == len(nodes)
    assert {idx_b} == get_ns_of_nodes(nodes)

    nodes = await ua_utils.get_nodes_of_namespace(server, namespaces=['a'])
    assert 1 == len(nodes)
    assert {idx_a} == get_ns_of_nodes(nodes)

    nodes = await ua_utils.get_nodes_of_namespace(server, namespaces=['a', 'c'])
    assert 2 == len(nodes)
    assert {idx_a, idx_c} == get_ns_of_nodes(nodes)

    nodes = await ua_utils.get_nodes_of_namespace(server, namespaces='b')
    assert 1 == len(nodes)
    assert {idx_b} == get_ns_of_nodes(nodes)

    nodes = await ua_utils.get_nodes_of_namespace(server, namespaces=idx_b)
    assert 1 == len(nodes)
    assert {idx_b} == get_ns_of_nodes(nodes)
    with pytest.raises(ValueError):
        await ua_utils.get_nodes_of_namespace(server, namespaces='non_existing_ns')


async def test_load_enum_strings(server):
    dt = await server.nodes.enum_data_type.add_data_type(0, "MyStringEnum")
    await dt.add_property(
        0,
        "EnumStrings",
        [ua.LocalizedText("e1"), ua.LocalizedText("e2"), ua.LocalizedText("e3"), ua.LocalizedText("e 4")]
    )
    await server.load_enums()
    e = getattr(ua, "MyStringEnum")
    assert isinstance(e, EnumMeta)
    assert hasattr(e, "e1")
    assert hasattr(e, "e4")
    assert 3 == getattr(e, "e4")


async def test_load_enum_values(server):
    dt = await server.nodes.enum_data_type.add_data_type(0, "MyValuesEnum")
    v1 = ua.EnumValueType(DisplayName=ua.LocalizedText("v1"), Value=2)
    v2 = ua.EnumValueType(DisplayName=ua.LocalizedText("v2"), Value=3)
    v3 = ua.EnumValueType(DisplayName=ua.LocalizedText("v 3 "), Value=4.)
    await dt.add_property(0, "EnumValues", [v1, v2, v3])
    await server.load_enums()
    e = getattr(ua, "MyValuesEnum")
    assert isinstance(e, EnumMeta)
    assert hasattr(e, "v1")
    assert hasattr(e, "v3")
    assert 4 == getattr(e, "v3")


async def check_eventgenerator_source_server(evgen, server: Server):
    server_node = server.nodes.server
    assert evgen.event.SourceName == (await server_node.read_browse_name()).Name
    assert evgen.event.SourceNode == ua.NodeId(ua.ObjectIds.Server)
    assert await server_node.read_event_notifier() == {ua.EventNotifier.SubscribeToEvents}
    refs = await server_node.get_referenced_nodes(ua.ObjectIds.GeneratesEvent, ua.BrowseDirection.Forward,
                                                  ua.NodeClass.ObjectType, False)
    assert len(refs) >= 1


async def check_event_generator_object(evgen, obj, emitting_node=None):
    assert evgen.event.SourceName == (await obj.read_browse_name()).Name
    assert evgen.event.SourceNode == obj.nodeid

    if not emitting_node:
        assert await obj.read_event_notifier() == {ua.EventNotifier.SubscribeToEvents}
        refs = await obj.get_referenced_nodes(ua.ObjectIds.GeneratesEvent, ua.BrowseDirection.Forward, ua.NodeClass.ObjectType, False)
    else:
        assert await emitting_node.read_event_notifier() == {ua.EventNotifier.SubscribeToEvents}
        refs = await emitting_node.get_referenced_nodes(ua.ObjectIds.GeneratesEvent, ua.BrowseDirection.Forward, ua.NodeClass.ObjectType, False)

    assert evgen.event.EventType in [x.nodeid for x in refs]


async def check_eventgenerator_base_event(evgen, server: Server):
    # we did not receive event generator
    assert evgen is not None
    assert evgen.isession is server.iserver.isession
    check_base_event(evgen.event)


def check_base_event(ev):
    # we did not receive event
    assert ev is not None
    assert isinstance(ev, BaseEvent)
    assert ev.EventType == ua.NodeId(ua.ObjectIds.BaseEventType)
    assert ev.Severity == 1


def check_eventgenerator_custom_event(evgen, etype, server: Server):
    # we did not receive event generator
    assert evgen is not None
    assert evgen.isession is server.iserver.isession
    check_custom_event(evgen.event, etype)


def check_custom_event(ev, etype):
    # we did not receive event
    assert ev is not None
    assert isinstance(ev, BaseEvent)
    assert ev.EventType == etype.nodeid
    assert ev.Severity == 1


async def check_custom_type(ntype, base_type, server: Server, node_class=None):
    base = asyncua.Node(server.iserver.isession, ua.NodeId(base_type))
    assert ntype in await base.get_children()
    nodes = await ntype.get_referenced_nodes(refs=ua.ObjectIds.HasSubtype, direction=ua.BrowseDirection.Inverse, includesubtypes=True)
    assert base == nodes[0]
    if node_class:
        assert node_class == await ntype.read_node_class()
    properties = await ntype.get_properties()
    assert properties is not None
    assert len(properties) == 2
    assert await ntype.get_child("2:PropertyNum") in properties
    assert (await(await ntype.get_child("2:PropertyNum")).read_data_value()).Value.VariantType == ua.VariantType.Int32
    assert await ntype.get_child("2:PropertyString") in properties
    assert (await(await ntype.get_child("2:PropertyString")).read_data_value()).Value.VariantType == ua.VariantType.String


async def test_server_read_write_attribute_value(server: Server):
    node = await server.get_objects_node().add_variable(0, "0:TestVar", 0, varianttype=ua.VariantType.Int64)
    dv = server.read_attribute_value(node.nodeid, attr=ua.AttributeIds.Value)
    assert dv.Value.Value == 0
    dv = ua.DataValue(Value=ua.Variant(Value=5, VariantType=ua.VariantType.Int64))
    await server.write_attribute_value(node.nodeid, dv, attr=ua.AttributeIds.Value)
    dv = server.read_attribute_value(node.nodeid, attr=ua.AttributeIds.Value)
    assert dv.Value.Value == 5
    await server.delete_nodes([node])


async def test_server_read_set_attribute_value_callback(server: Server):
    node = await server.get_objects_node().add_variable(0, "0:TestVar", 0, varianttype=ua.VariantType.Int64)
    dv = server.read_attribute_value(node.nodeid, attr=ua.AttributeIds.Value)
    assert dv.Value.Value == 0

    def callback(nodeid, attr):
        return ua.DataValue(Value=ua.Variant(Value=5, VariantType=ua.VariantType.Int64))

    server.set_attribute_value_callback(node.nodeid, callback, attr=ua.AttributeIds.Value)
    dv = server.read_attribute_value(node.nodeid, attr=ua.AttributeIds.Value)
    assert dv.Value.Value == 5

    dv = ua.DataValue(Value=ua.Variant(Value=10, VariantType=ua.VariantType.Int64))
    await server.write_attribute_value(node.nodeid, dv, attr=ua.AttributeIds.Value)
    dv = server.read_attribute_value(node.nodeid, attr=ua.AttributeIds.Value)
    assert dv.Value.Value == 10

    await server.delete_nodes([node])


@pytest.fixture(scope="function")
def restore_transport_limits_server(server: Server):
    # Restore limits after test
    assert server.bserver is not None
    max_recv = server.bserver.limits.max_recv_buffer
    max_chunk_count = server.bserver.limits.max_chunk_count
    yield server
    server.bserver.limits.max_recv_buffer = max_recv
    server.bserver.limits.max_chunk_count = max_chunk_count


async def test_message_limits_fail_write(restore_transport_limits_server: Server):
    server = restore_transport_limits_server
    assert server.bserver is not None
    server.bserver.limits.max_recv_buffer = 1024
    server.bserver.limits.max_send_buffer = 10240000
    server.bserver.limits.max_chunk_count = 10
    test_string = b'a' * 100 * 1024
    n = await server.nodes.objects.add_variable(1, "MyLimitVariable", test_string)
    await n.set_writable(True)
    client = Client(server.endpoint.geturl())
    # This should trigger a timeout error because the message is to large
    async with client:
        n = client.get_node(n.nodeid)
        await n.read_value()
        with pytest.raises(ConnectionError):
            await n.write_value(test_string, ua.VariantType.ByteString)


async def test_message_limits_fail_read(restore_transport_limits_server: Server):
    server = restore_transport_limits_server
    assert server.bserver is not None
    server.bserver.limits.max_recv_buffer = 10240000
    server.bserver.limits.max_send_buffer = 1024
    server.bserver.limits.max_chunk_count = 10
    test_string = b'a' * 100 * 1024
    n = await server.nodes.objects.add_variable(1, "MyLimitVariable", test_string)
    await n.set_writable(True)
    client = Client(server.endpoint.geturl())
    # This should trigger a connection error because the message is to large
    async with client:
        n = client.get_node(n.nodeid)
        await n.write_value(test_string, ua.VariantType.ByteString)
        with pytest.raises(ConnectionError):
            await n.read_value()


async def test_message_limits_works(restore_transport_limits_server: Server):
    server = restore_transport_limits_server
    # server.bserver.limits.max_recv_buffer = 1024
    assert server.bserver is not None
    server.bserver.limits.max_send_buffer = 1024
    server.bserver.limits.max_chunk_count = 10
    n = await server.nodes.objects.add_variable(1, "MyLimitVariable2", "t")
    await n.set_writable(True)
    client = Client(server.endpoint.geturl())
    # Test that chunks are working correct
    async with client:
        n = client.get_node(n.nodeid)
        test_string = 'a' * (1024 * 5)
        await n.write_value(test_string, ua.VariantType.String)
        await n.read_value()


"""
class TestServerCaching(unittest.TestCase):
    def runTest(self):
        return # FIXME broken
        tmpfile = NamedTemporaryFile()
        path = tmpfile.name
        tmpfile.close()

        # create cache file
        server = Server(shelffile=path)

        # modify cache content
        id = ua.NodeId(ua.ObjectIds.Server_ServerStatus_SecondsTillShutdown)
        s = shelve.open(path, "w", writeback=True)
        s[id.to_string()].attributes[ua.AttributeIds.Value].value = ua.DataValue(123)
        s.close()

        # ensure that we are actually loading from the cache
        server = Server(shelffile=path)
        assert server.get_node(id).read_value(), 123)

        os.remove(path)

"""


async def test_null_auth(server):
    """
    OPC-UA Specification Part 4, 5.6.3 specifies that a:
    > Null or empty user token shall always be interpreted as anonymous

    Ensure a Null token is accepted as an anonymous connection token.
    """
    client = Client(server.endpoint.geturl())

    # Modify the authentication creation in the client request
    def _add_null_auth(self, params):
        params.UserIdentityToken = ua.ExtensionObject(ua.NodeId(ua.ObjectIds.Null))
    client._add_anonymous_auth = _add_null_auth.__get__(client, Client)
    # Attempt to connect, this should be accepted without error
    async with client:
        pass


async def test_start_server_when_port_is_in_use(server: Server):
    server2 = Server()
    await server2.init()
    url = server.endpoint.geturl()
    server2.set_endpoint(url)  # try to bind on the same endpoint as an already running server
    with pytest.raises(OSError):
        await server2.start()
    # now it should still be possible to stop the server with exceptions
    await server2.stop()
