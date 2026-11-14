import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from asyncua import Server, ua
from asyncua.server.history_sql import HistorySQLite

from .conftest import find_free_port

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def sqlite_server():
    srv = Server()
    await srv.init()
    srv.set_endpoint(f"opc.tcp://127.0.0.1:{find_free_port()}")
    history = HistorySQLite(":memory:")
    await history.init()
    srv.iserver.history_manager.set_storage(history)
    async with srv:
        yield srv


async def _read_all(node, evtype):
    end = datetime.now(UTC) + timedelta(days=1)
    return await node.read_event_history(datetime.now(UTC) - timedelta(days=1), end, 0, [evtype])


async def test_event_type_with_variable_is_stored(sqlite_server):
    srv = sqlite_server
    idx = await srv.register_namespace("urn:test:history")
    etype = await srv._create_custom_type(
        idx,
        "MachineEventType",
        ua.ObjectIds.BaseEventType,
        [("Station", ua.VariantType.String)],
        [("Temperature", ua.VariantType.Double)],
        [],
    )
    emitter = await srv.nodes.objects.add_object(idx, "Machine")
    await emitter.set_event_notifier([ua.EventNotifier.SubscribeToEvents, ua.EventNotifier.HistoryRead])
    await emitter.add_reference(etype.nodeid, ua.ObjectIds.GeneratesEvent)
    await srv.historize_node_event(emitter, period=None)

    gen = await srv.get_event_generator(etype, emitter)
    gen.event.Station = "S1"
    gen.event.Temperature = 71.5
    await gen.trigger(message="hot")
    await asyncio.sleep(1)

    events = await _read_all(emitter, etype)
    assert len(events) == 1
    assert events[0].Temperature == 71.5
    assert events[0].Station == "S1"


async def test_alarm_states_are_stored(sqlite_server):
    srv = sqlite_server
    idx = await srv.register_namespace("urn:test:history")
    emitter = await srv.nodes.objects.add_object(idx, "Tank")
    await emitter.set_event_notifier([ua.EventNotifier.SubscribeToEvents, ua.EventNotifier.HistoryRead])
    alarm_type = srv.get_node(ua.ObjectIds.AlarmConditionType)
    await emitter.add_reference(alarm_type.nodeid, ua.ObjectIds.GeneratesEvent)
    await srv.historize_node_event(emitter, period=None)

    gen = await srv.get_event_generator(alarm_type, emitter)
    gen.event.Severity = 700
    gen.event.ActiveState = ua.LocalizedText("Active")
    setattr(gen.event, "ActiveState/Id", True)
    await gen.trigger(message="level high")
    await asyncio.sleep(1)

    events = await _read_all(emitter, alarm_type)
    assert len(events) == 1
    assert events[0].Severity == 700
    assert getattr(events[0], "ActiveState/Id") is True


async def test_select_clause_with_a_browse_path_reads_its_own_column(sqlite_server):
    history = sqlite_server.iserver.history_manager.storage
    clause = ua.SimpleAttributeOperand(
        BrowsePath=[ua.QualifiedName("ActiveState", 0), ua.QualifiedName("Id", 0)],
        AttributeId=ua.AttributeIds.Value,
    )
    condition_id = ua.SimpleAttributeOperand(AttributeId=ua.AttributeIds.NodeId)
    assert history._select_clause_name(clause) == "ActiveState/Id"
    assert history._select_clause_name(condition_id) == "NodeId"
