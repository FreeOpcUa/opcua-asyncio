import sys
import asyncio
import pytest
from copy import copy
from asyncio import Future, sleep, wait_for, TimeoutError
from datetime import datetime, timedelta, timezone
from asyncua.common.subscription import Subscription
try:
    from unittest.mock import AsyncMock
except ImportError:
    from asynctest import CoroutineMock as AsyncMock  # type: ignore[no-redef]
import asyncua
from asyncua import ua, Client

from .conftest import Opc


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
    if sys.version_info.major == 3 and sys.version_info.minor == 7:
        pytest.skip("this test seems to be hanging in version 3.7.x")

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
    await opc.opc.delete_nodes(variables)


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
    await opc.opc.delete_nodes([var])


@pytest.mark.parametrize("handler_class", [MySubHandlerCounter, MySubHandlerCounterAsync])
async def test_subscription_count_list(opc, handler_class):
    myhandler = handler_class()
    sub = await opc.opc.create_subscription(1, myhandler)
    o = opc.opc.nodes.objects
    var = await o.add_variable(3, 'SubVarCounter1', [0.1, 0.2])
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
    await opc.opc.delete_nodes([var])


@pytest.mark.parametrize("handler_class", [MySubHandlerCounter, MySubHandlerCounterAsync])
async def test_subscription_count_no_change(opc, handler_class):
    myhandler = handler_class()
    sub = await opc.opc.create_subscription(1, myhandler)
    o = opc.opc.nodes.objects
    var = await o.add_variable(3, 'SubVarCounter2', [0.1, 0.2])
    await sub.subscribe_data_change(var)
    nb = 12
    for i in range(nb):
        val = await var.read_value()
        await var.write_value(val)
    await sleep(0.2)  # let last event arrive
    assert 1 == myhandler.datachange_count
    await sub.delete()
    await opc.opc.delete_nodes([var])


@pytest.mark.parametrize("handler_class", [MySubHandlerCounter, MySubHandlerCounterAsync])
async def test_subscription_count_empty(opc, handler_class):
    myhandler = handler_class()
    sub = await opc.opc.create_subscription(1, myhandler)
    o = opc.opc.nodes.objects
    var = await o.add_variable(3, 'SubVarCounter3', [0.1, 0.2, 0.3])
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
    await opc.opc.delete_nodes([var])


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
    await opc.opc.delete_nodes([v1])


async def test_subscription_monitored_item(opc: Opc):
    """
    test subscriptions with a monitored item with a datachange filter.

    filter is Trigger=ua.DataChangeTrigger.StatusValueTimestamp (Part 4 7.17.2 DataChangeFilter)
    """
    myhandler = MySubHandler()
    o = opc.opc.nodes.objects
    # subscribe to a variable, adding the variable will also set a sourcetimestamp on the value
    startv1 = [1, 2, 3]
    v1 = await o.add_variable(3, 'SubscriptionVariableV1', startv1)
    sub: Subscription = await opc.opc.create_subscription(100, myhandler)

    mfilter = ua.DataChangeFilter(Trigger=ua.DataChangeTrigger.StatusValueTimestamp)

    # For creating monitor items create_monitored_items is availablem, but that one is not very easy in use.
    # So use the internal function instead.
    # TODO: Should there be an easy shorthand for making monitored items with filter?
    handles = await sub._subscribe(nodes=v1, mfilter=mfilter)

    # # Now check we get the start value
    node, val, data = await myhandler.result()
    assert startv1 == val
    assert v1 == node
    myhandler.reset()  # reset future object

    # modify v1 and check we get value
    # Instead of  v1.write_value([5]) use the datavalue to prevent setting a source stamp
    await v1.write_value(ua.DataValue([5]))

    # first change will trigger an event (now the new sourcetimestamp becomes not set)
    node, val, data = await myhandler.result()
    assert v1 == node
    assert [5] == val
    myhandler.reset()  # reset future object

    # second update; again use the datavalue to prevent setting a source stamp
    await v1.write_value(ua.DataValue([6]))

    # seccond change will trigger based on value (no change in sourcetimestamp)
    node, val, data = await myhandler.result()
    assert v1 == node
    assert [6] == val

    await sub.unsubscribe(handles)  # typing issues
    await sub.delete()
    await opc.opc.delete_nodes([v1])


