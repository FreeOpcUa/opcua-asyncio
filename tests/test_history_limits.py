import pytest
from datetime import datetime, timedelta
from opcua import ua

pytestmark = pytest.mark.asyncio
NODE_ID = ua.NodeId(123)


async def result_count(history):
    results, cont = await history.read_node_history(NODE_ID, None, None, None)
    return len(results)


def add_value(history, age):
    value = ua.DataValue()
    value.SourceTimestamp = datetime.utcnow() - timedelta(hours=age)
    return history.save_node_value(NODE_ID, value)


async def test_count_limit(history):
    await history.new_historized_node(NODE_ID, period=None, count=3)
    assert 0 == await result_count(history)
    await add_value(history, 5)
    assert 1 == await result_count(history)
    await add_value(history, 4)
    assert 2 == await result_count(history)
    await add_value(history, 3)
    assert 3 == await result_count(history)
    await add_value(history, 2)
    assert 3 == await result_count(history)
    await add_value(history, 1)
    assert 3 == await result_count(history)


async def test_period_limit(history):
    await history.new_historized_node(NODE_ID, period=timedelta(hours=3))
    assert 0 == await result_count(history)
    await add_value(history, 5)
    assert 0 == await result_count(history)
    await add_value(history, 4)
    assert 0 == await result_count(history)
    await add_value(history, 2)
    assert 1 == await result_count(history)
    await add_value(history, 1)
    assert 2 == await result_count(history)
    await add_value(history, 0)
    assert 3 == await result_count(history)


async def test_combined_limit(history):
    await history.new_historized_node(NODE_ID, period=timedelta(hours=3), count=2)
    assert 0 == await result_count(history)
    await add_value(history, 5)
    assert 0 == await result_count(history)
    await add_value(history, 4)
    assert 0 == await result_count(history)
    await add_value(history, 2)
    assert 1 == await result_count(history)
    await add_value(history, 1)
    assert 2 == await result_count(history)
    await add_value(history, 0)
    assert 2 == await result_count(history)
