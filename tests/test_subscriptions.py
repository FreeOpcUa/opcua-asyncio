import asyncio
import pytest
from copy import copy
from asyncio import Future, sleep, wait_for, TimeoutError
from datetime import datetime, timedelta

import asyncua
from asyncua import ua

pytestmark = pytest.mark.asyncio

class MySubHandler:
    """
    More advanced subscription client using Future, so we can await events in tests.
    """

    def __init__(self):
        self.future = Future()

    def reset(self):
        self.future = Future()

    async def result(self):
        return await wait_for(self.future, 2)

    def datachange_notification(self, node, val, data):
        if not self.future.done():
            self.future.set_result((node, val, data))

    def event_notification(self, event):
        if not self.future.done():
            self.future.set_result(event)


class MySubHandler2:
    def __init__(self, limit=None):
        self.results = []
        self.limit = limit
        self._done = asyncio.Event()

    async def done(self):
        return await wait_for(self._done.wait(), 2)

    def check_done(self):
        if self.limit and len(self.results) == self.limit and not self._done.is_set():
            self._done.set()

    def datachange_notification(self, node, val, data):
        self.results.append((node, val))
        self.check_done()

    def event_notification(self, event):
        self.results.append(event)
        self.check_done()


class MySubHandlerCounter:
    def __init__(self):
        self.datachange_count = 0
        self.event_count = 0

    def datachange_notification(self, node, val, data):
        self.datachange_count += 1

    def event_notification(self, event):
        self.event_count += 1


class MySubHandlerCounterAsync(MySubHandlerCounter):
    async def datachange_notification(self, node, val, data):
        self.datachange_count += 1

    async def event_notification(self, event):
        self.event_count += 1


async def test_subscription_failure(opc):
    myhandler = MySubHandler()
    o = opc.opc.nodes.objects
    sub = await opc.opc.create_subscription(100, myhandler)
    with pytest.raises(ua.UaStatusCodeError):
        # we can only subscribe to variables so this should fail
        await sub.subscribe_data_change(o)
    await sub.delete()


@pytest.mark.parametrize("handler_class", [MySubHandlerCounter, MySubHandlerCounterAsync])
async def test_subscription_overload(opc, handler_class):
    nb = 10
    myhandler = handler_class()
    o = opc.opc.nodes.objects
    sub = await opc.opc.create_subscription(1, myhandler)
    variables = []
    subs = []
    for i in range(nb):
        v = await o.add_variable(3, f'SubscriptionVariableOverload{i}', 99)
        variables.append(v)
    for i in range(nb):
        await sub.subscribe_data_change(variables)
    for i in range(nb):
        for j in range(nb):
            await variables[i].write_value(j)
        s = await opc.opc.create_subscription(1, myhandler)
        await s.subscribe_data_change(variables)
        subs.append(s)
        await sub.subscribe_data_change(variables[i])
    for i in range(nb):
        for j in range(nb):
            await variables[i].write_value(j)
    # await asyncio.sleep(4)
    await sub.delete()
    for s in subs:
        await s.delete()
    # assert myhandler.datachange_count == 1000
    # assert myhandler.event_count == 0


@pytest.mark.parametrize("handler_class", [MySubHandlerCounter, MySubHandlerCounterAsync])
async def test_subscription_count(opc, handler_class):
    myhandler = handler_class()
    sub = await opc.opc.create_subscription(1, myhandler)
    o = opc.opc.nodes.objects
    var = await o.add_variable(3, 'SubVarCounter', 0.1)
    await sub.subscribe_data_change(var)
    nb = 100
    for i in range(nb):
        val = await var.read_value()
        await var.write_value(val + 1)
    await sleep(0.2)  # let last event arrive
    assert nb + 1 == myhandler.datachange_count
    await sub.delete()


@pytest.mark.parametrize("handler_class", [MySubHandlerCounter, MySubHandlerCounterAsync])
async def test_subscription_count_list(opc, handler_class):
    myhandler = handler_class()
    sub = await opc.opc.create_subscription(1, myhandler)
    o = opc.opc.nodes.objects
    var = await o.add_variable(3, 'SubVarCounter', [0.1, 0.2])
    await sub.subscribe_data_change(var)
    nb = 12
    for i in range(nb):
        val = await var.read_value()
        #  we do not want to modify object in our db, we need a copy in order to generate event
        val = copy(val)
        val.append(i)
        await var.write_value(copy(val))
    await sleep(0.2)  # let last event arrive
    assert nb + 1 == myhandler.datachange_count
    await sub.delete()