@pytest.mark.parametrize("opc", ["client"], indirect=True)
async def test_create_subscription_publishing(opc):
    """
    Test the publishing argument is set during subscription creation
    """
    myhandler = MySubHandler()
    o = opc.opc.nodes.objects
    _ = await o.add_variable(3, 'SubscriptionVariable', 123)
    # publishing default to True
    sub = await opc.opc.create_subscription(100, myhandler)
    assert sub.parameters.PublishingEnabled
    sub = await opc.opc.create_subscription(100, myhandler, publishing=False)
    assert not sub.parameters.PublishingEnabled


@pytest.mark.parametrize("opc", ["client"], indirect=True)
async def test_set_monitoring_mode(opc, mocker):
    """
    test set_monitoring_mode parameter for all MIs of a subscription
    """
    myhandler = MySubHandler()
    o = opc.opc.nodes.objects
    monitoring_mode = ua.SetMonitoringModeParameters()
    _ = mocker.patch.object(ua, "SetMonitoringModeParameters", return_value=monitoring_mode)
    _ = mocker.patch("asyncua.client.ua_client.UaClient.set_monitoring_mode", new=AsyncMock())
    _ = await o.add_variable(3, 'SubscriptionVariable2', 123)
    sub = await opc.opc.create_subscription(100, myhandler)

    await sub.set_monitoring_mode(ua.MonitoringMode.Disabled)
    assert monitoring_mode.MonitoringMode == ua.MonitoringMode.Disabled

    await sub.set_monitoring_mode(ua.MonitoringMode.Reporting)
    assert monitoring_mode.MonitoringMode == ua.MonitoringMode.Reporting


@pytest.mark.parametrize("opc", ["client"], indirect=True)
async def test_set_publishing_mode(opc, mocker):
    """
    test flipping the publishing parameter for an existing subscription
    """
    myhandler = MySubHandler()
    o = opc.opc.nodes.objects
    publishing_mode = ua.SetPublishingModeParameters()
    _ = mocker.patch.object(ua, "SetPublishingModeParameters", return_value=publishing_mode)
    _ = mocker.patch("asyncua.client.ua_client.UaClient.set_publishing_mode", new=AsyncMock())
    _ = await o.add_variable(3, 'SubscriptionVariable3', 123)
    sub = await opc.opc.create_subscription(100, myhandler)

    await sub.set_publishing_mode(False)
    assert not publishing_mode.PublishingEnabled

    await sub.set_publishing_mode(True)
    assert publishing_mode.PublishingEnabled


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
    _ = await sub.subscribe_data_change(v1)
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
    await opc.opc.delete_nodes([v1])


async def test_subscription_data_change_complex(opc):
    """
    test subscriptions. This is far too complicated for
    a unittest but, setting up subscriptions requires a lot
    of code, so when we first set it up, it is best
    to test as many things as possible.
    Check if a mutable object is handeled corretly
    """
    myhandler = MySubHandler()
    o = opc.opc.nodes.objects
    # subscribe to a variable
    startv1 = ua.BuildInfo('ABC')
    v1 = await o.add_variable(3, 'SubscriptionVariableLoc', startv1)
    sub = await opc.opc.create_subscription(100, myhandler)
    _ = await sub.subscribe_data_change(v1)
    # Now check we get the start value
    node, val, data = await myhandler.result()
    assert startv1 == val
    assert v1 == node
    myhandler.reset()  # reset future object
    # modify v1 and check we get value
    startv1.ProductUri = 'BB'
    await v1.write_value(startv1)
    node, val, data = await myhandler.result()
    assert v1 == node
    assert startv1 == val
    assert val.ProductUri == 'BB'
    await sub.delete()  # should delete our monitoreditem too
    await opc.opc.delete_nodes([v1])


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
    await opc.opc.delete_nodes([v1, v2])


