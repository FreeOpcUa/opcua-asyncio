import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from asyncua import Server, ua
from asyncua.server.history_sql import HistorySQLite

from .conftest import find_free_port

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


@pytest.mark.parametrize("storage", ["dict", "sqlite"])
async def test_history_ev_rehistorize_with_new_event_type(storage: str) -> None:
    srv = Server()
    await srv.init()
    srv.set_endpoint(f"opc.tcp://127.0.0.1:{find_free_port()}")
    if storage == "sqlite":
        history = HistorySQLite(":memory:")
        await history.init()
        srv.iserver.history_manager.set_storage(history)
    async with srv:
        idx = await srv.register_namespace("urn:test:rehistorize")
        evtype = await srv.create_custom_event_type(
            idx, "RehistorizeEvent", properties=[("Code", ua.VariantType.String)]
        )
        node = srv.get_node(ua.ObjectIds.Server)
        base_evgen = await srv.get_event_generator(emitting_node=node)
        await srv.historize_node_event(node, period=None)
        await base_evgen.trigger(message="before")
        await asyncio.sleep(0.5)
        evgen = await srv.get_event_generator(evtype, node)
        await srv.dehistorize_node_event(node)
        await srv.historize_node_event(node, period=None)
        evgen.event.Code = "E42"
        await evgen.trigger(message="after")
        await asyncio.sleep(0.5)
        now = datetime.now(UTC)
        res = await node.read_event_history(now - timedelta(days=1), now + timedelta(days=1), 0, [evtype])
    fields = [ev.get_event_props_as_fields_dict() for ev in res]
    assert [(f["Message"].Value.Text, f["Code"].Value) for f in fields] == [("before", None), ("after", "E42")]
