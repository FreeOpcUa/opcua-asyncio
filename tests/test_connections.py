import asyncio
import struct
from unittest.mock import AsyncMock, MagicMock

import pytest

from asyncua import Client, Server, ua
from asyncua.client.ua_client import (
    SubscriptionDispatchOverflowPolicy,
    SubscriptionStaleError,
    UaClient,
    _compute_republish_window,
)
from asyncua.common.connection import TransportLimits
from asyncua.server.uaprocessor import UaProcessor
from asyncua.ua.uaerrors import BadMaxConnectionsReached, BadSessionNotActivated

from .conftest import find_free_port, port_num

pytestmark = pytest.mark.asyncio


async def test_max_connections_1(opc):
    opc.server.iserver.isession.__class__.max_connections = 1
    port = opc.server.endpoint.port
    if port == port_num:
        # if client we already have one connection
        with pytest.raises(BadMaxConnectionsReached):
            async with Client(f"opc.tcp://127.0.0.1:{port}"):
                pass
    else:
        async with Client(f"opc.tcp://127.0.0.1:{port}"):
            with pytest.raises(BadMaxConnectionsReached):
                async with Client(f"opc.tcp://127.0.0.1:{port}"):
                    pass
    opc.server.iserver.isession.__class__.max_connections = 1000


async def test_dos_server(opc):
    # See issue 1013 a crafted packet triggered dos
    port = opc.server.endpoint.port
    async with Client(f"opc.tcp://127.0.0.1:{port}") as c:
        # craft invalid packet that trigger dos
        message_type, chunk_type, packet_size = [ua.MessageType.SecureOpen, b"E", 0]
        c.uaclient.protocol.transport.write(struct.pack("<3scI", message_type, chunk_type, packet_size))
        # sleep to give the server time to handle the message because we bypass the asyncio
        await asyncio.sleep(1.0)
        with pytest.raises(ConnectionError):
            # now try to read a value to see if server is still alive
            server_time_node = c.get_node(ua.NodeId(ua.ObjectIds.Server_ServerStatus_CurrentTime))
            await server_time_node.read_value()


async def test_safe_disconnect():
    c = Client(url="opc.tcp://example:4840")
    await c.disconnect()
    # second disconnect should be noop
    await c.disconnect()


async def test_client_connection_lost():
    class LostSubHandler:
        def __init__(self) -> None:
            self.status = ua.StatusCodes.Good

        def status_change_notification(self, status: ua.StatusChangeNotification):
            self.status = status.Status

    # Test the disconnect behavoir
    port = find_free_port()
    srv = Server()
    await srv.init()
    srv.set_endpoint(f"opc.tcp://127.0.0.1:{port}")
    await srv.start()
    async with Client(f"opc.tcp://127.0.0.1:{port}", timeout=0.5, watchdog_intervall=1) as cl:
        myhandler = LostSubHandler()
        _ = await cl.create_subscription(1, myhandler)
        await srv.stop()
        await asyncio.sleep(2)
        with pytest.raises(ConnectionError):
            # check if connection is alive
            await cl.check_connection()
        # check if the status_change_notification was triggered
        assert myhandler.status.value == ua.StatusCodes.BadShutdown
        # check if exception is correct rethrown on second call
        with pytest.raises(ConnectionError):
            await cl.check_connection()
        # check if a exception is thrown when a normal function is called
        with pytest.raises(ConnectionError):
            await cl.get_namespace_array()


async def test_client_connection_lost_callback():
    port = find_free_port()
    srv = Server()
    await srv.init()
    srv.set_endpoint(f"opc.tcp://127.0.0.1:{port}")
    await srv.start()

    class Clb:
        def __init__(self):
            self.called = False
            self.ex = None

        async def clb(self, ex):
            self.called = True
            self.ex = ex

    clb = Clb()

    async with Client(f"opc.tcp://127.0.0.1:{port}", timeout=0.5, watchdog_intervall=1) as cl:
        cl.connection_lost_callback = clb.clb
        await srv.stop()
        await asyncio.sleep(2)
        assert clb.called
        assert isinstance(clb.ex, Exception)