def test_get_keepalive_count(mocker):
    """
    Check the subscription parameter MaxKeepAliveCount value
    with various publishInterval and session_timeout values.
    """

    c = Client("opc.tcp://fake")
    # session timeout < publish_interval
    publish_interval = 1000  # ms
    c.session_timeout = 30000  # ms
    keepalive_count = c.get_keepalive_count(publish_interval)
    assert keepalive_count == 22
    # session_timeout > publish_interval
    publish_interval = 75000
    c.session_timeout = 30000
    keepalive_count = c.get_keepalive_count(publish_interval)
    assert keepalive_count == 0
    # RequestedPublishingInterval == 0
    publish_interval = 0
    keepalive_count = c.get_keepalive_count(publish_interval)
    assert keepalive_count == 22


async def test_subscribe_server_time(opc):
    """
    Test the subscription of the `Server_ServerStatus_CurrentTime` objects `Value` attribute.
    """
    myhandler = MySubHandler()
    server_time_node = opc.opc.get_node(ua.NodeId(ua.ObjectIds.Server_ServerStatus_CurrentTime))
    sub = await opc.opc.create_subscription(200, myhandler)
    handle = await sub.subscribe_data_change(server_time_node)
    assert isinstance(handle, int)
    node, val, data = await myhandler.result()
    assert server_time_node == node
    delta = datetime.now(timezone.utc) - val
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
    assert type(results[0]) is ua.MonitoredItemModifyResult
    assert results[0].RevisedSamplingInterval == 2000
    await sub.unsubscribe(handle)
    await sub.delete()


async def test_create_delete_subscription(opc):
    o = opc.opc.nodes.objects
    v = await o.add_variable(3, 'SubscriptionVariable4', [1, 2, 3])
    sub = await opc.opc.create_subscription(100, MySubHandler())
    handle = await sub.subscribe_data_change(v)
    await sleep(0.1)
    await sub.unsubscribe(handle)
    await sub.delete()
    await opc.opc.delete_nodes([v])


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
    assert isinstance(handles, list)
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
        _ = await sub.subscribe_events(opc.opc.get_node("i=85"))
    o = opc.opc.nodes.objects
    v = await o.add_variable(3, 'VariableNoEventNofierAttribute', 4)
    with pytest.raises(ua.UaStatusCodeError):
        _ = await sub.subscribe_events(v)
    await sub.delete()
    await opc.opc.delete_nodes([v])


async def test_get_event_attributes_from_type_node_BaseEvent(opc):
    etype = opc.opc.get_node(ua.ObjectIds.BaseEventType)
    properties = await asyncua.common.events.get_event_properties_from_type_node(etype)
    for child in await etype.get_properties():
        assert child in properties


async def test_get_event_attributes_from_type_node_AlarmConditionType(opc):
    alarmType = opc.opc.get_node(ua.ObjectIds.AlarmConditionType)
    ackType = opc.opc.get_node(ua.ObjectIds.AcknowledgeableConditionType)
    condType = opc.opc.get_node(ua.ObjectIds.ConditionType)
    baseType = opc.opc.get_node(ua.ObjectIds.BaseEventType)
    allProperties = await asyncua.common.events.get_event_properties_from_type_node(alarmType)
    propertiesToCheck = await alarmType.get_properties()
    propertiesToCheck.extend(await ackType.get_properties())
    propertiesToCheck.extend(await condType.get_properties())
    propertiesToCheck.extend(await baseType.get_properties())
    for child in propertiesToCheck:
        assert child in allProperties
    allVariables = await asyncua.common.events.get_event_variables_from_type_node(alarmType)
    variablesToCheck = await alarmType.get_variables()
    variablesToCheck.extend(await ackType.get_variables())
    variablesToCheck.extend(await condType.get_variables())
    variablesToCheck.extend(await baseType.get_variables())
    for child in await alarmType.get_variables():
        assert child in allVariables


