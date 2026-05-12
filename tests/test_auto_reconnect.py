"""Tests for the auto-reconnect supervisor and subscription re-creation."""

from __future__ import annotations

import asyncio
import time

import pytest

from asyncua import Client, Server, ua
from asyncua.client.ua_client import UaClientState

from .conftest import find_free_port

pytestmark = pytest.mark.asyncio


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


async def test_subscription_transferred_after_reconnect() -> None:
    """After reconnect, the supervisor transfers the existing subscription (id preserved)."""
    from asyncua.common.subscription import DataChangeEvent

    port = find_free_port()
    srv = await _start_server(port)
    objects = srv.get_objects_node()
    variable = await objects.add_variable(2, "ReconnectVar", 0)
    await variable.set_writable()

    client = Client(f"opc.tcp://127.0.0.1:{port}", timeout=1.0, watchdog_intervall=0.3)
    await client.connect(auto_reconnect=True, reconnect_max_delay=0.5, reconnect_request_timeout=5.0)
    try:
        sub = await client.create_subscription(50)
        client_var = client.get_node(variable.nodeid)
        await sub.subscribe_data_change(client_var)
        first = await sub.next_event(timeout=3.0)
        assert isinstance(first, DataChangeEvent)
        old_sub_id = sub.subscription_id
        old_handles = set(sub._monitored_items.keys())

        await _force_transport_close_and_wait(client)
        await _wait_until_state(client, UaClientState.CONNECTED, timeout=5.0)

        assert sub.subscription_id == old_sub_id
        assert set(sub._monitored_items.keys()) == old_handles

        await variable.write_value(42)
        loop = asyncio.get_event_loop()
        deadline = loop.time() + 3.0
        seen = []
        while 42 not in seen:
            if loop.time() > deadline:
                raise AssertionError(f"Never saw the post-reconnect write (saw {seen})")
            ev = await sub.next_event(timeout=1.0)
            if isinstance(ev, DataChangeEvent):
                seen.append(ev.value)
        await sub.delete()
    finally:
        await client.disconnect()
        await srv.stop()


async def test_subscription_recreated_when_transfer_fails() -> None:
    """If transfer returns Bad (server dropped the subscription), recreate falls back."""
    from asyncua.common.subscription import DataChangeEvent

    port = find_free_port()
    srv = await _start_server(port)
    objects = srv.get_objects_node()
    variable = await objects.add_variable(2, "RecreateVar", 0)
    await variable.set_writable()

    client = Client(f"opc.tcp://127.0.0.1:{port}", timeout=1.0, watchdog_intervall=0.3)
    await client.connect(auto_reconnect=True, reconnect_max_delay=0.5, reconnect_request_timeout=5.0)
    try:
        sub = await client.create_subscription(50)
        client_var = client.get_node(variable.nodeid)
        await sub.subscribe_data_change(client_var)
        await sub.next_event(timeout=3.0)
        old_sub_id = sub.subscription_id
        old_handles = set(sub._monitored_items.keys())

        srv.iserver.isession.subscription_service.subscriptions.pop(old_sub_id, None)

        await _force_transport_close_and_wait(client)
        await _wait_until_state(client, UaClientState.CONNECTED, timeout=5.0)
        loop = asyncio.get_event_loop()
        deadline = loop.time() + 3.0
        while sub.subscription_id is None or sub.subscription_id == old_sub_id:
            if loop.time() > deadline:
                raise AssertionError(f"Subscription was not re-created (id={sub.subscription_id})")
            await asyncio.sleep(0.01)
        assert sub.subscription_id != old_sub_id
        assert set(sub._monitored_items.keys()) == old_handles

        await variable.write_value(7)
        deadline = loop.time() + 3.0
        seen = []
        while 7 not in seen:
            if loop.time() > deadline:
                raise AssertionError(f"Never saw the post-recreate write (saw {seen})")
            ev = await sub.next_event(timeout=1.0)
            if isinstance(ev, DataChangeEvent):
                seen.append(ev.value)
        await sub.delete()
    finally:
        await client.disconnect()
        await srv.stop()