async def test_session_watchdog():
    port = find_free_port()
    srv = Server()
    await srv.init()
    srv.set_endpoint(f"opc.tcp://127.0.0.1:{port}")
    await srv.start()
    client = Client(f"opc.tcp://127.0.0.1:{port}", timeout=0.5, watchdog_intervall=1)
    client.session_timeout = 1000  # 1 second
    await client.connect()
    await client._cancel_background_tasks(disable_pre_hook=False)  # Kill the keepalive tasks
    await asyncio.sleep(2)  # Wait for the watchdog to terminate the session due to inactivity
    with pytest.raises(BadSessionNotActivated):
        server_time_node = client.get_node(ua.NodeId(ua.ObjectIds.Server_ServerStatus_CurrentTime))
        await server_time_node.read_value()
    await client.disconnect()


async def _start_test_server(port: int) -> Server:
    srv = Server()
    await srv.init()
    srv.set_endpoint(f"opc.tcp://127.0.0.1:{port}")
    await srv.start()
    return srv


async def _stop_test_server(srv: Server, timeout: float = 10.0) -> None:
    await asyncio.wait_for(srv.stop(), timeout=timeout)


async def _wait_for_recovered_client(cl: Client, timeout: float = 10.0) -> None:
    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        try:
            await cl.get_namespace_array()
            return
        except Exception:
            await asyncio.sleep(0.1)
    raise TimeoutError("Client did not recover in time")


async def test_client_reconnect_after_server_restart():
    port = find_free_port()
    srv = await _start_test_server(port)
    client = Client(f"opc.tcp://127.0.0.1:{port}", timeout=0.5, watchdog_intervall=0.2)
    client.reconnect_initial_delay = 0.1
    client.reconnect_max_delay = 0.2
    client.reconnect_request_timeout = 3.0

    await client.connect()
    client.reconnect_enabled = False
    await _stop_test_server(srv)
    await asyncio.sleep(0.5)

    srv = await _start_test_server(port)
    try:
        client.reconnect_enabled = True
        await client._schedule_reconnect(ConnectionError("forced reconnect after server restart"))
        await _wait_for_recovered_client(client)
        assert client.uaclient.connection_state == client.uaclient.CONNECTION_STATE.SESSION_READY
    finally:
        client.reconnect_enabled = False
        await client.disconnect()
        await _stop_test_server(srv)


async def test_client_on_reconnected_called_once():
    port = find_free_port()
    srv = await _start_test_server(port)
    client = Client(f"opc.tcp://127.0.0.1:{port}", timeout=0.5, watchdog_intervall=0.2)
    client.reconnect_initial_delay = 0.1
    client.reconnect_max_delay = 0.2
    client.reconnect_request_timeout = 3.0

    callback_event = asyncio.Event()
    callback_count = 0

    async def on_reconnected():
        nonlocal callback_count
        callback_count += 1
        callback_event.set()

    client.on_reconnected = on_reconnected

    await client.connect()
    client.reconnect_enabled = False
    await _stop_test_server(srv)
    await asyncio.sleep(0.5)

    srv = await _start_test_server(port)
    try:
        client.reconnect_enabled = True
        await client._schedule_reconnect(ConnectionError("forced reconnect after server restart"))
        await asyncio.wait_for(callback_event.wait(), timeout=10)
        await _wait_for_recovered_client(client)
        assert callback_count == 1
        assert client.uaclient.connection_state == client.uaclient.CONNECTION_STATE.SESSION_READY
    finally:
        client.reconnect_enabled = False
        await client.disconnect()
        await _stop_test_server(srv)


async def test_request_waits_during_reconnect_and_recovers():
    port = find_free_port()
    srv = await _start_test_server(port)
    client = Client(f"opc.tcp://127.0.0.1:{port}", timeout=0.5, watchdog_intervall=0.2)
    client.reconnect_initial_delay = 0.1
    client.reconnect_max_delay = 0.2
    client.reconnect_request_timeout = 10.0

    await client.connect()
    client.reconnect_enabled = False
    await _stop_test_server(srv)
    client.reconnect_enabled = True
    await client._schedule_reconnect(ConnectionError("forced test reconnect"))

    wait_task = asyncio.create_task(client.check_connection())

    srv = await _start_test_server(port)
    try:
        await asyncio.wait_for(wait_task, timeout=20)
        namespace_array = await asyncio.wait_for(client.get_namespace_array(), timeout=10)
        assert isinstance(namespace_array, list)
        assert namespace_array
    finally:
        client.reconnect_enabled = False
        await client.disconnect()
        await _stop_test_server(srv)


