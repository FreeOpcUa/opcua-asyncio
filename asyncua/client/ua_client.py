"""
Low level binary client.

`UaClient` provides:
- transport: socket and secure channel via `UASocketProtocol`,
- sessionless services (Discovery, Register/Unregister Server),
- a default `UaSession` accessible via `_session`, and back-compat delegating methods
  for code that used to call session services directly on `UaClient`.
"""

from __future__ import annotations

import asyncio
import copy
import logging
from collections.abc import Awaitable, Callable
from enum import Enum
from typing import Any

from asyncua import ua
from asyncua.common.session_interface import AbstractSession
from asyncua.common.utils import Buffer
from asyncua.ua.uaerrors._base import UaError

from ..common.connection import SecureConnection, TransportLimits
from ..common.utils import wait_for
from ..crypto import security_policies
from ..ua.ua_binary import header_from_binary, nodeid_from_binary, struct_from_binary, struct_to_binary, uatcp_to_binary
from ..ua.uaprotocol_auto import OpenSecureChannelResult
from .ua_session import UaSession


class UaClientState(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    SOCKET_OPEN = "socket_open"
    CHANNEL_OPEN = "channel_open"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"


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
        limits: TransportLimits | None = None,
    ) -> None:
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
        self._callbackmap: dict[int, asyncio.Future[Any]] = {}
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

    def connection_made(self, transport: asyncio.Transport) -> None:  # type: ignore[override]
        self.state = self.OPEN
        self.transport = transport

    def connection_lost(self, exc: Exception | None) -> None:
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

    def _process_received_message(self, msg: ua.Message | ua.Acknowledge | ua.ErrorMessage | None) -> None:
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

    def _send_request(
        self, request: Any, timeout: float = 1, message_type: ua.MessageType = ua.MessageType.SecureMessage
    ) -> asyncio.Future[Any]:
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
        future: asyncio.Future[Any] = asyncio.get_running_loop().create_future()
        self._callbackmap[self._request_id] = future

        # Change to the new security token if the connection has been renewed.
        if self._connection.next_security_token.TokenId != 0:
            self._connection.revolve_tokens()

        msg = self._connection.message_to_binary(binreq, message_type=message_type, request_id=self._request_id)
        if self.transport is not None:
            self.transport.write(msg)
        return future

    async def send_request(
        self, request: Any, timeout: float | None = None, message_type: ua.MessageType = ua.MessageType.SecureMessage
    ) -> Buffer:
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
        except Exception as ex:
            if self.state != self.OPEN:
                raise ConnectionError("Connection is closed") from None
            raise Exception("Unhandled exception while sending request to OPC UA server") from ex
        self.check_answer(data, f" in response to {request.__class__.__name__}")
        return data

    def check_answer(self, data: Buffer, context: str) -> bool:
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

    def _call_callback(self, request_id: int, body: Buffer | ua.Acknowledge) -> None:
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

    def _setup_request_header(self, hdr: ua.RequestHeader, timeout: float = 1) -> None:
        """
        :param hdr: Request header
        :param timeout: Timeout in seconds
        """
        hdr.AuthenticationToken = self.authentication_token
        self._request_handle += 1
        hdr.RequestHandle = self._request_handle
        hdr.TimeoutHint = int(timeout * 1000)

    def disconnect_socket(self) -> None:
        self.logger.info("Request to close socket received")
        if self.transport:
            self.transport.close()
        else:
            self.logger.warning("disconnect_socket was called but transport is None")

    async def send_hello(self, url: str, max_messagesize: int = 0, max_chunkcount: int = 0) -> ua.Acknowledge:
        hello = ua.Hello()
        hello.EndpointUrl = url
        hello.MaxMessageSize = max_messagesize
        hello.MaxChunkCount = max_chunkcount
        ack: asyncio.Future[ua.Acknowledge] = asyncio.Future()
        self._callbackmap[0] = ack
        if self.transport is not None:
            self.transport.write(uatcp_to_binary(ua.MessageType.Hello, hello))
        return await wait_for(ack, self.timeout)

    async def open_secure_channel(self, params: ua.OpenSecureChannelParameters) -> OpenSecureChannelResult:
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
        assert isinstance(self._open_secure_channel_exchange, ua.OpenSecureChannelResponse)

        _return = self._open_secure_channel_exchange.Parameters
        self._open_secure_channel_exchange = None
        return _return

    async def close_secure_channel(self) -> None:
        """
        Close secure channel.
        It seems to trigger a shutdown of socket in most servers, so be prepared to reconnect.
        OPC UA specs Part 6, 7.1.4 say that Server does not send a CloseSecureChannel response
        and should just close socket.
        """
        self.logger.info("close_secure_channel")
        request = ua.CloseSecureChannelRequest()
        future = self._send_request(request, message_type=ua.MessageType.SecureClose)
        future.cancel()
        # Fail any in-flight RPC futures with ConnectionError so awaiters can clean up,
        # rather than leaving them as silently cancelled.
        for pending in self._callbackmap.values():
            if not pending.done():
                pending.set_exception(ConnectionError("Secure channel closed"))
        self._callbackmap.clear()