async def test_republish_returns_buffered_notification() -> None:
    """Republish RPC retrieves an unacked notification kept on the server."""
    port = find_free_port()
    srv = await _start_server(port)
    objects = srv.get_objects_node()
    variable = await objects.add_variable(2, "GapVar", 0)

    client = Client(f"opc.tcp://127.0.0.1:{port}", timeout=1.0)
    await client.connect()
    try:
        sub = await client.create_subscription(50)
        await sub.subscribe_data_change(client.get_node(variable.nodeid))
        await sub.next_event(timeout=3.0)

        srv_sub = next(iter(srv.iserver.isession.subscription_service.subscriptions.values()))
        fake_seq = 9999
        fake_msg = ua.NotificationMessage()
        fake_msg.SequenceNumber = fake_seq
        srv_sub._not_acknowledged_results[fake_seq] = ua.PublishResult(
            sub.subscription_id, NotificationMessage=fake_msg
        )

        msg = await client.uaclient.session.republish(sub.subscription_id, fake_seq)
        assert int(msg.SequenceNumber) == fake_seq

        await sub.delete()
    finally:
        await client.disconnect()
        await srv.stop()


async def test_deleted_subscription_not_recreated_after_reconnect() -> None:
    """A subscription the user deleted before the drop must not be re-created."""
    port = find_free_port()
    srv = await _start_server(port)
    client = Client(f"opc.tcp://127.0.0.1:{port}", timeout=1.0, watchdog_intervall=0.3)
    await client.connect(auto_reconnect=True, reconnect_max_delay=0.5, reconnect_request_timeout=5.0)
    try:
        sub = await client.create_subscription(50)
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


def _short_keepalive_params(period_ms: float = 50.0) -> ua.CreateSubscriptionParameters:
    """Subscription params with a small keepalive_count so the stale threshold is short."""
    params = ua.CreateSubscriptionParameters()
    params.RequestedPublishingInterval = period_ms
    params.RequestedLifetimeCount = 100
    params.RequestedMaxKeepAliveCount = 2
    params.MaxNotificationsPerPublish = 10000
    params.PublishingEnabled = True
    params.Priority = 0
    return params


async def test_stale_watchdog_recreates_subscription() -> None:
    """If a subscription's last_publish_at is too old, the watchdog recreates it."""
    port = find_free_port()
    srv = await _start_server(port)
    objects = srv.get_objects_node()
    variable = await objects.add_variable(2, "StaleVar", 0)
    await variable.set_writable()

    client = Client(f"opc.tcp://127.0.0.1:{port}", timeout=1.0, watchdog_intervall=0.3)
    client._stale_check_interval = 0.1
    await client.connect(auto_reconnect=True, reconnect_max_delay=0.5, reconnect_request_timeout=5.0)
    try:
        sub = await client.create_subscription(_short_keepalive_params())
        await sub.subscribe_data_change(client.get_node(variable.nodeid))
        # Wait for the first publish to arrive so last_publish_at is set.
        loop = asyncio.get_event_loop()
        deadline = loop.time() + 2.0
        while sub.last_publish_at is None:
            if loop.time() > deadline:
                raise AssertionError("never got initial publish")
            await asyncio.sleep(0.01)
        old_sub_id = sub.subscription_id
        assert old_sub_id is not None

        # Freeze the staleness clock: swap the registered publish callback for
        # a no-op so subsequent server keep-alives don't refresh last_publish_at
        # back to "now".
        client.uaclient.session._subscription_callbacks[old_sub_id] = lambda _r: None
        sub.last_publish_at = time.monotonic() - 1000.0

        # Watchdog should pick this up within an interval or two and recreate.
        deadline = loop.time() + 3.0
        while sub.subscription_id == old_sub_id:
            if loop.time() > deadline:
                raise AssertionError(f"watchdog did not recreate stale subscription (id={sub.subscription_id})")
            await asyncio.sleep(0.05)
        assert sub.subscription_id is not None
        assert sub.subscription_id != old_sub_id
    finally:
        await client.disconnect()
        await srv.stop()