async def test_reconnect_fallback_to_new_session_when_activate_fails(mocker):
    client = Client("opc.tcp://127.0.0.1:4840", timeout=0.5, watchdog_intervall=0.2)
    client.reconnect_enabled = True
    client._session_authentication_token = ua.NodeId(ua.ObjectIds.RootFolder)
    client._session_counter = 10

    client.uaclient.protocol = mocker.MagicMock()
    client.uaclient.protocol.authentication_token = ua.NodeId()
    client.uaclient.get_subscription_ids = mocker.MagicMock(return_value=[])
    client.uaclient.ensure_publish_loop_running = mocker.MagicMock()

    client._cancel_background_tasks = AsyncMock()  # type: ignore[method-assign]
    client.disconnect_socket = mocker.MagicMock()
    client.connect_socket = AsyncMock()  # type: ignore[method-assign]
    client.send_hello = AsyncMock()  # type: ignore[method-assign]
    client.open_secure_channel = AsyncMock()  # type: ignore[method-assign]
    client.create_session = AsyncMock()  # type: ignore[method-assign]

    activate_calls = 0

    async def _activate_side_effect(*_args, **_kwargs):
        nonlocal activate_calls
        activate_calls += 1
        if activate_calls == 1:
            raise ua.UaError("activate failed on old session")
        return mocker.MagicMock(ServerNonce=b"ok")

    client.activate_session = AsyncMock(side_effect=_activate_side_effect)  # type: ignore[method-assign]

    await client._reconnect_loop(ConnectionError("test reconnect"))

    assert activate_calls == 2
    client.create_session.assert_awaited_once()
    assert client.uaclient.connection_state == client.uaclient.CONNECTION_STATE.SESSION_READY
    assert client._reconnect_event.is_set()


async def test_reconnect_logs_transfer_subscriptions_failure(mocker):
    client = Client("opc.tcp://127.0.0.1:4840", timeout=0.5, watchdog_intervall=0.2)
    client.reconnect_enabled = True
    client._session_authentication_token = ua.NodeId(ua.ObjectIds.RootFolder)

    client.uaclient.protocol = mocker.MagicMock()
    client.uaclient.protocol.authentication_token = ua.NodeId()
    client.uaclient.get_subscription_ids = mocker.MagicMock(return_value=[1])
    client.uaclient.get_next_sequence_number = mocker.MagicMock(return_value=1)
    client.uaclient.ensure_publish_loop_running = mocker.MagicMock()

    transfer_result = ua.TransferResult()
    transfer_result.StatusCode = ua.StatusCode(ua.StatusCodes.BadSubscriptionIdInvalid)
    client.uaclient.transfer_subscriptions = AsyncMock(return_value=[transfer_result])
    client._republish_subscriptions = AsyncMock(return_value=set())  # type: ignore[method-assign]

    client._cancel_background_tasks = AsyncMock()  # type: ignore[method-assign]
    client.disconnect_socket = mocker.MagicMock()
    client.connect_socket = AsyncMock()  # type: ignore[method-assign]
    client.send_hello = AsyncMock()  # type: ignore[method-assign]
    client.open_secure_channel = AsyncMock()  # type: ignore[method-assign]
    client.create_session = AsyncMock()  # type: ignore[method-assign]

    async def _activate_side_effect(*_args, **_kwargs):
        if client._session_authentication_token is not None:
            client._session_authentication_token = None
            raise ua.UaError("force new session")
        return mocker.MagicMock(ServerNonce=b"ok")

    client.activate_session = AsyncMock(side_effect=_activate_side_effect)  # type: ignore[method-assign]
    log_warning = mocker.patch("asyncua.client.client._logger.warning")

    await client._reconnect_loop(ConnectionError("test reconnect"))

    assert client.uaclient.transfer_subscriptions.await_count == 1
    assert any("TransferSubscriptions failed" in str(call.args[0]) for call in log_warning.call_args_list)