async def test_get_filter(opc):
    auditType = opc.opc.get_node(ua.ObjectIds.AuditEventType)
    baseType = opc.opc.get_node(ua.ObjectIds.BaseEventType)
    properties = await baseType.get_properties()
    properties.extend(await auditType.get_properties())
    evfilter = await asyncua.common.events.get_filter_from_event_type([auditType])
    # Check number of elements in select clause
    assert len(evfilter.SelectClauses) == len(properties)


async def test_get_filter_from_ConditionType(opc):
    condType = opc.opc.get_node(ua.ObjectIds.ConditionType)
    baseType = opc.opc.get_node(ua.ObjectIds.BaseEventType)
    properties = await baseType.get_properties()
    properties.extend(await condType.get_properties())
    variables = await baseType.get_variables()
    variables.extend(await condType.get_variables())
    subproperties = []
    for var in variables:
        subproperties.extend(await var.get_properties())
    evfilter = await asyncua.common.events.get_filter_from_event_type([condType])
    # Check number of elements in select clause
    assert len(evfilter.SelectClauses) == (len(properties) + len(variables) + len(subproperties) + 1)
    # Check browse path variable with property
    browsePathList = [o.BrowsePath for o in evfilter.SelectClauses if o.BrowsePath]
    browsePathEnabledState = [ua.uatypes.QualifiedName("EnabledState")]
    browsePathEnabledStateId = [ua.uatypes.QualifiedName("EnabledState"), ua.uatypes.QualifiedName("Id")]
    assert browsePathEnabledState in browsePathList
    assert browsePathEnabledStateId in browsePathList
    # Check for additional NodeId attribute, which is not directly contained in ConditionType
    assert len([o for o in evfilter.SelectClauses if o.AttributeId == ua.AttributeIds.NodeId]) == 1
    # Check some subtypes in where clause
    alarmType = opc.opc.get_node(ua.ObjectIds.AlarmConditionType)
    systemType = opc.opc.get_node(ua.ObjectIds.SystemOffNormalAlarmType)
    filterOperands = evfilter.WhereClause.Elements[0].FilterOperands
    operandNodeIds = [f.Value.Value for f in filterOperands if type(f) is ua.uaprotocol_auto.LiteralOperand]
    assert alarmType.nodeid in operandNodeIds
    assert systemType.nodeid in operandNodeIds


async def test_get_event_contains_object(opc):
    """ Shelving State is a object this should be in the filter list!"""
    alarm_type = opc.opc.get_node(ua.ObjectIds.AlarmConditionType)
    evfilter = await asyncua.common.events.get_filter_from_event_type([alarm_type])
    browsePathList = [o.BrowsePath for o in evfilter.SelectClauses if o.BrowsePath]
    browsePathId = [ua.QualifiedName('ShelvingState'), ua.QualifiedName('CurrentState'), ua.QualifiedName('Id')]
    assert browsePathId in browsePathList


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
    await opc.opc.delete_nodes([etype])


async def test_events_default(opc):
    evgen = await opc.server.get_event_generator()
    myhandler = MySubHandler()
    sub = await opc.opc.create_subscription(100, myhandler)
    handle = await sub.subscribe_events()
    tid = datetime.now(timezone.utc)
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
    tid = datetime.now(timezone.utc)
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
    await opc.opc.delete_nodes([o])


