"""Tests for the auto-reconnect supervisor and subscription re-creation."""

from __future__ import annotations

import asyncio

import pytest

from asyncua import Client, Server, ua
from asyncua.client.ua_client import UaClientState

from .conftest import find_free_port

pytestmark = pytest.mark.asyncio


class _DataChangeCollector:
    """Subscription handler that records every data change with an Event for awaiting."""

    def __init__(self) -> None:
        self.values: list[object] = []
        self._event = asyncio.Event()

    def datachange_notification(self, _node, val, _data) -> None:
        self.values.append(val)
        self._event.set()

    async def wait_for_value(self, timeout: float = 3.0) -> None:
        await asyncio.wait_for(self._event.wait(), timeout)
        self._event.clear()


async def _start_server(port: int) -> Server:
    srv = Server()
    await srv.init()
    srv.set_endpoint(f"opc.tcp://127.0.0.1:{port}")
    await srv.start()
    return srv


async def _force_transport_close_and_wait(client: Client, *, expect_reconnect: bool = True) -> None:
    """Force a transport-level disconnect and wait until the supervisor has reacted.

    With `expect_reconnect=True` (auto_reconnect on), waits for state to leave
    CONNECTED and then return to CONNECTED after the reconnect cycle.
    With `expect_reconnect=False`, waits for state to settle at DISCONNECTED.

    Entering the `subscribe_state()` block before `transport.close()` is the
    point of using a context-manager subscription: any transition that fires
    between the close and our `wait_for_state` call is buffered, not lost.
    """
    async with client.subscribe_state() as sub:
        proto = client.uaclient.protocol
        assert proto is not None
        assert proto.transport is not None
        proto.transport.close()
        if expect_reconnect:

            async def _wait_round_trip() -> None:
                saw_leave = False
                while True:
                    state = await sub.next_change()
                    if state is not UaClientState.CONNECTED:
                        saw_leave = True
                    elif saw_leave:
                        return

            await asyncio.wait_for(_wait_round_trip(), timeout=5.0)
        else:
            await sub.wait_for_state(UaClientState.DISCONNECTED, timeout=5.0)


async def _wait_until_state(client: Client, target: UaClientState, timeout: float = 5.0) -> None:
    """Poll for the client to reach `target` state."""
    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout
    while client.state is not target:
        if loop.time() > deadline:
            raise AssertionError(f"Timed out waiting for state {target.value} (current={client.state.value})")
        await asyncio.sleep(0.05)


async def test_auto_reconnect_recovers_from_transport_drop() -> None:
    """Closing the transport triggers the supervisor; client reaches CONNECTED again."""
    port = find_free_port()
    srv = await _start_server(port)
    client = Client(f"opc.tcp://127.0.0.1:{port}", timeout=1.0, watchdog_intervall=0.3)
    await client.connect(auto_reconnect=True, reconnect_max_delay=0.5, reconnect_request_timeout=5.0)
    try:
        assert client.state is UaClientState.CONNECTED
        await _force_transport_close_and_wait(client)
        await _wait_until_state(client, UaClientState.CONNECTED, timeout=5.0)
        # Verify the recovered connection is usable.
        server_time = client.get_node(ua.NodeId(ua.ObjectIds.Server_ServerStatus_CurrentTime))
        value = await server_time.read_value()
        assert value is not None
    finally:
        await client.disconnect()
        await srv.stop()


async def test_auto_reconnect_disabled_settles_in_disconnected() -> None:
    """With auto_reconnect=False, supervisor exits on loss and state goes to DISCONNECTED."""
    port = find_free_port()
    srv = await _start_server(port)
    client = Client(f"opc.tcp://127.0.0.1:{port}", timeout=1.0, watchdog_intervall=0.3)
    await client.connect(auto_reconnect=False)
    try:
        await _force_transport_close_and_wait(client, expect_reconnect=False)
        await _wait_until_state(client, UaClientState.DISCONNECTED, timeout=5.0)
        # Subsequent requests should fail fast with ConnectionError.
        with pytest.raises(ConnectionError):
            server_time = client.get_node(ua.NodeId(ua.ObjectIds.Server_ServerStatus_CurrentTime))
            await server_time.read_value()
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass
        await srv.stop()