async def test_republish_handles_bad_subscription_id_invalid(mocker):
    client = Client("opc.tcp://127.0.0.1:4840", timeout=0.5, watchdog_intervall=0.2)
    dispatch = AsyncMock()
    client.uaclient.dispatch_notification_message = dispatch

    async def _republish(_subscription_id, _seq):
        raise ua.UaStatusCodeError(ua.StatusCodes.BadSubscriptionIdInvalid)

    client.uaclient.republish = AsyncMock(side_effect=_republish)
    log_warning = mocker.patch("asyncua.client.client._logger.warning")

    invalid_ids = await client._republish_subscriptions({42: 1})

    assert dispatch.await_count == 0
    assert invalid_ids == {42}
    assert any("must be recreated" in str(call.args[0]) for call in log_warning.call_args_list)


async def test_reconnect_recreates_invalid_managed_subscription(mocker):
    client = Client("opc.tcp://127.0.0.1:4840", timeout=0.5, watchdog_intervall=0.2)
    client.auto_recreate_invalid_subscriptions = True
    subscription = mocker.MagicMock()
    subscription.subscription_id = 42
    subscription.recreate = AsyncMock(return_value=(42, 142))
    client._managed_subscriptions.add(subscription)

    log_warning = mocker.patch("asyncua.client.client._logger.warning")

    await client._recreate_invalid_subscriptions({42})

    subscription.recreate.assert_awaited_once()
    assert any("Recreated invalid subscription" in str(call.args[0]) for call in log_warning.call_args_list)


async def test_reconnect_does_not_recreate_invalid_subscription_when_disabled(mocker):
    client = Client("opc.tcp://127.0.0.1:4840", timeout=0.5, watchdog_intervall=0.2)
    client.reconnect_enabled = True
    client.auto_recreate_invalid_subscriptions = False
    client._session_authentication_token = ua.NodeId(ua.ObjectIds.RootFolder)

    client.uaclient.protocol = mocker.MagicMock()
    client.uaclient.protocol.authentication_token = ua.NodeId()
    client.uaclient.get_subscription_ids = mocker.MagicMock(return_value=[42])
    client.uaclient.get_next_sequence_number = mocker.MagicMock(return_value=1)
    client.uaclient.ensure_publish_loop_running = mocker.MagicMock()
    client.uaclient.transfer_subscriptions = AsyncMock(return_value=[])

    client._cancel_background_tasks = AsyncMock()  # type: ignore[method-assign]
    client.disconnect_socket = mocker.MagicMock()
    client.connect_socket = AsyncMock()  # type: ignore[method-assign]
    client.send_hello = AsyncMock()  # type: ignore[method-assign]
    client.open_secure_channel = AsyncMock()  # type: ignore[method-assign]

    async def _activate_side_effect(*_args, **_kwargs):
        if client._session_authentication_token is not None:
            client._session_authentication_token = None
            raise ua.UaError("force new session")
        return mocker.MagicMock(ServerNonce=b"ok")

    client.activate_session = AsyncMock(side_effect=_activate_side_effect)  # type: ignore[method-assign]
    client.create_session = AsyncMock()  # type: ignore[method-assign]
    client._republish_subscriptions = AsyncMock(return_value={42})  # type: ignore[method-assign]
    client._recreate_invalid_subscriptions = AsyncMock()  # type: ignore[method-assign]

    await client._reconnect_loop(ConnectionError("test reconnect"))

    client._republish_subscriptions.assert_awaited_once()
    client._recreate_invalid_subscriptions.assert_not_awaited()


async def test_keepalive_does_not_advance_last_notification_sequence_number():
    uaclient = UaClient()
    subscription_id = 42
    uaclient._last_publish_sequence_numbers[subscription_id] = 4

    keepalive_message = ua.NotificationMessage()
    keepalive_message.SequenceNumber = 5
    keepalive_message.NotificationData = []

    uaclient._record_notification_sequence_number(subscription_id, keepalive_message)

    assert uaclient._last_publish_sequence_numbers[subscription_id] == 4
    assert uaclient.get_next_sequence_number(subscription_id) == 5


