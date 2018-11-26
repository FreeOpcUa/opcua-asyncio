import unittest
import os
import shelve
import time
from enum import Enum, EnumMeta

from tests_common import CommonTests, add_server_methods
from tests_xml import XmlTests
from tests_subscriptions import SubscriptionTests
from datetime import timedelta, datetime
from tempfile import NamedTemporaryFile

import opcua
from opcua import Server
from opcua import Client
from opcua import ua
from opcua import uamethod
from opcua.common.event_objects import BaseEvent, AuditEvent, AuditChannelEvent, AuditSecurityEvent, AuditOpenSecureChannelEvent
from opcua.common import ua_utils


port_num = 48540
port_discovery = 48550


class TestServer(unittest.TestCase, CommonTests, SubscriptionTests, XmlTests):

    '''
    Run common tests on server side
    Tests that can only be run on server side must be defined here
    '''
    @classmethod
    def setUpClass(cls):
        cls.srv = Server()
        cls.srv.set_endpoint('opc.tcp://127.0.0.1:{0:d}'.format(port_num))
        add_server_methods(cls.srv)
        cls.srv.start()
        cls.opc = cls.srv
        cls.discovery = Server()
        cls.discovery.set_application_uri("urn:freeopcua:python:discovery")
        cls.discovery.set_endpoint('opc.tcp://127.0.0.1:{0:d}'.format(port_discovery))
        cls.discovery.start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.stop()
        cls.discovery.stop()

    def test_discovery(self):
        client = Client(self.discovery.endpoint.geturl())
        client.connect()
        try:
            servers = client.find_servers()
            new_app_uri = "urn:freeopcua:python:server:test_discovery"
            self.srv.application_uri = new_app_uri
            self.srv.register_to_discovery(self.discovery.endpoint.geturl(), 0)
            time.sleep(0.1)  # let server register registration
            new_servers = client.find_servers()
            self.assertEqual(len(new_servers) - len(servers) , 1)
            self.assertFalse(new_app_uri in [s.ApplicationUri for s in servers])
            self.assertTrue(new_app_uri in [s.ApplicationUri for s in new_servers])
        finally:
            client.disconnect()

    def test_find_servers2(self):
        client = Client(self.discovery.endpoint.geturl())
        client.connect()
        try:
            servers = client.find_servers()
            new_app_uri1 = "urn:freeopcua:python:server:test_discovery1"
            self.srv.application_uri = new_app_uri1
            self.srv.register_to_discovery(self.discovery.endpoint.geturl(), period=0)
            new_app_uri2 = "urn:freeopcua:python:test_discovery2"
            self.srv.application_uri = new_app_uri2
            self.srv.register_to_discovery(self.discovery.endpoint.geturl(), period=0)
            time.sleep(0.1)  # let server register registration
            new_servers = client.find_servers()
            self.assertEqual(len(new_servers) - len(servers) , 2)
            self.assertFalse(new_app_uri1 in [s.ApplicationUri for s in servers])
            self.assertFalse(new_app_uri2 in [s.ApplicationUri for s in servers])
            self.assertTrue(new_app_uri1 in [s.ApplicationUri for s in new_servers])
            self.assertTrue(new_app_uri2 in [s.ApplicationUri for s in new_servers])
            # now do a query with filer
            new_servers = client.find_servers(["urn:freeopcua:python:server"])
            self.assertEqual(len(new_servers) - len(servers) , 0)
            self.assertTrue(new_app_uri1 in [s.ApplicationUri for s in new_servers])
            self.assertFalse(new_app_uri2 in [s.ApplicationUri for s in new_servers])
            # now do a query with filer
            new_servers = client.find_servers(["urn:freeopcua:python"])
            self.assertEqual(len(new_servers) - len(servers) , 2)
            self.assertTrue(new_app_uri1 in [s.ApplicationUri for s in new_servers])
            self.assertTrue(new_app_uri2 in [s.ApplicationUri for s in new_servers])
        finally:
            client.disconnect()


    """
    # not sure if this test is necessary, and there is a lot repetition with previous test
    def test_discovery_server_side(self):
        servers = self.discovery.find_servers()
        self.assertEqual(len(servers), 1)
        self.srv.register_to_discovery(self.discovery.endpoint.geturl(), 1)
        time.sleep(1) # let server register registration
        servers = self.discovery.find_servers()
        print("SERVERS 2", servers)
        self.assertEqual(len(servers), 2)
    """
    # def test_register_server2(self):
        # servers = self.opc.register_server()

    def test_register_namespace(self):
        uri = 'http://mycustom.Namespace.com'
        idx1 = self.opc.register_namespace(uri)
        idx2 = self.opc.get_namespace_index(uri)
        self.assertEqual(idx1, idx2)

    def test_register_existing_namespace(self):
        uri = 'http://mycustom.Namespace.com'
        idx1 = self.opc.register_namespace(uri)
        idx2 = self.opc.register_namespace(uri)
        idx3 = self.opc.get_namespace_index(uri)
        self.assertEqual(idx1, idx2)
        self.assertEqual(idx1, idx3)

    def test_register_use_namespace(self):
        uri = 'http://my_very_custom.Namespace.com'
        idx = self.opc.register_namespace(uri)
        root = self.opc.get_root_node()
        myvar = root.add_variable(idx, 'var_in_custom_namespace', [5])
        myid = myvar.nodeid
        self.assertEqual(idx, myid.NamespaceIndex)

    def test_server_method(self):
        def func(parent, variant):
            variant.Value *= 2
            return [variant]
        o = self.opc.get_objects_node()
        v = o.add_method(3, 'Method1', func, [ua.VariantType.Int64], [ua.VariantType.Int64])
        result = o.call_method(v, ua.Variant(2.1))
        self.assertEqual(result, 4.2)

    def test_historize_variable(self):
        o = self.opc.get_objects_node()
        var = o.add_variable(3, "test_hist", 1.0)
        self.srv.iserver.enable_history_data_change(var, timedelta(days=1))
        time.sleep(1)
        var.set_value(2.0)
        var.set_value(3.0)
        self.srv.iserver.disable_history_data_change(var)

    def test_historize_events(self):
        srv_node = self.srv.get_node(ua.ObjectIds.Server)
        self.assertEqual(
            srv_node.get_event_notifier(),
            {ua.EventNotifier.SubscribeToEvents}
        )
        srvevgen = self.srv.get_event_generator()
        self.srv.iserver.enable_history_event(srv_node, period=None)
        self.assertEqual(
            srv_node.get_event_notifier(),
            {ua.EventNotifier.SubscribeToEvents, ua.EventNotifier.HistoryRead}
        )
        srvevgen.trigger(message="Message")
        self.srv.iserver.disable_history_event(srv_node)

    def test_references_for_added_nodes_method(self):
        objects = self.opc.get_objects_node()
        o = objects.add_object(3, 'MyObject')
        nodes = objects.get_referenced_nodes(refs=ua.ObjectIds.Organizes, direction=ua.BrowseDirection.Forward, includesubtypes=False)
        self.assertTrue(o in nodes)
        nodes = o.get_referenced_nodes(refs=ua.ObjectIds.Organizes, direction=ua.BrowseDirection.Inverse, includesubtypes=False)
        self.assertTrue(objects in nodes)
        self.assertEqual(o.get_parent(), objects)
        self.assertEqual(o.get_type_definition().Identifier, ua.ObjectIds.BaseObjectType)

        @uamethod
        def callback(parent):
            return

        m = o.add_method(3, 'MyMethod', callback)
        nodes = o.get_referenced_nodes(refs=ua.ObjectIds.HasComponent, direction=ua.BrowseDirection.Forward, includesubtypes=False)
        self.assertTrue(m in nodes)
        nodes = m.get_referenced_nodes(refs=ua.ObjectIds.HasComponent, direction=ua.BrowseDirection.Inverse, includesubtypes=False)
        self.assertTrue(o in nodes)
        self.assertEqual(m.get_parent(), o)

    # This should work for following BaseEvent tests to work (maybe to write it a bit differentlly since they are not independent)
    def test_get_event_from_type_node_BaseEvent(self):
        ev = opcua.common.events.get_event_obj_from_type_node(opcua.Node(self.opc.iserver.isession, ua.NodeId(ua.ObjectIds.BaseEventType)))
        check_base_event(self, ev)

    def test_get_event_from_type_node_Inhereted_AuditEvent(self):
        ev = opcua.common.events.get_event_obj_from_type_node(opcua.Node(self.opc.iserver.isession, ua.NodeId(ua.ObjectIds.AuditEventType)))
        self.assertIsNot(ev, None)  # we did not receive event
        self.assertIsInstance(ev, BaseEvent)
        self.assertIsInstance(ev, AuditEvent)
        self.assertEqual(ev.EventType, ua.NodeId(ua.ObjectIds.AuditEventType))
        self.assertEqual(ev.Severity, 1)
        self.assertEqual(ev.ActionTimeStamp, None)
        self.assertEqual(ev.Status, False)
        self.assertEqual(ev.ServerId, None)
        self.assertEqual(ev.ClientAuditEntryId, None)
        self.assertEqual(ev.ClientUserId, None)

    def test_get_event_from_type_node_MultiInhereted_AuditOpenSecureChannelEvent(self):
        ev = opcua.common.events.get_event_obj_from_type_node(opcua.Node(self.opc.iserver.isession, ua.NodeId(ua.ObjectIds.AuditOpenSecureChannelEventType)))
        self.assertIsNot(ev, None)
        self.assertIsInstance(ev, BaseEvent)
        self.assertIsInstance(ev, AuditEvent)
        self.assertIsInstance(ev, AuditSecurityEvent)
        self.assertIsInstance(ev, AuditChannelEvent)
        self.assertIsInstance(ev, AuditOpenSecureChannelEvent)
        self.assertEqual(ev.EventType, ua.NodeId(ua.ObjectIds.AuditOpenSecureChannelEventType))
        self.assertEqual(ev.Severity, 1),
        self.assertEqual(ev.ClientCertificate, None)
        self.assertEqual(ev.ClientCertificateThumbprint, None)
        self.assertEqual(ev.RequestType, None)
        self.assertEqual(ev.SecurityPolicyUri, None)
        self.assertEqual(ev.SecurityMode, None)
        self.assertEqual(ev.RequestedLifetime, None)

    def test_eventgenerator_default(self):
        evgen = self.opc.get_event_generator()
        check_eventgenerator_BaseEvent(self, evgen)
        check_eventgenerator_SourceServer(self, evgen)

    def test_eventgenerator_BaseEvent_object(self):
        evgen = self.opc.get_event_generator(BaseEvent())
        check_eventgenerator_BaseEvent(self, evgen)
        check_eventgenerator_SourceServer(self, evgen)

    def test_eventgenerator_BaseEvent_Node(self):
        evgen = self.opc.get_event_generator(opcua.Node(self.opc.iserver.isession, ua.NodeId(ua.ObjectIds.BaseEventType)))
        check_eventgenerator_BaseEvent(self, evgen)
        check_eventgenerator_SourceServer(self, evgen)

    def test_eventgenerator_BaseEvent_NodeId(self):
        evgen = self.opc.get_event_generator(ua.NodeId(ua.ObjectIds.BaseEventType))
        check_eventgenerator_BaseEvent(self, evgen)
        check_eventgenerator_SourceServer(self, evgen)

    def test_eventgenerator_BaseEvent_ObjectIds(self):
        evgen = self.opc.get_event_generator(ua.ObjectIds.BaseEventType)
        check_eventgenerator_BaseEvent(self, evgen)
        check_eventgenerator_SourceServer(self, evgen)

    def test_eventgenerator_BaseEvent_Identifier(self):
        evgen = self.opc.get_event_generator(2041)
        check_eventgenerator_BaseEvent(self, evgen)
        check_eventgenerator_SourceServer(self, evgen)

    def test_eventgenerator_sourceServer_Node(self):
        evgen = self.opc.get_event_generator(emitting_node=opcua.Node(self.opc.iserver.isession, ua.NodeId(ua.ObjectIds.Server)))
        check_eventgenerator_BaseEvent(self, evgen)
        check_eventgenerator_SourceServer(self, evgen)

    def test_eventgenerator_sourceServer_NodeId(self):
        evgen = self.opc.get_event_generator(emitting_node=ua.NodeId(ua.ObjectIds.Server))
        check_eventgenerator_BaseEvent(self, evgen)
        check_eventgenerator_SourceServer(self, evgen)

    def test_eventgenerator_sourceServer_ObjectIds(self):
        evgen = self.opc.get_event_generator(emitting_node=ua.ObjectIds.Server)
        check_eventgenerator_BaseEvent(self, evgen)
        check_eventgenerator_SourceServer(self, evgen)

    def test_eventgenerator_sourceMyObject(self):
        objects = self.opc.get_objects_node()
        o = objects.add_object(3, 'MyObject')
        evgen = self.opc.get_event_generator(emitting_node=o)
        check_eventgenerator_BaseEvent(self, evgen)
        check_event_generator_object(self, evgen, o)

    def test_eventgenerator_source_collision(self):
        objects = self.opc.get_objects_node()
        o = objects.add_object(3, 'MyObject')
        event = BaseEvent(sourcenode=o.nodeid)
        evgen = self.opc.get_event_generator(event, ua.ObjectIds.Server)
        evgen.event.SourceNode = o.nodeid
        evgen.event.SourceName = o.get_browse_name().Name
        check_eventgenerator_BaseEvent(self, evgen)
        check_event_generator_object(self, evgen, o, emitting_node=opcua.Node(self.opc.iserver.isession, ua.ObjectIds.Server))

    def test_eventgenerator_InheritedEvent(self):
        evgen = self.opc.get_event_generator(ua.ObjectIds.AuditEventType)
        check_eventgenerator_SourceServer(self, evgen)

        ev = evgen.event
        self.assertIsNot(ev, None)  # we did not receive event
        self.assertIsInstance(ev, BaseEvent)
        self.assertIsInstance(ev, AuditEvent)
        self.assertEqual(ev.EventType, ua.NodeId(ua.ObjectIds.AuditEventType))
        self.assertEqual(ev.Severity, 1)
        self.assertEqual(ev.ActionTimeStamp, None)
        self.assertEqual(ev.Status, False)
        self.assertEqual(ev.ServerId, None)
        self.assertEqual(ev.ClientAuditEntryId, None)
        self.assertEqual(ev.ClientUserId, None)

    def test_eventgenerator_MultiInheritedEvent(self):
        evgen = self.opc.get_event_generator(ua.ObjectIds.AuditOpenSecureChannelEventType)
        check_eventgenerator_SourceServer(self, evgen)

        ev = evgen.event
        self.assertIsNot(ev, None)  # we did not receive event
        self.assertIsInstance(ev, BaseEvent)
        self.assertIsInstance(ev, AuditEvent)
        self.assertIsInstance(ev, AuditSecurityEvent)
        self.assertIsInstance(ev, AuditChannelEvent)
        self.assertIsInstance(ev, AuditOpenSecureChannelEvent)
        self.assertEqual(ev.EventType, ua.NodeId(ua.ObjectIds.AuditOpenSecureChannelEventType))
        self.assertEqual(ev.Severity, 1),
        self.assertEqual(ev.ClientCertificate, None)
        self.assertEqual(ev.ClientCertificateThumbprint, None)
        self.assertEqual(ev.RequestType, None)
        self.assertEqual(ev.SecurityPolicyUri, None)
        self.assertEqual(ev.SecurityMode, None)
        self.assertEqual(ev.RequestedLifetime, None)

    # For the custom events all posibilites are tested. For other custom types only one test case is done since they are using the same code
    def test_create_custom_data_type_ObjectId(self):
        type = self.opc.create_custom_data_type(2, 'MyDataType', ua.ObjectIds.BaseDataType, [('PropertyNum', ua.VariantType.Int32), ('PropertyString', ua.VariantType.String)])
        check_custom_type(self, type, ua.ObjectIds.BaseDataType)

    def test_create_custom_event_type_ObjectId(self):
        type = self.opc.create_custom_event_type(2, 'MyEvent', ua.ObjectIds.BaseEventType, [('PropertyNum', ua.VariantType.Int32), ('PropertyString', ua.VariantType.String)])
        check_custom_type(self, type, ua.ObjectIds.BaseEventType)

    def test_create_custom_object_type_ObjectId(self):
        def func(parent, variant):
            return [ua.Variant(ret, ua.VariantType.Boolean)]

        properties = [('PropertyNum', ua.VariantType.Int32),
                      ('PropertyString', ua.VariantType.String)]
        variables = [('VariableString', ua.VariantType.String),
                     ('MyEnumVar', ua.VariantType.Int32, ua.NodeId(ua.ObjectIds.ApplicationType))]
        methods = [('MyMethod', func, [ua.VariantType.Int64], [ua.VariantType.Boolean])]

        node_type = self.opc.create_custom_object_type(2, 'MyObjectType', ua.ObjectIds.BaseObjectType, properties, variables, methods)

        check_custom_type(self, node_type, ua.ObjectIds.BaseObjectType)
        variables = node_type.get_variables()
        self.assertTrue(node_type.get_child("2:VariableString") in variables)
        self.assertEqual(node_type.get_child("2:VariableString").get_data_value().Value.VariantType, ua.VariantType.String)
        self.assertTrue(node_type.get_child("2:MyEnumVar") in variables)
        self.assertEqual(node_type.get_child("2:MyEnumVar").get_data_value().Value.VariantType, ua.VariantType.Int32)
        self.assertEqual(node_type.get_child("2:MyEnumVar").get_data_type(), ua.NodeId(ua.ObjectIds.ApplicationType))
        methods = node_type.get_methods()
        self.assertTrue(node_type.get_child("2:MyMethod") in methods)

    # def test_create_custom_refrence_type_ObjectId(self):
        # type = self.opc.create_custom_reference_type(2, 'MyEvent', ua.ObjectIds.Base, [('PropertyNum', ua.VariantType.Int32), ('PropertyString', ua.VariantType.String)])
        # check_custom_type(self, type, ua.ObjectIds.BaseObjectType)

    def test_create_custom_variable_type_ObjectId(self):
        type = self.opc.create_custom_variable_type(2, 'MyVariableType', ua.ObjectIds.BaseVariableType, [('PropertyNum', ua.VariantType.Int32), ('PropertyString', ua.VariantType.String)])
        check_custom_type(self, type, ua.ObjectIds.BaseVariableType)

    def test_create_custom_event_type_NodeId(self):
        etype = self.opc.create_custom_event_type(2, 'MyEvent', ua.NodeId(ua.ObjectIds.BaseEventType), [('PropertyNum', ua.VariantType.Int32), ('PropertyString', ua.VariantType.String)])
        check_custom_type(self, etype, ua.ObjectIds.BaseEventType)

    def test_create_custom_event_type_Node(self):
        etype = self.opc.create_custom_event_type(2, 'MyEvent', opcua.Node(self.opc.iserver.isession, ua.NodeId(ua.ObjectIds.BaseEventType)), [('PropertyNum', ua.VariantType.Int32), ('PropertyString', ua.VariantType.String)])
        check_custom_type(self, etype, ua.ObjectIds.BaseEventType)

    def test_get_event_from_type_node_CustomEvent(self):
        etype = self.opc.create_custom_event_type(2, 'MyEvent', ua.ObjectIds.BaseEventType, [('PropertyNum', ua.VariantType.Int32), ('PropertyString', ua.VariantType.String)])

        ev = opcua.common.events.get_event_obj_from_type_node(etype)
        check_custom_event(self, ev, etype)
        self.assertEqual(ev.PropertyNum, 0)
        self.assertEqual(ev.PropertyString, None)

    def test_eventgenerator_customEvent(self):
        etype = self.opc.create_custom_event_type(2, 'MyEvent', ua.ObjectIds.BaseEventType, [('PropertyNum', ua.VariantType.Int32), ('PropertyString', ua.VariantType.String)])

        evgen = self.opc.get_event_generator(etype, ua.ObjectIds.Server)
        check_eventgenerator_CustomEvent(self, evgen, etype)
        check_eventgenerator_SourceServer(self, evgen)

        self.assertEqual(evgen.event.PropertyNum, 0)
        self.assertEqual(evgen.event.PropertyString, None)

    def test_eventgenerator_double_customEvent(self):
        event1 = self.opc.create_custom_event_type(3, 'MyEvent1', ua.ObjectIds.BaseEventType, [('PropertyNum', ua.VariantType.Int32), ('PropertyString', ua.VariantType.String)])

        event2 = self.opc.create_custom_event_type(4, 'MyEvent2', event1, [('PropertyBool', ua.VariantType.Boolean), ('PropertyInt', ua.VariantType.Int32)])

        evgen = self.opc.get_event_generator(event2, ua.ObjectIds.Server)
        check_eventgenerator_CustomEvent(self, evgen, event2)
        check_eventgenerator_SourceServer(self, evgen)

        # Properties from MyEvent1
        self.assertEqual(evgen.event.PropertyNum, 0)
        self.assertEqual(evgen.event.PropertyString, None)

         # Properties from MyEvent2
        self.assertEqual(evgen.event.PropertyBool, False)
        self.assertEqual(evgen.event.PropertyInt, 0)

    def test_eventgenerator_customEvent_MyObject(self):
        objects = self.opc.get_objects_node()
        o = objects.add_object(3, 'MyObject')
        etype = self.opc.create_custom_event_type(2, 'MyEvent', ua.ObjectIds.BaseEventType, [('PropertyNum', ua.VariantType.Int32), ('PropertyString', ua.VariantType.String)])

        evgen = self.opc.get_event_generator(etype, o)
        check_eventgenerator_CustomEvent(self, evgen, etype)
        check_event_generator_object(self, evgen, o)

        self.assertEqual(evgen.event.PropertyNum, 0)
        self.assertEqual(evgen.event.PropertyString, None)

    def test_context_manager(self):
        """ Context manager calls start() and stop()
        """
        state = [0]
        def increment_state(self, *args, **kwargs):
            state[0] += 1

        # create server and replace instance methods with dummy methods
        server = Server()
        server.start = increment_state.__get__(server)
        server.stop = increment_state.__get__(server)

        assert state[0] == 0
        with server:
            # test if server started
            self.assertEqual(state[0], 1)
        # test if server stopped
        self.assertEqual(state[0], 2)

    def test_get_node_by_ns(self):

        def get_ns_of_nodes(nodes):
            ns_list = set()
            for node in nodes:
                ns_list.add(node.nodeid.NamespaceIndex)
            return ns_list

        # incase other testss created nodes  in unregistered namespace
        _idx_d = self.opc.register_namespace('dummy1')
        _idx_d = self.opc.register_namespace('dummy2')
        _idx_d = self.opc.register_namespace('dummy3')

        # create the test namespaces and vars
        idx_a = self.opc.register_namespace('a')
        idx_b = self.opc.register_namespace('b')
        idx_c = self.opc.register_namespace('c')
        o = self.opc.get_objects_node()
        _myvar2 = o.add_variable(idx_a, "MyBoolVar2", True)
        _myvar3 = o.add_variable(idx_b, "MyBoolVar3", True)
        _myvar4 = o.add_variable(idx_c, "MyBoolVar4", True)

        # the tests
        nodes = ua_utils.get_nodes_of_namespace(self.opc, namespaces=[idx_a, idx_b, idx_c])
        self.assertEqual(len(nodes), 3)
        self.assertEqual(get_ns_of_nodes(nodes), set([idx_a, idx_b, idx_c]))

        nodes = ua_utils.get_nodes_of_namespace(self.opc, namespaces=[idx_a])
        self.assertEqual(len(nodes), 1)
        self.assertEqual(get_ns_of_nodes(nodes), set([idx_a]))

        nodes = ua_utils.get_nodes_of_namespace(self.opc, namespaces=[idx_b])
        self.assertEqual(len(nodes), 1)
        self.assertEqual(get_ns_of_nodes(nodes), set([idx_b]))

        nodes = ua_utils.get_nodes_of_namespace(self.opc, namespaces=['a'])
        self.assertEqual(len(nodes), 1)
        self.assertEqual(get_ns_of_nodes(nodes), set([idx_a]))

        nodes = ua_utils.get_nodes_of_namespace(self.opc, namespaces=['a', 'c'])
        self.assertEqual(len(nodes), 2)
        self.assertEqual(get_ns_of_nodes(nodes), set([idx_a, idx_c]))

        nodes = ua_utils.get_nodes_of_namespace(self.opc, namespaces='b')
        self.assertEqual(len(nodes), 1)
        self.assertEqual(get_ns_of_nodes(nodes), set([idx_b]))

        nodes = ua_utils.get_nodes_of_namespace(self.opc, namespaces=idx_b)
        self.assertEqual(len(nodes), 1)
        self.assertEqual(get_ns_of_nodes(nodes), set([idx_b]))

        self.assertRaises(ValueError, ua_utils.get_nodes_of_namespace, self.opc, namespaces='non_existing_ns')

    def test_load_enum_strings(self):
        dt = self.opc.nodes.enum_data_type.add_data_type(0, "MyStringEnum")
        dt.add_variable(0, "EnumStrings", [ua.LocalizedText("e1"), ua.LocalizedText("e2"), ua.LocalizedText("e3"), ua.LocalizedText("e 4")])
        self.opc.load_enums()
        e = getattr(ua, "MyStringEnum")
        self.assertIsInstance(e, EnumMeta)
        self.assertTrue(hasattr(e, "e1"))
        self.assertTrue(hasattr(e, "e4"))
        self.assertEqual(getattr(e, "e4"), 3)

    def test_load_enum_values(self):
        dt = self.opc.nodes.enum_data_type.add_data_type(0, "MyValuesEnum")
        v1 = ua.EnumValueType()
        v1.DisplayName.Text = "v1"
        v1.Value = 2
        v2 = ua.EnumValueType()
        v2.DisplayName.Text = "v2"
        v2.Value = 3
        v3 = ua.EnumValueType()
        v3.DisplayName.Text = "v 3 "
        v3.Value = 4
        dt.add_variable(0, "EnumValues", [v1, v2, v3])
        self.opc.load_enums()
        e = getattr(ua, "MyValuesEnum")
        self.assertIsInstance(e, EnumMeta)
        self.assertTrue(hasattr(e, "v1"))
        self.assertTrue(hasattr(e, "v3"))
        self.assertEqual(getattr(e, "v3"), 4)