async def test_events_wrong_source(opc):
    objects = opc.server.nodes.objects
    o = await objects.add_object(3, 'MyObject')
    evgen = await opc.server.get_event_generator(emitting_node=o)
    myhandler = MySubHandler()
    sub = await opc.opc.create_subscription(100, myhandler)
    handle = await sub.subscribe_events()
    tid = datetime.now(timezone.utc)
    msg = "this is my msg "
    await evgen.trigger(tid, msg)
    with pytest.raises(TimeoutError):  # we should not receive event
        _ = await myhandler.result()
    await sub.unsubscribe(handle)
    await sub.delete()
    await opc.opc.delete_nodes([o])


async def test_events_CustomEvent(opc):
    etype = await opc.server.create_custom_event_type(2, 'MyEvent', ua.ObjectIds.BaseEventType, [
        ('PropertyNum', ua.VariantType.Float),
        ('PropertyString', ua.VariantType.String)
    ])
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
    tid = datetime.now(timezone.utc)
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
    await opc.opc.delete_nodes([etype])


async def test_events_CustomEvent_CustomFilter(opc):
    etype = await opc.server.create_custom_event_type(2, 'MyEventCustom', ua.ObjectIds.ProgramTransitionAuditEventType,
                                                      [('NodeId', ua.VariantType.NodeId), ('PropertyString', ua.VariantType.String)])
    # Create Custom Event filter including AttributeId.NodeId
    efilter = ua.EventFilter()
    browsePathes = [[ua.uatypes.QualifiedName("PropertyString", 2)],
                    [ua.uatypes.QualifiedName("Transition"), ua.uatypes.QualifiedName("Id")],
                    [ua.uatypes.QualifiedName("Message")],
                    [ua.uatypes.QualifiedName("EventType")]]
    # SelectClause
    for bp in browsePathes:
        op = ua.SimpleAttributeOperand()
        op.AttributeId = ua.AttributeIds.Value
        op.BrowsePath = bp
        efilter.SelectClauses.append(op)
    op = ua.SimpleAttributeOperand()  # For NodeId
    op.AttributeId = ua.AttributeIds.NodeId
    op.TypeDefinitionId = ua.NodeId(ua.ObjectIds.BaseEventType)
    efilter.SelectClauses.append(op)
    # WhereClause
    el = ua.ContentFilterElement()
    el.FilterOperator = ua.FilterOperator.OfType
    op = ua.LiteralOperand()
    op.Value = ua.Variant(etype.nodeid)  # Define type
    el.FilterOperands.append(op)
    efilter.WhereClause.Elements.append(el)
    # Create Subscription
    myhandler = MySubHandler()
    sub = await opc.opc.create_subscription(100, myhandler)
    handle = await sub.subscribe_events(evtypes=etype, evfilter=efilter)
    # Create Custom Event
    evgen = await opc.server.get_event_generator(etype)
    propertystring = "This is my test"
    msg = "this is my msg "
    myNodeId = ua.NodeId(8)
    transId = ua.NodeId(99)
    evgen.event.PropertyString = propertystring
    evgen.event.Message = ua.LocalizedText(msg)
    evgen.event.NodeId = myNodeId
    setattr(evgen.event, "Transition/Id", transId)
    # Fire Custom Event
    await evgen.trigger()
    ev = await myhandler.result()
    # Perform tests
    assert ev is not None  # we did not receive event
    assert etype.nodeid == ev.EventType
    assert msg == ev.Message.Text
    assert propertystring == ev.PropertyString
    assert myNodeId == ev.NodeId
    assert transId == getattr(ev, "Transition/Id")
    await sub.unsubscribe(handle)
    await sub.delete()
    await opc.opc.delete_nodes([etype])


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
    tid = datetime.now(timezone.utc)
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
    await opc.opc.delete_nodes([etype, o])


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
    await opc.opc.delete_nodes([etype1, etype2])
    await opc.opc.delete_nodes([o])


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
    evgen3.event.PropertyString = propertystring3
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
    await opc.opc.delete_nodes([etype1, etype2, etype3])
    await opc.opc.delete_nodes([o])


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
    await opc.opc.delete_nodes([sub_obj])


