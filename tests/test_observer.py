import asyncio
from unittest import mock

import pytest

from asyncua import Client, ua
from asyncua.client.ua_client import UaClient, UaClientState

from .conftest import port_num


class RecordingObserver:
    def __init__(self):
        self.requests = []
        self.states = []
        self.subscriptions = []
        self.notifications = []

    def on_request(self, request_type, duration, error):
        self.requests.append((request_type, duration, error))

    def on_state_change(self, state):
        self.states.append(state)

    def on_subscription_event(self, event, subscription_id):
        self.subscriptions.append((event, subscription_id))

    def on_notification(self, subscription_id, item_count):
        self.notifications.append((subscription_id, item_count))


class BrokenObserver:
    def on_request(self, request_type, duration, error):
        raise RuntimeError("observer is broken")

    def on_state_change(self, state):
        raise RuntimeError("observer is broken")

    def on_subscription_event(self, event, subscription_id):
        raise RuntimeError("observer is broken")

    def on_notification(self, subscription_id, item_count):
        raise RuntimeError("observer is broken")


def test_a_client_starts_without_an_observer():
    assert UaClient().observer is None


async def test_an_observer_only_implements_what_it_cares_about():
    class OnlyRequests:
        def __init__(self):
            self.seen = []

        def on_request(self, request_type, duration, error):
            self.seen.append(request_type)

    observer = OnlyRequests()
    client = UaClient()
    client.observer = observer
    client.protocol = mock.AsyncMock()

    await client._send_request(ua.ReadRequest())
    client._set_state(UaClientState.CONNECTED)

    assert observer.seen == ["ReadRequest"]


async def test_nothing_is_measured_without_an_observer():
    client = UaClient()
    client.protocol = mock.AsyncMock()

    with mock.patch("asyncua.client.ua_client.time.monotonic") as clock:
        await client._send_request(ua.ReadRequest())

    assert not clock.called, "the clock is only read when someone is watching"


async def test_a_request_is_reported_with_its_type_and_duration():
    observer = RecordingObserver()
    client = UaClient()
    client.observer = observer
    client.protocol = mock.AsyncMock()

    await client._send_request(ua.ReadRequest())

    assert len(observer.requests) == 1
    request_type, duration, error = observer.requests[0]
    assert request_type == "ReadRequest"
    assert duration >= 0
    assert error is None


async def test_a_failing_request_is_reported_with_its_error_and_still_raises():
    observer = RecordingObserver()
    client = UaClient()
    client.observer = observer
    client.protocol = mock.AsyncMock()
    client.protocol.send_request.side_effect = ConnectionError("gone")

    with pytest.raises(ConnectionError):
        await client._send_request(ua.ReadRequest())

    _, _, error = observer.requests[0]
    assert isinstance(error, ConnectionError)


def test_state_changes_are_reported_once_each():
    observer = RecordingObserver()
    client = UaClient()
    client.observer = observer

    client._set_state(UaClientState.CONNECTING)
    client._set_state(UaClientState.CONNECTING)
    client._set_state(UaClientState.CONNECTED)

    assert observer.states == ["connecting", "connected"]


async def test_a_broken_observer_does_not_break_a_request():
    client = UaClient()
    client.observer = BrokenObserver()
    client.protocol = mock.AsyncMock()

    await client._send_request(ua.ReadRequest())


def test_a_broken_observer_does_not_break_a_state_change():
    client = UaClient()
    client.observer = BrokenObserver()

    client._set_state(UaClientState.CONNECTED)

    assert client.state is UaClientState.CONNECTED


async def test_the_subscription_lifecycle_is_reported(server):
    observer = RecordingObserver()
    async with Client(f"opc.tcp://127.0.0.1:{port_num}") as client:
        client.uaclient.observer = observer
        subscription = await client.create_subscription(100, mock.MagicMock())
        created = [e for e in observer.subscriptions if e[0] == "created"]
        assert created, "creating a subscription is reported"
        await subscription.delete()

    assert any(event == "deleted" for event, _ in observer.subscriptions)


async def test_notifications_are_reported_with_their_item_count(server):
    observer = RecordingObserver()
    async with Client(f"opc.tcp://127.0.0.1:{port_num}") as client:
        client.uaclient.observer = observer
        node = client.get_node(ua.ObjectIds.Server_ServerStatus_CurrentTime)
        subscription = await client.create_subscription(50, mock.MagicMock())
        await subscription.subscribe_data_change(node)
        await asyncio.sleep(0.5)
        await subscription.delete()

    assert observer.notifications, "publish responses are reported"
    assert all(count >= 0 for _, count in observer.notifications)


async def test_the_request_slot_is_free_while_the_observer_runs():
    held = []
    client = UaClient()
    client._request_semaphore = asyncio.Semaphore(1)
    client.protocol = mock.AsyncMock()

    class Probe:
        def on_request(self, request_type, duration, error):
            held.append(client._request_semaphore.locked())

    client.observer = Probe()
    await client._send_request(ua.ReadRequest())

    assert held == [False]


async def test_a_recreated_subscription_is_reported_once(server):
    observer = RecordingObserver()
    async with Client(f"opc.tcp://127.0.0.1:{port_num}") as client:
        client.uaclient.observer = observer
        subscription = await client.create_subscription(100, mock.MagicMock())
        observer.subscriptions.clear()
        await subscription.recreate()
        await subscription.delete()

    events = [event for event, _ in observer.subscriptions]
    assert events.count("recreated") == 1, "a recreate is one event, not created plus recreated"
    assert "created" not in events