async def test_notification_advances_last_notification_sequence_number():
    uaclient = UaClient()
    subscription_id = 42
    uaclient._last_publish_sequence_numbers[subscription_id] = 4

    notification_message = ua.NotificationMessage()
    notification_message.SequenceNumber = 5
    notification_message.NotificationData = [ua.StatusChangeNotification()]

    uaclient._record_notification_sequence_number(subscription_id, notification_message)

    assert uaclient._last_publish_sequence_numbers[subscription_id] == 5
    assert uaclient.get_next_sequence_number(subscription_id) == 6


async def test_sequence_mismatch_logs_warning(caplog):
    uaclient = UaClient()
    subscription_id = 42
    uaclient._last_publish_sequence_numbers[subscription_id] = 4

    notification_message = ua.NotificationMessage()
    notification_message.SequenceNumber = 7
    notification_message.NotificationData = [ua.StatusChangeNotification()]

    with caplog.at_level("WARNING", logger="asyncua.client.ua_client.UaClient"):
        uaclient._record_notification_sequence_number(subscription_id, notification_message, source="publish")

    assert "Detected notification sequence mismatch" in caplog.text
    assert "expected 5 but received 7" in caplog.text


async def test_keepalive_sequence_mismatch_does_not_log_warning(caplog):
    uaclient = UaClient()
    subscription_id = 42
    uaclient._last_publish_sequence_numbers[subscription_id] = 4

    keepalive_message = ua.NotificationMessage()
    keepalive_message.SequenceNumber = 7
    keepalive_message.NotificationData = []

    with caplog.at_level("WARNING", logger="asyncua.client.ua_client.UaClient"):
        uaclient._record_notification_sequence_number(subscription_id, keepalive_message, source="publish")

    assert "Detected notification sequence mismatch" not in caplog.text


async def test_publish_loop_recovers_sequence_gap_via_republish(mocker):
    uaclient = UaClient()
    subscription_id = 42
    observed_sequences = []

    def _callback(result):
        observed_sequences.append(int(result.NotificationMessage.SequenceNumber))
        if int(result.NotificationMessage.SequenceNumber) == 7:
            uaclient._closing = True

    uaclient._subscription_callbacks[subscription_id] = _callback
    uaclient._last_publish_sequence_numbers[subscription_id] = 4

    publish_message = ua.NotificationMessage()
    publish_message.SequenceNumber = 7
    publish_message.NotificationData = [ua.StatusChangeNotification()]

    publish_result = ua.PublishResult(subscription_id, NotificationMessage=publish_message)
    publish_response = ua.PublishResponse()
    publish_response.Parameters = publish_result
    uaclient.publish = AsyncMock(return_value=publish_response)  # type: ignore[method-assign]

    async def _republish(_subscription_id, sequence_number):
        msg = ua.NotificationMessage()
        msg.SequenceNumber = sequence_number
        msg.NotificationData = [ua.StatusChangeNotification()]
        return msg

    uaclient.republish = AsyncMock(side_effect=_republish)  # type: ignore[method-assign]

    await uaclient._publish_loop()
    await uaclient.flush_subscription_dispatch()

    assert [args.args for args in uaclient.republish.await_args_list] == [
        (subscription_id, 5),
        (subscription_id, 6),
    ]
    assert observed_sequences == [5, 6, 7]
    assert uaclient._last_publish_sequence_numbers[subscription_id] == 7


