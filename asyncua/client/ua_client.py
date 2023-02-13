"""
Low level binary client
"""
import asyncio
import copy
import logging
from typing import Awaitable, Callable, Dict, List, Optional, Union

from asyncua import ua
from asyncua.common.session_interface import AbstractSession
from ..ua.ua_binary import struct_from_binary, uatcp_to_binary, struct_to_binary, nodeid_from_binary, header_from_binary
from ..ua.uaerrors import BadTimeout, BadNoSubscription, BadSessionClosed, BadUserAccessDenied, UaStructParsingError
from ..common.connection import SecureConnection, TransportLimits


class UASocketProtocol(asyncio.Protocol):
    """
    Handle socket connection and send ua messages.
    Timeout is the timeout used while waiting for an ua answer from server.
    """
    INITIALIZED = 'initialized'
    OPEN = 'open'
    CLOSED = 'closed'

    def __init__(self, timeout: float = 1, security_policy: ua.SecurityPolicy = ua.SecurityPolicy(), limits: TransportLimits = None):
        """
        :param timeout: Timeout in seconds
        :param security_policy: Security policy (optional)
        """
        self.logger = logging.getLogger(f"{__name__}.UASocketProtocol")
        self.transport: Optional[asyncio.Transport] = None
        self.receive_buffer: Optional[bytes] = None
        self.is_receiving = False
        self.timeout = timeout
        self.authentication_token = ua.NodeId()
        self._request_id = 0
        self._request_handle = 0
        self._callbackmap: Dict[int, asyncio.Future] = {}
        if limits is None:
            limits = TransportLimits(65535, 65535, 0, 0)
        else:
            limits = copy.deep_copy(limits)  # Make a copy because the limits can change in the session
        self._connection = SecureConnection(security_policy, limits)

        self.state = self.INITIALIZED
        self.closed: bool = False
        # needed to pass params from asynchronous request to synchronous data receive callback, as well as
        # passing back the processed response to the request so that it can return it.
        self._open_secure_channel_exchange: Union[ua.OpenSecureChannelResponse, ua.OpenSecureChannelParameters, None] = None
        # Hook for upper layer tasks before a request is sent (optional)
        self.pre_request_hook: Optional[Callable[[], Awaitable[None]]] = None

    def connection_made(self, transport: asyncio.Transport):  # type: ignore
        self.state = self.OPEN
        self.transport = transport

    def connection_lost(self, exc: Optional[Exception]):
        self.logger.info("Socket has closed connection")
        self.state = self.CLOSED
        self.transport = None

    def data_received(self, data: bytes):
        if self.receive_buffer:
            data = self.receive_buffer + data
            self.receive_buffer = None
        self._process_received_data(data)

    def _process_received_data(self, data: bytes):
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
                    self.logger.debug('Not enough data while parsing header from server, waiting for more')
                    self.receive_buffer = data
                    return
                if len(buf) < header.body_size:
                    self.logger.debug('We did not receive enough data from server. Need %s got %s', header.body_size, len(buf))
                    self.receive_buffer = data
                    return
                msg = self._connection.receive_from_header_and_body(header, buf)
                self._process_received_message(msg)
                if header.MessageType == ua.MessageType.SecureOpen:
                    params: ua.OpenSecureChannelParameters = self._open_secure_channel_exchange
                    response: ua.OpenSecureChannelResponse = struct_from_binary(ua.OpenSecureChannelResponse, msg.body())
                    response.ResponseHeader.ServiceResult.check()
                    self._open_secure_channel_exchange = response
                    self._connection.set_channel(response.Parameters, params.RequestType, params.ClientNonce)
                if not buf:
                    return
                # Buffer still has bytes left, try to process again
                data = bytes(buf)
            except Exception:
                self.logger.exception('Exception raised while parsing message from server')
                self.disconnect_socket()
                return

    def _process_received_message(self, msg: Union[ua.Message, ua.Acknowledge, ua.ErrorMessage]):
        if msg is None:
            pass
        elif isinstance(msg, ua.Message):
            self._call_callback(msg.request_id(), msg.body())
        elif isinstance(msg, ua.Acknowledge):
            self._call_callback(0, msg)
        elif isinstance(msg, ua.ErrorMessage):
            self.logger.fatal("Received an error: %r", msg)
            self.disconnect_socket()
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
        self.logger.debug('Sending: %s', request)
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

    async def send_request(self, request, timeout: Optional[float] = None, message_type=ua.MessageType.SecureMessage):
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
            data = await asyncio.wait_for(self._send_request(request, timeout, message_type), timeout if timeout else None)
        except Exception:
            if self.state != self.OPEN:
                raise ConnectionError("Connection is closed") from None
            raise
        self.check_answer(data, f" in response to {request.__class__.__name__}")
        return data

    def check_answer(self, data, context):
        data = data.copy()
        typeid = nodeid_from_binary(data)
        if typeid == ua.FourByteNodeId(ua.ObjectIds.ServiceFault_Encoding_DefaultBinary):
            hdr = struct_from_binary(ua.ResponseHeader, data)
            self.logger.warning("ServiceFault (%s, diagnostics: %s) from server received %s", hdr.ServiceResult.name, hdr.ServiceDiagnostics, context)
            hdr.ServiceResult.check()
            return False
        return True

    def _call_callback(self, request_id, body):
        try:
            self._callbackmap[request_id].set_result(body)
        except KeyError as ex:
            raise ua.UaError(f"No request found for request id: {request_id}, pending are {self._callbackmap.keys()}, body was {body}") from ex
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
        return await asyncio.wait_for(ack, self.timeout)

    async def open_secure_channel(self, params):
        self.logger.info("open_secure_channel")
        request = ua.OpenSecureChannelRequest()
        request.Parameters = params
        if self._open_secure_channel_exchange is not None:
            raise RuntimeError('Two Open Secure Channel requests can not happen too close to each other. ' 'The response must be processed and returned before the next request can be sent.')
        self._open_secure_channel_exchange = params
        await asyncio.wait_for(self._send_request(request, message_type=ua.MessageType.SecureOpen), self.timeout)
        _return = self._open_secure_channel_exchange.Parameters
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

    def __init__(self, timeout: float = 1.0):
        """
        :param timeout: Timout in seconds
        """
        self.logger = logging.getLogger(f'{__name__}.UaClient')
        self._subscription_callbacks = {}
        self._timeout = timeout
        self.security_policy = ua.SecurityPolicy()
        self.protocol: UASocketProtocol = None
        self._publish_task = None
        self._pre_request_hook: Optional[Callable[[], Awaitable[None]]] = None
        self._closing: bool = False

    def set_security(self, policy: ua.SecurityPolicy):
        self.security_policy = policy

    def _make_protocol(self):
        self.protocol = UASocketProtocol(self._timeout, security_policy=self.security_policy)
        self.protocol.pre_request_hook = self._pre_request_hook
        return self.protocol

    @property
    def pre_request_hook(self) -> Callable[[], Awaitable[None]]:
        return self._pre_request_hook

    @pre_request_hook.setter
    def pre_request_hook(self, hook: Optional[Callable[[], Awaitable[None]]]):
        self._pre_request_hook = hook
        if self.protocol:
            self.protocol.pre_request_hook = self._pre_request_hook

    async def connect_socket(self, host: str, port: int):
        """Connect to server socket."""
        self.logger.info("opening connection")
        self._closing: bool = False
        # Timeout the connection when the server isn't available
        await asyncio.wait_for(asyncio.get_running_loop().create_connection(self._make_protocol, host, port), self._timeout)

    def disconnect_socket(self):
        if not self.protocol:
            return
        if self.protocol and self.protocol.state == UASocketProtocol.CLOSED:
            self.logger.warning("disconnect_socket was called but connection is closed")
            return None
        self.protocol.disconnect_socket()
        self.protocol = None

    async def send_hello(self, url, max_messagesize: int = 0, max_chunkcount: int = 0):
        await self.protocol.send_hello(url, max_messagesize, max_chunkcount)

    async def open_secure_channel(self, params):
        return await self.protocol.open_secure_channel(params)

    async def close_secure_channel(self):
        """
        close secure channel. It seems to trigger a shutdown of socket
        in most servers, so be prepared to reconnect
        """
        if not self.protocol or self.protocol.state == UASocketProtocol.CLOSED:
            self.logger.warning("close_secure_channel was called but connection is closed")
            return
        return await self.protocol.close_secure_channel()

    async def create_session(self, parameters):
        self.logger.info("create_session")
        self._closing = False
        # FIXME: setting a value on an object to set it its state is suspicious,
        # especially when that object has its own state
        self.protocol.closed = False
        request = ua.CreateSessionRequest()
        request.Parameters = parameters
        data = await self.protocol.send_request(request)
        response = struct_from_binary(ua.CreateSessionResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        self.protocol.authentication_token = response.Parameters.AuthenticationToken
        return response.Parameters

    async def activate_session(self, parameters):
        self.logger.info("activate_session")
        request = ua.ActivateSessionRequest()
        request.Parameters = parameters
        data = await self.protocol.send_request(request)
        response = struct_from_binary(ua.ActivateSessionResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Parameters

    async def close_session(self, delete_subscriptions):
        self.logger.info("close_session")
        if not self.protocol:
            self.logger.warning("close_session but connection wasn't established")
            return
        self.protocol.closed = True
        self._closing = True
        if self._publish_task and not self._publish_task.done():
            self._publish_task.cancel()
        if self.protocol and self.protocol.state == UASocketProtocol.CLOSED:
            self.logger.warning("close_session was called but connection is closed")
            return
        request = ua.CloseSessionRequest()
        request.DeleteSubscriptions = delete_subscriptions
        data = await self.protocol.send_request(request)
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

    async def browse(self, parameters):
        self.logger.info("browse")
        request = ua.BrowseRequest()
        request.Parameters = parameters
        data = await self.protocol.send_request(request)
        response = struct_from_binary(ua.BrowseResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def browse_next(self, parameters):
        self.logger.debug("browse next")
        request = ua.BrowseNextRequest()
        request.Parameters = parameters
        data = await self.protocol.send_request(request)
        response = struct_from_binary(ua.BrowseNextResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Parameters.Results

    async def read(self, parameters):
        self.logger.debug("read")
        request = ua.ReadRequest()
        request.Parameters = parameters
        data = await self.protocol.send_request(request)
        response = struct_from_binary(ua.ReadResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def write(self, params):
        self.logger.debug("write")
        request = ua.WriteRequest()
        request.Parameters = params
        data = await self.protocol.send_request(request)
        response = struct_from_binary(ua.WriteResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def get_endpoints(self, params):
        self.logger.debug("get_endpoint")
        request = ua.GetEndpointsRequest()
        request.Parameters = params
        data = await self.protocol.send_request(request)
        response = struct_from_binary(ua.GetEndpointsResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Endpoints

    async def find_servers(self, params):
        self.logger.debug("find_servers")
        request = ua.FindServersRequest()
        request.Parameters = params
        data = await self.protocol.send_request(request)
        response = struct_from_binary(ua.FindServersResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Servers

    async def find_servers_on_network(self, params):
        self.logger.debug("find_servers_on_network")
        request = ua.FindServersOnNetworkRequest()
        request.Parameters = params
        data = await self.protocol.send_request(request)
        response = struct_from_binary(ua.FindServersOnNetworkResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Parameters

    async def register_server(self, registered_server):
        self.logger.debug("register_server")
        request = ua.RegisterServerRequest()
        request.Server = registered_server
        data = await self.protocol.send_request(request)
        response = struct_from_binary(ua.RegisterServerResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        # nothing to return for this service
    
    async def unregister_server(self, registered_server):
        self.logger.debug("unregister_server")
        request = ua.RegisterServerRequest()
        request.Server = registered_server
        data = await self.protocol.send_request(request)
        response = struct_from_binary(ua.RegisterServerResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        # nothing to return for this service

    async def register_server2(self, params):
        self.logger.debug("register_server2")
        request = ua.RegisterServer2Request()
        request.Parameters = params
        data = await self.protocol.send_request(request)
        response = struct_from_binary(ua.RegisterServer2Response, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.ConfigurationResults

    async def unregister_server2(self, params):
        self.logger.debug("unregister_server2")
        request = ua.RegisterServer2Request()
        request.Parameters = params
        data = await self.protocol.send_request(request)
        response = struct_from_binary(ua.RegisterServer2Response, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.ConfigurationResults

    async def translate_browsepaths_to_nodeids(self, browse_paths):
        self.logger.debug("translate_browsepath_to_nodeid")
        request = ua.TranslateBrowsePathsToNodeIdsRequest()
        request.Parameters.BrowsePaths = browse_paths
        data = await self.protocol.send_request(request)
        response = struct_from_binary(ua.TranslateBrowsePathsToNodeIdsResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def create_subscription(
        self, params, callback
    ) -> ua.CreateSubscriptionResult:
        self.logger.debug("create_subscription")
        request = ua.CreateSubscriptionRequest()
        request.Parameters = params
        data = await self.protocol.send_request(request)
        response = struct_from_binary(ua.CreateSubscriptionResponse, data)
        response.ResponseHeader.ServiceResult.check()
        self._subscription_callbacks[response.Parameters.SubscriptionId] = callback
        self.logger.info(
            "create_subscription success SubscriptionId %s",
            response.Parameters.SubscriptionId
        )
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
        notification_message = ua.NotificationMessage(NotificationData=[status_message])
        for subid, callback in self._subscription_callbacks.items():
            try:
                parameters = ua.PublishResult(
                    subid,
                    NotificationMessage_=notification_message
                )
                if asyncio.iscoroutinefunction(callback):
                    await callback(parameters)
                else:
                    callback(parameters)
            except Exception:  # we call user code, catch everything!
                self.logger.exception("Exception while calling user callback: %s")

    async def update_subscription(
        self, params: ua.ModifySubscriptionParameters
    ) -> ua.ModifySubscriptionResult:
        request = ua.ModifySubscriptionRequest()
        request.Parameters = params
        data = await self.protocol.send_request(request)
        response = struct_from_binary(ua.ModifySubscriptionResponse, data)
        response.ResponseHeader.ServiceResult.check()
        self.logger.info(
            "update_subscription success SubscriptionId %s",
            params.SubscriptionId
        )
        return response.Parameters

    modify_subscription = update_subscription # legacy support

    async def delete_subscriptions(self, subscription_ids):
        self.logger.debug("delete_subscriptions %r", subscription_ids)
        request = ua.DeleteSubscriptionsRequest()
        request.Parameters.SubscriptionIds = subscription_ids
        data = await self.protocol.send_request(request)
        response = struct_from_binary(ua.DeleteSubscriptionsResponse, data)
        response.ResponseHeader.ServiceResult.check()
        self.logger.info("remove subscription callbacks for %r", subscription_ids)
        for sid in subscription_ids:
            self._subscription_callbacks.pop(sid)
        return response.Results

    async def publish(self, acks: List[ua.SubscriptionAcknowledgement]) -> ua.PublishResponse:
        """
        Send a PublishRequest to the server.
        """
        self.logger.debug('publish %r', acks)
        request = ua.PublishRequest()
        request.Parameters.SubscriptionAcknowledgements = acks if acks else []
        data = await self.protocol.send_request(request, timeout=0)
        self.protocol.check_answer(data, "while waiting for publish response")
        try:
            response = struct_from_binary(ua.PublishResponse, data)
        except Exception as ex:
            self.logger.exception("Error parsing notification from server")
            raise UaStructParsingError from ex
        return response

    async def _publish_loop(self):
        """
        Start a loop that sends a publish requests and waits for the publish responses.
        Forward the `PublishResult` to the matching `Subscription` by callback.
        """
        ack = None
        while not self._closing:
            try:
                response = await self.publish([ack] if ack else [])
            except BadTimeout:  # See Spec. Part 4, 7.28
                # Repeat without acknowledgement
                ack = None
                continue
            except BadNoSubscription:  # See Spec. Part 5, 13.8.1
                # BadNoSubscription is expected to be received after deleting the last subscription.
                # We use this as a signal to exit this task and stop sending PublishRequests. This is easier than
                # checking if there are no more subscriptions registered in this client (). A Publish response
                # could still arrive before the DeleteSubscription response.
                #
                # We could remove the callback already when sending the DeleteSubscription request,
                # but there are some legitimate reasons to keep them around, such as when the server
                # responds with "BadTimeout" and we should try again later instead of just removing
                # the subscription client-side.
                #
                # There are a variety of ways to act correctly, but the most practical solution seems
                # to be to just silently ignore any BadNoSubscription responses.
                self.logger.info("BadNoSubscription received, ignoring because it's probably valid.")
                # End task
                return
            except UaStructParsingError:
                ack = None
                continue
            subscription_id = response.Parameters.SubscriptionId
            if not subscription_id:
                # The value 0 is used to indicate that there were no Subscriptions defined for which a
                # response could be sent. See Spec. Part 4 - Section 5.13.5 "Publish"
                # End task
                return
            try:
                callback = self._subscription_callbacks[subscription_id]
            except KeyError:
                self.logger.warning("Received data for unknown subscription %s active are %s", subscription_id, self._subscription_callbacks.keys())
            else:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(response.Parameters)
                    else:
                        callback(response.Parameters)
                except Exception:  # we call user code, catch everything!
                    self.logger.exception("Exception while calling user callback: %s")
            # Repeat with acknowledgement
            if response.Parameters.NotificationMessage.NotificationData:
                ack = ua.SubscriptionAcknowledgement()
                ack.SubscriptionId = subscription_id
                ack.SequenceNumber = response.Parameters.NotificationMessage.SequenceNumber
            else:
                ack = None

    async def create_monitored_items(self, params):
        self.logger.info("create_monitored_items")
        request = ua.CreateMonitoredItemsRequest()
        request.Parameters = params
        data = await self.protocol.send_request(request)
        response = struct_from_binary(ua.CreateMonitoredItemsResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def delete_monitored_items(self, params):
        self.logger.info("delete_monitored_items")
        request = ua.DeleteMonitoredItemsRequest()
        request.Parameters = params
        data = await self.protocol.send_request(request)
        response = struct_from_binary(ua.DeleteMonitoredItemsResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def add_nodes(self, nodestoadd):
        self.logger.info("add_nodes")
        request = ua.AddNodesRequest()
        request.Parameters.NodesToAdd = nodestoadd
        data = await self.protocol.send_request(request)
        response = struct_from_binary(ua.AddNodesResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def add_references(self, refs):
        self.logger.info("add_references")
        request = ua.AddReferencesRequest()
        request.Parameters.ReferencesToAdd = refs
        data = await self.protocol.send_request(request)
        response = struct_from_binary(ua.AddReferencesResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def delete_references(self, refs):
        self.logger.info("delete")
        request = ua.DeleteReferencesRequest()
        request.Parameters.ReferencesToDelete = refs
        data = await self.protocol.send_request(request)
        response = struct_from_binary(ua.DeleteReferencesResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Parameters.Results

    async def delete_nodes(self, params):
        self.logger.info("delete_nodes")
        request = ua.DeleteNodesRequest()
        request.Parameters = params
        data = await self.protocol.send_request(request)
        response = struct_from_binary(ua.DeleteNodesResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def call(self, methodstocall):
        request = ua.CallRequest()
        request.Parameters.MethodsToCall = methodstocall
        data = await self.protocol.send_request(request)
        response = struct_from_binary(ua.CallResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def history_read(self, params):
        self.logger.info("history_read")
        request = ua.HistoryReadRequest()
        request.Parameters = params
        data = await self.protocol.send_request(request)
        response = struct_from_binary(ua.HistoryReadResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def modify_monitored_items(self, params):
        self.logger.info("modify_monitored_items")
        request = ua.ModifyMonitoredItemsRequest()
        request.Parameters = params
        data = await self.protocol.send_request(request)
        response = struct_from_binary(ua.ModifyMonitoredItemsResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def register_nodes(self, nodes):
        self.logger.info("register_nodes")
        request = ua.RegisterNodesRequest()
        request.Parameters.NodesToRegister = nodes
        data = await self.protocol.send_request(request)
        response = struct_from_binary(ua.RegisterNodesResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Parameters.RegisteredNodeIds

    async def unregister_nodes(self, nodes):
        self.logger.info("unregister_nodes")
        request = ua.UnregisterNodesRequest()
        request.Parameters.NodesToUnregister = nodes
        data = await self.protocol.send_request(request)
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
        data = await self.protocol.send_request(request)
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
        data = await self.protocol.send_request(request)
        response = struct_from_binary(ua.WriteResponse, data)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def set_monitoring_mode(self, params) -> ua.uatypes.StatusCode:
        """
        Update the subscription monitoring mode
        """
        self.logger.info("set_monitoring_mode")
        request = ua.SetMonitoringModeRequest()
        request.Parameters = params
        data = await self.protocol.send_request(request)
        response = struct_from_binary(ua.SetMonitoringModeResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Parameters.Results

    async def set_publishing_mode(self, params) -> ua.uatypes.StatusCode:
        """
        Update the subscription publishing mode
        """
        self.logger.info("set_publishing_mode")
        request = ua.SetPublishingModeRequest()
        request.Parameters = params
        data = await self.protocol.send_request(request)
        response = struct_from_binary(ua.SetPublishingModeResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Parameters.Results

    async def transfer_subscriptions(self, params: ua.TransferSubscriptionsParameters) -> List[ua.TransferResult]:
        # Subscriptions aren't bound to a Session and can be transferred!
        # https://reference.opcfoundation.org/Core/Part4/v104/5.13.7/
        raise NotImplementedError