class UaClient(AbstractSession):
    """
    Low level OPC-UA client.

    Owns the transport (`UASocketProtocol`) and a default `UaSession`.
    Sessionless services (Discovery, Register/Unregister Server) live here.
    Session-scoped services delegate to `self._session` for back-compat.
    """

    def __init__(self, timeout: float = 1.0) -> None:
        """
        :param timeout: Timout in seconds
        """
        self.logger = logging.getLogger(f"{__name__}.UaClient")
        self._timeout = timeout
        self.security_policy: security_policies.SecurityPolicy = security_policies.SecurityPolicyNone()
        self.protocol: UASocketProtocol | None = None
        self._pre_request_hook: Callable[[], Awaitable[None]] | None = None
        self._state: UaClientState = UaClientState.DISCONNECTED
        self._session: UaSession = UaSession(self)

    @property
    def state(self) -> UaClientState:
        return self._state

    def _set_state(self, target: UaClientState) -> None:
        """Set state. Internal helper; callers know the right transition."""
        self._state = target

    # --- transport helpers ---

    def set_security(self, policy: security_policies.SecurityPolicy) -> None:
        self.security_policy = policy

    def _make_protocol(self) -> UASocketProtocol:
        self.protocol = UASocketProtocol(self._timeout, security_policy=self.security_policy)
        self.protocol.pre_request_hook = self._pre_request_hook
        return self.protocol

    @property
    def pre_request_hook(self) -> Callable[[], Awaitable[None]] | None:
        return self._pre_request_hook

    @pre_request_hook.setter
    def pre_request_hook(self, hook: Callable[[], Awaitable[None]] | None) -> None:
        self._pre_request_hook = hook
        if self.protocol:
            self.protocol.pre_request_hook = self._pre_request_hook

    async def connect_socket(self, host: str, port: int) -> None:
        """Connect to server socket."""
        self.logger.info("opening connection")
        self._session._closing = False
        self._set_state(UaClientState.CONNECTING)
        try:
            await asyncio.wait_for(
                asyncio.get_running_loop().create_connection(self._make_protocol, host, port), self._timeout
            )
        except BaseException:
            self._set_state(UaClientState.DISCONNECTED)
            raise
        self._set_state(UaClientState.SOCKET_OPEN)

    def disconnect_socket(self) -> None:
        if self._state is UaClientState.DISCONNECTED:
            return
        if self._state is UaClientState.DISCONNECTING:
            # already tearing down; let the in-flight call complete
            return
        self._set_state(UaClientState.DISCONNECTING)
        if self.protocol is not None and self.protocol.state != UASocketProtocol.CLOSED:
            self.protocol.disconnect_socket()
        self.protocol = None
        self._set_state(UaClientState.DISCONNECTED)

    async def send_hello(self, url: str, max_messagesize: int = 0, max_chunkcount: int = 0) -> ua.Acknowledge:
        if self.protocol is None:
            raise ConnectionError("Connection is not open")
        return await self.protocol.send_hello(url, max_messagesize, max_chunkcount)

    async def open_secure_channel(self, params: ua.OpenSecureChannelParameters) -> OpenSecureChannelResult:
        if self.protocol is None:
            raise ConnectionError("Connection is not open")
        is_renew = params.RequestType == ua.SecurityTokenRequestType.Renew
        result = await self.protocol.open_secure_channel(params)
        if not is_renew:
            self._set_state(UaClientState.CHANNEL_OPEN)
        return result

    async def close_secure_channel(self) -> None:
        if not self.protocol or self.protocol.state == UASocketProtocol.CLOSED:
            self.logger.warning("close_secure_channel was called but connection is closed")
            return
        await self.protocol.close_secure_channel()
        if self._state is UaClientState.CHANNEL_OPEN:
            self._set_state(UaClientState.SOCKET_OPEN)

    async def _send_request(
        self, request: Any, timeout: float = 1, message_type: ua.MessageType = ua.MessageType.SecureMessage
    ) -> Buffer:
        if self.protocol is None:
            raise ConnectionError("Connection is not open")
        return await self.protocol.send_request(request, timeout, message_type)

    # --- back-compat: properties that previously lived on UaClient ---

    @property
    def _subscription_callbacks(self) -> dict[int, Callable[..., Any]]:
        return self._session._subscription_callbacks

    @property
    def _publish_task(self) -> asyncio.Task[None] | None:
        return self._session._publish_task

    @property
    def _closing(self) -> bool:
        return self._session._closing

    @_closing.setter
    def _closing(self, value: bool) -> None:
        self._session._closing = value

    # --- session lifecycle: delegate to default session ---

    async def create_session(self, parameters: ua.CreateSessionParameters) -> ua.CreateSessionResult:
        return await self._session.create_session(parameters)

    async def activate_session(self, parameters: ua.ActivateSessionParameters) -> ua.ActivateSessionResult:
        result = await self._session.activate_session(parameters)
        # Only transition on the first activation; re-activate of an already-ACTIVATED
        # session leaves UaClient in CONNECTED.
        if self._state is UaClientState.CHANNEL_OPEN:
            self._set_state(UaClientState.CONNECTED)
        return result

    async def close_session(self, delete_subscriptions: bool) -> None:
        await self._session.close_session(delete_subscriptions)
        if self._state is UaClientState.CONNECTED:
            self._set_state(UaClientState.CHANNEL_OPEN)

    # --- sessionless services ---

    async def get_endpoints(self, params: ua.GetEndpointsParameters) -> list[ua.EndpointDescription]:
        self.logger.debug("get_endpoint")
        request = ua.GetEndpointsRequest()
        request.Parameters = params
        data = await self._send_request(request)
        response = struct_from_binary(ua.GetEndpointsResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Endpoints

    async def find_servers(self, params: ua.FindServersParameters) -> list[ua.ApplicationDescription]:
        self.logger.debug("find_servers")
        request = ua.FindServersRequest()
        request.Parameters = params
        data = await self._send_request(request)
        response = struct_from_binary(ua.FindServersResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Servers

    async def find_servers_on_network(self, params: ua.FindServersOnNetworkParameters) -> ua.FindServersOnNetworkResult:
        self.logger.debug("find_servers_on_network")
        request = ua.FindServersOnNetworkRequest()
        request.Parameters = params
        data = await self._send_request(request)
        response = struct_from_binary(ua.FindServersOnNetworkResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Parameters

    async def register_server(self, registered_server: ua.RegisteredServer) -> None:
        self.logger.debug("register_server")
        request = ua.RegisterServerRequest()
        request.Server = registered_server
        data = await self._send_request(request)
        response = struct_from_binary(ua.RegisterServerResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()

    async def unregister_server(self, registered_server: ua.RegisteredServer) -> None:
        self.logger.debug("unregister_server")
        request = ua.RegisterServerRequest()
        request.Server = registered_server
        data = await self._send_request(request)
        response = struct_from_binary(ua.RegisterServerResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()

    async def register_server2(self, params: ua.RegisterServer2Parameters) -> list[ua.StatusCode]:
        self.logger.debug("register_server2")
        request = ua.RegisterServer2Request()
        request.Parameters = params
        data = await self._send_request(request)
        response = struct_from_binary(ua.RegisterServer2Response, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.ConfigurationResults

    async def unregister_server2(self, params: ua.RegisterServer2Parameters) -> list[ua.StatusCode]:
        self.logger.debug("unregister_server2")
        request = ua.RegisterServer2Request()
        request.Parameters = params
        data = await self._send_request(request)
        response = struct_from_binary(ua.RegisterServer2Response, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.ConfigurationResults

    # --- AbstractSession: delegate to default session ---

    async def browse(self, parameters: ua.BrowseParameters) -> list[ua.BrowseResult]:
        return await self._session.browse(parameters)

    async def browse_next(self, parameters: ua.BrowseNextParameters) -> list[ua.BrowseResult]:
        return await self._session.browse_next(parameters)

    async def translate_browsepaths_to_nodeids(self, browse_paths: list[ua.BrowsePath]) -> list[ua.BrowsePathResult]:
        return await self._session.translate_browsepaths_to_nodeids(browse_paths)

    async def register_nodes(self, nodes: list[ua.NodeId]) -> list[ua.NodeId]:
        return await self._session.register_nodes(nodes)

    async def unregister_nodes(self, nodes: list[ua.NodeId]) -> None:
        return await self._session.unregister_nodes(nodes)

    async def read(self, parameters: ua.ReadParameters) -> list[ua.DataValue]:
        return await self._session.read(parameters)

    async def write(self, params: ua.WriteParameters) -> list[ua.StatusCode]:
        return await self._session.write(params)

    async def history_read(self, params: ua.HistoryReadParameters) -> list[ua.HistoryReadResult]:
        return await self._session.history_read(params)

    async def read_attributes(self, nodeids: list[ua.NodeId], attr: ua.AttributeIds) -> list[ua.DataValue]:
        return await self._session.read_attributes(nodeids, attr)

    async def write_attributes(
        self,
        nodeids: list[ua.NodeId],
        datavalues: list[ua.DataValue],
        attributeid: ua.AttributeIds = ua.AttributeIds.Value,
    ) -> list[ua.StatusCode]:
        return await self._session.write_attributes(nodeids, datavalues, attributeid)

    async def add_nodes(self, nodestoadd: list[ua.AddNodesItem]) -> list[ua.AddNodesResult]:
        return await self._session.add_nodes(nodestoadd)

    async def add_references(self, refs: list[ua.AddReferencesItem]) -> list[ua.StatusCode]:
        return await self._session.add_references(refs)

    async def delete_references(self, refs: list[ua.DeleteReferencesItem]) -> list[ua.StatusCode]:
        return await self._session.delete_references(refs)

    async def delete_nodes(self, params: ua.DeleteNodesParameters) -> list[ua.StatusCode]:
        return await self._session.delete_nodes(params)

    async def call(self, methodstocall: list[ua.CallMethodRequest]) -> list[ua.CallMethodResult]:
        return await self._session.call(methodstocall)

    async def create_subscription(  # type: ignore[override]
        self, params: ua.CreateSubscriptionParameters, callback: Callable[..., Any]
    ) -> ua.CreateSubscriptionResult:
        return await self._session.create_subscription(params, callback)

    async def update_subscription(self, params: ua.ModifySubscriptionParameters) -> ua.ModifySubscriptionResult:
        return await self._session.update_subscription(params)

    modify_subscription = update_subscription  # legacy support

    async def delete_subscriptions(self, subscription_ids: list[int]) -> list[ua.StatusCode]:  # type: ignore[override]
        return await self._session.delete_subscriptions(subscription_ids)

    async def transfer_subscriptions(self, params: ua.TransferSubscriptionsParameters) -> list[ua.TransferResult]:
        return await self._session.transfer_subscriptions(params)

    async def inform_subscriptions(self, status: ua.StatusCode) -> None:
        return await self._session.inform_subscriptions(status)

    async def publish(self, acks: list[ua.SubscriptionAcknowledgement]) -> ua.PublishResponse:
        return await self._session.publish(acks)

    async def create_monitored_items(
        self, params: ua.CreateMonitoredItemsParameters
    ) -> list[ua.MonitoredItemCreateResult]:
        return await self._session.create_monitored_items(params)

    async def delete_monitored_items(self, params: ua.DeleteMonitoredItemsParameters) -> list[ua.StatusCode]:
        return await self._session.delete_monitored_items(params)

    async def modify_monitored_items(
        self, params: ua.ModifyMonitoredItemsParameters
    ) -> list[ua.MonitoredItemModifyResult]:
        return await self._session.modify_monitored_items(params)

    async def set_monitoring_mode(self, params: ua.SetMonitoringModeParameters) -> list[ua.uatypes.StatusCode]:
        return await self._session.set_monitoring_mode(params)

    async def set_publishing_mode(self, params: ua.SetPublishingModeParameters) -> list[ua.uatypes.StatusCode]:
        return await self._session.set_publishing_mode(params)