def check_eventgenerator_SourceServer(test, evgen):
    server = test.opc.get_server_node()
    test.assertEqual(evgen.event.SourceName, server.get_browse_name().Name)
    test.assertEqual(evgen.event.SourceNode, ua.NodeId(ua.ObjectIds.Server))
    test.assertEqual(server.get_event_notifier(), {ua.EventNotifier.SubscribeToEvents})

    refs = server.get_referenced_nodes(ua.ObjectIds.GeneratesEvent, ua.BrowseDirection.Forward, ua.NodeClass.ObjectType, False)
    test.assertGreaterEqual(len(refs), 1)


def check_event_generator_object(test, evgen, obj, emitting_node=None):
    test.assertEqual(evgen.event.SourceName, obj.get_browse_name().Name)
    test.assertEqual(evgen.event.SourceNode, obj.nodeid)
    if not emitting_node:
        test.assertEqual(obj.get_event_notifier(), {ua.EventNotifier.SubscribeToEvents})
        refs = obj.get_referenced_nodes(ua.ObjectIds.GeneratesEvent, ua.BrowseDirection.Forward, ua.NodeClass.ObjectType, False)
    else:
        test.assertEqual(emitting_node.get_event_notifier(), {ua.EventNotifier.SubscribeToEvents})
        refs = emitting_node.get_referenced_nodes(ua.ObjectIds.GeneratesEvent, ua.BrowseDirection.Forward, ua.NodeClass.ObjectType, False)

    test.assertIn(evgen.event.EventType, [x.nodeid for x in refs])