async def test_publish_loop_sequence_gap_republish_cap(mocker):
    uaclient = UaClient()
    subscription_id = 42
    observed_sequences = []
    uaclient.max_republish_messages_per_gap = 1

    def _callback(result):
        observed_sequences.append(int(result.NotificationMessage.SequenceNumber))
        if int(result.NotificationMessage.SequenceNumber) == 7:
            uaclient._closing = True

    uaclient._subscription_callbacks[subscription_id] = _callback
    uaclient._last_publish_sequence_numbers[subscription_id] = 4

    publish_message = ua.NotificationMessage()
    publish_message.SequenceNumber = 7
    publish_message.NotificationData = [ua.StatusChangeNotification()]

    publish_result = ua.PublishResult(subscription_id, NotificationMessage=publish_message)
    publish_response = ua.PublishResponse()
    publish_response.Parameters = publish_result
    uaclient.publish = AsyncMock(return_value=publish_response)  # type: ignore[method-assign]

    async def _republish(_subscription_id, sequence_number):
        msg = ua.NotificationMessage()
        msg.SequenceNumber = sequence_number
        msg.NotificationData = [ua.StatusChangeNotification()]
        return msg

    uaclient.republish = AsyncMock(side_effect=_republish)  # type: ignore[method-assign]

    await uaclient._publish_loop()
    await uaclient.flush_subscription_dispatch()

    assert [args.args for args in uaclient.republish.await_args_list] == [(subscription_id, 5)]
    assert observed_sequences == [5, 7]


async def test_compute_republish_window_caps_and_handles_empty():
    assert _compute_republish_window(5, 5, 10) is None
    assert _compute_republish_window(5, 7, 0) is None
    assert _compute_republish_window(5, 7, 10) == (5, 7)
    assert _compute_republish_window(5, 20, 3) == (5, 8)


async def test_recover_sequence_gap_stops_on_unexpected_republish_sequence(mocker):
    uaclient = UaClient()
    subscription_id = 42
    uaclient.dispatch_notification_message = AsyncMock()  # type: ignore[method-assign]

    async def _republish(_subscription_id, _sequence_number):
        msg = ua.NotificationMessage()
        msg.SequenceNumber = 999
        msg.NotificationData = [ua.StatusChangeNotification()]
        return msg

    uaclient.republish = AsyncMock(side_effect=_republish)  # type: ignore[method-assign]

    await uaclient._recover_sequence_gap(subscription_id, expected_sequence=5, received_sequence=8)

    uaclient.dispatch_notification_message.assert_not_awaited()
    assert [args.args for args in uaclient.republish.await_args_list] == [(subscription_id, 5)]


async def test_dispatch_queue_overflow_drop_oldest_keeps_latest():
    uaclient = UaClient()
    subscription_id = 42
    observed_sequences: list[int] = []

    def _callback(result):
        observed_sequences.append(int(result.NotificationMessage.SequenceNumber))

    uaclient.subscription_dispatch_queue_maxsize = 1
    uaclient.subscription_dispatch_overflow_policy = SubscriptionDispatchOverflowPolicy.DROP_OLDEST
    uaclient._subscription_callbacks[subscription_id] = _callback
    uaclient._ensure_subscription_dispatch_worker(subscription_id)

    msg1 = ua.NotificationMessage()
    msg1.SequenceNumber = 1
    msg1.NotificationData = [ua.StatusChangeNotification()]

    msg2 = ua.NotificationMessage()
    msg2.SequenceNumber = 2
    msg2.NotificationData = [ua.StatusChangeNotification()]

    assert uaclient._enqueue_publish_result(subscription_id, ua.PublishResult(subscription_id, NotificationMessage=msg1))
    assert uaclient._enqueue_publish_result(subscription_id, ua.PublishResult(subscription_id, NotificationMessage=msg2))

    await uaclient.flush_subscription_dispatch()

    assert observed_sequences == [2]


async def test_dispatch_queue_overflow_warn_drops_newest(caplog):
    uaclient = UaClient()
    subscription_id = 42
    observed_sequences: list[int] = []

    def _callback(result):
        observed_sequences.append(int(result.NotificationMessage.SequenceNumber))

    uaclient.subscription_dispatch_queue_maxsize = 1
    uaclient.subscription_dispatch_overflow_policy = SubscriptionDispatchOverflowPolicy.WARN
    uaclient._subscription_callbacks[subscription_id] = _callback
    uaclient._ensure_subscription_dispatch_worker(subscription_id)

    msg1 = ua.NotificationMessage()
    msg1.SequenceNumber = 1
    msg1.NotificationData = [ua.StatusChangeNotification()]

    msg2 = ua.NotificationMessage()
    msg2.SequenceNumber = 2
    msg2.NotificationData = [ua.StatusChangeNotification()]

    with caplog.at_level("WARNING", logger="asyncua.client.ua_client.UaClient"):
        assert uaclient._enqueue_publish_result(subscription_id, ua.PublishResult(subscription_id, NotificationMessage=msg1))
        assert not uaclient._enqueue_publish_result(subscription_id, ua.PublishResult(subscription_id, NotificationMessage=msg2))

    await uaclient.flush_subscription_dispatch()

    assert observed_sequences == [1]
    assert "dispatch queue overflow" in caplog.text