@pytest.mark.parametrize("handler_class", [MySubHandlerCounter, MySubHandlerCounterAsync])
async def test_subscription_count_no_change(opc, handler_class):
    myhandler = handler_class()
    sub = await opc.opc.create_subscription(1, myhandler)
    o = opc.opc.nodes.objects
    var = await o.add_variable(3, 'SubVarCounter', [0.1, 0.2])
    await sub.subscribe_data_change(var)
    nb = 12
    for i in range(nb):
        val = await var.read_value()
        await var.write_value(val)
    await sleep(0.2)  # let last event arrive
    assert 1 == myhandler.datachange_count
    await sub.delete()


@pytest.mark.parametrize("handler_class", [MySubHandlerCounter, MySubHandlerCounterAsync])
async def test_subscription_count_empty(opc, handler_class):
    myhandler = handler_class()
    sub = await opc.opc.create_subscription(1, myhandler)
    o = opc.opc.nodes.objects
    var = await o.add_variable(3, 'SubVarCounter', [0.1, 0.2, 0.3])
    await sub.subscribe_data_change(var)
    while True:
        val = await var.read_value()
        # we do not want to modify object in our db, we need a copy in order to generate event
        val = copy(val)
        val.pop()
        await var.write_value(val, ua.VariantType.Double)
        if not val:
            break
    await sleep(0.2)  # let last event arrive
    assert 4 == myhandler.datachange_count
    await sub.delete()


async def test_subscription_overload_simple(opc):
    nb = 10
    myhandler = MySubHandler()
    o = opc.opc.nodes.objects
    sub = await opc.opc.create_subscription(1, myhandler)
    variables = []
    for i in range(nb):
        variables.append(await o.add_variable(3, f'SubVarOverload{i}', i))
    for i in range(nb):
        await sub.subscribe_data_change(variables)
    await sub.delete()


async def test_subscription_data_change(opc):
    """
    test subscriptions. This is far too complicated for
    a unittest but, setting up subscriptions requires a lot
    of code, so when we first set it up, it is best
    to test as many things as possible
    """
    myhandler = MySubHandler()
    o = opc.opc.nodes.objects
    # subscribe to a variable
    startv1 = [1, 2, 3]
    v1 = await o.add_variable(3, 'SubscriptionVariableV1', startv1)
    sub = await opc.opc.create_subscription(100, myhandler)
    handle1 = await sub.subscribe_data_change(v1)
    # Now check we get the start value
    node, val, data = await myhandler.result()
    assert startv1 == val
    assert v1 == node
    myhandler.reset()  # reset future object
    # modify v1 and check we get value
    await v1.write_value([5])
    node, val, data = await myhandler.result()
    assert v1 == node
    assert [5] == val
    with pytest.raises(ua.UaStatusCodeError):
        await sub.unsubscribe(999)  # non existing handle
    await sub.unsubscribe(handle1)
    with pytest.raises(ua.UaStatusCodeError):
        await sub.unsubscribe(handle1)  # second try should fail
    await sub.delete()
    with pytest.raises(ua.UaStatusCodeError):
        await sub.unsubscribe(handle1)  # sub does not exist anymore


async def test_subscription_data_change_bool(opc):
    """
    test subscriptions. This is far too complicated for
    a unittest but, setting up subscriptions requires a lot
    of code, so when we first set it up, it is best
    to test as many things as possible
    """
    myhandler = MySubHandler()
    o = opc.opc.nodes.objects
    # subscribe to a variable
    startv1 = True
    v1 = await o.add_variable(3, 'SubscriptionVariableBool', startv1)
    sub = await opc.opc.create_subscription(100, myhandler)
    handle1 = await sub.subscribe_data_change(v1)
    # Now check we get the start value
    node, val, data = await myhandler.result()
    assert startv1 == val
    assert v1 == node
    myhandler.reset()  # reset future object
    # modify v1 and check we get value
    await v1.write_value(False)
    node, val, data = await myhandler.result()
    assert v1 == node
    assert val is False
    await sub.delete()  # should delete our monitoreditem too


