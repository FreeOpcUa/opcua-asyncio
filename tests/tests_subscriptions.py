
from concurrent.futures import Future, TimeoutError
import time
from datetime import datetime, timedelta
from copy import copy

import opcua
from opcua import ua


class SubHandler():

    """
    Dummy subscription client
    """

    def datachange_notification(self, node, val, data):
        pass

    def event_notification(self, event):
        pass


class MySubHandler():

    """
    More advanced subscription client using Future, so we can wait for events in tests
    """

    def __init__(self):
        self.future = Future()

    def reset(self):
        self.future = Future()

    def datachange_notification(self, node, val, data):
        self.future.set_result((node, val, data))

    def event_notification(self, event):
        self.future.set_result(event)


class MySubHandler2():
    def __init__(self):
        self.results = []

    def datachange_notification(self, node, val, data):
        self.results.append((node, val))

    def event_notification(self, event):
        self.results.append(event)


class MySubHandlerCounter():
    def __init__(self):
        self.datachange_count = 0
        self.event_count = 0

    def datachange_notification(self, node, val, data):
        self.datachange_count += 1

    def event_notification(self, event):
        self.event_count += 1


class SubscriptionTests(object):

    def test_subscription_failure(self):
        myhandler = MySubHandler()
        o = self.opc.get_objects_node()
        sub = self.opc.create_subscription(100, myhandler)
        with self.assertRaises(ua.UaStatusCodeError):
            handle1 = sub.subscribe_data_change(o) # we can only subscribe to variables so this should fail
        sub.delete()

    def test_subscription_overload(self):
        nb = 10
        myhandler = MySubHandler()
        o = self.opc.get_objects_node()
        sub = self.opc.create_subscription(1, myhandler)
        variables = []
        subs = []
        for i in range(nb):
            v = o.add_variable(3, 'SubscriptionVariableOverload' + str(i), 99)
            variables.append(v)
        for i in range(nb):
            sub.subscribe_data_change(variables)
        for i in range(nb):
            for j in range(nb):
                variables[i].set_value(j)
            s = self.opc.create_subscription(1, myhandler)
            s.subscribe_data_change(variables)
            subs.append(s)
            sub.subscribe_data_change(variables[i])
        for i in range(nb):
            for j in range(nb):
                variables[i].set_value(j)
        sub.delete()
        for s in subs:
            s.delete()

    def test_subscription_count(self):
        myhandler = MySubHandlerCounter()
        sub = self.opc.create_subscription(1, myhandler)
        o = self.opc.get_objects_node()
        var = o.add_variable(3, 'SubVarCounter', 0.1)
        sub.subscribe_data_change(var)
        nb = 12
        for i in range(nb):
            val = var.get_value()
            var.set_value(val +1)
        time.sleep(0.2)  # let last event arrive
        self.assertEqual(myhandler.datachange_count, nb + 1)
        sub.delete()

    def test_subscription_count_list(self):
        myhandler = MySubHandlerCounter()
        sub = self.opc.create_subscription(1, myhandler)
        o = self.opc.get_objects_node()
        var = o.add_variable(3, 'SubVarCounter', [0.1, 0.2])
        sub.subscribe_data_change(var)
        nb = 12
        for i in range(nb):
            val = var.get_value()
            val = copy(val)  # we do not want to modify object in our db, we need a copy in order to generate event
            val.append(i)
            var.set_value(copy(val))
        time.sleep(0.2)  # let last event arrive
        self.assertEqual(myhandler.datachange_count, nb + 1)
        sub.delete()

    def test_subscription_count_no_change(self):
        myhandler = MySubHandlerCounter()
        sub = self.opc.create_subscription(1, myhandler)
        o = self.opc.get_objects_node()
        var = o.add_variable(3, 'SubVarCounter', [0.1, 0.2])
        sub.subscribe_data_change(var)
        nb = 12
        for i in range(nb):
            val = var.get_value()
            var.set_value(val)
        time.sleep(0.2)  # let last event arrive
        self.assertEqual(myhandler.datachange_count, 1)
        sub.delete()

    def test_subscription_count_empty(self):
        myhandler = MySubHandlerCounter()
        sub = self.opc.create_subscription(1, myhandler)
        o = self.opc.get_objects_node()
        var = o.add_variable(3, 'SubVarCounter', [0.1, 0.2, 0.3])
        sub.subscribe_data_change(var)
        while True:
            val = var.get_value()
            val = copy(val)  # we do not want to modify object in our db, we need a copy in order to generate event
            val.pop()
            var.set_value(val, ua.VariantType.Double)
            if not val:
                break
        time.sleep(0.2)  # let last event arrive
        self.assertEqual(myhandler.datachange_count, 4)
        sub.delete()

    def test_subscription_overload_simple(self):
        nb = 10
        myhandler = MySubHandler()
        o = self.opc.get_objects_node()
        sub = self.opc.create_subscription(1, myhandler)
        variables = [o.add_variable(3, 'SubVarOverload' + str(i), i) for i in range(nb)]
        for i in range(nb):
            sub.subscribe_data_change(variables)
        sub.delete()

    def test_subscription_data_change(self):
        """
        test subscriptions. This is far too complicated for
        a unittest but, setting up subscriptions requires a lot
        of code, so when we first set it up, it is best
        to test as many things as possible
        """
        myhandler = MySubHandler()

        o = self.opc.get_objects_node()

        # subscribe to a variable
        startv1 = [1, 2, 3]
        v1 = o.add_variable(3, 'SubscriptionVariableV1', startv1)
        sub = self.opc.create_subscription(100, myhandler)
        handle1 = sub.subscribe_data_change(v1)

        # Now check we get the start value
        node, val, data = myhandler.future.result()
        self.assertEqual(val, startv1)
        self.assertEqual(node, v1)

        myhandler.reset()  # reset future object

        # modify v1 and check we get value
        v1.set_value([5])
        node, val, data = myhandler.future.result()

        self.assertEqual(node, v1)
        self.assertEqual(val, [5])

        with self.assertRaises(ua.UaStatusCodeError):
            sub.unsubscribe(999)  # non existing handle
        sub.unsubscribe(handle1)
        with self.assertRaises(ua.UaStatusCodeError):
            sub.unsubscribe(handle1)  # second try should fail
        sub.delete()
        with self.assertRaises(ua.UaStatusCodeError):
            sub.unsubscribe(handle1)  # sub does not exist anymore

    def test_subscription_data_change_bool(self):
        """
        test subscriptions. This is far too complicated for
        a unittest but, setting up subscriptions requires a lot
        of code, so when we first set it up, it is best
        to test as many things as possible
        """
        myhandler = MySubHandler()

        o = self.opc.get_objects_node()

        # subscribe to a variable
        startv1 = True
        v1 = o.add_variable(3, 'SubscriptionVariableBool', startv1)
        sub = self.opc.create_subscription(100, myhandler)
        handle1 = sub.subscribe_data_change(v1)

        # Now check we get the start value
        node, val, data = myhandler.future.result()
        self.assertEqual(val, startv1)
        self.assertEqual(node, v1)

        myhandler.reset()  # reset future object

        # modify v1 and check we get value
        v1.set_value(False)
        node, val, data = myhandler.future.result()
        self.assertEqual(node, v1)
        self.assertEqual(val, False)

        sub.delete() # should delete our monitoreditem too

    def test_subscription_data_change_many(self):
        """
        test subscriptions. This is far too complicated for
        a unittest but, setting up subscriptions requires a lot
        of code, so when we first set it up, it is best
        to test as many things as possible
        """
        myhandler = MySubHandler2()
        o = self.opc.get_objects_node()

        startv1 = True
        v1 = o.add_variable(3, 'SubscriptionVariableMany1', startv1)
        startv2 = [1.22, 1.65]
        v2 = o.add_variable(3, 'SubscriptionVariableMany2', startv2)

        sub = self.opc.create_subscription(100, myhandler)
        handle1, handle2 = sub.subscribe_data_change([v1, v2])

        # Now check we get the start values
        nodes = [v1, v2]

        count = 0
        while not len(myhandler.results) > 1:
            count += 1
            time.sleep(0.1)
            if count > 100:
                self.fail("Did not get result from subscription")
        for node, val in myhandler.results:
            self.assertIn(node, nodes)
            nodes.remove(node)
            if node == v1:
                self.assertEqual(startv1, val)
            elif node == v2:
                self.assertEqual(startv2, val)
            else:
                self.fail("Error node {0} is neither {1} nor {2}".format(node, v1, v2))

        sub.delete()

    def test_subscribe_server_time(self):
        myhandler = MySubHandler()

        server_time_node = self.opc.get_node(ua.NodeId(ua.ObjectIds.Server_ServerStatus_CurrentTime))

        sub = self.opc.create_subscription(200, myhandler)
        handle = sub.subscribe_data_change(server_time_node)

        node, val, data = myhandler.future.result()
        self.assertEqual(node, server_time_node)
        delta = datetime.utcnow() - val
        self.assertTrue(delta < timedelta(seconds=2))

        sub.unsubscribe(handle)
        sub.delete()



    def test_create_delete_subscription(self):
        o = self.opc.get_objects_node()
        v = o.add_variable(3, 'SubscriptionVariable', [1, 2, 3])
        sub = self.opc.create_subscription(100, MySubHandler())
        handle = sub.subscribe_data_change(v)
        time.sleep(0.1)
        sub.unsubscribe(handle)
        sub.delete()

    def test_subscribe_events(self):
        sub = self.opc.create_subscription(100, MySubHandler())
        handle = sub.subscribe_events()
        time.sleep(0.1)
        sub.unsubscribe(handle)
        sub.delete()

    def test_subscribe_events_to_wrong_node(self):
        sub = self.opc.create_subscription(100, MySubHandler())
        with self.assertRaises(ua.UaStatusCodeError):
            handle = sub.subscribe_events(self.opc.get_node("i=85"))
        o = self.opc.get_objects_node()
        v = o.add_variable(3, 'VariableNoEventNofierAttribute', 4)
        with self.assertRaises(ua.UaStatusCodeError):
            handle = sub.subscribe_events(v)
        sub.delete()

    def test_get_event_from_type_node_BaseEvent(self):
        etype = self.opc.get_node(ua.ObjectIds.BaseEventType)
        properties = opcua.common.events.get_event_properties_from_type_node(etype)
        for child in etype.get_properties():
            self.assertTrue(child in properties)

    def test_get_event_from_type_node_CustomEvent(self):
        etype = self.srv.create_custom_event_type(2, 'MyEvent', ua.ObjectIds.AuditEventType, [('PropertyNum', ua.VariantType.Float), ('PropertyString', ua.VariantType.String)])

        properties = opcua.common.events.get_event_properties_from_type_node(etype)

        for child in self.opc.get_node(ua.ObjectIds.BaseEventType).get_properties():
            self.assertTrue(child in properties)
        for child in self.opc.get_node(ua.ObjectIds.AuditEventType).get_properties():
            self.assertTrue(child in properties)
        for child in self.opc.get_node(etype.nodeid).get_properties():
                self.assertTrue(child in properties)

        self.assertTrue(etype.get_child("2:PropertyNum") in properties)
        self.assertTrue(etype.get_child("2:PropertyString") in properties)

    def test_events_default(self):
        evgen = self.srv.get_event_generator()

        myhandler = MySubHandler()
        sub = self.opc.create_subscription(100, myhandler)
        handle = sub.subscribe_events()

        tid = datetime.utcnow()
        msg = "this is my msg "
        evgen.trigger(tid, msg)

        ev = myhandler.future.result()
        self.assertIsNot(ev, None)  # we did not receive event
        self.assertEqual(ev.EventType, ua.NodeId(ua.ObjectIds.BaseEventType))
        self.assertEqual(ev.Severity, 1)
        self.assertEqual(ev.SourceName, self.opc.get_server_node().get_browse_name().Name)
        self.assertEqual(ev.SourceNode, self.opc.get_server_node().nodeid)
        self.assertEqual(ev.Message.Text, msg)
        self.assertEqual(ev.Time, tid)

        # time.sleep(0.1)
        sub.unsubscribe(handle)
        sub.delete()

    def test_events_MyObject(self):
        objects = self.srv.get_objects_node()
        o = objects.add_object(3, 'MyObject')
        evgen = self.srv.get_event_generator(source=o)

        myhandler = MySubHandler()
        sub = self.opc.create_subscription(100, myhandler)
        handle = sub.subscribe_events(o)

        tid = datetime.utcnow()
        msg = "this is my msg "
        evgen.trigger(tid, msg)

        ev = myhandler.future.result(10)
        self.assertIsNot(ev, None)  # we did not receive event
        self.assertEqual(ev.EventType, ua.NodeId(ua.ObjectIds.BaseEventType))
        self.assertEqual(ev.Severity, 1)
        self.assertEqual(ev.SourceName, 'MyObject')
        self.assertEqual(ev.SourceNode, o.nodeid)
        self.assertEqual(ev.Message.Text, msg)
        self.assertEqual(ev.Time, tid)

        # time.sleep(0.1)
        sub.unsubscribe(handle)
        sub.delete()

    def test_events_wrong_source(self):
        objects = self.srv.get_objects_node()
        o = objects.add_object(3, 'MyObject')
        evgen = self.srv.get_event_generator(source=o)

        myhandler = MySubHandler()
        sub = self.opc.create_subscription(100, myhandler)
        handle = sub.subscribe_events()

        tid = datetime.utcnow()
        msg = "this is my msg "
        evgen.trigger(tid, msg)

        with self.assertRaises(TimeoutError):  # we should not receive event
            ev = myhandler.future.result(2)

        # time.sleep(0.1)
        sub.unsubscribe(handle)
        sub.delete()

    def test_events_CustomEvent(self):
        etype = self.srv.create_custom_event_type(2, 'MyEvent', ua.ObjectIds.BaseEventType, [('PropertyNum', ua.VariantType.Float), ('PropertyString', ua.VariantType.String)])
        evgen = self.srv.get_event_generator(etype)

        myhandler = MySubHandler()
        sub = self.opc.create_subscription(100, myhandler)
        handle = sub.subscribe_events(evtypes=etype)

        propertynum = 2
        propertystring = "This is my test"
        evgen.event.PropertyNum = propertynum
        evgen.event.PropertyString = propertystring
        serverity = 500
        evgen.event.Severity = serverity
        tid = datetime.utcnow()
        msg = "this is my msg "
        evgen.trigger(tid, msg)

        ev = myhandler.future.result(10)
        self.assertIsNot(ev, None)  # we did not receive event
        self.assertEqual(ev.EventType, etype.nodeid)
        self.assertEqual(ev.Severity, serverity)
        self.assertEqual(ev.SourceName, self.opc.get_server_node().get_browse_name().Name)
        self.assertEqual(ev.SourceNode, self.opc.get_server_node().nodeid)
        self.assertEqual(ev.Message.Text, msg)
        self.assertEqual(ev.Time, tid)
        self.assertEqual(ev.PropertyNum, propertynum)
        self.assertEqual(ev.PropertyString, propertystring)

        # time.sleep(0.1)
        sub.unsubscribe(handle)
        sub.delete()

    def test_events_CustomEvent_MyObject(self):
        objects = self.srv.get_objects_node()
        o = objects.add_object(3, 'MyObject')
        etype = self.srv.create_custom_event_type(2, 'MyEvent', ua.ObjectIds.BaseEventType, [('PropertyNum', ua.VariantType.Float), ('PropertyString', ua.VariantType.String)])
        evgen = self.srv.get_event_generator(etype, o)

        myhandler = MySubHandler()
        sub = self.opc.create_subscription(100, myhandler)
        handle = sub.subscribe_events(o, etype)

        propertynum = 2
        propertystring = "This is my test"
        evgen.event.PropertyNum = propertynum
        evgen.event.PropertyString = propertystring
        tid = datetime.utcnow()
        msg = "this is my msg "
        evgen.trigger(tid, msg)

        ev = myhandler.future.result(10)
        self.assertIsNot(ev, None)  # we did not receive event
        self.assertEqual(ev.EventType, etype.nodeid)
        self.assertEqual(ev.Severity, 1)
        self.assertEqual(ev.SourceName, 'MyObject')
        self.assertEqual(ev.SourceNode, o.nodeid)
        self.assertEqual(ev.Message.Text, msg)
        self.assertEqual(ev.Time, tid)
        self.assertEqual(ev.PropertyNum, propertynum)
        self.assertEqual(ev.PropertyString, propertystring)

        # time.sleep(0.1)
        sub.unsubscribe(handle)
        sub.delete()

    def test_several_different_events(self):
        objects = self.srv.get_objects_node()
        o = objects.add_object(3, 'MyObject')

        etype1 = self.srv.create_custom_event_type(2, 'MyEvent1', ua.ObjectIds.BaseEventType, [('PropertyNum', ua.VariantType.Float), ('PropertyString', ua.VariantType.String)])
        evgen1 = self.srv.get_event_generator(etype1, o)

        etype2 = self.srv.create_custom_event_type(2, 'MyEvent2', ua.ObjectIds.BaseEventType, [('PropertyNum', ua.VariantType.Float), ('PropertyString', ua.VariantType.String)])
        evgen2 = self.srv.get_event_generator(etype2, o)

        myhandler = MySubHandler2()
        sub = self.opc.create_subscription(100, myhandler)
        handle = sub.subscribe_events(o, etype1)

        propertynum1 = 1
        propertystring1 = "This is my test 1"
        evgen1.event.PropertyNum = propertynum1
        evgen1.event.PropertyString = propertystring1

        propertynum2 = 2
        propertystring2 = "This is my test 2"
        evgen2.event.PropertyNum = propertynum2
        evgen2.event.PropertyString = propertystring2

        for i in range(3):
            evgen1.trigger()
            evgen2.trigger()
        time.sleep(1)

        self.assertEqual(len(myhandler.results), 3)
        ev = myhandler.results[-1]
        self.assertEqual(ev.EventType, etype1.nodeid)

        handle = sub.subscribe_events(o, etype2)
        for i in range(4):
            evgen1.trigger()
            evgen2.trigger()
        time.sleep(1)


        ev1s = [ev for ev in myhandler.results if ev.EventType == etype1.nodeid]
        ev2s = [ev for ev in myhandler.results if ev.EventType == etype2.nodeid]

        self.assertEqual(len(myhandler.results), 11)
        self.assertEqual(len(ev2s), 4)
        self.assertEqual(len(ev1s), 7)

        sub.unsubscribe(handle)
        sub.delete()

    def test_several_different_events_2(self):
        objects = self.srv.get_objects_node()
        o = objects.add_object(3, 'MyObject')

        etype1 = self.srv.create_custom_event_type(2, 'MyEvent1', ua.ObjectIds.BaseEventType, [('PropertyNum', ua.VariantType.Float), ('PropertyString', ua.VariantType.String)])
        evgen1 = self.srv.get_event_generator(etype1, o)

        etype2 = self.srv.create_custom_event_type(2, 'MyEvent2', ua.ObjectIds.BaseEventType, [('PropertyNum2', ua.VariantType.Float), ('PropertyString', ua.VariantType.String)])
        evgen2 = self.srv.get_event_generator(etype2, o)

        etype3 = self.srv.create_custom_event_type(2, 'MyEvent3', ua.ObjectIds.BaseEventType, [('PropertyNum3', ua.VariantType.Float), ('PropertyString', ua.VariantType.String)])
        evgen3 = self.srv.get_event_generator(etype3, o)

        myhandler = MySubHandler2()
        sub = self.opc.create_subscription(100, myhandler)
        handle = sub.subscribe_events(o, [etype1, etype3])

        propertynum1 = 1
        propertystring1 = "This is my test 1"
        evgen1.event.PropertyNum = propertynum1
        evgen1.event.PropertyString = propertystring1

        propertynum2 = 2
        propertystring2 = "This is my test 2"
        evgen2.event.PropertyNum2 = propertynum2
        evgen2.event.PropertyString = propertystring2

        propertynum3 = 3
        propertystring3 = "This is my test 3"
        evgen3.event.PropertyNum3 = propertynum3
        evgen3.event.PropertyString = propertystring2

        for i in range(3):
            evgen1.trigger()
            evgen2.trigger()
            evgen3.trigger()
        evgen3.event.PropertyNum3 = 9999
        evgen3.trigger()
        time.sleep(1)

        ev1s = [ev for ev in myhandler.results if ev.EventType == etype1.nodeid]
        ev2s = [ev for ev in myhandler.results if ev.EventType == etype2.nodeid]
        ev3s = [ev for ev in myhandler.results if ev.EventType == etype3.nodeid]

        self.assertEqual(len(myhandler.results), 7)
        self.assertEqual(len(ev1s), 3)
        self.assertEqual(len(ev2s), 0)
        self.assertEqual(len(ev3s), 4)
        self.assertEqual(ev1s[0].PropertyNum, propertynum1)
        self.assertEqual(ev3s[0].PropertyNum3, propertynum3)
        self.assertEqual(ev3s[-1].PropertyNum3, 9999)
        self.assertEqual(ev1s[0].PropertyNum3, None)

        sub.unsubscribe(handle)
        sub.delete()