def check_eventgenerator_BaseEvent(test, evgen):
    test.assertIsNot(evgen, None)  # we did not receive event generator
    test.assertIs(evgen.isession, test.opc.iserver.isession)
    check_base_event(test, evgen.event)


def check_base_event(test, ev):
    test.assertIsNot(ev, None)  # we did not receive event
    test.assertIsInstance(ev, BaseEvent)
    test.assertEqual(ev.EventType, ua.NodeId(ua.ObjectIds.BaseEventType))
    test.assertEqual(ev.Severity, 1)


def check_eventgenerator_CustomEvent(test, evgen, etype):
    test.assertIsNot(evgen, None)  # we did not receive event generator
    test.assertIs(evgen.isession, test.opc.iserver.isession)
    check_custom_event(test, evgen.event, etype)


def check_custom_event(test, ev, etype):
    test.assertIsNot(ev, None)  # we did not receive event
    test.assertIsInstance(ev, BaseEvent)
    test.assertEqual(ev.EventType, etype.nodeid)
    test.assertEqual(ev.Severity, 1)


def check_custom_type(test, type, base_type):
    base = opcua.Node(test.opc.iserver.isession, ua.NodeId(base_type))
    test.assertTrue(type in base.get_children())
    nodes = type.get_referenced_nodes(refs=ua.ObjectIds.HasSubtype, direction=ua.BrowseDirection.Inverse, includesubtypes=True)
    test.assertEqual(base, nodes[0])
    properties = type.get_properties()
    test.assertIsNot(properties, None)
    test.assertEqual(len(properties), 2)
    test.assertTrue(type.get_child("2:PropertyNum") in properties)
    test.assertEqual(type.get_child("2:PropertyNum").get_data_value().Value.VariantType, ua.VariantType.Int32)
    test.assertTrue(type.get_child("2:PropertyString") in properties)
    test.assertEqual(type.get_child("2:PropertyString").get_data_value().Value.VariantType, ua.VariantType.String)


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
        self.assertEqual(server.get_node(id).get_value(), 123)

        os.remove(path)


class TestServerStartError(unittest.TestCase):

    def test_port_in_use(self):

        server1 = Server()
        server1.set_endpoint('opc.tcp://127.0.0.1:{0:d}'.format(port_num + 1))
        server1.start()

        server2 = Server()
        server2.set_endpoint('opc.tcp://127.0.0.1:{0:d}'.format(port_num + 1))
        try:
            server2.start()
        except Exception:
            pass

        server1.stop()
        server2.stop()
