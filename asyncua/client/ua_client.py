"""
Low level binary client
"""

import asyncio
import copy
import inspect
import logging
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum

from asyncua import ua
from asyncua.common.session_interface import AbstractSession
from asyncua.ua.uaerrors._base import UaError

from ..common.connection import SecureConnection, TransportLimits
from ..common.utils import wait_for
from ..crypto import security_policies
from ..ua.ua_binary import header_from_binary, nodeid_from_binary, struct_from_binary, struct_to_binary, uatcp_to_binary
from ..ua.uaerrors import BadNoSubscription, BadSessionClosed, BadTimeout, BadUserAccessDenied, UaStructParsingError
from ..ua.uaprotocol_auto import OpenSecureChannelResult, SubscriptionAcknowledgement


@dataclass
class _SubscriptionWatchdogState:
    publishing_interval_ms: float
    keepalive_count: int
    last_seen_at: float
    stale_reported: bool = False


class SubscriptionStaleError(ConnectionError):
    def __init__(self, subscription_ids: list[int]):
        self.subscription_ids = subscription_ids
        super().__init__(
            f"Detected stale subscriptions with no Publish messages within keep-alive window: {subscription_ids}"
        )


class SubscriptionDispatchOverflowError(ConnectionError):
    def __init__(self, subscription_id: int, queue_size: int):
        self.subscription_id = subscription_id
        self.queue_size = queue_size
        super().__init__(
            f"Subscription dispatch queue overflow for subscription {subscription_id} at size {queue_size}"
        )


class SubscriptionDispatchOverflowPolicy(str, Enum):
    DROP_OLDEST = "drop_oldest"
    WARN = "warn"
    DISCONNECT = "disconnect"


@dataclass
class _DispatchSettings:
    queue_maxsize: int = 1000
    overflow_policy: SubscriptionDispatchOverflowPolicy | str = SubscriptionDispatchOverflowPolicy.DROP_OLDEST


@dataclass
class _SequenceRecoverySettings:
    auto_republish_on_gap: bool = True
    max_republish_messages_per_gap: int = 1000


@dataclass
class _WatchdogSettings:
    stale_detection_enabled: bool = True
    stale_detection_margin: float = 1.2


@dataclass
class _SubscriptionDispatchRuntime:
    queue: asyncio.Queue[ua.PublishResult | None]
    task: asyncio.Task | None = None


def _compute_republish_window(
    expected_sequence: int,
    received_sequence: int,
    max_republish: int,
) -> tuple[int, int] | None:
    """
    Return an inclusive-exclusive replay window [start, end) for missing messages.
    Returns None when no replay should be attempted.
    """
    if received_sequence <= expected_sequence:
        return None
    if max_republish <= 0:
        return None

    missing_count = received_sequence - expected_sequence
    replay_end_exclusive = received_sequence
    if missing_count > max_republish:
        replay_end_exclusive = expected_sequence + max_republish
    return expected_sequence, replay_end_exclusive