async def test_stale_watchdog_escalates_to_reconnect_on_recreate_failure() -> None:
    """If recreate raises, the watchdog drives the supervisor through a full reconnect cycle."""
    port = find_free_port()
    srv = await _start_server(port)
    objects = srv.get_objects_node()
    variable = await objects.add_variable(2, "StaleVar2", 0)
    await variable.set_writable()

    client = Client(f"opc.tcp://127.0.0.1:{port}", timeout=1.0, watchdog_intervall=0.3)
    client._stale_check_interval = 0.1
    await client.connect(auto_reconnect=True, reconnect_max_delay=0.5, reconnect_request_timeout=5.0)
    try:
        sub = await client.create_subscription(_short_keepalive_params())
        await sub.subscribe_data_change(client.get_node(variable.nodeid))
        loop = asyncio.get_event_loop()
        deadline = loop.time() + 2.0
        while sub.last_publish_at is None:
            if loop.time() > deadline:
                raise AssertionError("never got initial publish")
            await asyncio.sleep(0.01)

        sub_id = sub.subscription_id
        assert sub_id is not None
        # Freeze staleness clock (see other stale test for rationale).
        client.uaclient.session._subscription_callbacks[sub_id] = lambda _r: None

        async def boom() -> None:
            raise RuntimeError("synthetic recreate failure")

        sub.recreate = boom  # type: ignore[method-assign]

        async with client.subscribe_state() as state_sub:
            sub.last_publish_at = time.monotonic() - 1000.0
            saw_leave = False

            async def _wait_round_trip() -> None:
                nonlocal saw_leave
                while True:
                    state = await state_sub.next_change()
                    if state is not UaClientState.CONNECTED:
                        saw_leave = True
                    elif saw_leave:
                        return

            await asyncio.wait_for(_wait_round_trip(), timeout=5.0)
    finally:
        await client.disconnect()
        await srv.stop()


async def test_delete_subscriptions_keeps_local_state_on_server_failure() -> None:
    """SF4: a failed delete on the server side must not drop the local callback."""
    port = find_free_port()
    srv = await _start_server(port)
    client = Client(f"opc.tcp://127.0.0.1:{port}", timeout=1.0, watchdog_intervall=0.3)
    await client.connect()
    try:
        sub = await client.create_subscription(50)
        sub_id = sub.subscription_id
        assert sub_id is not None
        assert sub_id in client.uaclient.session._subscription_callbacks

        # Ask the server to delete an id it doesn't know about; it should
        # respond Bad and our local state for the real subscription must stay.
        bogus_id = 999999
        results = await client.uaclient.session.delete_subscriptions([bogus_id])
        assert not results[0].is_good()
        assert sub_id in client.uaclient.session._subscription_callbacks
    finally:
        await client.disconnect()
        await srv.stop()


async def test_legacy_handler_api_still_works_through_reconnect() -> None:
    """Legacy callback API back-compat: the subscription handler still receives
    data changes after the supervisor reconnects.

    Most tests in this file (and downstream code) use the new iterator API.
    This one explicitly exercises the legacy handler path to make sure the
    publish_callback's task-based dispatch still delivers notifications
    through a reconnect cycle.
    """
    port = find_free_port()
    srv = await _start_server(port)
    objects = srv.get_objects_node()
    variable = await objects.add_variable(2, "LegacyVar", 0)
    await variable.set_writable()

    class Collector:
        def __init__(self) -> None:
            self.values: list[object] = []
            self._event = asyncio.Event()

        def datachange_notification(self, _node, val, _data) -> None:
            self.values.append(val)
            self._event.set()

        async def wait(self, timeout: float = 3.0) -> None:
            await asyncio.wait_for(self._event.wait(), timeout)
            self._event.clear()

    handler = Collector()
    client = Client(f"opc.tcp://127.0.0.1:{port}", timeout=1.0, watchdog_intervall=0.3)
    await client.connect(auto_reconnect=True, reconnect_max_delay=0.5, reconnect_request_timeout=5.0)
    try:
        sub = await client.create_subscription(50, handler)
        await sub.subscribe_data_change(client.get_node(variable.nodeid))
        await handler.wait(timeout=3.0)  # initial value

        await _force_transport_close_and_wait(client)
        await _wait_until_state(client, UaClientState.CONNECTED, timeout=5.0)

        handler.values.clear()
        handler._event.clear()
        await variable.write_value(99)
        await handler.wait(timeout=5.0)
        assert 99 in handler.values
    finally:
        await client.disconnect()
        await srv.stop()