async def test_subscription_data_change_many(opc):
    """
    test subscriptions. This is far too complicated for
    a unittest but, setting up subscriptions requires a lot
    of code, so when we first set it up, it is best
    to test as many things as possible
    """
    myhandler = MySubHandler2()
    o = opc.opc.nodes.objects
    startv1 = True
    v1 = await o.add_variable(3, 'SubscriptionVariableMany1', startv1)
    startv2 = [1.22, 1.65]
    v2 = await o.add_variable(3, 'SubscriptionVariableMany2', startv2)
    sub = await opc.opc.create_subscription(100, myhandler)
    handle1, handle2 = await sub.subscribe_data_change([v1, v2])
    # Now check we get the start values
    nodes = [v1, v2]
    count = 0
    while not len(myhandler.results) > 1:
        count += 1
        await sleep(0.1)
        if count > 100:
            raise RuntimeError("Did not get result from subscription")
    for node, val in myhandler.results:
        assert node in nodes
        nodes.remove(node)
        if node == v1:
            assert val == startv1
        elif node == v2:
            assert val == startv2
        else:
            raise RuntimeError(f"Error node {node} is neither {v1} nor {v2}")
    await sub.delete()


async def test_subscribe_server_time(opc):
    """
    Test the subscription of the `Server_ServerStatus_CurrentTime` objects `Value` attribute.
    """
    myhandler = MySubHandler()
    server_time_node = opc.opc.get_node(ua.NodeId(ua.ObjectIds.Server_ServerStatus_CurrentTime))
    sub = await opc.opc.create_subscription(200, myhandler)
    handle = await sub.subscribe_data_change(server_time_node)
    assert type(handle) is int
    node, val, data = await myhandler.result()
    assert server_time_node == node
    delta = datetime.utcnow() - val
    assert delta < timedelta(seconds=2)
    await sub.unsubscribe(handle)
    await sub.delete()


async def test_modify_monitored_item(opc):
    """
    Test that the subscription of the `Server_ServerStatus_CurrentTime` object can be modified.
    """
    myhandler = MySubHandler()
    server_time_node = opc.opc.get_node(ua.NodeId(ua.ObjectIds.Server_ServerStatus_CurrentTime))
    sub = await opc.opc.create_subscription(1000, myhandler)
    handle = await sub.subscribe_data_change(server_time_node)
    await myhandler.result()
    myhandler.reset()
    results = await sub.modify_monitored_item(handle, 2000)
    assert results
    assert len(results) == 1
    assert type(results[0]) == ua.MonitoredItemModifyResult
    assert results[0].RevisedSamplingInterval == 2000
    await sub.unsubscribe(handle)
    await sub.delete()


async def test_create_delete_subscription(opc):
    o = opc.opc.nodes.objects
    v = await o.add_variable(3, 'SubscriptionVariable', [1, 2, 3])
    sub = await opc.opc.create_subscription(100, MySubHandler())
    handle = await sub.subscribe_data_change(v)
    await sleep(0.1)
    await sub.unsubscribe(handle)
    await sub.delete()


async def test_unsubscribe_two_objects_simultaneously(opc):
    """
    Test the subscription/unsub. of the `ServerStatus_StartTime` and `ServerStatus_State` objects.
    Unsubscribe from both Nodes simultaneously.
    """
    handler = MySubHandler2(limit=1)
    nodes = [
        opc.opc.get_node(ua.NodeId(ua.ObjectIds.Server_ServerStatus_StartTime)),
        opc.opc.get_node(ua.NodeId(ua.ObjectIds.Server_ServerStatus_State)),
    ]
    sub = await opc.opc.create_subscription(100, handler)
    handles = await sub.subscribe_data_change(nodes, queuesize=1)
    await handler.done()
    assert handler.results[0][0] == nodes[0]
    assert handler.results[1][0] == nodes[1]
    await sub.unsubscribe(handles)
    await sub.delete()