class UASocketProtocol(asyncio.Protocol):
    """
    Handle socket connection and send ua messages.
    Timeout is the timeout used while waiting for an ua answer from server.
    """

    INITIALIZED = "initialized"
    OPEN = "open"
    CLOSED = "closed"

    def __init__(
        self,
        timeout: float = 1,
        security_policy: security_policies.SecurityPolicy = security_policies.SecurityPolicyNone(),
        limits: TransportLimits = None,
    ):
        """
        :param timeout: Timeout in seconds
        :param security_policy: Security policy (optional)
        """
        self.logger = logging.getLogger(f"{__name__}.UASocketProtocol")
        self.transport: asyncio.Transport | None = None
        self.receive_buffer: bytes | None = None
        self.is_receiving = False
        self.timeout = timeout
        self.authentication_token = ua.NodeId()
        self._request_id = 0
        self._request_handle = 0
        self._callbackmap: dict[int, asyncio.Future] = {}
        if limits is None:
            limits = TransportLimits(65535, 65535, 0, 0)
        else:
            limits = copy.deepcopy(limits)  # Make a copy because the limits can change in the session
        self._connection = SecureConnection(security_policy, limits)

        self.state = self.INITIALIZED
        self.closed: bool = False
        # needed to pass params from asynchronous request to synchronous data receive callback, as well as
        # passing back the processed response to the request so that it can return it.
        self._open_secure_channel_exchange: ua.OpenSecureChannelResponse | ua.OpenSecureChannelParameters | None = None
        # Hook for upper layer tasks before a request is sent (optional)
        self.pre_request_hook: Callable[[], Awaitable[None]] | None = None

    def connection_made(self, transport: asyncio.Transport):  # type: ignore[override]
        self.state = self.OPEN
        self.transport = transport

    def connection_lost(self, exc: Exception | None):
        self.logger.info("Socket has closed connection")
        self.state = self.CLOSED
        self.transport = None

    def data_received(self, data: bytes) -> None:
        if self.receive_buffer:
            data = self.receive_buffer + data
            self.receive_buffer = None
        self._process_received_data(data)

    def _process_received_data(self, data: bytes) -> None:
        """
        Try to parse received data as asyncua message. Data may be chunked but will be in correct order.
        See: https://docs.python.org/3/library/asyncio-protocol.html#asyncio.Protocol.data_received
        Reassembly is done by filling up a buffer until it verifies as a valid message (or a MessageChunk).
        """
        buf = ua.utils.Buffer(data)
        while True:
            try:
                try:
                    header = header_from_binary(buf)
                except ua.utils.NotEnoughData:
                    self.logger.debug("Not enough data while parsing header from server, waiting for more")
                    self.receive_buffer = data
                    return
                if len(buf) < header.body_size:
                    self.logger.debug(
                        "We did not receive enough data from server. Need %s got %s", header.body_size, len(buf)
                    )
                    self.receive_buffer = data
                    return
                msg = self._connection.receive_from_header_and_body(header, buf)
                self._process_received_message(msg)
                if header.MessageType == ua.MessageType.SecureOpen:
                    params: ua.OpenSecureChannelParameters = self._open_secure_channel_exchange
                    response: ua.OpenSecureChannelResponse = struct_from_binary(
                        ua.OpenSecureChannelResponse, msg.body()
                    )
                    response.ResponseHeader.ServiceResult.check()
                    self._open_secure_channel_exchange = response
                    self._connection.set_channel(response.Parameters, params.RequestType, params.ClientNonce)
                if not buf:
                    return
                # Buffer still has bytes left, try to process again
                data = bytes(buf)
            except ua.UaStatusCodeError as e:
                self.logger.error("Got error status from server: %s", e)
                self._fail_all_pending(e)
                self.disconnect_socket()
                return
            except Exception:
                self.logger.exception("Exception raised while parsing message from server")
                self.disconnect_socket()
                return

    def _process_received_message(self, msg: ua.Message | ua.Acknowledge | ua.ErrorMessage):
        if msg is None:
            pass
        elif isinstance(msg, ua.Message):
            self._call_callback(msg.request_id(), msg.body())
        elif isinstance(msg, ua.Acknowledge):
            self._call_callback(0, msg)
        elif isinstance(msg, ua.ErrorMessage):
            self.logger.fatal("Received an error: %r", msg)
            self.disconnect_socket()
            if msg.Error is not None:
                # Automatically print human-readable error text.
                msg.Error.check()
        else:
            raise ua.UaError(f"Unsupported message type: {msg}")

    def _send_request(self, request, timeout: float = 1, message_type=ua.MessageType.SecureMessage) -> asyncio.Future:
        """
        Send request to server, lower-level method.
        Timeout is the timeout written in ua header.
        :param request: Request
        :param timeout: Timeout in seconds
        :param message_type: UA Message Type (optional)
        :return: Future that resolves with the Response
        """
        self._setup_request_header(request.RequestHeader, timeout)
        self.logger.debug("Sending: %s", request)
        try:
            binreq = struct_to_binary(request)
        except Exception:
            # reset request handle if any error
            # see self._setup_request_header
            self._request_handle -= 1
            raise
        self._request_id += 1
        future = asyncio.get_running_loop().create_future()
        self._callbackmap[self._request_id] = future

        # Change to the new security token if the connection has been renewed.
        if self._connection.next_security_token.TokenId != 0:
            self._connection.revolve_tokens()

        msg = self._connection.message_to_binary(binreq, message_type=message_type, request_id=self._request_id)
        if self.transport is not None:
            self.transport.write(msg)
        return future

    async def send_request(self, request, timeout: float | None = None, message_type=ua.MessageType.SecureMessage):
        """
        Send a request to the server.
        Timeout is the timeout written in ua header.
        Returns response object if no callback is provided.
        """
        timeout = self.timeout if timeout is None else timeout
        if self.pre_request_hook:
            # This will propagate exceptions from background tasks to the library user before calling a request which will
            # time out then.
            await self.pre_request_hook()
        try:
            data = await wait_for(self._send_request(request, timeout, message_type), timeout if timeout else None)
        except UaError as ex:
            # Recieved UA error, re-raise it to the caller
            raise ex
        except (TimeoutError, asyncio.TimeoutError) as ex:
            if self.state != self.OPEN:
                raise ConnectionError("Connection is closed") from None
            raise ConnectionError("Request timed out while waiting for OPC UA server response") from ex
        except Exception as ex:
            if self.state != self.OPEN:
                raise ConnectionError("Connection is closed") from None
            raise Exception("Unhandled exception while sending request to OPC UA server") from ex
        self.check_answer(data, f" in response to {request.__class__.__name__}")
        return data

    def check_answer(self, data, context):
        data = data.copy()
        typeid = nodeid_from_binary(data)
        if typeid == ua.FourByteNodeId(ua.ObjectIds.ServiceFault_Encoding_DefaultBinary):
            hdr = struct_from_binary(ua.ResponseHeader, data)
            self.logger.warning(
                "ServiceFault (%s, diagnostics: %s) from server received %s",
                hdr.ServiceResult.name,
                hdr.ServiceDiagnostics,
                context,
            )
            hdr.ServiceResult.check()
            return False
        return True

    def _fail_all_pending(self, exc: Exception) -> None:
        for fut in self._callbackmap.values():
            if not fut.done():
                fut.set_exception(exc)
        self._callbackmap.clear()

    def _call_callback(self, request_id, body):
        try:
            self._callbackmap[request_id].set_result(body)
        except KeyError as ex:
            raise ua.UaError(
                f"No request found for request id: {request_id}, pending are {self._callbackmap.keys()}, body was {body}"
            ) from ex
        except asyncio.InvalidStateError:
            if not self.closed:
                self.logger.warning("Future for request id %s is already done", request_id)
                return
            self.logger.debug("Future for request id %s not handled due to disconnect", request_id)
        del self._callbackmap[request_id]

    def _setup_request_header(self, hdr: ua.RequestHeader, timeout=1) -> None:
        """
        :param hdr: Request header
        :param timeout: Timeout in seconds
        """
        hdr.AuthenticationToken = self.authentication_token
        self._request_handle += 1
        hdr.RequestHandle = self._request_handle
        hdr.TimeoutHint = int(timeout * 1000)

    def disconnect_socket(self):
        self.logger.info("Request to close socket received")
        if self.transport:
            self.transport.close()
        else:
            self.logger.warning("disconnect_socket was called but transport is None")

    async def send_hello(self, url, max_messagesize: int = 0, max_chunkcount: int = 0):
        hello = ua.Hello()
        hello.EndpointUrl = url
        hello.MaxMessageSize = max_messagesize
        hello.MaxChunkCount = max_chunkcount
        ack = asyncio.Future()
        self._callbackmap[0] = ack
        if self.transport is not None:
            self.transport.write(uatcp_to_binary(ua.MessageType.Hello, hello))
        return await wait_for(ack, self.timeout)

    async def open_secure_channel(self, params) -> OpenSecureChannelResult:
        self.logger.info("open_secure_channel")
        request = ua.OpenSecureChannelRequest()
        request.Parameters = params
        if self._open_secure_channel_exchange is not None:
            raise UaError(
                "Two Open Secure Channel requests can not happen too close to each other. "
                "The response must be processed and returned before the next request can be sent."
            )
        self._open_secure_channel_exchange = params
        await wait_for(self._send_request(request, message_type=ua.MessageType.SecureOpen), self.timeout)
        _return = self._open_secure_channel_exchange.Parameters  # type: ignore[union-attr]
        self._open_secure_channel_exchange = None
        return _return

    async def close_secure_channel(self):
        """
        Close secure channel.
        It seems to trigger a shutdown of socket in most servers, so be prepared to reconnect.
        OPC UA specs Part 6, 7.1.4 say that Server does not send a CloseSecureChannel response
        and should just close socket.
        """
        self.logger.info("close_secure_channel")
        request = ua.CloseSecureChannelRequest()
        future = self._send_request(request, message_type=ua.MessageType.SecureClose)
        # don't expect any more answers
        future.cancel()
        self._callbackmap.clear()
        # some servers send a response here, most do not ... so we ignore


