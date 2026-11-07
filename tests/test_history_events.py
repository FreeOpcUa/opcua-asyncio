import asyncio
from datetime import datetime, timedelta, timezone

import pytest

pytestmark = pytest.mark.asyncio


async def test_history_ev_read_2_with_end(history_server):
    """only has end time, should return reverse order"""
    now = datetime.now(timezone.utc)
    res = await history_server.srv_node.read_event_history(None, now, 2)
    assert 2 == len(res)
    assert res[-1].Severity == history_server.ev_values[-2]


async def test_history_ev_read_all(history_server):
    """both start and end time, return from start to end"""
    now = datetime.now(timezone.utc)
    old = now - timedelta(days=6)

    res = await history_server.srv_node.read_event_history(old, now, 0)
    assert 20 == len(res)
    assert res[-1].Severity == history_server.ev_values[-1]
    assert res[0].Severity == history_server.ev_values[0]


async def test_history_ev_read_5_in_timeframe(history_server):
    now = datetime.now(timezone.utc)
    old = now - timedelta(days=6)

    res = await history_server.srv_node.read_event_history(old, now, 5)
    assert 5 == len(res)
    assert res[-1].Severity == history_server.ev_values[4]
    assert res[0].Severity == history_server.ev_values[0]


async def test_history_ev_read_5_in_timeframe_start_greater_than_end(history_server):
    """start time greater than end time, should return reverse order"""
    now = datetime.now(timezone.utc)
    old = now - timedelta(days=6)

    res = await history_server.srv_node.read_event_history(now, old, 5)
    assert 5 == len(res)
    assert res[-1].Severity == history_server.ev_values[-5]
    assert res[0].Severity == history_server.ev_values[-1]


async def test_history_ev_read_6_with_start(history_server):
    """only start return original order"""
    now = datetime.now(timezone.utc)
    old = now - timedelta(days=6)
    res = await history_server.srv_node.read_event_history(old, None, 6)
    assert 6 == len(res)
    assert res[-1].Severity == history_server.ev_values[5]
    assert res[0].Severity == history_server.ev_values[0]


async def test_history_ev_read_all_with_start(history_server):
    """only start return original order"""
    now = datetime.now(timezone.utc)
    old = now - timedelta(days=6)
    res = await history_server.srv_node.read_event_history(old, None, 0)
    assert 20 == len(res)
    assert res[-1].Severity == history_server.ev_values[-1]
    assert res[0].Severity == history_server.ev_values[0]


async def test_history_ev_read_all_with_end(history_server):
    """only end return reversed order"""
    end = datetime.now(timezone.utc) + timedelta(days=6)
    res = await history_server.srv_node.read_event_history(None, end, 0)
    assert 20 == len(res)
    assert res[-1].Severity == history_server.ev_values[0]
    assert res[0].Severity == history_server.ev_values[-1]


async def test_history_ev_read_3_with_end(history_server):
    """only end return reversed order"""
    end = datetime.now(timezone.utc) + timedelta(days=6)
    res = await history_server.srv_node.read_event_history(None, end, 3)
    assert 3 == len(res)
    assert res[2].Severity == history_server.ev_values[-3]
    assert res[0].Severity == history_server.ev_values[-1]


async def test_history_ev_read_all_filter_order_reversed(history_server):
    """reverse event filter select clauses and test that results match the filter order"""
    now = datetime.now(timezone.utc)
    old = now - timedelta(days=6)
    res = await history_server.srv_node.read_event_history(old, None, 0)
    assert 20 == len(res)
    assert res[-1].Severity == history_server.ev_values[-1]
    assert res[0].Severity == history_server.ev_values[0]


async def test_history_ev_node_other_than_server(history_server):
    """events of a historized node are stored under that node, not under the Server node"""
    srv = history_server.srv
    obj = await srv.nodes.objects.add_object(3, "history_ev_obj")
    evgen = await srv.get_event_generator(emitting_node=obj)
    await srv.historize_node_event(obj, period=None)
    for severity in range(3):
        evgen.event.Severity = severity
        await evgen.trigger(message="obj message")
        await asyncio.sleep(0.1)
    await asyncio.sleep(2)
    now = datetime.now(timezone.utc)
    old = now - timedelta(days=6)

    res = await obj.read_event_history(old, now, 0)
    assert [ev.Severity for ev in res] == [0, 1, 2]

    res = await history_server.srv_node.read_event_history(old, now, 0)
    assert 20 == len(res)