async def test_connection_lost_callback_fires_on_loss() -> None:
    """User-registered callback should be invoked when the supervisor detects loss."""
    port = find_free_port()
    srv = await _start_server(port)

    call_count = 0
    last_exc: Exception | None = None

    async def on_lost(exc: Exception) -> None:
        nonlocal call_count, last_exc
        call_count += 1
        last_exc = exc

    client = Client(f"opc.tcp://127.0.0.1:{port}", timeout=1.0, watchdog_intervall=0.3)
    client.connection_lost_callback = on_lost
    await client.connect(auto_reconnect=True, reconnect_max_delay=0.5, reconnect_request_timeout=5.0)
    try:
        await _force_transport_close_and_wait(client)
        # Give the supervisor a moment to fire the callback and reconnect.
        await _wait_until_state(client, UaClientState.CONNECTED, timeout=5.0)
        assert call_count >= 1
        assert isinstance(last_exc, Exception)
    finally:
        await client.disconnect()
        await srv.stop()


async def test_subscription_recreated_after_reconnect() -> None:
    """A data-change subscription is re-created server-side after a transport drop."""
    port = find_free_port()
    srv = await _start_server(port)
    objects = srv.get_objects_node()
    variable = await objects.add_variable(2, "ReconnectVar", 0)
    await variable.set_writable()

    client = Client(f"opc.tcp://127.0.0.1:{port}", timeout=1.0, watchdog_intervall=0.3)
    await client.connect(auto_reconnect=True, reconnect_max_delay=0.5, reconnect_request_timeout=5.0)
    handler = _DataChangeCollector()
    try:
        sub = await client.create_subscription(50, handler)
        client_var = client.get_node(variable.nodeid)
        await sub.subscribe_data_change(client_var)
        await handler.wait_for_value(timeout=3.0)
        old_sub_id = sub.subscription_id
        old_handles = set(sub._monitored_items.keys())

        await _force_transport_close_and_wait(client)
        await _wait_until_state(client, UaClientState.CONNECTED, timeout=5.0)
        # _recreate_subscriptions runs after state goes back to CONNECTED, so wait
        # until the subscription has its new server-side id assigned.
        loop = asyncio.get_event_loop()
        deadline = loop.time() + 3.0
        while sub.subscription_id is None or sub.subscription_id == old_sub_id:
            if loop.time() > deadline:
                raise AssertionError(f"Subscription was not re-created (id={sub.subscription_id})")
            await asyncio.sleep(0.01)

        # Subscription should have been re-created with a new server-side id but the
        # same client-handle map.
        assert sub.subscription_id is not None
        assert sub.subscription_id != old_sub_id
        assert set(sub._monitored_items.keys()) == old_handles

        # Notifications should resume on the new subscription. Clear any
        # straggler events from the recreate (e.g. initial-value broadcast)
        # so we deterministically wait for the new write.
        handler.values.clear()
        handler._event.clear()
        await variable.write_value(42)
        await handler.wait_for_value(timeout=3.0)
        assert 42 in handler.values
    finally:
        await client.disconnect()
        await srv.stop()


async def test_deleted_subscription_not_recreated_after_reconnect() -> None:
    """A subscription the user deleted before the drop must not be re-created."""
    port = find_free_port()
    srv = await _start_server(port)
    client = Client(f"opc.tcp://127.0.0.1:{port}", timeout=1.0, watchdog_intervall=0.3)
    await client.connect(auto_reconnect=True, reconnect_max_delay=0.5, reconnect_request_timeout=5.0)
    handler = _DataChangeCollector()
    try:
        sub = await client.create_subscription(50, handler)
        await sub.delete()
        assert sub._deleted is True

        await _force_transport_close_and_wait(client)
        await _wait_until_state(client, UaClientState.CONNECTED, timeout=5.0)

        # The deleted subscription should still be marked deleted, and no
        # new subscription_id assigned.
        assert sub._deleted is True
        # Client's registry should no longer carry it after the supervisor sweeps.
        assert sub not in client._subscriptions
    finally:
        await client.disconnect()
        await srv.stop()


async def test_disconnect_promptly_after_reconnect() -> None:
    """A connect-disconnect cycle through one transport drop should complete promptly."""
    port = find_free_port()
    srv = await _start_server(port)
    client = Client(f"opc.tcp://127.0.0.1:{port}", timeout=1.0, watchdog_intervall=0.3)
    await client.connect(auto_reconnect=True, reconnect_max_delay=0.5, reconnect_request_timeout=5.0)
    try:
        await _force_transport_close_and_wait(client)
        # After supervisor reconnects, disconnect should complete in a few seconds.
        await asyncio.wait_for(client.disconnect(), timeout=5.0)
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass
        await srv.stop()
