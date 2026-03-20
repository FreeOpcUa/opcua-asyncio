"""
Low-level OPC-UA client for connection, secure channel, and discovery services.

This module provides the sessionless foundation for OPC-UA operations.
Session-specific operations (browse, read, write, subscriptions) are
handled by UaSession instances created via create_session_object().
"""

from __future__ import annotations

import asyncio
import copy
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

from asyncua import ua
from asyncua.ua.uaerrors._base import UaError

from ..common.connection import SecureConnection, TransportLimits
from ..common.utils import wait_for
from ..crypto import security_policies
from ..ua.ua_binary import (
    header_from_binary,
    nodeid_from_binary,
    struct_from_binary,
    struct_to_binary,
    uatcp_to_binary,
)
from ..ua.uaerrors import BadSessionClosed, BadUserAccessDenied
from ..ua.uaprotocol_auto import OpenSecureChannelResult
from .ua_session import (
    SessionState,
    SubscriptionDispatchOverflowError,
    SubscriptionDispatchOverflowPolicy,
    SubscriptionStaleError,
    UaSession,
)

__all__ = [
    "SessionState",
    "SubscriptionDispatchOverflowError",
    "SubscriptionDispatchOverflowPolicy",
    "SubscriptionStaleError",
    "UASocketProtocol",
    "UaClient",
    "UaSession",
]