async def test_unsubscribe_two_objects_consecutively(opc):
    """
    Test the subscription/unsub. of the `ServerStatus_StartTime` and `ServerStatus_State` objects.
    Unsubscribe from both Nodes consecutively.
    """
    handler = MySubHandler2(limit=1)
    nodes = [
        opc.opc.get_node(ua.NodeId(ua.ObjectIds.Server_ServerStatus_StartTime)),
        opc.opc.get_node(ua.NodeId(ua.ObjectIds.Server_ServerStatus_State)),
    ]
    sub = await opc.opc.create_subscription(100, handler)
    handles = await sub.subscribe_data_change(nodes, queuesize=1)
    assert type(handles) is list
    await handler.done()
    for handle in handles:
        await sub.unsubscribe(handle)
    await sub.delete()


async def test_subscribe_events(opc):
    sub = await opc.opc.create_subscription(100, MySubHandler())
    handle = await sub.subscribe_events()
    await sleep(0.1)
    await sub.unsubscribe(handle)
    await sub.delete()


async def test_subscribe_events_to_wrong_node(opc):
    sub = await opc.opc.create_subscription(100, MySubHandler())
    with pytest.raises(ua.UaStatusCodeError):
        handle = await sub.subscribe_events(opc.opc.get_node("i=85"))
    o = opc.opc.nodes.objects
    v = await o.add_variable(3, 'VariableNoEventNofierAttribute', 4)
    with pytest.raises(ua.UaStatusCodeError):
        handle = await sub.subscribe_events(v)
    await sub.delete()


async def test_get_event_from_type_node_BaseEvent(opc):
    etype = opc.opc.get_node(ua.ObjectIds.BaseEventType)
    properties = await asyncua.common.events.get_event_properties_from_type_node(etype)
    for child in await etype.get_properties():
        assert child in properties


async def test_get_event_from_type_node_CustomEvent(opc):
    etype = await opc.server.create_custom_event_type(
        2, 'MyEvent', ua.ObjectIds.AuditEventType,
        [('PropertyNum', ua.VariantType.Float), ('PropertyString', ua.VariantType.String)]
    )
    properties = await asyncua.common.events.get_event_properties_from_type_node(etype)
    for child in await opc.opc.get_node(ua.ObjectIds.BaseEventType).get_properties():
        assert child in properties
    for child in await opc.opc.get_node(ua.ObjectIds.AuditEventType).get_properties():
        assert child in properties
    for child in await opc.opc.get_node(etype.nodeid).get_properties():
        assert child in properties
    assert await etype.get_child("2:PropertyNum") in properties
    assert await etype.get_child("2:PropertyString") in properties


async def test_events_default(opc):
    evgen = await opc.server.get_event_generator()
    myhandler = MySubHandler()
    sub = await opc.opc.create_subscription(100, myhandler)
    handle = await sub.subscribe_events()
    tid = datetime.utcnow()
    msg = "this is my msg "
    await evgen.trigger(tid, msg)
    ev = await myhandler.result()
    assert ev is not None  # we did not receive event
    assert ua.NodeId(ua.ObjectIds.BaseEventType) == ev.EventType
    assert 1 == ev.Severity
    assert (await opc.opc.nodes.server.read_browse_name()).Name == ev.SourceName
    assert opc.opc.nodes.server.nodeid == ev.SourceNode
    assert msg == ev.Message.Text
    assert tid == ev.Time
    await sub.unsubscribe(handle)
    await sub.delete()


async def test_events_MyObject(opc):
    objects = opc.server.nodes.objects
    o = await objects.add_object(3, 'MyObject')
    evgen = await opc.server.get_event_generator(emitting_node=o)
    myhandler = MySubHandler()
    sub = await opc.opc.create_subscription(100, myhandler)
    handle = await sub.subscribe_events(o)
    tid = datetime.utcnow()
    msg = "this is my msg "
    await evgen.trigger(tid, msg)
    ev = await myhandler.result()
    assert ev is not None  # we did not receive event
    assert ua.NodeId(ua.ObjectIds.BaseEventType) == ev.EventType
    assert 1 == ev.Severity
    assert 'MyObject' == ev.SourceName
    assert o.nodeid == ev.SourceNode
    assert msg == ev.Message.Text
    assert tid == ev.Time
    await sub.unsubscribe(handle)
    await sub.delete()