@pytest.mark.parametrize("opc", ["client"], indirect=True)
async def test_maxkeepalive_count(opc, mocker):
    sub_handler = MySubHandler()
    client, server = opc

    period = 1
    max_keepalive_count = client.get_keepalive_count(period)
    mock_period = 500
    mock_max_keepalive_count = client.get_keepalive_count(mock_period)

    mock_response = ua.CreateSubscriptionResult(
        SubscriptionId=78,
        RevisedPublishingInterval=mock_period,
        RevisedLifetimeCount=10000,
        RevisedMaxKeepAliveCount=2700
    )
    mock_create_subscription = mocker.patch.object(
        client.uaclient,
        "create_subscription",
        new=AsyncMock(return_value=mock_response)
    )
    mock_update_subscription = mocker.patch.object(
        client.uaclient,
        "update_subscription",
        new=AsyncMock()
    )

    sub = await client.create_subscription(period, sub_handler)
    assert sub.parameters.RequestedMaxKeepAliveCount == mock_max_keepalive_count
    assert mock_max_keepalive_count != max_keepalive_count
    # mock point to the object at its finale state,
    # here the subscription params have already been updated
    mock_create_subscription.assert_awaited_with(
        ua.CreateSubscriptionParameters(
            RequestedPublishingInterval=mock_period,
            RequestedLifetimeCount=10000,
            RequestedMaxKeepAliveCount=mock_max_keepalive_count,
            MaxNotificationsPerPublish=10000,
            PublishingEnabled=True,
            Priority=0
        ),
        callback=mocker.ANY
    )
    mock_update_subscription.assert_awaited_with(
        ua.ModifySubscriptionParameters(
            SubscriptionId=78,
            RequestedPublishingInterval=mock_period,
            RequestedLifetimeCount=10000,
            RequestedMaxKeepAliveCount=mock_max_keepalive_count,
            MaxNotificationsPerPublish=10000
        )
    )

    # we don't update when sub params == revised params
    mock_update_subscription.reset_mock()
    mock_create_subscription.reset_mock()
    sub = await client.create_subscription(mock_period, sub_handler)
    mock_update_subscription.assert_not_called()


@pytest.mark.parametrize("opc", ["client"], indirect=True)
async def test_publish(opc, mocker):
    client, _ = opc

    o = opc.opc.nodes.objects
    var = await o.add_variable(3, 'SubscriptionVariable', 0)

    publish_event = asyncio.Event()
    publish_org = client.uaclient.publish

    async def publish(acks):
        await publish_event.wait()
        publish_event.clear()
        return await publish_org(acks)

    class PublishCallback:
        def __init__(self):
            self.fut = asyncio.Future()

        def reset(self):
            self.fut = Future()

        def set_result(self, publish_result):
            values = []
            if publish_result.NotificationMessage.NotificationData is not None:
                for notif in publish_result.NotificationMessage.NotificationData:
                    if isinstance(notif, ua.DataChangeNotification):
                        values.extend((item.Value.Value.Value for item in notif.MonitoredItems))
            self.fut.set_result(values)

        async def result(self):
            return await wait_for(asyncio.shield(self.fut), 1)

    publish_callback = PublishCallback()

    mocker.patch.object(asyncua.common.subscription.Subscription, "publish_callback", publish_callback.set_result)
    mocker.patch.object(client.uaclient, "publish", publish)

    sub = await client.create_subscription(30, None)
    await sub.subscribe_data_change(var, queuesize=2)

    with pytest.raises(asyncio.TimeoutError):
        await publish_callback.result()

    publish_event.set()
    result = await publish_callback.result()
    publish_callback.reset()
    assert result == [0]

    for val in [1, 2, 3, 4]:
        await var.write_value(val)
        await asyncio.sleep(0.1)
    with pytest.raises(asyncio.TimeoutError):
        await publish_callback.result()

    publish_event.set()
    result = await publish_callback.result()
    publish_callback.reset()
    assert result == [3, 4]