class UASocketProtocol(asyncio.Protocol):
    """Handle socket connection and send OPC-UA messages."""

    INITIALIZED = "initialized"
    OPEN = "open"
    CLOSED = "closed"

    def __init__(
        self,
        timeout: float = 1,
        security_policy: security_policies.SecurityPolicy | None = None,
        limits: TransportLimits | None = None,
    ) -> None:
        """Initialize protocol handler.

        Args:
            timeout: Request timeout in seconds
            security_policy: Security policy for encryption/signing
            limits: Transport limits (max message size, chunk count, etc.)
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
            limits = copy.deepcopy(limits)

        if security_policy is None:
            security_policy = security_policies.SecurityPolicyNone()

        self._connection = SecureConnection(security_policy, limits)
        self.state = self.INITIALIZED
        self.closed: bool = False
        self._open_secure_channel_exchange: (
            ua.OpenSecureChannelResponse
            | ua.OpenSecureChannelParameters
            | None
        ) = None
        self.pre_request_hook: Callable[[], Awaitable[None]] | None = None

    def connection_made(self, transport: asyncio.Transport) -> None:  # type: ignore[override]
        """Called when connection is established."""
        self.state = self.OPEN
        self.transport = transport

    def connection_lost(self, exc: Exception | None) -> None:
        """Called when connection is lost."""
        self.logger.info("Socket connection closed")
        self.state = self.CLOSED
        self.transport = None

    def data_received(self, data: bytes) -> None:
        """Process received data."""
        if self.receive_buffer:
            data = self.receive_buffer + data
            self.receive_buffer = None
        self._process_received_data(data)

    def _process_received_data(self, data: bytes) -> None:
        """Parse OPC-UA messages from received data."""
        buf = ua.utils.Buffer(data)
        while True:
            try:
                try:
                    header = header_from_binary(buf)
                except ua.utils.NotEnoughData:
                    self.logger.debug(
                        "Incomplete header, waiting for more data"
                    )
                    self.receive_buffer = data
                    return

                if len(buf) < header.body_size:
                    self.logger.debug(
                        "Incomplete message body, waiting for more data"
                    )
                    self.receive_buffer = data
                    return

                msg = self._connection.receive_from_header_and_body(
                    header, buf
                )
                self._process_received_message(msg)

                if header.MessageType == ua.MessageType.SecureOpen:
                    params: ua.OpenSecureChannelParameters = (
                        self._open_secure_channel_exchange
                    )
                    response: ua.OpenSecureChannelResponse = (
                        struct_from_binary(
                            ua.OpenSecureChannelResponse, msg.body()
                        )
                    )
                    response.ResponseHeader.ServiceResult.check()
                    self._open_secure_channel_exchange = response
                    self._connection.set_channel(
                        response.Parameters,
                        params.RequestType,
                        params.ClientNonce,
                    )

                if not buf:
                    return
                data = bytes(buf)
            except ua.UaStatusCodeError as e:
                self.logger.error("OPC-UA status error: %s", e)
                self._fail_all_pending(e)
                self.disconnect_socket()
                return
            except Exception:
                self.logger.exception(
                    "Unexpected error parsing message from server"
                )
                self.disconnect_socket()
                return

    def _process_received_message(
        self, msg: ua.Message | ua.Acknowledge | ua.ErrorMessage
    ) -> None:
        """Process parsed OPC-UA message."""
        if msg is None:
            pass
        elif isinstance(msg, ua.Message):
            self._call_callback(msg.request_id(), msg.body())
        elif isinstance(msg, ua.Acknowledge):
            self._call_callback(0, msg)
        elif isinstance(msg, ua.ErrorMessage):
            self.logger.fatal("Received error message: %r", msg)
            self.disconnect_socket()
            if msg.Error is not None:
                msg.Error.check()
        else:
            raise ua.UaError(f"Unsupported message type: {msg}")

    def _send_request(
        self,
        request: Any,
        timeout: float = 1,
        message_type: ua.MessageType = ua.MessageType.SecureMessage,
        authentication_token: ua.NodeId | None = None,
    ) -> asyncio.Future:
        """Send OPC-UA request, return future for response."""
        self._setup_request_header(
            request.RequestHeader,
            timeout,
            authentication_token=authentication_token,
        )
        self.logger.debug("Sending: %s", request)

        try:
            binreq = struct_to_binary(request)
        except Exception:
            self._request_handle -= 1
            raise

        self._request_id += 1
        future: asyncio.Future = asyncio.get_running_loop().create_future()
        self._callbackmap[self._request_id] = future

        if self._connection.next_security_token.TokenId != 0:
            self._connection.revolve_tokens()

        msg = self._connection.message_to_binary(
            binreq, message_type=message_type, request_id=self._request_id
        )
        if self.transport is not None:
            self.transport.write(msg)
        return future

    async def send_request(
        self,
        request: Any,
        timeout: float | None = None,
        message_type: ua.MessageType = ua.MessageType.SecureMessage,
        authentication_token: ua.NodeId | None = None,
    ) -> bytes:
        """Send request and wait for response."""
        timeout = self.timeout if timeout is None else timeout
        if self.pre_request_hook:
            await self.pre_request_hook()

        try:
            data = await wait_for(
                self._send_request(
                    request,
                    timeout,
                    message_type,
                    authentication_token=authentication_token,
                ),
                timeout if timeout else None,
            )
        except UaError as ex:
            raise ex
        except (TimeoutError, asyncio.TimeoutError) as ex:
            if self.state != self.OPEN:
                raise ConnectionError("Connection is closed") from None
            raise ConnectionError(
                "Request timed out waiting for server response"
            ) from ex
        except Exception as ex:
            if self.state != self.OPEN:
                raise ConnectionError("Connection is closed") from None
            raise Exception(
                "Error sending request to OPC-UA server"
            ) from ex

        self.check_answer(data, f" in response to {request.__class__.__name__}")
        return data

    def check_answer(self, data: Any, context: str) -> bool:
        """Verify response is valid OPC-UA message."""
        if hasattr(data, "copy"):
            data_buffer = data.copy()
        else:
            data_buffer = ua.utils.Buffer(bytes(data))

        typeid = nodeid_from_binary(data_buffer)
        if typeid == ua.FourByteNodeId(
            ua.ObjectIds.ServiceFault_Encoding_DefaultBinary
        ):
            hdr = struct_from_binary(ua.ResponseHeader, data_buffer)
            self.logger.warning(
                "ServiceFault (%s, diagnostics: %s) %s",
                hdr.ServiceResult.name,
                hdr.ServiceDiagnostics,
                context,
            )
            hdr.ServiceResult.check()
            return False
        return True

    def _fail_all_pending(self, exc: Exception) -> None:
        """Signal all pending requests of error."""
        for fut in self._callbackmap.values():
            if not fut.done():
                fut.set_exception(exc)
        self._callbackmap.clear()

    def _call_callback(self, request_id: int, body: bytes) -> None:
        """Call response callback for request."""
        try:
            self._callbackmap[request_id].set_result(body)
        except KeyError as ex:
            raise ua.UaError(
                f"No request found for id {request_id}, body was {body!r}"
            ) from ex
        except asyncio.InvalidStateError:
            if not self.closed:
                self.logger.warning(
                    "Future for request id %s already done", request_id
                )
                return
            self.logger.debug(
                "Future for request id %s not handled due to disconnect",
                request_id,
            )
        del self._callbackmap[request_id]

    def _setup_request_header(
        self,
        hdr: ua.RequestHeader,
        timeout: float = 1,
        authentication_token: ua.NodeId | None = None,
    ) -> None:
        """Prepare request header with token and timeouts."""
        hdr.AuthenticationToken = (
            self.authentication_token
            if authentication_token is None
            else authentication_token
        )
        self._request_handle += 1
        hdr.RequestHandle = self._request_handle
        hdr.TimeoutHint = int(timeout * 1000)

    def disconnect_socket(self) -> None:
        """Close socket connection."""
        self.logger.info("Closing socket")
        if self.transport:
            self.transport.close()
        else:
            self.logger.warning("disconnect_socket but transport is None")

    async def send_hello(
        self,
        url: str,
        max_messagesize: int = 0,
        max_chunkcount: int = 0,
    ) -> ua.Acknowledge:
        """Send HELLO message for protocol handshake."""
        hello = ua.Hello()
        hello.EndpointUrl = url
        hello.MaxMessageSize = max_messagesize
        hello.MaxChunkCount = max_chunkcount
        ack: asyncio.Future = asyncio.Future()
        self._callbackmap[0] = ack
        if self.transport is not None:
            self.transport.write(uatcp_to_binary(ua.MessageType.Hello, hello))
        return await wait_for(ack, self.timeout)

    async def open_secure_channel(
        self, params: ua.OpenSecureChannelParameters
    ) -> OpenSecureChannelResult:
        """Open secure channel with server."""
        self.logger.info("Opening secure channel")
        request = ua.OpenSecureChannelRequest()
        request.Parameters = params

        if self._open_secure_channel_exchange is not None:
            raise UaError(
                "Secure channel request already in progress"
            )

        self._open_secure_channel_exchange = params
        await wait_for(
            self._send_request(
                request, message_type=ua.MessageType.SecureOpen
            ),
            self.timeout,
        )
        exchange = self._open_secure_channel_exchange
        self._open_secure_channel_exchange = None
        if isinstance(exchange, ua.OpenSecureChannelResponse):
            return exchange.Parameters
        raise UaError("Secure channel open failed: missing response")

    async def close_secure_channel(self) -> None:
        """Close secure channel.

        Note: Most servers close the socket after this per OPC-UA spec.
        """
        self.logger.info("Closing secure channel")
        request = ua.CloseSecureChannelRequest()
        future = self._send_request(
            request, message_type=ua.MessageType.SecureClose
        )
        future.cancel()
        self._callbackmap.clear()


class UaClient:
    """
    Sessionless OPC-UA client for discovery and session management.

    Handles connection establishment, secure channel negotiation, and
    session creation/activation. Session-dependent operations are delegated
    to UaSession instances.

    For session-specific operations (browse, read, write, subscriptions),
    use create_session_object() to get a UaSession instance.
    """

    class CONNECTION_STATE:
        """Connection state enumeration."""

        DISCONNECTED = 1
        CONNECTING = 2
        CHANNEL_READY = 3
        DISCONNECTING = 4

    def __init__(self, timeout: float = 1.0) -> None:
        """Initialize sessionless client.

        Args:
            timeout: Default request timeout in seconds
        """
        self.logger = logging.getLogger(f"{__name__}.UaClient")
        self._timeout = timeout
        self.protocol: UASocketProtocol | None = None
        self.security_policy = security_policies.SecurityPolicyNone()

        # State management
        self._connection_state = UaClient.CONNECTION_STATE.DISCONNECTED
        self._ready_event = asyncio.Event()
        self._closing = False
        self._internal_service_call_depth = 0

        # Session registry
        self._sessions: dict[int, UaSession] = {}
        self._session_id_counter = 0
        self._default_session: UaSession | None = None

        # Pre-request hook for diagnostics
        self._pre_request_hook: Callable[[], Awaitable[None]] | None = None

    @property
    def connection_state(self) -> int:
        """Get current connection state."""
        return self._connection_state

    @property
    def pre_request_hook(self) -> Callable[[], Awaitable[None]] | None:
        """Get pre-request hook."""
        return self._pre_request_hook

    @pre_request_hook.setter
    def pre_request_hook(
        self, hook: Callable[[], Awaitable[None]] | None
    ) -> None:
        """Set pre-request hook."""
        self._pre_request_hook = hook
        if self.protocol:
            self.protocol.pre_request_hook = hook

    # ========== CONNECTION MANAGEMENT ==========

    async def connect_socket(self, host: str, port: int) -> None:
        """Establish TCP connection to OPC-UA server.

        Args:
            host: Server hostname or IP address
            port: Server port number

        Raises:
            TimeoutError: If connection cannot be established within timeout
            ConnectionError: If socket creation fails
        """
        self.logger.info("Opening connection to %s:%d", host, port)
        self._closing = False
        self.set_connection_state(UaClient.CONNECTION_STATE.CONNECTING)

        try:
            await asyncio.wait_for(
                asyncio.get_running_loop().create_connection(
                    self._make_protocol, host, port
                ),
                self._timeout,
            )
        except (TimeoutError, asyncio.TimeoutError) as ex:
            self.set_connection_state(UaClient.CONNECTION_STATE.DISCONNECTED)
            raise ConnectionError(
                f"Failed to connect to {host}:{port}"
            ) from ex

    def disconnect_socket(self) -> None:
        """Close socket and cleanup."""
        self.logger.info("Disconnecting socket")

        if not self.protocol:
            self.set_connection_state(UaClient.CONNECTION_STATE.DISCONNECTED)
            return

        if self.protocol.state == UASocketProtocol.CLOSED:
            self.logger.warning("Socket already closed")
            self.set_connection_state(UaClient.CONNECTION_STATE.DISCONNECTED)
            for session in self._sessions.values():
                session.on_transport_lost()
            return

        self.protocol.disconnect_socket()
        self.protocol = None
        self.set_connection_state(UaClient.CONNECTION_STATE.DISCONNECTED)
        for session in self._sessions.values():
            session.on_transport_lost()

    # ========== SECURE CHANNEL ==========

    async def send_hello(
        self,
        url: str,
        max_messagesize: int = 0,
        max_chunkcount: int = 0,
    ) -> ua.Acknowledge:
        """Send HELLO message to establish protocol version.

        Args:
            url: Server endpoint URL
            max_messagesize: Maximum message size (0 = use default)
            max_chunkcount: Maximum chunk count (0 = use default)

        Returns:
            Server's acknowledgement message

        Raises:
            ConnectionError: If socket not connected
        """
        if not self.protocol:
            raise ConnectionError("Socket not connected")
        return await self.protocol.send_hello(
            url, max_messagesize, max_chunkcount
        )

    async def open_secure_channel(
        self, params: ua.OpenSecureChannelParameters
    ) -> OpenSecureChannelResult:
        """Open secure channel with server.

        Transitions state from CONNECTING to CHANNEL_READY.

        Args:
            params: OpenSecureChannelParameters with token, nonce, etc.

        Returns:
            Server's channel response

        Raises:
            UaError: If channel establishment fails
            ConnectionError: If socket not connected
        """
        self.logger.info("Opening secure channel")

        if not self.protocol:
            raise ConnectionError("Socket not connected")

        result = await self.protocol.open_secure_channel(params)

        if (
            self._connection_state
            != UaClient.CONNECTION_STATE.CHANNEL_READY
        ):
            self.set_connection_state(UaClient.CONNECTION_STATE.CHANNEL_READY)
        for session in self._sessions.values():
            if session.state == SessionState.SUSPENDED:
                session.on_transport_restored()

        return result

    async def close_secure_channel(self) -> None:
        """Close secure channel (may close socket per OPC-UA spec)."""
        self.logger.info("Closing secure channel")

        if not self.protocol or self.protocol.state == UASocketProtocol.CLOSED:
            self.logger.warning("Channel already closed")
            self.set_connection_state(UaClient.CONNECTION_STATE.DISCONNECTED)
            return

        self.set_connection_state(UaClient.CONNECTION_STATE.DISCONNECTING)
        for session in self._sessions.values():
            session.on_transport_lost()
        await self.protocol.close_secure_channel()

    # ========== SESSION LIFECYCLE ==========

    async def create_session(
        self, parameters: ua.CreateSessionParameters
    ) -> ua.CreateSessionResult:
        """Create session on server (low-level operation).

        Prefer create_session_object() for high-level usage.

        Args:
            parameters: CreateSessionParameters with description, timeout, etc.

        Returns:
            Session parameters including session ID, authentication token

        Raises:
            BadUserAccessDenied: If authentication fails
            ConnectionError: If secure channel not open
        """
        self.logger.info("Creating session")
        self._closing = False
        if self.protocol:
            self.protocol.closed = False

        request = ua.CreateSessionRequest()
        request.Parameters = parameters

        data = await self._send_request(request, bypass_ready_gate=True)
        response = struct_from_binary(ua.CreateSessionResponse, data)
        self.logger.debug("CreateSessionResponse: %s", response)
        response.ResponseHeader.ServiceResult.check()

        if self._default_session is None:
            self._default_session = UaSession(
                self,
                response.Parameters.SessionId,
                response.Parameters.AuthenticationToken,
            )
            self._default_session._set_state(SessionState.ESTABLISHING)
            self._register_session(self._default_session)
        else:
            self._default_session.session_id = response.Parameters.SessionId
            self._default_session.authentication_token = (
                response.Parameters.AuthenticationToken
            )
            self._default_session._set_state(SessionState.ESTABLISHING)

        return response.Parameters

    async def activate_session(
        self,
        parameters: ua.ActivateSessionParameters,
        session: UaSession | None = None,
    ) -> ua.ActivateSessionResult:
        """Activate (authenticate) existing session.

        Args:
            parameters: ActivateSessionParameters with credentials, etc.

        Returns:
            ActivateSessionResult with new session cookie

        Raises:
            BadUserAccessDenied: If credentials invalid
            ConnectionError: If secure channel closed
        """
        self.logger.info("Activating session")

        request = ua.ActivateSessionRequest()
        request.Parameters = parameters

        target_session = session if session is not None else self._default_session
        if target_session is None:
            raise UaError(
                "No target session for activate_session. "
                "Pass session=... or create a default session first."
            )

        data = await self._send_request(
            request,
            bypass_ready_gate=True,
            authentication_token=target_session.authentication_token,
        )
        response = struct_from_binary(ua.ActivateSessionResponse, data)
        self.logger.debug("ActivateSessionResponse: %s", response)
        response.ResponseHeader.ServiceResult.check()

        if target_session is not None:
            target_session._set_state(SessionState.READY)
        for registered_session in self._sessions.values():
            if (
                registered_session is not target_session
                and registered_session.state == SessionState.RECOVERING
            ):
                registered_session._set_state(SessionState.READY)
        return response.Parameters

    async def close_session(
        self,
        delete_subscriptions: bool = True,
        session: UaSession | None = None,
    ) -> None:
        """Close session on server.

        Args:
            delete_subscriptions: If True, delete all subscriptions

        Note:
            Ignores BadSessionClosed and BadUserAccessDenied (expected
            for some edge cases or older server versions)
        """
        target_session = session if session is not None else self._default_session
        if target_session is None:
            self.logger.debug("close_session called with no active session")
            return

        self.logger.info("Closing session %s", target_session.session_id)

        protocol = self.protocol
        can_send_close = protocol is not None and protocol.state != UASocketProtocol.CLOSED
        if can_send_close:
            try:
                data = await self._send_close_session_request(
                    delete_subscriptions,
                    authentication_token=target_session.authentication_token,
                )
                response = struct_from_binary(ua.CloseSessionResponse, data)

                try:
                    response.ResponseHeader.ServiceResult.check()
                except (BadSessionClosed, BadUserAccessDenied):
                    self.logger.debug("Ignored close_session error (expected)")
            except ConnectionError:
                self.logger.debug(
                    "Skipping CloseSessionRequest for %s because connection is closed",
                    target_session.session_id,
                )
        else:
            self.logger.debug(
                "Skipping CloseSessionRequest for %s because protocol is not open",
                target_session.session_id,
            )

        try:
            await target_session._close_local()
        finally:
            self._unregister_session(target_session)
            if self._default_session is target_session:
                self._default_session = None
            if self._default_session is None and self._sessions:
                self._default_session = next(iter(self._sessions.values()))

    # ========== SESSIONLESS DISCOVERY SERVICES ==========

    async def get_endpoints(
        self, params: ua.GetEndpointsParameters
    ) -> list[ua.EndpointDescription]:
        """Query available server endpoints (sessionless).

        Args:
            params: GetEndpointsParameters with URL, locale, profiles

        Returns:
            List of available endpoints
        """
        self.logger.debug("get_endpoints")

        request = ua.GetEndpointsRequest()
        request.Parameters = params

        data = await self._send_request(request, bypass_ready_gate=True)
        response = struct_from_binary(ua.GetEndpointsResponse, data)
        self.logger.debug("GetEndpointsResponse: %d endpoints",
                          len(response.Endpoints))
        response.ResponseHeader.ServiceResult.check()

        return response.Endpoints

    async def find_servers(
        self, params: ua.FindServersParameters
    ) -> list[ua.ApplicationDescription]:
        """Find servers on discovery server (sessionless).

        Args:
            params: FindServersParameters

        Returns:
            List of available servers
        """
        self.logger.debug("find_servers")

        request = ua.FindServersRequest()
        request.Parameters = params

        data = await self._send_request(request, bypass_ready_gate=True)
        response = struct_from_binary(ua.FindServersResponse, data)
        response.ResponseHeader.ServiceResult.check()

        return response.Servers

    async def find_servers_on_network(
        self, params: ua.FindServersOnNetworkParameters
    ) -> ua.FindServersOnNetworkResult:
        """Find servers on local network via mDNS (sessionless).

        Args:
            params: FindServersOnNetworkParameters

        Returns:
            Discovery result
        """
        self.logger.debug("find_servers_on_network")

        request = ua.FindServersOnNetworkRequest()
        request.Parameters = params

        data = await self._send_request(request, bypass_ready_gate=True)
        response = struct_from_binary(ua.FindServersOnNetworkResponse, data)
        response.ResponseHeader.ServiceResult.check()

        return response.Parameters

    async def register_server(
        self, registered_server: ua.RegisteredServer
    ) -> None:
        """Register server with discovery server (sessionless).

        Args:
            registered_server: Server registration details
        """
        self.logger.debug("register_server")

        request = ua.RegisterServerRequest()
        request.Server = registered_server

        data = await self._send_request(request, bypass_ready_gate=True)
        response = struct_from_binary(ua.RegisterServerResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()

    async def unregister_server(
        self, registered_server: ua.RegisteredServer
    ) -> None:
        """Unregister server from discovery server (sessionless).

        Args:
            registered_server: Server to unregister
        """
        self.logger.debug("unregister_server")

        request = ua.RegisterServerRequest()
        request.Server = registered_server

        data = await self._send_request(request, bypass_ready_gate=True)
        response = struct_from_binary(ua.RegisterServerResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()

    async def register_server2(
        self, params: ua.RegisterServer2Parameters
    ) -> list[ua.StatusCode]:
        """Register server with extended parameters (sessionless).

        Args:
            params: RegisterServer2Parameters

        Returns:
            List of configuration result status codes
        """
        self.logger.debug("register_server2")

        request = ua.RegisterServer2Request()
        request.Parameters = params

        data = await self._send_request(request, bypass_ready_gate=True)
        response = struct_from_binary(ua.RegisterServer2Response, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()

        return response.ConfigurationResults

    async def unregister_server2(
        self, params: ua.RegisterServer2Parameters
    ) -> list[ua.StatusCode]:
        """Unregister server with extended parameters (sessionless).

        Args:
            params: RegisterServer2Parameters

        Returns:
            List of configuration result status codes
        """
        self.logger.debug("unregister_server2")

        request = ua.RegisterServer2Request()
        request.Parameters = params

        data = await self._send_request(request, bypass_ready_gate=True)
        response = struct_from_binary(ua.RegisterServer2Response, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()

        return response.ConfigurationResults

    # ========== INTERNAL & UTILITIES ==========

    def _make_protocol(self) -> UASocketProtocol:
        """Create new socket protocol handler."""
        self.protocol = UASocketProtocol(
            self._timeout, security_policy=self.security_policy
        )
        self.protocol.pre_request_hook = self._pre_request_hook
        return self.protocol

    def set_connection_state(self, state: int) -> None:
        """Update connection state and signal ready event."""
        self._connection_state = state
        if state == UaClient.CONNECTION_STATE.CHANNEL_READY:
            self._ready_event.set()
        else:
            self._ready_event.clear()

    def try_set_connection_state(self, state: int) -> bool:
        """Attempt guarded state transition (prevents backward states)."""
        if self._connection_state == UaClient.CONNECTION_STATE.DISCONNECTING and state == UaClient.CONNECTION_STATE.CHANNEL_READY:
            self.logger.warning(
                "Ignoring state transition %s -> %s during disconnect",
                self._connection_state,
                state,
            )
            return False
        self.set_connection_state(state)
        return True

    async def await_ready(self, timeout: float | None = None) -> None:
        """Block until CHANNEL_READY state.

        Args:
            timeout: Seconds to wait (default: client timeout)

        Raises:
            ConnectionError: If timeout expires before ready
        """
        if (
            self._connection_state
            == UaClient.CONNECTION_STATE.CHANNEL_READY
        ):
            return

        wait_timeout = self._timeout if timeout is None else timeout
        try:
            await asyncio.wait_for(
                self._ready_event.wait(), wait_timeout
            )
        except (TimeoutError, asyncio.TimeoutError) as ex:
            raise ConnectionError("Client is not ready") from ex

    @asynccontextmanager
    async def internal_service_calls(self) -> AsyncIterator[None]:
        """Context manager for internal operations bypassing ready gate."""
        self._internal_service_call_depth += 1
        try:
            yield
        finally:
            self._internal_service_call_depth -= 1

    async def _send_request(
        self,
        request: Any,
        timeout: float | None = None,
        message_type: ua.MessageType = ua.MessageType.SecureMessage,
        bypass_ready_gate: bool = False,
        authentication_token: ua.NodeId | None = None,
    ) -> bytes:
        """Send OPC-UA request and wait for response.

        Args:
            request: OPC-UA request structure
            timeout: Override default timeout
            message_type: Message type (SecureMessage, SecureOpen, etc.)
            bypass_ready_gate: Skip CHANNEL_READY check if True

        Returns:
            Response body (usually parsed by caller)

        Raises:
            ConnectionError: If channel not open or request times out
        """
        if (
            not bypass_ready_gate
            and self._internal_service_call_depth == 0
        ):
            await self.await_ready(timeout=timeout)

        protocol = self.protocol
        if not protocol or protocol.state != UASocketProtocol.OPEN:
            self.set_connection_state(UaClient.CONNECTION_STATE.DISCONNECTED)
            raise ConnectionError("Connection is closed")

        return await protocol.send_request(
            request,
            timeout=timeout,
            message_type=message_type,
            authentication_token=authentication_token,
        )

    async def _send_close_session_request(
        self,
        delete_subscriptions: bool,
        authentication_token: ua.NodeId | None = None,
    ) -> bytes:
        """Send CloseSessionRequest to server."""
        request = ua.CloseSessionRequest()
        request.DeleteSubscriptions = delete_subscriptions
        return await self._send_request(
            request,
            bypass_ready_gate=True,
            authentication_token=authentication_token,
        )

    def set_security(
        self, policy: security_policies.SecurityPolicy
    ) -> None:
        """Configure security policy before connecting.

        Must be called before connect_socket().

        Args:
            policy: SecurityPolicy to apply
        """
        self.security_policy = policy

    # ========== SESSION MANAGEMENT ==========

    async def create_session_object(
        self,
        parameters: ua.CreateSessionParameters,
        make_default: bool = True,
        activate_parameters: ua.ActivateSessionParameters | None = None,
    ) -> UaSession:
        """Create and activate a new UaSession object.

        This is the recommended way to create sessions. It handles creation,
        activation, and wrapping in a UaSession for high-level operations.

        Args:
            parameters: CreateSessionParameters (description, timeout, etc.)
            make_default: If True, creates/reuses the default session slot.
                If False, creates an additional non-default session.
            activate_parameters: Optional ActivateSessionParameters used to
                authenticate this specific session (for example per-session
                user identity tokens). If omitted, anonymous activation is used.

        Returns:
            Ready-to-use UaSession object

        Raises:
            BadUserAccessDenied: If activation fails
            ConnectionError: If secure channel not open

        Example:
            >>> client = UaClient()
            >>> await client.connect_socket("localhost", 4840)
            >>> params = ua.CreateSessionParameters()
            >>> session = await client.create_session_object(params)
            >>> nodes = await session.browse(...)
            >>> await session.close()
        """
        self.logger.info("Creating session object")

        if make_default:
            await self.create_session(parameters)
            session = self._require_default_session()
        else:
            request = ua.CreateSessionRequest()
            request.Parameters = parameters

            data = await self._send_request(request, bypass_ready_gate=True)
            response = struct_from_binary(ua.CreateSessionResponse, data)
            self.logger.debug("CreateSessionResponse (additional): %s", response)
            response.ResponseHeader.ServiceResult.check()

            session = UaSession(
                self,
                response.Parameters.SessionId,
                response.Parameters.AuthenticationToken,
            )
            session._set_state(SessionState.ESTABLISHING)
            self._register_session(session)

        try:
            # Activate the session
            activate_params = (
                activate_parameters
                if activate_parameters is not None
                else ua.ActivateSessionParameters()
            )
            await self.activate_session(activate_params, session=session)

            self.set_connection_state(UaClient.CONNECTION_STATE.CHANNEL_READY)
            self.logger.info("Session %s activated", session.session_id)
            return session

        except Exception as ex:
            # Cleanup on failure
            try:
                await self.close_session(
                    delete_subscriptions=True,
                    session=session,
                )
            except Exception:
                pass
            raise ex

    def get_sessions(self) -> list[UaSession]:
        """Get list of active sessions.

        Returns:
            Copy of active session list
        """
        return list(self._sessions.values())

    async def close_all_sessions(
        self, delete_subscriptions: bool = True
    ) -> None:
        """Close all active sessions.

        Args:
            delete_subscriptions: If True, delete subscriptions on server
        """
        sessions = list(self._sessions.values())
        for session in sessions:
            try:
                await session.close(delete_subscriptions=delete_subscriptions)
            except Exception:
                self.logger.exception("Error closing session %s",
                                      session.session_id)

    def _register_session(self, session: UaSession) -> None:
        """Track newly created session."""
        self._session_id_counter += 1
        session.registry_session_id = self._session_id_counter
        self._sessions[self._session_id_counter] = session

    def _unregister_session(self, session: UaSession) -> None:
        """Remove closed session from registry."""
        if session.registry_session_id is not None:
            self._sessions.pop(session.registry_session_id, None)

    # ========== BACKWARD-COMPAT SESSION DELEGATION ==========

    def _require_default_session(self) -> UaSession:
        """Return the default active session used by legacy UaClient APIs."""
        if self._default_session is None:
            raise UaError(
                "No active session. Call create_session/activate_session first."
            )
        return self._default_session

    @property
    def _publish_task(self) -> asyncio.Task[None] | None:
        if self._default_session is None:
            return None
        return self._default_session._publish_task

    async def browse(self, parameters: ua.BrowseParameters) -> list[ua.BrowseResult]:
        return await self._require_default_session().browse(parameters)

    async def browse_next(self, parameters: ua.BrowseNextParameters) -> list[ua.BrowseResult]:
        return await self._require_default_session().browse_next(parameters)

    async def read(self, parameters: ua.ReadParameters) -> list[ua.DataValue]:
        return await self._require_default_session().read(parameters)

    async def write(self, parameters: ua.WriteParameters) -> list[ua.StatusCode]:
        return await self._require_default_session().write(parameters)

    async def history_read(self, parameters: ua.HistoryReadParameters) -> list[ua.HistoryReadResult]:
        return await self._require_default_session().history_read(parameters)

    async def add_nodes(self, params: ua.AddNodesParameters | list[ua.AddNodesItem]) -> list[ua.AddNodesResult]:
        return await self._require_default_session().add_nodes(params)

    async def add_references(self, refs: list[ua.AddReferencesItem]) -> list[ua.StatusCode]:
        return await self._require_default_session().add_references(refs)

    async def delete_nodes(self, params: ua.DeleteNodesParameters) -> list[ua.StatusCode]:
        return await self._require_default_session().delete_nodes(params)

    async def delete_references(self, refs: list[ua.DeleteReferencesItem]) -> list[ua.StatusCode]:
        return await self._require_default_session().delete_references(refs)

    async def call(self, methodstocall: list[ua.CallMethodRequest]) -> list[ua.CallMethodResult]:
        return await self._require_default_session().call(methodstocall)

    async def translate_browsepaths_to_nodeids(
        self, browse_paths: list[ua.BrowsePath]
    ) -> list[ua.BrowsePathResult]:
        return await self._require_default_session().translate_browsepaths_to_nodeids(browse_paths)

    async def register_nodes(self, nodes: list[ua.NodeId]) -> list[ua.NodeId]:
        return await self._require_default_session().register_nodes(nodes)

    async def unregister_nodes(self, nodes: list[ua.NodeId]) -> None:
        await self._require_default_session().unregister_nodes(nodes)

    async def create_subscription(
        self, params: ua.CreateSubscriptionParameters, callback: Callable[[ua.PublishResult], Any]
    ) -> ua.CreateSubscriptionResult:
        return await self._require_default_session().create_subscription(params, callback)

    async def modify_subscription(self, params: ua.ModifySubscriptionParameters) -> ua.ModifySubscriptionResult:
        return await self._require_default_session().modify_subscription(params)

    async def update_subscription(self, params: ua.ModifySubscriptionParameters) -> ua.ModifySubscriptionResult:
        """Backward-compatible alias for modify_subscription."""
        return await self.modify_subscription(params)

    async def delete_subscriptions(
        self, params: ua.DeleteSubscriptionsParameters | list[int]
    ) -> list[ua.StatusCode]:
        actual_params = params
        if isinstance(params, list):
            actual_params = ua.DeleteSubscriptionsParameters()
            actual_params.SubscriptionIds = params
        return await self._require_default_session().delete_subscriptions(actual_params)

    async def create_monitored_items(
        self, params: ua.CreateMonitoredItemsParameters
    ) -> list[ua.MonitoredItemCreateResult]:
        return await self._require_default_session().create_monitored_items(params)

    async def modify_monitored_items(
        self, params: ua.ModifyMonitoredItemsParameters
    ) -> list[ua.MonitoredItemModifyResult]:
        return await self._require_default_session().modify_monitored_items(params)

    async def delete_monitored_items(
        self, params: ua.DeleteMonitoredItemsParameters
    ) -> list[ua.StatusCode]:
        return await self._require_default_session().delete_monitored_items(params)

    async def transfer_subscriptions(
        self, params: ua.TransferSubscriptionsParameters
    ) -> list[ua.TransferResult]:
        return await self._require_default_session().transfer_subscriptions(params)

    async def set_monitoring_mode(
        self, params: ua.SetMonitoringModeParameters
    ) -> list[ua.StatusCode]:
        return await self._require_default_session().set_monitoring_mode(params)

    async def set_publishing_mode(
        self, params: ua.SetPublishingModeParameters
    ) -> list[ua.StatusCode]:
        return await self._require_default_session().set_publishing_mode(params)

    async def republish(
        self, subscription_id: int, retransmit_sequence_number: int
    ) -> ua.NotificationMessage:
        return await self._require_default_session().republish(
            subscription_id, retransmit_sequence_number
        )

    async def dispatch_notification_message(
        self, subscription_id: int, notification_message: ua.NotificationMessage
    ) -> None:
        await self._require_default_session().dispatch_notification_message(
            subscription_id, notification_message
        )

    async def restart_publish_loop(self) -> None:
        await self._require_default_session().restart_publish_loop()

    async def inform_subscriptions(self, status: ua.StatusCode) -> None:
        await self._require_default_session().inform_subscriptions(status)

    def get_subscription_ids(self) -> list[int]:
        return self._require_default_session().get_subscription_ids()

    def get_next_sequence_number(self, subscription_id: int) -> int:
        return self._require_default_session().get_next_sequence_number(subscription_id)

    async def read_attributes(
        self, nodeids: list[ua.NodeId], attr: ua.AttributeIds = ua.AttributeIds.Value
    ) -> list[ua.DataValue]:
        params = ua.ReadParameters()
        params.NodesToRead = []
        for nodeid in nodeids:
            read_value = ua.ReadValueId()
            read_value.NodeId = nodeid
            read_value.AttributeId = attr
            params.NodesToRead.append(read_value)
        return await self.read(params)

    async def write_attributes(
        self,
        nodeids: list[ua.NodeId],
        datavalues: list[ua.DataValue],
        attributeid: ua.AttributeIds = ua.AttributeIds.Value,
    ) -> list[ua.StatusCode]:
        if len(nodeids) != len(datavalues):
            raise ValueError("nodeids and datavalues must have the same length")
        params = ua.WriteParameters()
        params.NodesToWrite = []
        for nodeid, datavalue in zip(nodeids, datavalues):
            write_value = ua.WriteValue()
            write_value.NodeId = nodeid
            write_value.AttributeId = attributeid
            write_value.Value = datavalue
            params.NodesToWrite.append(write_value)
        return await self.write(params)