async def test_flush_subscription_dispatch_waits_for_callback_completion():
    uaclient = UaClient()
    subscription_id = 42
    callback_started = asyncio.Event()
    callback_resume = asyncio.Event()

    async def _callback(_result):
        callback_started.set()
        await callback_resume.wait()

    uaclient._subscription_callbacks[subscription_id] = _callback
    uaclient._ensure_subscription_dispatch_worker(subscription_id)

    msg = ua.NotificationMessage()
    msg.SequenceNumber = 1
    msg.NotificationData = [ua.StatusChangeNotification()]

    assert uaclient._enqueue_publish_result(subscription_id, ua.PublishResult(subscription_id, NotificationMessage=msg))
    await callback_started.wait()

    flush_task = asyncio.create_task(uaclient.flush_subscription_dispatch())
    await asyncio.sleep(0)
    assert not flush_task.done()

    callback_resume.set()
    await flush_task


async def test_prepare_close_session_without_protocol_cancels_dispatch_worker():
    uaclient = UaClient()
    subscription_id = 42
    uaclient._subscription_callbacks[subscription_id] = lambda _result: None
    uaclient._ensure_subscription_dispatch_worker(subscription_id)

    runtime = uaclient._subscription_dispatch_runtime[subscription_id]
    task = runtime.task
    assert task is not None

    uaclient.protocol = None
    assert uaclient._prepare_close_session() is False

    await asyncio.sleep(0)
    assert subscription_id not in uaclient._subscription_dispatch_runtime
    assert task.done()


async def test_uaprocessor_close_skips_self_watchdog_await():
    transport = MagicMock()
    transport.get_extra_info.side_effect = lambda _key: ("127.0.0.1", 4840)
    processor = UaProcessor(MagicMock(), transport, TransportLimits())

    session = MagicMock()
    session.close_session = AsyncMock()
    processor.session = session
    processor._session_watchdog_task = asyncio.current_task()

    await processor.close()

    session.close_session.assert_awaited_once_with(True)


async def test_overflow_policy_string_is_normalized_to_enum():
    uaclient = UaClient()
    uaclient.subscription_dispatch_overflow_policy = "DROP_OLDEST"

    policy = uaclient._resolve_overflow_policy()

    assert policy == SubscriptionDispatchOverflowPolicy.DROP_OLDEST
    assert uaclient.subscription_dispatch_overflow_policy == SubscriptionDispatchOverflowPolicy.DROP_OLDEST


async def test_subscription_watchdog_detects_stale_subscription():
    uaclient = UaClient()
    uaclient.subscription_stale_detection_enabled = True
    uaclient.subscription_stale_detection_margin = 1.0
    uaclient._subscription_callbacks[1] = lambda _result: None

    uaclient._register_subscription_watchdog(subscription_id=1, publishing_interval_ms=1000.0, keepalive_count=2)
    uaclient._subscription_watchdog_states[1].last_seen_at = 0.0

    stale_ids = uaclient._get_stale_subscription_ids(now=2.5)

    assert stale_ids == [1]


async def test_subscription_watchdog_activity_clears_stale_state():
    uaclient = UaClient()
    uaclient.subscription_stale_detection_enabled = True
    uaclient.subscription_stale_detection_margin = 1.0
    uaclient._subscription_callbacks[1] = lambda _result: None

    uaclient._register_subscription_watchdog(subscription_id=1, publishing_interval_ms=1000.0, keepalive_count=2)
    state = uaclient._subscription_watchdog_states[1]
    state.last_seen_at = 0.0
    state.stale_reported = True

    uaclient._mark_subscription_watchdog_activity(1)

    assert uaclient._subscription_watchdog_states[1].stale_reported is False


