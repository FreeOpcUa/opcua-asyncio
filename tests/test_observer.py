import asyncio
from contextlib import contextmanager
from unittest import mock

import pytest

from asyncua import Client, ua
from asyncua.client.ua_client import UaClient, UaClientState
from asyncua.observer import NULL_OBSERVER, Observer, SubscriptionEvent

from .conftest import port_num


class RecordingObserver(Observer):
    def __init__(self):
        self.requests = []
        self.states = []
        self.subscriptions = []
        self.notifications = []

    @contextmanager
    def observe_request(self, request):
        entry = [type(request).__name__, None]
        self.requests.append(entry)
        try:
            yield
        except BaseException as exc:
            entry[1] = exc
            raise

    def on_state_change(self, state):
        self.states.append(state)

    def on_subscription_event(self, event, subscription_id):
        self.subscriptions.append((event, subscription_id))

    def on_notification(self, subscription_id, item_count):
        self.notifications.append((subscription_id, item_count))


async def test_a_client_starts_with_an_observer_that_does_nothing():
    client = UaClient()
    client.protocol = mock.AsyncMock()

    assert client.observer is NULL_OBSERVER

    await client._send_request(ua.ReadRequest())
    client._set_state(UaClientState.CONNECTED)


async def test_an_observer_only_implements_what_it_cares_about():
    class OnlyStates(Observer):
        def __init__(self):
            self.seen = []

        def on_state_change(self, state):
            self.seen.append(state)

    observer = OnlyStates()
    client = UaClient()
    client.observer = observer
    client.protocol = mock.AsyncMock()

    await client._send_request(ua.ReadRequest())
    client._set_state(UaClientState.CONNECTED)

    assert observer.seen == [UaClientState.CONNECTED]


async def test_the_request_runs_inside_the_observer_context():
    order = []
    client = UaClient()
    client.protocol = mock.AsyncMock()
    client.protocol.send_request.side_effect = lambda *a: order.append("sent")

    class Tracer(Observer):
        @contextmanager
        def observe_request(self, request):
            order.append(f"enter {type(request).__name__}")
            yield
            order.append("exit")

    client.observer = Tracer()
    await client._send_request(ua.ReadRequest())

    assert order == ["enter ReadRequest", "sent", "exit"]


async def test_a_failing_request_is_raised_inside_the_observer_context():
    observer = RecordingObserver()
    client = UaClient()
    client.observer = observer
    client.protocol = mock.AsyncMock()
    client.protocol.send_request.side_effect = ConnectionError("gone")

    with pytest.raises(ConnectionError):
        await client._send_request(ua.ReadRequest())

    assert isinstance(observer.requests[0][1], ConnectionError)


async def test_the_request_slot_is_free_when_the_context_closes():
    held = []
    client = UaClient()
    client._request_semaphore = asyncio.Semaphore(1)
    client.protocol = mock.AsyncMock()

    class Probe(Observer):
        @contextmanager
        def observe_request(self, request):
            yield
            held.append(client._request_semaphore.locked())

    client.observer = Probe()
    await client._send_request(ua.ReadRequest())

    assert held == [False]


def test_state_changes_are_reported_once_each():
    observer = RecordingObserver()
    client = UaClient()
    client.observer = observer

    client._set_state(UaClientState.CONNECTING)
    client._set_state(UaClientState.CONNECTING)
    client._set_state(UaClientState.CONNECTED)

    assert observer.states == [UaClientState.CONNECTING, UaClientState.CONNECTED]


def test_a_raising_observer_is_not_shielded():
    class Broken(Observer):
        def on_state_change(self, state):
            raise RuntimeError("observer is broken")

    client = UaClient()
    client.observer = Broken()

    with pytest.raises(RuntimeError):
        client._set_state(UaClientState.CONNECTED)


async def test_the_session_shares_the_observer_of_its_client():
    observer = RecordingObserver()
    client = UaClient()
    client.observer = observer

    assert client.session.observer is observer


async def test_the_subscription_lifecycle_is_reported(server):
    observer = RecordingObserver()
    async with Client(f"opc.tcp://127.0.0.1:{port_num}") as client:
        client.uaclient.observer = observer
        subscription = await client.create_subscription(100, mock.MagicMock())
        created = [e for e in observer.subscriptions if e[0] is SubscriptionEvent.CREATED]
        assert created, "creating a subscription is reported"
        await subscription.delete()

    assert any(event is SubscriptionEvent.DELETED for event, _ in observer.subscriptions)


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


async def test_a_recreated_subscription_is_reported_once(server):
    observer = RecordingObserver()
    async with Client(f"opc.tcp://127.0.0.1:{port_num}") as client:
        client.uaclient.observer = observer
        subscription = await client.create_subscription(100, mock.MagicMock())
        observer.subscriptions.clear()
        await subscription.recreate()
        await subscription.delete()

    events = [event for event, _ in observer.subscriptions]
    assert events.count(SubscriptionEvent.RECREATED) == 1, "a recreate is one event, not created plus recreated"
    assert SubscriptionEvent.CREATED not in events


async def test_a_deleted_subscription_is_marked_deleted_before_the_observer_runs(server):
    seen = []
    async with Client(f"opc.tcp://127.0.0.1:{port_num}") as client:
        subscription = await client.create_subscription(100, mock.MagicMock())

        class Late(Observer):
            def on_subscription_event(self, event, subscription_id):
                seen.append((event, subscription.is_deleted))

        client.uaclient.observer = Late()
        await subscription.delete()

    assert (SubscriptionEvent.DELETED, True) in seen


async def test_a_server_side_subscription_has_a_no_op_observer(server):
    subscription = await server.create_subscription(100, mock.MagicMock())

    assert subscription.server.observer is NULL_OBSERVER

    await subscription.delete()


def test_a_raising_state_listener_is_not_shielded_either():
    def broken(state):
        raise RuntimeError("listener is broken")

    client = UaClient()
    client._add_state_listener(broken)

    with pytest.raises(RuntimeError):
        client._set_state(UaClientState.CONNECTED)