async def test_events_wrong_source(opc):
    objects = opc.server.nodes.objects
    o = await objects.add_object(3, 'MyObject')
    o2 = await objects.add_object(3, 'MyObject2')
    evgen = await opc.server.get_event_generator(emitting_node=o)
    evgen2 = await opc.server.get_event_generator(2782, emitting_node=o2)
    myhandler = MySubHandler()
    sub = await opc.opc.create_subscription(100, myhandler)
    handle = await sub.subscribe_events(o2)
    tid = datetime.utcnow()
    msg = "this is my msg "
    await evgen.trigger(tid, msg)
    with pytest.raises(TimeoutError):  # we should not receive event
        ev = await myhandler.result()
    await sub.unsubscribe(handle)
    await sub.delete()


async def test_events_CustomEvent(opc):
    etype = await opc.server.create_custom_event_type(2, 'MyEvent', ua.ObjectIds.BaseEventType,
        [('PropertyNum', ua.VariantType.Float),
            ('PropertyString', ua.VariantType.String)])
    evgen = await opc.server.get_event_generator(etype)
    myhandler = MySubHandler()
    sub = await opc.opc.create_subscription(100, myhandler)
    handle = await sub.subscribe_events(evtypes=etype)
    propertynum = 2
    propertystring = "This is my test"
    evgen.event.PropertyNum = propertynum
    evgen.event.PropertyString = propertystring
    serverity = 500
    evgen.event.Severity = serverity
    tid = datetime.utcnow()
    msg = "this is my msg "
    await evgen.trigger(tid, msg)
    ev = await myhandler.result()
    assert ev is not None  # we did not receive event
    assert etype.nodeid == ev.EventType
    assert serverity == ev.Severity
    assert (await opc.opc.nodes.server.read_browse_name()).Name == ev.SourceName
    assert opc.opc.nodes.server.nodeid == ev.SourceNode
    assert msg == ev.Message.Text
    assert tid == ev.Time
    assert propertynum == ev.PropertyNum
    assert propertystring == ev.PropertyString
    await sub.unsubscribe(handle)
    await sub.delete()


async def test_events_CustomEvent_MyObject(opc):
    objects = opc.server.nodes.objects
    o = await objects.add_object(3, 'MyObject')
    etype = await opc.server.create_custom_event_type(2, 'MyEvent', ua.ObjectIds.BaseEventType,
        [('PropertyNum', ua.VariantType.Float),
            ('PropertyString', ua.VariantType.String)])
    evgen = await opc.server.get_event_generator(etype, emitting_node=o)
    myhandler = MySubHandler()
    sub = await opc.opc.create_subscription(100, myhandler)
    handle = await sub.subscribe_events(o, etype)
    propertynum = 2
    propertystring = "This is my test"
    evgen.event.PropertyNum = propertynum
    evgen.event.PropertyString = propertystring
    tid = datetime.utcnow()
    msg = "this is my msg "
    await evgen.trigger(tid, msg)
    ev = await myhandler.result()
    assert ev is not None  # we did not receive event
    assert etype.nodeid == ev.EventType
    assert 1 == ev.Severity
    assert 'MyObject' == ev.SourceName
    assert o.nodeid == ev.SourceNode
    assert msg == ev.Message.Text
    assert tid == ev.Time
    assert propertynum == ev.PropertyNum
    assert propertystring == ev.PropertyString
    await sub.unsubscribe(handle)
    await sub.delete()


async def test_several_different_events(opc):
    objects = opc.server.nodes.objects
    o = await objects.add_object(3, 'MyObject')
    etype1 = await opc.server.create_custom_event_type(2, 'MyEvent1', ua.ObjectIds.BaseEventType,
        [('PropertyNum', ua.VariantType.Float),
            ('PropertyString', ua.VariantType.String)])
    evgen1 = await opc.server.get_event_generator(etype1, o)
    etype2 = await opc.server.create_custom_event_type(2, 'MyEvent2', ua.ObjectIds.BaseEventType,
        [('PropertyNum', ua.VariantType.Float),
            ('PropertyString', ua.VariantType.String)])
    evgen2 = await opc.server.get_event_generator(etype2, o)
    myhandler = MySubHandler2()
    sub = await opc.opc.create_subscription(100, myhandler)
    handle = await sub.subscribe_events(o, etype1)
    propertynum1 = 1
    propertystring1 = "This is my test 1"
    evgen1.event.PropertyNum = propertynum1
    evgen1.event.PropertyString = propertystring1
    propertynum2 = 2
    propertystring2 = "This is my test 2"
    evgen2.event.PropertyNum = propertynum2
    evgen2.event.PropertyString = propertystring2
    for i in range(3):
        await evgen1.trigger()
        await evgen2.trigger()
    await sleep(1)  # ToDo: replace
    assert 3 == len(myhandler.results)
    ev = myhandler.results[-1]
    assert etype1.nodeid == ev.EventType
    handle = await sub.subscribe_events(o, etype2)
    for i in range(4):
        await evgen1.trigger()
        await evgen2.trigger()
    await sleep(1)  # ToDo: replace
    ev1s = [ev for ev in myhandler.results if ev.EventType == etype1.nodeid]
    ev2s = [ev for ev in myhandler.results if ev.EventType == etype2.nodeid]
    assert 11 == len(myhandler.results)
    assert 4 == len(ev2s)
    assert 7 == len(ev1s)
    await sub.unsubscribe(handle)
    await sub.delete()


