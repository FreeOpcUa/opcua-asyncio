import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from asyncua import Server, ua
from asyncua.server.history_sql import HistorySQLite

pytestmark = pytest.mark.asyncio


async def test_history_ev_read_2_with_end(history_server):
    """only has end time, should return reverse order"""
    now = datetime.now(UTC)
    res = await history_server.srv_node.read_event_history(None, now, 2)
    assert 2 == len(res)
    assert res[-1].Severity == history_server.ev_values[-2]


async def test_history_ev_read_all(history_server):
    """both start and end time, return from start to end"""
    now = datetime.now(UTC)
    old = now - timedelta(days=6)

    res = await history_server.srv_node.read_event_history(old, now, 0)
    assert 20 == len(res)
    assert res[-1].Severity == history_server.ev_values[-1]
    assert res[0].Severity == history_server.ev_values[0]


async def test_history_ev_read_5_in_timeframe(history_server):
    now = datetime.now(UTC)
    old = now - timedelta(days=6)

    res = await history_server.srv_node.read_event_history(old, now, 5)
    assert 5 == len(res)
    assert res[-1].Severity == history_server.ev_values[4]
    assert res[0].Severity == history_server.ev_values[0]


async def test_history_ev_read_5_in_timeframe_start_greater_than_end(history_server):
    """start time greater than end time, should return reverse order"""
    now = datetime.now(UTC)
    old = now - timedelta(days=6)

    res = await history_server.srv_node.read_event_history(now, old, 5)
    assert 5 == len(res)
    assert res[-1].Severity == history_server.ev_values[-5]
    assert res[0].Severity == history_server.ev_values[-1]


async def test_history_ev_read_6_with_start(history_server):
    """only start return original order"""
    now = datetime.now(UTC)
    old = now - timedelta(days=6)
    res = await history_server.srv_node.read_event_history(old, None, 6)
    assert 6 == len(res)
    assert res[-1].Severity == history_server.ev_values[5]
    assert res[0].Severity == history_server.ev_values[0]


async def test_history_ev_read_all_with_start(history_server):
    """only start return original order"""
    now = datetime.now(UTC)
    old = now - timedelta(days=6)
    res = await history_server.srv_node.read_event_history(old, None, 0)
    assert 20 == len(res)
    assert res[-1].Severity == history_server.ev_values[-1]
    assert res[0].Severity == history_server.ev_values[0]


async def test_history_ev_read_all_with_end(history_server):
    """only end return reversed order"""
    end = datetime.now(UTC) + timedelta(days=6)
    res = await history_server.srv_node.read_event_history(None, end, 0)
    assert 20 == len(res)
    assert res[-1].Severity == history_server.ev_values[0]
    assert res[0].Severity == history_server.ev_values[-1]


async def test_history_ev_read_3_with_end(history_server):
    """only end return reversed order"""
    end = datetime.now(UTC) + timedelta(days=6)
    res = await history_server.srv_node.read_event_history(None, end, 3)
    assert 3 == len(res)
    assert res[2].Severity == history_server.ev_values[-3]
    assert res[0].Severity == history_server.ev_values[-1]


async def test_history_ev_read_all_filter_order_reversed(history_server):
    """reverse event filter select clauses and test that results match the filter order"""
    now = datetime.now(UTC)
    old = now - timedelta(days=6)
    res = await history_server.srv_node.read_event_history(old, None, 0)
    assert 20 == len(res)
    assert res[-1].Severity == history_server.ev_values[-1]
    assert res[0].Severity == history_server.ev_values[0]


async def test_history_sqlite_event_type_with_variable():
    """Events whose type has variables (not only properties) are stored (#2077)."""
    srv = Server()
    await srv.init()
    history = HistorySQLite(":memory:")
    await history.init()
    srv.iserver.history_manager.set_storage(history)
    try:
        etype = await srv.create_custom_event_type(
            2, "MyVariableEvent", ua.ObjectIds.BaseEventType, [("Level", ua.VariantType.Int32)]
        )
        await etype.add_variable(2, "Temperature", 0.0)
        source = await srv.nodes.objects.add_object(2, "Boiler")
        await source.set_event_notifier([ua.EventNotifier.SubscribeToEvents, ua.EventNotifier.HistoryRead])
        evgen = await srv.get_event_generator(etype, source)
        await srv.historize_node_event(source, period=None)

        evgen.event.Level = 3
        evgen.event.Temperature = 21.5
        await evgen.trigger(message="hot")
        await asyncio.sleep(0.5)

        res = await source.read_event_history(None, None, 0, [etype])
        assert len(res) == 1
        assert res[0].Level == 3
        assert res[0].Message.Text == "hot"
    finally:
        await history.stop()
