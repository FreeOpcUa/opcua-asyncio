import asyncio
from collections import Counter
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from asyncua import ua

from .conftest import Opc


@pytest.mark.parametrize("node_count", [1, 2])
@pytest.mark.parametrize("subscriber_count", [1, 2])
async def test_delete_monitored_node_notifies_subscriber(opc: Opc, node_count: int, subscriber_count: int) -> None:
    nodes = [
        await opc.opc.nodes.objects.add_variable(2, f"DeletedMonitoredVariable{index}", 42)
        for index in range(node_count)
    ]
    handler = AsyncMock()
    received: asyncio.Queue[tuple[ua.NodeId, Any, ua.StatusCode]] = asyncio.Queue()

    async def datachange(node: Any, value: Any, data: Any) -> None:
        received.put_nowait((node.nodeid, value, data.monitored_item.Value.StatusCode))

    handler.datachange_notification.side_effect = datachange
    subscriptions = []
    try:
        for _ in range(subscriber_count):
            subscription = await opc.opc.create_subscription(10, handler)
            subscriptions.append(subscription)
            await subscription.subscribe_data_change(nodes)
        for _ in range(node_count * subscriber_count):
            assert (await asyncio.wait_for(received.get(), 2))[1] == 42
        _, results = await opc.opc.delete_nodes(nodes)
        assert results == [ua.StatusCode()] * node_count
        deleted = [await asyncio.wait_for(received.get(), 2) for _ in range(node_count * subscriber_count)]
        assert Counter(nodeid for nodeid, _, _ in deleted) == Counter({node.nodeid: subscriber_count for node in nodes})
        assert all(
            value is None and status == ua.StatusCode(ua.StatusCodes.BadNodeIdUnknown) for _, value, status in deleted
        )
        handler.status_change_notification.assert_not_awaited()
    finally:
        for subscription in subscriptions:
            await subscription.delete()


async def test_delete_node_cleans_up_failed_callback_and_notifies_others(
    opc: Opc, caplog: pytest.LogCaptureFixture
) -> None:
    node = await opc.opc.nodes.objects.add_variable(2, "DeletedCallbackVariable", 42)
    aspace = opc.server.iserver.aspace
    failed_callback = AsyncMock(side_effect=RuntimeError("callback failed"))
    callbacks = (failed_callback, AsyncMock(), Mock())
    handles = []
    for callback in callbacks:
        status, handle = aspace.add_datachange_callback(node.nodeid, ua.AttributeIds.Value, callback)
        status.check()
        handles.append(handle)

    _, results = await opc.opc.delete_nodes([node])

    assert results == [ua.StatusCode()]
    for callback, handle in zip(callbacks, handles):
        callback.assert_called_once_with(handle, None, ua.StatusCode(ua.StatusCodes.BadNodeIdUnknown))
        aspace.delete_datachange_callback(handle)
    errors = [record.args for record in caplog.records if record.msg == "Error calling delete node callback %s"]
    assert errors == [(handles[0],)]
    assert node.nodeid not in aspace


async def test_delete_batch_finishes_mutation_before_callback_yields(opc: Opc) -> None:
    parent = await opc.opc.nodes.objects.add_object(2, "AtomicDeletionParent")
    nodes = [await parent.add_variable(2, f"AtomicDeletion{index}", 42) for index in range(2)]
    aspace = opc.server.iserver.aspace
    entered = asyncio.Event()
    release = asyncio.Event()
    notifications = []

    async def suspended_callback(handle, value, status):
        notifications.append(handle)
        entered.set()
        await release.wait()

    handles = []
    for node in nodes:
        status, handle = aspace.add_datachange_callback(node.nodeid, ua.AttributeIds.Value, suspended_callback)
        status.check()
        handles.append(handle)

    deletion = asyncio.create_task(opc.opc.delete_nodes(nodes))
    try:
        await asyncio.wait_for(entered.wait(), 2)
        deleted_ids = {node.nodeid for node in nodes}
        assert all(nodeid not in aspace for nodeid in deleted_ids)
        for handle in handles:
            aspace.delete_datachange_callback(handle)
        assert all(ref.NodeId not in deleted_ids for ref in aspace[parent.nodeid].references)
        params = ua.DeleteNodesParameters(
            NodesToDelete=[ua.DeleteNodesItem(NodeId=node.nodeid, DeleteTargetReferences=True) for node in nodes]
        )
        results = await asyncio.wait_for(opc.server.iserver.isession.delete_nodes(params), 2)
        assert results == [ua.StatusCode(ua.StatusCodes.BadNodeIdUnknown)] * len(nodes)
    finally:
        release.set()
        await asyncio.wait_for(deletion, 2)
        await parent.delete()
    assert notifications == handles
