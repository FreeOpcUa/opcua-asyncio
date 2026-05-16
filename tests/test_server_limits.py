"""Tests for server-side resource limits that guard against exhaustion."""

from __future__ import annotations

import pytest

from asyncua import Client, Server, ua

from .conftest import find_free_port

pytestmark = pytest.mark.asyncio


async def _start_server(port: int) -> Server:
    srv = Server()
    await srv.init()
    srv.set_endpoint(f"opc.tcp://127.0.0.1:{port}")
    await srv.start()
    return srv


async def test_session_timeout_clamped_to_max() -> None:
    """A client requesting a huge session timeout gets the server's max instead."""
    port = find_free_port()
    srv = await _start_server(port)
    srv.iserver.max_session_timeout_ms = 60_000
    client = Client(f"opc.tcp://127.0.0.1:{port}")
    client.session_timeout = 24 * 60 * 60 * 1000
    await client.connect()
    try:
        assert client.session_timeout == pytest.approx(60_000)
    finally:
        await client.disconnect()
        await srv.stop()


async def test_session_timeout_clamped_to_min() -> None:
    """A client requesting a very short session timeout gets the server's floor."""
    port = find_free_port()
    srv = await _start_server(port)
    srv.iserver.min_session_timeout_ms = 5_000
    client = Client(f"opc.tcp://127.0.0.1:{port}")
    client.session_timeout = 100
    await client.connect()
    try:
        assert client.session_timeout == pytest.approx(5_000)
    finally:
        await client.disconnect()
        await srv.stop()


async def test_unacked_buffer_cap_propagated_from_iserver() -> None:
    """SubscriptionService threads max_unacked_messages_per_subscription into each InternalSubscription."""
    port = find_free_port()
    srv = await _start_server(port)
    srv.iserver.max_unacked_messages_per_subscription = 42
    client = Client(f"opc.tcp://127.0.0.1:{port}")
    await client.connect()
    try:
        sub = await client.create_subscription(50)
        assert sub.subscription_id is not None
        srv_sub = srv.iserver.isession.subscription_service.subscriptions[sub.subscription_id]
        assert srv_sub._no_acks_limit == 42
        await sub.delete()
    finally:
        await client.disconnect()
        await srv.stop()




async def test_monitored_item_queue_size_clamped() -> None:
    """RequestedQueueSize larger than max_monitored_item_queue_size is revised down."""
    port = find_free_port()
    srv = await _start_server(port)
    srv.iserver.max_monitored_item_queue_size = 100
    objects = srv.get_objects_node()
    variable = await objects.add_variable(2, "ClampVar", 0)

    client = Client(f"opc.tcp://127.0.0.1:{port}")
    await client.connect()
    try:
        sub = await client.create_subscription(50)
        request = ua.CreateMonitoredItemsParameters()
        request.SubscriptionId = sub.subscription_id
        request.TimestampsToReturn = ua.TimestampsToReturn.Both
        rv = ua.ReadValueId()
        rv.NodeId = variable.nodeid
        rv.AttributeId = ua.AttributeIds.Value
        mparams = ua.MonitoringParameters()
        mparams.ClientHandle = 9999
        mparams.SamplingInterval = 50
        mparams.QueueSize = 100_000
        mparams.DiscardOldest = True
        mir = ua.MonitoredItemCreateRequest()
        mir.ItemToMonitor = rv
        mir.MonitoringMode = ua.MonitoringMode.Reporting
        mir.RequestedParameters = mparams
        request.ItemsToCreate = [mir]
        results = await client.uaclient.create_monitored_items(request)
        assert results[0].StatusCode.is_good()
        assert results[0].RevisedQueueSize == 100
        await sub.delete()
    finally:
        await client.disconnect()
        await srv.stop()


async def test_zero_queue_size_uses_server_default() -> None:
    """RequestedQueueSize of 0 (the spec's 'server picks') resolves to the configured max."""
    port = find_free_port()
    srv = await _start_server(port)
    srv.iserver.max_monitored_item_queue_size = 250
    objects = srv.get_objects_node()
    variable = await objects.add_variable(2, "DefaultVar", 0)

    client = Client(f"opc.tcp://127.0.0.1:{port}")
    await client.connect()
    try:
        sub = await client.create_subscription(50)
        request = ua.CreateMonitoredItemsParameters()
        request.SubscriptionId = sub.subscription_id
        request.TimestampsToReturn = ua.TimestampsToReturn.Both
        rv = ua.ReadValueId()
        rv.NodeId = variable.nodeid
        rv.AttributeId = ua.AttributeIds.Value
        mparams = ua.MonitoringParameters()
        mparams.ClientHandle = 9998
        mparams.SamplingInterval = 50
        mparams.QueueSize = 0
        mparams.DiscardOldest = True
        mir = ua.MonitoredItemCreateRequest()
        mir.ItemToMonitor = rv
        mir.MonitoringMode = ua.MonitoringMode.Reporting
        mir.RequestedParameters = mparams
        request.ItemsToCreate = [mir]
        results = await client.uaclient.create_monitored_items(request)
        assert results[0].StatusCode.is_good()
        assert results[0].RevisedQueueSize == 250
        await sub.delete()
    finally:
        await client.disconnect()
        await srv.stop()