async def test_subscription_watchdog_ignores_orphaned_state():
    uaclient = UaClient()
    uaclient.subscription_stale_detection_enabled = True
    uaclient.subscription_stale_detection_margin = 1.2

    uaclient._register_subscription_watchdog(subscription_id=571478, publishing_interval_ms=100.0, keepalive_count=10)
    uaclient._subscription_watchdog_states[571478].last_seen_at = 0.0

    stale_ids = uaclient._get_stale_subscription_ids(now=10.0)

    assert stale_ids == []
    assert 571478 not in uaclient._subscription_watchdog_states


async def test_try_recover_stale_subscriptions_recovers_subset_once(mocker):
    client = Client("opc.tcp://127.0.0.1:4840", timeout=0.5, watchdog_intervall=0.2)
    client.uaclient.restart_publish_loop = AsyncMock()  # type: ignore[method-assign]

    stale_sub = mocker.MagicMock()
    stale_sub.subscription_id = 1
    stale_sub.recreate = AsyncMock(return_value=(1, 101))

    healthy_sub = mocker.MagicMock()
    healthy_sub.subscription_id = 2
    healthy_sub.recreate = AsyncMock(return_value=(2, 102))

    client._managed_subscriptions = {stale_sub, healthy_sub}

    recovered = await client._try_recover_stale_subscriptions([1])

    assert recovered is True
    stale_sub.recreate.assert_awaited_once()
    healthy_sub.recreate.assert_not_awaited()
    client.uaclient.restart_publish_loop.assert_awaited_once()


async def test_try_recover_stale_subscriptions_escalates_when_all_stale(mocker):
    client = Client("opc.tcp://127.0.0.1:4840", timeout=0.5, watchdog_intervall=0.2)
    client.uaclient.restart_publish_loop = AsyncMock()  # type: ignore[method-assign]

    sub_a = mocker.MagicMock()
    sub_a.subscription_id = 1
    sub_a.recreate = AsyncMock(return_value=(1, 101))

    sub_b = mocker.MagicMock()
    sub_b.subscription_id = 2
    sub_b.recreate = AsyncMock(return_value=(2, 102))

    client._managed_subscriptions = {sub_a, sub_b}

    recovered = await client._try_recover_stale_subscriptions([1, 2])

    assert recovered is False
    sub_a.recreate.assert_not_awaited()
    sub_b.recreate.assert_not_awaited()
    client.uaclient.restart_publish_loop.assert_not_awaited()


async def test_check_connection_stale_publish_task_uses_targeted_recovery(mocker):
    client = Client("opc.tcp://127.0.0.1:4840", timeout=0.5, watchdog_intervall=0.2)
    client._is_protocol_open = mocker.MagicMock(return_value=True)
    client._try_recover_stale_subscriptions = AsyncMock(return_value=True)  # type: ignore[method-assign]
    client._lost_connection = AsyncMock()  # type: ignore[method-assign]
    client._schedule_reconnect = AsyncMock()  # type: ignore[method-assign]
    client.uaclient.inform_subscriptions = AsyncMock()  # type: ignore[method-assign]

    task = asyncio.get_running_loop().create_future()
    task.set_exception(SubscriptionStaleError([1]))
    client.uaclient._publish_task = task

    await client.check_connection()

    client._try_recover_stale_subscriptions.assert_awaited_once_with([1])
    client._lost_connection.assert_not_awaited()
    client.uaclient.inform_subscriptions.assert_not_awaited()
    client._schedule_reconnect.assert_not_awaited()


async def test_finalize_successful_reconnect_restarts_background_tasks_when_missing(mocker):
    client = Client("opc.tcp://127.0.0.1:4840", timeout=0.5, watchdog_intervall=0.2)
    client._monitor_server_task = None
    client._renew_channel_task = None

    async def _noop_monitor_loop():
        return None

    async def _noop_renew_loop():
        return None

    client._monitor_server_loop = _noop_monitor_loop  # type: ignore[method-assign]
    client._renew_channel_loop = _noop_renew_loop  # type: ignore[method-assign]

    await client._finalize_successful_reconnect(1)

    assert client._monitor_server_task is not None
    assert client._renew_channel_task is not None
    assert client.uaclient.connection_state == client.uaclient.CONNECTION_STATE.SESSION_READY