class UaClient(AbstractSession):
    """
    low level OPC-UA client.

    It implements (almost) all methods defined in asyncua spec
    taking in argument the structures defined in asyncua spec.

    In this Python implementation  most of the structures are defined in
    uaprotocol_auto.py and uaprotocol_hand.py available under asyncua.ua
    """

    class CONNECTION_STATE(Enum):
        DISCONNECTED = 1
        CONNECTING = 2
        CHANNEL_READY = 3
        SESSION_READY = 4
        SESSION_ESTABLISHING = 5
        DISCONNECTING = 6

    def __init__(self, timeout: float = 1.0):
        """
        :param timeout: Timout in seconds
        """
        self.logger = logging.getLogger(f"{__name__}.UaClient")
        self._subscription_callbacks = {}
        self._subscription_dispatch_runtime: dict[int, _SubscriptionDispatchRuntime] = {}
        self._last_publish_sequence_numbers: dict[int, int] = {}
        self._subscription_watchdog_states: dict[int, _SubscriptionWatchdogState] = {}
        self.dispatch_settings = _DispatchSettings()
        self.sequence_recovery_settings = _SequenceRecoverySettings()
        self.watchdog_settings = _WatchdogSettings()
        self._timeout = timeout
        self.security_policy = security_policies.SecurityPolicyNone()
        self.protocol: UASocketProtocol = None
        self._publish_task = None
        self._pre_request_hook: Callable[[], Awaitable[None]] | None = None
        self._closing: bool = False
        self._connection_state: UaClient.CONNECTION_STATE = UaClient.CONNECTION_STATE.DISCONNECTED
        self._ready_event = asyncio.Event()
        # Nesting counter for internal operations (connect/recover/disconnect) that must bypass await_ready gating.
        self._internal_service_call_depth = 0

    @property
    def subscription_dispatch_queue_maxsize(self) -> int:
        return self.dispatch_settings.queue_maxsize

    @subscription_dispatch_queue_maxsize.setter
    def subscription_dispatch_queue_maxsize(self, value: int) -> None:
        self.dispatch_settings.queue_maxsize = int(value)

    @property
    def subscription_dispatch_overflow_policy(self) -> SubscriptionDispatchOverflowPolicy | str:
        return self.dispatch_settings.overflow_policy

    @subscription_dispatch_overflow_policy.setter
    def subscription_dispatch_overflow_policy(self, value: SubscriptionDispatchOverflowPolicy | str) -> None:
        self.dispatch_settings.overflow_policy = value

    @property
    def subscription_stale_detection_enabled(self) -> bool:
        return self.watchdog_settings.stale_detection_enabled

    @subscription_stale_detection_enabled.setter
    def subscription_stale_detection_enabled(self, value: bool) -> None:
        self.watchdog_settings.stale_detection_enabled = bool(value)

    @property
    def subscription_stale_detection_margin(self) -> float:
        return self.watchdog_settings.stale_detection_margin

    @subscription_stale_detection_margin.setter
    def subscription_stale_detection_margin(self, value: float) -> None:
        self.watchdog_settings.stale_detection_margin = float(value)

    @property
    def auto_republish_on_sequence_gap(self) -> bool:
        return self.sequence_recovery_settings.auto_republish_on_gap

    @auto_republish_on_sequence_gap.setter
    def auto_republish_on_sequence_gap(self, value: bool) -> None:
        self.sequence_recovery_settings.auto_republish_on_gap = bool(value)

    @property
    def max_republish_messages_per_gap(self) -> int:
        return self.sequence_recovery_settings.max_republish_messages_per_gap

    @max_republish_messages_per_gap.setter
    def max_republish_messages_per_gap(self, value: int) -> None:
        self.sequence_recovery_settings.max_republish_messages_per_gap = int(value)

    @property
    def connection_state(self) -> CONNECTION_STATE:
        return self._connection_state

    def _is_transition_allowed(self, state: CONNECTION_STATE) -> bool:
        # Once disconnect starts, do not move back to session setup/ready states.
        # This guards against reconnect/disconnect races and keeps state progression monotonic.
        if self._connection_state == UaClient.CONNECTION_STATE.DISCONNECTING and state in (
            UaClient.CONNECTION_STATE.SESSION_ESTABLISHING,
            UaClient.CONNECTION_STATE.SESSION_READY,
        ):
            return False
        return True

    def try_set_connection_state(self, state: CONNECTION_STATE) -> bool:
        if not self._is_transition_allowed(state):
            self.logger.warning(
                "Ignoring state transition %s -> %s during disconnect",
                self._connection_state,
                state,
            )
            return False
        self.set_connection_state(state)
        return True

    def set_connection_state(self, state: CONNECTION_STATE) -> None:
        self._connection_state = state
        if state == UaClient.CONNECTION_STATE.SESSION_READY:
            self._ready_event.set()
        else:
            self._ready_event.clear()

    async def await_ready(self, timeout: float | None = None) -> None:
        if self._connection_state == UaClient.CONNECTION_STATE.SESSION_READY:
            return
        wait_timeout = self._timeout if timeout is None else timeout
        try:
            await asyncio.wait_for(self._ready_event.wait(), wait_timeout)
        except (TimeoutError, asyncio.TimeoutError) as ex:
            raise ConnectionError("Client is not ready") from ex

    @asynccontextmanager
    async def internal_service_calls(self):
        self._internal_service_call_depth += 1
        try:
            yield
        finally:
            self._internal_service_call_depth -= 1

    def set_security(self, policy: security_policies.SecurityPolicy):
        self.security_policy = policy

    def _make_protocol(self):
        self.protocol = UASocketProtocol(self._timeout, security_policy=self.security_policy)
        self.protocol.pre_request_hook = self._pre_request_hook
        return self.protocol

    @property
    def pre_request_hook(self) -> Callable[[], Awaitable[None]] | None:
        return self._pre_request_hook

    @pre_request_hook.setter
    def pre_request_hook(self, hook: Callable[[], Awaitable[None]] | None):
        self._pre_request_hook = hook
        if self.protocol:
            self.protocol.pre_request_hook = self._pre_request_hook

    async def connect_socket(self, host: str, port: int):
        """Connect to server socket."""
        self.logger.info("opening connection")
        self._closing = False
        self.set_connection_state(UaClient.CONNECTION_STATE.CONNECTING)
        # Timeout the connection when the server isn't available
        await asyncio.wait_for(
            asyncio.get_running_loop().create_connection(self._make_protocol, host, port), self._timeout
        )

    def disconnect_socket(self):
        self._cancel_subscription_dispatch_workers()
        if not self.protocol:
            self.set_connection_state(UaClient.CONNECTION_STATE.DISCONNECTED)
            return
        if self.protocol and self.protocol.state == UASocketProtocol.CLOSED:
            self.logger.warning("disconnect_socket was called but connection is closed")
            self.set_connection_state(UaClient.CONNECTION_STATE.DISCONNECTED)
            return
        self.protocol.disconnect_socket()
        self.protocol = None
        self.set_connection_state(UaClient.CONNECTION_STATE.DISCONNECTED)

    async def _send_request(
        self,
        request,
        timeout: float | None = None,
        message_type=ua.MessageType.SecureMessage,
        bypass_ready_gate: bool = False,
    ):
        if not bypass_ready_gate and self._internal_service_call_depth == 0:
            await self.await_ready(timeout=timeout)
        protocol = self.protocol
        if protocol is None or protocol.state != UASocketProtocol.OPEN:
            self.set_connection_state(UaClient.CONNECTION_STATE.DISCONNECTED)
            raise ConnectionError("Connection is closed")
        return await protocol.send_request(request, timeout=timeout, message_type=message_type)

    async def send_hello(self, url, max_messagesize: int = 0, max_chunkcount: int = 0):
        await self.protocol.send_hello(url, max_messagesize, max_chunkcount)

    async def open_secure_channel(self, params):
        result = await self.protocol.open_secure_channel(params)
        if self._connection_state != UaClient.CONNECTION_STATE.SESSION_READY:
            self.set_connection_state(UaClient.CONNECTION_STATE.CHANNEL_READY)
        return result

    async def close_secure_channel(self):
        """
        close secure channel. It seems to trigger a shutdown of socket
        in most servers, so be prepared to reconnect
        """
        if not self.protocol or self.protocol.state == UASocketProtocol.CLOSED:
            self.logger.warning("close_secure_channel was called but connection is closed")
            self.set_connection_state(UaClient.CONNECTION_STATE.DISCONNECTED)
            return None
        self.set_connection_state(UaClient.CONNECTION_STATE.DISCONNECTING)
        return await self.protocol.close_secure_channel()

    async def create_session(self, parameters):
        self.logger.info("create_session")
        self._closing = False
        # FIXME: setting a value on an object to set it its state is suspicious,
        # especially when that object has its own state
        self.protocol.closed = False
        request = ua.CreateSessionRequest()
        request.Parameters = parameters
        data = await self._send_request(request, bypass_ready_gate=True)
        response = struct_from_binary(ua.CreateSessionResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        self.protocol.authentication_token = response.Parameters.AuthenticationToken
        return response.Parameters

    async def activate_session(self, parameters):
        self.logger.info("activate_session")
        request = ua.ActivateSessionRequest()
        request.Parameters = parameters
        data = await self._send_request(request, bypass_ready_gate=True)
        response = struct_from_binary(ua.ActivateSessionResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        self.set_connection_state(UaClient.CONNECTION_STATE.SESSION_READY)
        return response.Parameters

    async def close_session(self, delete_subscriptions):
        self.logger.info("close_session")
        if not self._prepare_close_session():
            return
        data = await self._send_close_session_request(delete_subscriptions)
        response = struct_from_binary(ua.CloseSessionResponse, data)
        try:
            response.ResponseHeader.ServiceResult.check()
        except BadSessionClosed:
            # Problem: closing the session with open publish requests leads to BadSessionClosed responses
            #          we can just ignore it therefore.
            #          Alternatively we could make sure that there are no publish requests in flight when
            #          closing the session.
            pass
        except BadUserAccessDenied:
            # Problem: older versions of asyncua didn't allow closing non-activated sessions. just ignore it.
            pass

    def _prepare_close_session(self) -> bool:
        self.set_connection_state(UaClient.CONNECTION_STATE.DISCONNECTING)
        self._closing = True
        if self._publish_task and not self._publish_task.done():
            self._publish_task.cancel()
        self._cancel_subscription_dispatch_workers()
        if not self.protocol:
            self.logger.warning("close_session but connection wasn't established")
            return False
        self.protocol.closed = True
        if self.protocol and self.protocol.state == UASocketProtocol.CLOSED:
            self.logger.warning("close_session was called but connection is closed")
            return False
        return True

    async def _send_close_session_request(self, delete_subscriptions):
        request = ua.CloseSessionRequest()
        request.DeleteSubscriptions = delete_subscriptions
        return await self._send_request(request, bypass_ready_gate=True)

    async def browse(self, parameters):
        self.logger.info("browse")
        request = ua.BrowseRequest()
        request.Parameters = parameters
        data = await self._send_request(request)
        response = struct_from_binary(ua.BrowseResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def browse_next(self, parameters):
        self.logger.debug("browse next")
        request = ua.BrowseNextRequest()
        request.Parameters = parameters
        data = await self._send_request(request)
        response = struct_from_binary(ua.BrowseNextResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Parameters.Results

    async def read(self, parameters):
        self.logger.debug("read")
        request = ua.ReadRequest()
        request.Parameters = parameters
        data = await self._send_request(request)
        response = struct_from_binary(ua.ReadResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def write(self, params):
        self.logger.debug("write")
        request = ua.WriteRequest()
        request.Parameters = params
        data = await self._send_request(request)
        response = struct_from_binary(ua.WriteResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def get_endpoints(self, params):
        self.logger.debug("get_endpoint")
        request = ua.GetEndpointsRequest()
        request.Parameters = params
        data = await self._send_request(request, bypass_ready_gate=True)
        response = struct_from_binary(ua.GetEndpointsResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Endpoints

    async def find_servers(self, params):
        self.logger.debug("find_servers")
        request = ua.FindServersRequest()
        request.Parameters = params
        data = await self._send_request(request, bypass_ready_gate=True)
        response = struct_from_binary(ua.FindServersResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Servers

    async def find_servers_on_network(self, params):
        self.logger.debug("find_servers_on_network")
        request = ua.FindServersOnNetworkRequest()
        request.Parameters = params
        data = await self._send_request(request, bypass_ready_gate=True)
        response = struct_from_binary(ua.FindServersOnNetworkResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Parameters

    async def register_server(self, registered_server):
        self.logger.debug("register_server")
        request = ua.RegisterServerRequest()
        request.Server = registered_server
        data = await self._send_request(request, bypass_ready_gate=True)
        response = struct_from_binary(ua.RegisterServerResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        # nothing to return for this service

    async def unregister_server(self, registered_server):
        self.logger.debug("unregister_server")
        request = ua.RegisterServerRequest()
        request.Server = registered_server
        data = await self._send_request(request, bypass_ready_gate=True)
        response = struct_from_binary(ua.RegisterServerResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        # nothing to return for this service

    async def register_server2(self, params):
        self.logger.debug("register_server2")
        request = ua.RegisterServer2Request()
        request.Parameters = params
        data = await self._send_request(request, bypass_ready_gate=True)
        response = struct_from_binary(ua.RegisterServer2Response, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.ConfigurationResults

    async def unregister_server2(self, params):
        self.logger.debug("unregister_server2")
        request = ua.RegisterServer2Request()
        request.Parameters = params
        data = await self._send_request(request, bypass_ready_gate=True)
        response = struct_from_binary(ua.RegisterServer2Response, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.ConfigurationResults

    async def translate_browsepaths_to_nodeids(self, browse_paths):
        self.logger.debug("translate_browsepath_to_nodeid")
        request = ua.TranslateBrowsePathsToNodeIdsRequest()
        request.Parameters.BrowsePaths = browse_paths
        data = await self._send_request(request)
        response = struct_from_binary(ua.TranslateBrowsePathsToNodeIdsResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def create_subscription(  # type: ignore[override]
        self, params: ua.CreateSubscriptionParameters, callback
    ) -> ua.CreateSubscriptionResult:
        self.logger.debug("create_subscription")
        request = ua.CreateSubscriptionRequest()
        request.Parameters = params
        data = await self._send_request(request)
        response = struct_from_binary(ua.CreateSubscriptionResponse, data)
        response.ResponseHeader.ServiceResult.check()
        subscription_id = response.Parameters.SubscriptionId
        self._subscription_callbacks[subscription_id] = callback
        self._ensure_subscription_dispatch_worker(subscription_id)
        publishing_interval_ms = float(
            getattr(response.Parameters, "RevisedPublishingInterval", params.RequestedPublishingInterval or 0.0) or 0.0
        )
        keepalive_count = int(
            getattr(response.Parameters, "RevisedMaxKeepAliveCount", params.RequestedMaxKeepAliveCount or 1) or 1
        )
        self._register_subscription_watchdog(subscription_id, publishing_interval_ms, keepalive_count)
        self.logger.info("create_subscription success SubscriptionId %s", subscription_id)
        if not self._publish_task or self._publish_task.done():
            # Start the publishing loop if it is not yet running
            # The current strategy is to have only one open publish request per UaClient. This might not be enough
            # in high latency networks or in case many subscriptions are created. A Set of Tasks of `_publish_loop`
            # could be used if necessary.
            self._publish_task = asyncio.create_task(self._publish_loop())
        return response.Parameters

    async def inform_subscriptions(self, status: ua.StatusCode):
        """
        Inform all current subscriptions with a status code. This calls the handler's status_change_notification
        """
        status_message = ua.StatusChangeNotification(Status=status)
        notification_message = ua.NotificationMessage(NotificationData=[status_message])  # type: ignore[list-item]
        for subid, callback in self._subscription_callbacks.items():
            try:
                parameters = ua.PublishResult(subid, NotificationMessage=notification_message)
                await self._invoke_subscription_callback(callback, parameters)
            except Exception:  # we call user code, catch everything!
                self.logger.exception("Exception while calling user callback: %s")

    async def update_subscription(self, params: ua.ModifySubscriptionParameters) -> ua.ModifySubscriptionResult:
        request = ua.ModifySubscriptionRequest()
        request.Parameters = params
        data = await self._send_request(request)
        response = struct_from_binary(ua.ModifySubscriptionResponse, data)
        response.ResponseHeader.ServiceResult.check()
        self._register_subscription_watchdog(
            int(params.SubscriptionId),
            float(getattr(response.Parameters, "RevisedPublishingInterval", params.RequestedPublishingInterval or 0.0) or 0.0),
            int(getattr(response.Parameters, "RevisedMaxKeepAliveCount", params.RequestedMaxKeepAliveCount or 1) or 1),
        )
        self.logger.info("update_subscription success SubscriptionId %s", params.SubscriptionId)
        return response.Parameters

    modify_subscription = update_subscription  # legacy support

    async def delete_subscriptions(self, subscription_ids):
        self.logger.debug("delete_subscriptions %r", subscription_ids)
        request = ua.DeleteSubscriptionsRequest()
        request.Parameters.SubscriptionIds = subscription_ids
        data = await self._send_request(request)
        response = struct_from_binary(ua.DeleteSubscriptionsResponse, data)
        response.ResponseHeader.ServiceResult.check()
        self.logger.info("remove subscription callbacks for %r", subscription_ids)
        for sid in subscription_ids:
            self._subscription_callbacks.pop(sid)
            self._stop_subscription_dispatch_worker(sid)
            self._last_publish_sequence_numbers.pop(sid, None)
            self._subscription_watchdog_states.pop(sid, None)
        return response.Results

    def _ensure_subscription_dispatch_worker(self, subscription_id: int) -> None:
        runtime = self._subscription_dispatch_runtime.get(subscription_id)
        if runtime is None:
            maxsize = max(int(self.subscription_dispatch_queue_maxsize), 0)
            runtime = _SubscriptionDispatchRuntime(queue=asyncio.Queue(maxsize=maxsize))
            self._subscription_dispatch_runtime[subscription_id] = runtime
        if runtime.task is None or runtime.task.done():
            runtime.task = asyncio.create_task(self._subscription_dispatch_worker(subscription_id))

    def _stop_subscription_dispatch_worker(self, subscription_id: int) -> None:
        runtime = self._subscription_dispatch_runtime.pop(subscription_id, None)
        if runtime is None:
            return
        queue = runtime.queue
        if queue is not None:
            try:
                queue.put_nowait(None)
            except asyncio.QueueFull:
                pass
        task = runtime.task
        if task is not None and not task.done():
            task.cancel()

    def _cancel_subscription_dispatch_workers(self) -> None:
        subscription_ids = list(self._subscription_dispatch_runtime.keys())
        for subscription_id in subscription_ids:
            self._stop_subscription_dispatch_worker(subscription_id)

    async def flush_subscription_dispatch(
        self,
        subscription_ids: list[int] | None = None,
        timeout: float | None = None,
    ) -> None:
        if subscription_ids is None:
            queues = [runtime.queue for runtime in self._subscription_dispatch_runtime.values()]
        else:
            queues = [
                self._subscription_dispatch_runtime[subscription_id].queue
                for subscription_id in subscription_ids
                if subscription_id in self._subscription_dispatch_runtime
            ]
        if not queues:
            return
        awaitable = asyncio.gather(*(queue.join() for queue in queues))
        if timeout is None:
            await awaitable
        else:
            await asyncio.wait_for(awaitable, timeout)

    async def _subscription_dispatch_worker(self, subscription_id: int) -> None:
        runtime = self._subscription_dispatch_runtime.get(subscription_id)
        if runtime is None:
            return
        queue = runtime.queue
        while True:
            publish_result = await queue.get()
            try:
                if publish_result is None:
                    return
                callback = self._subscription_callbacks.get(subscription_id)
                if callback is None:
                    self.logger.warning(
                        "Received queued publish result for unknown subscription %s active are %s",
                        subscription_id,
                        self._subscription_callbacks.keys(),
                    )
                    continue
                await self._invoke_subscription_callback(callback, publish_result)
            except Exception:
                self.logger.exception("Exception while calling user callback: %s")
            finally:
                queue.task_done()

    async def _invoke_subscription_callback(self, callback, publish_result: ua.PublishResult) -> None:
        result = callback(publish_result)
        if inspect.isawaitable(result):
            await result

    def _get_dispatch_queue(self, subscription_id: int) -> asyncio.Queue[ua.PublishResult | None] | None:
        self._ensure_subscription_dispatch_worker(subscription_id)
        runtime = self._subscription_dispatch_runtime.get(subscription_id)
        if runtime is None:
            return None
        return runtime.queue

    def _enqueue_with_drop_oldest(
        self,
        queue: asyncio.Queue[ua.PublishResult | None],
        subscription_id: int,
        publish_result: ua.PublishResult,
    ) -> bool:
        dropped = False
        try:
            oldest = queue.get_nowait()
            queue.task_done()
            dropped = True
            if oldest is None:
                queue.put_nowait(None)
        except asyncio.QueueEmpty:
            pass
        try:
            queue.put_nowait(publish_result)
        except asyncio.QueueFull:
            self.logger.warning(
                "Subscription %s dispatch queue still full after drop_oldest; dropping newest notification",
                subscription_id,
            )
            return False
        if dropped:
            self.logger.warning(
                "Subscription %s dispatch queue overflow; dropped oldest queued notification",
                subscription_id,
            )
        return True

    def _enqueue_with_disconnect_policy(
        self,
        queue: asyncio.Queue[ua.PublishResult | None],
        subscription_id: int,
    ) -> bool:
        overflow_error = SubscriptionDispatchOverflowError(subscription_id, queue.qsize())
        self.logger.error("%s", overflow_error)
        self._fail_all_dispatch_workers(overflow_error)
        self._closing = True
        return False

    def _enqueue_with_warn_policy(self, subscription_id: int) -> bool:
        self.logger.warning(
            "Subscription %s dispatch queue overflow; dropping newest notification",
            subscription_id,
        )
        return False

    def _enqueue_when_full(
        self,
        queue: asyncio.Queue[ua.PublishResult | None],
        subscription_id: int,
        publish_result: ua.PublishResult,
    ) -> bool:
        policy = self._resolve_overflow_policy()
        if policy == SubscriptionDispatchOverflowPolicy.DROP_OLDEST:
            return self._enqueue_with_drop_oldest(queue, subscription_id, publish_result)
        if policy == SubscriptionDispatchOverflowPolicy.DISCONNECT:
            return self._enqueue_with_disconnect_policy(queue, subscription_id)
        if policy == SubscriptionDispatchOverflowPolicy.WARN:
            return self._enqueue_with_warn_policy(subscription_id)
        return self._enqueue_with_warn_policy(subscription_id)

    def _resolve_overflow_policy(self) -> SubscriptionDispatchOverflowPolicy:
        policy = self.subscription_dispatch_overflow_policy
        if isinstance(policy, SubscriptionDispatchOverflowPolicy):
            return policy
        if isinstance(policy, str):
            normalized = policy.strip().lower()
            for candidate in SubscriptionDispatchOverflowPolicy:
                if candidate.value == normalized:
                    self.subscription_dispatch_overflow_policy = candidate
                    return candidate
            self.logger.warning(
                "Unknown subscription dispatch overflow policy '%s'; falling back to '%s'",
                policy,
                SubscriptionDispatchOverflowPolicy.WARN.value,
            )
            self.subscription_dispatch_overflow_policy = SubscriptionDispatchOverflowPolicy.WARN
            return SubscriptionDispatchOverflowPolicy.WARN
        self.logger.warning(
            "Unsupported subscription dispatch overflow policy type '%s'; falling back to '%s'",
            type(policy).__name__,
            SubscriptionDispatchOverflowPolicy.WARN.value,
        )
        self.subscription_dispatch_overflow_policy = SubscriptionDispatchOverflowPolicy.WARN
        return SubscriptionDispatchOverflowPolicy.WARN

    def _enqueue_publish_result(self, subscription_id: int, publish_result: ua.PublishResult) -> bool:
        callback = self._subscription_callbacks.get(subscription_id)
        if callback is None:
            self.logger.warning(
                "Received publish result for unknown subscription %s active are %s",
                subscription_id,
                self._subscription_callbacks.keys(),
            )
            return False
        queue = self._get_dispatch_queue(subscription_id)
        if queue is None:
            return False
        if not queue.full():
            queue.put_nowait(publish_result)
            return True
        return self._enqueue_when_full(queue, subscription_id, publish_result)

    def _fail_all_dispatch_workers(self, exc: Exception) -> None:
        for runtime in self._subscription_dispatch_runtime.values():
            task = runtime.task
            if task is not None and not task.done():
                task.cancel()
        self._subscription_dispatch_runtime.clear()

    def get_subscription_ids(self) -> list[int]:
        return list(self._subscription_callbacks.keys())

    def _register_subscription_watchdog(self, subscription_id: int, publishing_interval_ms: float, keepalive_count: int) -> None:
        if publishing_interval_ms <= 0:
            self._subscription_watchdog_states.pop(subscription_id, None)
            return
        self._subscription_watchdog_states[subscription_id] = _SubscriptionWatchdogState(
            publishing_interval_ms=publishing_interval_ms,
            keepalive_count=max(int(keepalive_count), 1),
            last_seen_at=asyncio.get_running_loop().time(),
        )

    def _mark_subscription_watchdog_activity(self, subscription_id: int) -> None:
        state = self._subscription_watchdog_states.get(subscription_id)
        if state is None:
            return
        state.last_seen_at = asyncio.get_running_loop().time()
        state.stale_reported = False

    def _get_stale_subscription_ids(self, now: float) -> list[int]:
        if not self.watchdog_settings.stale_detection_enabled:
            return []
        stale_subscription_ids: list[int] = []
        margin = max(self.watchdog_settings.stale_detection_margin, 1.0)
        stale_state_ids_to_prune: list[int] = []
        for subscription_id, state in self._subscription_watchdog_states.items():
            if subscription_id not in self._subscription_callbacks:
                stale_state_ids_to_prune.append(subscription_id)
                continue
            timeout = (state.publishing_interval_ms / 1000.0) * state.keepalive_count * margin
            if timeout <= 0:
                continue
            if (now - state.last_seen_at) <= timeout:
                continue
            if state.stale_reported:
                continue
            state.stale_reported = True
            stale_subscription_ids.append(subscription_id)
        for stale_state_id in stale_state_ids_to_prune:
            self._subscription_watchdog_states.pop(stale_state_id, None)
        return stale_subscription_ids

    def get_next_sequence_number(self, subscription_id: int) -> int:
        last_sequence = self._last_publish_sequence_numbers.get(subscription_id, 0)
        return last_sequence + 1

    def _record_notification_sequence_number(
        self,
        subscription_id: int,
        notification_message: ua.NotificationMessage,
        source: str = "publish",
    ) -> None:
        # Keep-alive messages contain the next sequence number and do not represent
        # a delivered NotificationMessage. Track only messages that include
        # NotificationData so reconnect republish starts from the correct sequence.
        if not notification_message.NotificationData:
            return

        received = int(notification_message.SequenceNumber)
        if subscription_id in self._last_publish_sequence_numbers:
            expected = self.get_next_sequence_number(subscription_id)
            if received != expected:
                self.logger.warning(
                    "Detected notification sequence mismatch on subscription %s (%s): expected %s but received %s",
                    subscription_id,
                    source,
                    expected,
                    received,
                )

        self._last_publish_sequence_numbers[subscription_id] = received

    async def dispatch_notification_message(self, subscription_id: int, notification_message: ua.NotificationMessage) -> None:
        self._record_notification_sequence_number(subscription_id, notification_message, source="republish")
        result = ua.PublishResult(subscription_id, NotificationMessage=notification_message)
        self._enqueue_publish_result(subscription_id, result)

    def ensure_publish_loop_running(self) -> None:
        if self._subscription_callbacks and (not self._publish_task or self._publish_task.done()):
            self._publish_task = asyncio.create_task(self._publish_loop())

    async def restart_publish_loop(self) -> None:
        if self._publish_task is not None and not self._publish_task.done():
            self._publish_task.cancel()
            try:
                await self._publish_task
            except (asyncio.CancelledError, Exception):
                pass
        self._publish_task = None
        self.ensure_publish_loop_running()

    async def republish(self, subscription_id: int, retransmit_sequence_number: int) -> ua.NotificationMessage:
        request = ua.RepublishRequest()
        request.Parameters.SubscriptionId = subscription_id
        request.Parameters.RetransmitSequenceNumber = retransmit_sequence_number
        data = await self._send_request(request)
        response = struct_from_binary(ua.RepublishResponse, data)
        response.ResponseHeader.ServiceResult.check()
        return response.NotificationMessage

    async def _recover_sequence_gap(self, subscription_id: int, expected_sequence: int, received_sequence: int) -> None:
        max_republish = max(int(self.max_republish_messages_per_gap), 0)
        replay_window = _compute_republish_window(expected_sequence, received_sequence, max_republish)
        if replay_window is None:
            return
        replay_start, replay_end_exclusive = replay_window
        missing_count = received_sequence - expected_sequence

        if (replay_end_exclusive - replay_start) < missing_count:
            self.logger.warning(
                "Sequence gap on subscription %s is %s messages; replay capped to %s messages",
                subscription_id,
                missing_count,
                max_republish,
            )

        self.logger.warning(
            "Detected notification sequence gap on subscription %s: expected %s but received %s. Attempting republish",
            subscription_id,
            expected_sequence,
            received_sequence,
        )

        for sequence_number in range(replay_start, replay_end_exclusive):
            try:
                notification_message = await self.republish(subscription_id, sequence_number)
            except ua.UaStatusCodeError as err:
                if err.code == ua.StatusCodes.BadMessageNotAvailable:
                    self.logger.warning(
                        "Republish missing sequence %s for subscription %s is not available on server",
                        sequence_number,
                        subscription_id,
                    )
                    break
                if err.code == ua.StatusCodes.BadSubscriptionIdInvalid:
                    self.logger.warning(
                        "Republish failed for subscription %s because subscription is invalid",
                        subscription_id,
                    )
                    break
                raise
            republished_sequence = int(notification_message.SequenceNumber)
            if republished_sequence != sequence_number:
                self.logger.warning(
                    "Republish returned unexpected sequence for subscription %s: requested %s but got %s",
                    subscription_id,
                    sequence_number,
                    republished_sequence,
                )
                break
            await self.dispatch_notification_message(subscription_id, notification_message)

    async def publish(self, acks: list[ua.SubscriptionAcknowledgement]) -> ua.PublishResponse:
        """
        Send a PublishRequest to the server.
        """
        self.logger.debug("publish %r", acks)
        request = ua.PublishRequest()
        request.Parameters.SubscriptionAcknowledgements = acks if acks else []
        data = await self._send_request(request, timeout=0)
        protocol = self.protocol
        if protocol is None:
            raise ConnectionError("Connection is closed")
        protocol.check_answer(data, "while waiting for publish response")
        try:
            response = struct_from_binary(ua.PublishResponse, data)
        except Exception as ex:
            self.logger.exception("Error parsing notification from server")
            raise UaStructParsingError from ex
        return response

    async def _read_publish_response(
        self,
        ack: SubscriptionAcknowledgement | None,
    ) -> ua.PublishResponse | None:
        try:
            return await self.publish([ack] if ack else [])
        except BadTimeout:  # See Spec. Part 4, 7.28
            # Repeat without acknowledgement
            return None
        except BadNoSubscription:  # See Spec. Part 5, 13.8.1
            # BadNoSubscription is expected to be received after deleting the last subscription.
            # We use this as a signal to exit this task and stop sending PublishRequests.
            self.logger.info("BadNoSubscription received, ignoring because it's probably valid.")
            raise
        except UaStructParsingError:
            # Keep loop alive, parse problems can happen with broken payloads.
            return None

    async def _maybe_recover_gap(
        self,
        subscription_id: int,
        notification_message: ua.NotificationMessage,
    ) -> None:
        if (
            not self.sequence_recovery_settings.auto_republish_on_gap
            or not notification_message.NotificationData
            or subscription_id not in self._last_publish_sequence_numbers
        ):
            return
        expected_sequence = self.get_next_sequence_number(subscription_id)
        received_sequence = int(notification_message.SequenceNumber)
        if received_sequence > expected_sequence:
            await self._recover_sequence_gap(subscription_id, expected_sequence, received_sequence)

    def _build_publish_ack(
        self,
        subscription_id: int,
        notification_message: ua.NotificationMessage,
    ) -> SubscriptionAcknowledgement | None:
        if not notification_message.NotificationData:
            return None
        ack = ua.SubscriptionAcknowledgement()
        ack.SubscriptionId = subscription_id
        ack.SequenceNumber = notification_message.SequenceNumber
        return ack

    async def _handle_publish_response(self, response: ua.PublishResponse) -> SubscriptionAcknowledgement | None:
        subscription_id = response.Parameters.SubscriptionId
        if not subscription_id:
            # The value 0 indicates there were no subscriptions for which a response could be sent.
            raise BadNoSubscription()

        self._mark_subscription_watchdog_activity(subscription_id)
        stale_subscription_ids = self._get_stale_subscription_ids(asyncio.get_running_loop().time())
        if stale_subscription_ids:
            raise SubscriptionStaleError(stale_subscription_ids)

        notification_message = response.Parameters.NotificationMessage
        await self._maybe_recover_gap(subscription_id, notification_message)
        self._enqueue_publish_result(subscription_id, response.Parameters)
        self._record_notification_sequence_number(
            subscription_id,
            notification_message,
            source="publish",
        )
        return self._build_publish_ack(subscription_id, notification_message)

    async def _publish_loop(self):
        """
        Start a loop that sends a publish requests and waits for the publish responses.
        Forward the `PublishResult` to the matching `Subscription` by callback.
        """
        ack: SubscriptionAcknowledgement | None = None
        while not self._closing:
            try:
                response = await self._read_publish_response(ack)
                if response is None:
                    ack = None
                    continue
                ack = await self._handle_publish_response(response)
            except BadNoSubscription:
                return
            except SubscriptionStaleError:
                raise
            except Exception:
                # Keep publish flow alive after unexpected callback or parsing edge cases.
                ack = None
                self.logger.exception("Unexpected error in publish loop")

    async def create_monitored_items(self, params):
        self.logger.info("create_monitored_items")
        request = ua.CreateMonitoredItemsRequest()
        request.Parameters = params
        data = await self._send_request(request)
        response = struct_from_binary(ua.CreateMonitoredItemsResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def delete_monitored_items(self, params):
        self.logger.info("delete_monitored_items")
        request = ua.DeleteMonitoredItemsRequest()
        request.Parameters = params
        data = await self._send_request(request)
        response = struct_from_binary(ua.DeleteMonitoredItemsResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def add_nodes(self, nodestoadd):
        self.logger.info("add_nodes")
        request = ua.AddNodesRequest()
        request.Parameters.NodesToAdd = nodestoadd
        data = await self._send_request(request)
        response = struct_from_binary(ua.AddNodesResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def add_references(self, refs):
        self.logger.info("add_references")
        request = ua.AddReferencesRequest()
        request.Parameters.ReferencesToAdd = refs
        data = await self._send_request(request)
        response = struct_from_binary(ua.AddReferencesResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def delete_references(self, refs):
        self.logger.info("delete")
        request = ua.DeleteReferencesRequest()
        request.Parameters.ReferencesToDelete = refs
        data = await self._send_request(request)
        response = struct_from_binary(ua.DeleteReferencesResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Parameters.Results

    async def delete_nodes(self, params):
        self.logger.info("delete_nodes")
        request = ua.DeleteNodesRequest()
        request.Parameters = params
        data = await self._send_request(request)
        response = struct_from_binary(ua.DeleteNodesResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def call(self, methodstocall):
        request = ua.CallRequest()
        request.Parameters.MethodsToCall = methodstocall
        data = await self._send_request(request)
        response = struct_from_binary(ua.CallResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def history_read(self, params):
        self.logger.info("history_read")
        request = ua.HistoryReadRequest()
        request.Parameters = params
        data = await self._send_request(request)
        response = struct_from_binary(ua.HistoryReadResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def modify_monitored_items(self, params):
        self.logger.info("modify_monitored_items")
        request = ua.ModifyMonitoredItemsRequest()
        request.Parameters = params
        data = await self._send_request(request)
        response = struct_from_binary(ua.ModifyMonitoredItemsResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def register_nodes(self, nodes):
        self.logger.info("register_nodes")
        request = ua.RegisterNodesRequest()
        request.Parameters.NodesToRegister = nodes
        data = await self._send_request(request)
        response = struct_from_binary(ua.RegisterNodesResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Parameters.RegisteredNodeIds

    async def unregister_nodes(self, nodes):
        self.logger.info("unregister_nodes")
        request = ua.UnregisterNodesRequest()
        request.Parameters.NodesToUnregister = nodes
        data = await self._send_request(request)
        response = struct_from_binary(ua.UnregisterNodesResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        # nothing to return for this service

    async def read_attributes(self, nodeids, attr):
        self.logger.info("read_attributes of several nodes")
        request = ua.ReadRequest()
        for nodeid in nodeids:
            rv = ua.ReadValueId()
            rv.NodeId = nodeid
            rv.AttributeId = attr
            request.Parameters.NodesToRead.append(rv)
        data = await self._send_request(request)
        response = struct_from_binary(ua.ReadResponse, data)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def write_attributes(self, nodeids, datavalues, attributeid=ua.AttributeIds.Value):
        """
        Set an attribute of multiple nodes
        datavalue is a ua.DataValue object
        """
        self.logger.info("write_attributes of several nodes")
        request = ua.WriteRequest()
        for idx, nodeid in enumerate(nodeids):
            attr = ua.WriteValue()
            attr.NodeId = nodeid
            attr.AttributeId = attributeid
            attr.Value = datavalues[idx]
            request.Parameters.NodesToWrite.append(attr)
        data = await self._send_request(request)
        response = struct_from_binary(ua.WriteResponse, data)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def set_monitoring_mode(self, params) -> list[ua.uatypes.StatusCode]:
        """
        Update the subscription monitoring mode
        """
        self.logger.info("set_monitoring_mode")
        request = ua.SetMonitoringModeRequest()
        request.Parameters = params
        data = await self._send_request(request)
        response = struct_from_binary(ua.SetMonitoringModeResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Parameters.Results

    async def set_publishing_mode(self, params) -> list[ua.uatypes.StatusCode]:
        """
        Update the subscription publishing mode
        """
        self.logger.info("set_publishing_mode")
        request = ua.SetPublishingModeRequest()
        request.Parameters = params
        data = await self._send_request(request)
        response = struct_from_binary(ua.SetPublishingModeResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Parameters.Results

    async def transfer_subscriptions(self, params: ua.TransferSubscriptionsParameters) -> list[ua.TransferResult]:
        # Subscriptions aren't bound to a Session and can be transferred!
        # https://reference.opcfoundation.org/Core/Part4/v104/5.13.7/
        request = ua.TransferSubscriptionsRequest()
        request.Parameters = params
        data = await self._send_request(request)
        response = struct_from_binary(ua.TransferSubscriptionsResponse, data)
        response.ResponseHeader.ServiceResult.check()
        return response.Parameters.Results
