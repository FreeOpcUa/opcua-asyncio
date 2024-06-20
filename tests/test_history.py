import pytest
from datetime import datetime, timedelta, timezone

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
    now = datetime.now(timezone.utc)
    res = await history_server.var.read_raw_history(None, now, 2)
    assert 2 == len(res)
    assert res[-1].Value.Value == history_server.values[-2]


async def test_history_var_read_all(history_server):
    """both start and endtime, return from start to end"""
    now = datetime.now(timezone.utc)
    old = now - timedelta(days=6)

    res = await history_server.var.read_raw_history(old, now, 0)
    assert 20 == len(res)
    assert res[-1].Value.Value == history_server.values[-1]
    assert res[0].Value.Value == history_server.values[0]


async def test_history_var_read_5_in_timeframe(history_server):
    now = datetime.now(timezone.utc)
    old = now - timedelta(days=6)

    res = await history_server.var.read_raw_history(old, now, 5)
    assert 5 == len(res)
    assert res[-1].Value.Value == history_server.values[4]
    assert res[0].Value.Value == history_server.values[0]


async def test_history_var_read_5_in_timeframe_start_greater_than_end(history_server):
    """start time greater than end time, should return reverse order"""
    now = datetime.now(timezone.utc)
    old = now - timedelta(days=6)

    res = await history_server.var.read_raw_history(now, old, 5)
    assert 5 == len(res)
    assert res[-1].Value.Value == history_server.values[-5]
    assert res[0].Value.Value == history_server.values[-1]


async def test_history_var_read_6_with_start(history_server):
    """only start return original order"""
    now = datetime.now(timezone.utc)
    old = now - timedelta(days=6)
    res = await history_server.var.read_raw_history(old, None, 6)
    assert 6 == len(res)
    assert res[-1].Value.Value == history_server.values[5]
    assert res[0].Value.Value == history_server.values[0]


async def test_history_var_read_all_with_start(history_server):
    """only start return original order"""
    now = datetime.now(timezone.utc)
    old = now - timedelta(days=6)
    res = await history_server.var.read_raw_history(old, None, 0)
    assert 20 == len(res)
    assert res[-1].Value.Value == history_server.values[-1]
    assert res[0].Value.Value == history_server.values[0]


async def test_history_var_read_all_with_end(history_server):
    """only end return reversed order"""
    end = datetime.now(timezone.utc) + timedelta(days=6)
    res = await history_server.var.read_raw_history(None, end, 0)
    assert 20 == len(res)
    assert res[-1].Value.Value == history_server.values[0]
    assert res[0].Value.Value == history_server.values[-1]


async def test_history_var_read_3_with_end(history_server):
    """only end return reversed order"""
    end = datetime.now(timezone.utc) + timedelta(days=6)
    res = await history_server.var.read_raw_history(None, end, 3)
    assert 3 == len(res)
    assert res[2].Value.Value == history_server.values[-3]
    assert res[0].Value.Value == history_server.values[-1]