async def test_several_different_events_2(opc):
    objects = opc.server.nodes.objects
    o = await objects.add_object(3, 'MyObject')
    etype1 = await opc.server.create_custom_event_type(
        2, 'MyEvent1', ua.ObjectIds.BaseEventType,
        [('PropertyNum', ua.VariantType.Float), ('PropertyString', ua.VariantType.String)]
    )
    evgen1 = await opc.server.get_event_generator(etype1, o)
    etype2 = await opc.server.create_custom_event_type(
        2, 'MyEvent2', ua.ObjectIds.BaseEventType,
        [('PropertyNum2', ua.VariantType.Float), ('PropertyString', ua.VariantType.String)]
    )
    evgen2 = await opc.server.get_event_generator(etype2, o)
    etype3 = await opc.server.create_custom_event_type(
        2, 'MyEvent3', ua.ObjectIds.BaseEventType,
        [('PropertyNum3', ua.VariantType.Float), ('PropertyString', ua.VariantType.String)]
    )
    evgen3 = await opc.server.get_event_generator(etype3, o)
    myhandler = MySubHandler2()
    sub = await opc.opc.create_subscription(100, myhandler)
    handle = await sub.subscribe_events(o, [etype1, etype3])
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
        await evgen1.trigger()
        await evgen2.trigger()
        await evgen3.trigger()
    evgen3.event.PropertyNum3 = 9999
    await evgen3.trigger()
    await sleep(1)
    ev1s = [ev for ev in myhandler.results if ev.EventType == etype1.nodeid]
    ev2s = [ev for ev in myhandler.results if ev.EventType == etype2.nodeid]
    ev3s = [ev for ev in myhandler.results if ev.EventType == etype3.nodeid]
    assert 7 == len(myhandler.results)
    assert 3 == len(ev1s)
    assert 0 == len(ev2s)
    assert 4 == len(ev3s)
    assert propertynum1 == ev1s[0].PropertyNum
    assert propertynum3 == ev3s[0].PropertyNum3
    assert 9999 == ev3s[-1].PropertyNum3
    assert ev1s[0].PropertyNum3 is None
    await sub.unsubscribe(handle)
    await sub.delete()


async def test_internal_server_subscription(opc):
    """
    Test that an internal server subscription is handled correctly when
    data of a node changes (by external client and internally).
    """
    sub_handler = MySubHandler2()
    uri = 'http://examples.freeopcua.github.io'
    idx = await opc.server.register_namespace(uri)
    objects = opc.server.nodes.objects
    sub_obj = await objects.add_object(idx, 'SubTestObject')
    sub_var = await sub_obj.add_variable(idx, 'SubTestVariable', 0)
    sub = await opc.server.create_subscription(1, sub_handler)
    # Server subscribes to own variable data changes
    await sub.subscribe_data_change([sub_var])
    client_var = await opc.opc.nodes.objects.get_child([f"{idx}:SubTestObject", f"{idx}:SubTestVariable"])
    for i in range(10):
        await client_var.write_value(i)
        await asyncio.sleep(0.01)
    assert [v for n, v in sub_handler.results] == list(range(10))
    internal_sub = opc.server.iserver.subscription_service.subscriptions[sub.subscription_id]
    # Check that the results are not left un-acknowledged on internal Server Subscriptions.
    assert len(internal_sub._not_acknowledged_results) == 0
