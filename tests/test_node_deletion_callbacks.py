import asyncio
from unittest.mock import AsyncMock

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
    initial_values: asyncio.Queue[None] = asyncio.Queue()
    received: asyncio.Queue[ua.StatusCode] = asyncio.Queue()
    handler.datachange_notification.side_effect = lambda *_: initial_values.put_nowait(None)

    async def status_change(notification: ua.StatusChangeNotification) -> None:
        received.put_nowait(notification.Status)

    handler.status_change_notification.side_effect = status_change
    subscriptions = []
    try:
        for _ in range(subscriber_count):
            subscription = await opc.opc.create_subscription(10, handler)
            subscriptions.append(subscription)
            await subscription.subscribe_data_change(nodes)
        for _ in range(node_count * subscriber_count):
            await asyncio.wait_for(initial_values.get(), 2)
        _, results = await opc.opc.delete_nodes(nodes)
        assert results == [ua.StatusCode()] * node_count
        for _ in range(node_count * subscriber_count):
            assert await asyncio.wait_for(received.get(), 2) == ua.StatusCode(ua.StatusCodes.BadNodeIdUnknown)
        assert handler.status_change_notification.await_count == node_count * subscriber_count
        deleted_ids = {node.nodeid for node in nodes}
        assert all(
            nodeid not in deleted_ids for nodeid, _ in opc.server.iserver.aspace._handle_to_attribute_map.values()
        )
    finally:
        for subscription in subscriptions:
            await subscription.delete()


async def test_delete_node_cleans_up_failed_callback_and_notifies_others(opc: Opc) -> None:
    node = await opc.opc.nodes.objects.add_variable(2, "DeletedCallbackVariable", 42)
    aspace = opc.server.iserver.aspace
    failed_callback = AsyncMock(side_effect=RuntimeError("callback failed"))
    completed_callback = AsyncMock()
    handles = []
    for callback in (failed_callback, completed_callback):
        status, handle = aspace.add_datachange_callback(node.nodeid, ua.AttributeIds.Value, callback)
        status.check()
        handles.append(handle)

    _, results = await opc.opc.delete_nodes([node])

    assert results == [ua.StatusCode()]
    for callback, handle in zip((failed_callback, completed_callback), handles):
        callback.assert_awaited_once_with(handle, None, ua.StatusCode(ua.StatusCodes.BadNodeIdUnknown))
        assert handle not in aspace._handle_to_attribute_map
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
        # The first notification is suspended: another task must already see
        # the complete batch and handle/reference cleanup, not half a request.
        deleted_ids = {node.nodeid for node in nodes}
        assert all(nodeid not in aspace for nodeid in deleted_ids)
        assert all(handle not in aspace._handle_to_attribute_map for handle in handles)
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
