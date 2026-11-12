from datetime import UTC, datetime, timedelta

import pytest

from asyncua import Server, ua
from asyncua.common.node import Node
from asyncua.server.history_sql import HistorySQLite

pytestmark = pytest.mark.asyncio


async def test_history_var_read_one(history_server):
    """
    no start and no end is not defined by spec, return reverse order
    Spec says that at least two parameters should be provided, so this one is out of spec
    """
    res = await history_server.var.read_raw_history(None, None, 1)
    assert 1 == len(res)
    assert res[0].Value.Value == history_server.values[-1]


async def test_history_var_read_none(history_server):
    """no start and no end is not defined by spec, return reverse order"""
    res = await history_server.var.read_raw_history(None, None, 0)
    assert 20 == len(res)
    assert res[0].Value.Value == history_server.values[-1]
    assert res[-1].Value.Value == history_server.values[0]


async def test_history_var_read_last_3(history_server):
    """no start and no end is not defined by spec, return reverse order"""
    res = await history_server.var.read_raw_history(None, None, 3)
    assert 3 == len(res)
    assert res[-1].Value.Value == history_server.values[-3]
    assert res[0].Value.Value == history_server.values[-1]


async def test_history_var_read_all2(history_server):
    """no start and no end is not defined by spec, return reverse order"""
    res = await history_server.var.read_raw_history(None, None, 9999)
    assert 20 == len(res)
    assert res[-1].Value.Value == history_server.values[0]
    assert res[0].Value.Value == history_server.values[-1]


async def test_history_var_read_2_with_end(history_server):
    """only has end time, should return reverse order"""
    now = datetime.now(UTC)
    res = await history_server.var.read_raw_history(None, now, 2)
    assert 2 == len(res)
    assert res[-1].Value.Value == history_server.values[-2]


async def test_history_var_read_all(history_server):
    """both start and endtime, return from start to end"""
    now = datetime.now(UTC)
    old = now - timedelta(days=6)

    res = await history_server.var.read_raw_history(old, now, 0)
    assert 20 == len(res)
    assert res[-1].Value.Value == history_server.values[-1]
    assert res[0].Value.Value == history_server.values[0]


async def test_history_var_read_5_in_timeframe(history_server):
    now = datetime.now(UTC)
    old = now - timedelta(days=6)

    res = await history_server.var.read_raw_history(old, now, 5)
    assert 5 == len(res)
    assert res[-1].Value.Value == history_server.values[4]
    assert res[0].Value.Value == history_server.values[0]


async def test_history_var_read_5_in_timeframe_start_greater_than_end(history_server):
    """start time greater than end time, should return reverse order"""
    now = datetime.now(UTC)
    old = now - timedelta(days=6)

    res = await history_server.var.read_raw_history(now, old, 5)
    assert 5 == len(res)
    assert res[-1].Value.Value == history_server.values[-5]
    assert res[0].Value.Value == history_server.values[-1]


async def test_history_var_read_6_with_start(history_server):
    """only start return original order"""
    now = datetime.now(UTC)
    old = now - timedelta(days=6)
    res = await history_server.var.read_raw_history(old, None, 6)
    assert 6 == len(res)
    assert res[-1].Value.Value == history_server.values[5]
    assert res[0].Value.Value == history_server.values[0]


async def test_history_var_read_all_with_start(history_server):
    """only start return original order"""
    now = datetime.now(UTC)
    old = now - timedelta(days=6)
    res = await history_server.var.read_raw_history(old, None, 0)
    assert 20 == len(res)
    assert res[-1].Value.Value == history_server.values[-1]
    assert res[0].Value.Value == history_server.values[0]


async def test_history_var_read_all_with_end(history_server):
    """only end return reversed order"""
    end = datetime.now(UTC) + timedelta(days=6)
    res = await history_server.var.read_raw_history(None, end, 0)
    assert 20 == len(res)
    assert res[-1].Value.Value == history_server.values[0]
    assert res[0].Value.Value == history_server.values[-1]


async def test_history_var_read_3_with_end(history_server):
    """only end return reversed order"""
    end = datetime.now(UTC) + timedelta(days=6)
    res = await history_server.var.read_raw_history(None, end, 3)
    assert 3 == len(res)
    assert res[2].Value.Value == history_server.values[-3]
    assert res[0].Value.Value == history_server.values[-1]


async def test_history_var_read_repeated_continuation_point():
    """
    Some servers do not treat numvalues=0 as "as many as you can" and answer
    with no data plus the same continuation point over and over. read_raw_history
    must not loop forever on such a server.
    """

    class _StuckServerNode(Node):
        def __init__(self):
            self.calls = 0

        async def history_read(self, details, continuation_point=None):
            self.calls += 1
            if self.calls > 10:
                raise AssertionError("read_raw_history did not stop on a repeated continuation point")
            result = ua.HistoryReadResult()
            result.StatusCode = ua.StatusCode(ua.StatusCodes.Good)
            result.ContinuationPoint = b"\x00\x00\x01\x9d"
            result.HistoryData = ua.HistoryData()
            result.HistoryData.DataValues = []
            return result

    node = _StuckServerNode()
    res = await node.read_raw_history(numvalues=0)
    assert [] == res
    assert 2 == node.calls


async def test_sqlite_event_table_with_same_property_name_in_two_event_types(server: Server) -> None:
    idx = await server.register_namespace("urn:history:duplicate-event-fields")
    type_a = await server.create_custom_event_type(
        idx, "DuplicateFieldEventA", properties=[("Temperature", ua.VariantType.Double)]
    )
    type_b = await server.create_custom_event_type(
        idx, "DuplicateFieldEventB", properties=[("Temperature", ua.VariantType.Double)]
    )
    source_id = ua.NodeId(4242, idx)
    history = HistorySQLite(":memory:")
    await history.init()
    try:
        await history.new_historized_event(source_id, [type_a, type_b], period=None)
        fields = history._event_fields[source_id]
        assert fields.count("Temperature") == 1
        async with history._db.execute(f'SELECT * FROM "{history._get_table_name(source_id)}"') as cursor:
            columns = [description[0] for description in cursor.description]
        assert columns.count("Temperature") == 1
    finally:
        await history.stop()
