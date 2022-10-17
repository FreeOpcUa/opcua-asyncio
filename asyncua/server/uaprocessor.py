import copy
import time
import logging
from typing import Deque, Optional
from collections import deque

from asyncua import ua
from ..ua.ua_binary import nodeid_from_binary, struct_from_binary, struct_to_binary, uatcp_to_binary
from .internal_server import InternalServer, InternalSession
from ..common.connection import SecureConnection, TransportLimits
from ..common.utils import ServiceError

_logger = logging.getLogger(__name__)


class PublishRequestData:

    def __init__(self, requesthdr=None, seqhdr=None):
        self.requesthdr = requesthdr
        self.seqhdr = seqhdr
        self.timestamp = time.time()


class UaProcessor:
    """
    Processor for OPC UA messages. Implements the OPC UA protocol for the server side.
    """

    def __init__(self, internal_server: InternalServer, transport, limits: TransportLimits):
        self.iserver: InternalServer = internal_server
        self.name = transport.get_extra_info('peername')
        self.sockname = transport.get_extra_info('sockname')
        self.session: Optional[InternalSession] = None
        self._transport = transport
        # deque for Publish Requests
        self._publish_requests: Deque[PublishRequestData] = deque()
        # used when we need to wait for PublishRequest
        self._publish_results: Deque[ua.PublishResult] = deque()
        self._limits = copy.deepcopy(limits)  # Copy limits because they get overriden
        self._connection = SecureConnection(ua.SecurityPolicy(), self._limits)

    def set_policies(self, policies):
        self._connection.set_policy_factories(policies)

    def send_response(self, requesthandle, seqhdr, response, msgtype=ua.MessageType.SecureMessage):
        response.ResponseHeader.RequestHandle = requesthandle
        data = self._connection.message_to_binary(
            struct_to_binary(response), message_type=msgtype, request_id=seqhdr.RequestId)
        self._transport.write(data)

    def open_secure_channel(self, algohdr, seqhdr, body):
        request = struct_from_binary(ua.OpenSecureChannelRequest, body)

        if not self._connection.is_open():
            # Only call select_policy if the channel isn't open. Otherwise
            # it will break the Secure channel renewal.
            self._connection.select_policy(
                algohdr.SecurityPolicyURI, algohdr.SenderCertificate, request.Parameters.SecurityMode)

        channel = self._connection.open(request.Parameters, self.iserver)
        # send response
        response = ua.OpenSecureChannelResponse()
        response.Parameters = channel
        self.send_response(request.RequestHeader.RequestHandle, seqhdr, response, ua.MessageType.SecureOpen)

    async def forward_publish_response(self, result: ua.PublishResult):
        """
        Try to send a `PublishResponse` with the given `PublishResult`.
        """
        # _logger.info("forward publish response %s", result)
        while True:
            if not self._publish_requests:
                self._publish_results.append(result)
                _logger.info(
                    "Server wants to send publish answer but no publish request is available,"
                    "enqueuing notification, length of result queue is %s",
                    len(self._publish_results)
                )
                return
            # We pop left from the Publish Request deque (FIFO)
            requestdata = self._publish_requests.popleft()
            if (requestdata.requesthdr.TimeoutHint == 0 or
                    requestdata.requesthdr.TimeoutHint != 0 and
                    time.time() - requestdata.timestamp < requestdata.requesthdr.TimeoutHint / 1000):
                # Continue and use `requestdata` only if there was no timeout
                break
        response = ua.PublishResponse()
        response.Parameters = result
        self.send_response(requestdata.requesthdr.RequestHandle, requestdata.seqhdr, response)

    async def process(self, header, body):
        try:
            msg = self._connection.receive_from_header_and_body(header, body)
        except ua.uaerrors.BadRequestTooLarge as e:
            _logger.warning("Recived request that exceed the transport limits")
            err = ua.ErrorMessage(ua.StatusCode(e.code), str(e))
            data = uatcp_to_binary(ua.MessageType.Error, err)
            self._transport.write(data)
            return True
        except ua.uaerrors.BadUserAccessDenied:
            _logger.warning("Unauthenticated user attempted to connect")
            return False
        if isinstance(msg, ua.Message):
            if header.MessageType == ua.MessageType.SecureOpen:
                self.open_secure_channel(msg.SecurityHeader(), msg.SequenceHeader(), msg.body())
            elif header.MessageType == ua.MessageType.SecureClose:
                self._connection.close()
                return False
            elif header.MessageType == ua.MessageType.SecureMessage:
                return await self.process_message(msg.SequenceHeader(), msg.body())
        elif isinstance(msg, ua.Hello):
            ack = self._limits.create_acknowledge_and_set_limits(msg)
            data = uatcp_to_binary(ua.MessageType.Acknowledge, ack)
            self._transport.write(data)
        elif isinstance(msg, ua.ErrorMessage):
            _logger.warning("Received an error message type")
        elif msg is None:
            pass  # msg is a ChunkType.Intermediate of an ua.MessageType.SecureMessage
        else:
            _logger.warning("Unsupported message type: %s", header.MessageType)
            raise ServiceError(ua.StatusCodes.BadTcpMessageTypeInvalid)
        return True

    async def process_message(self, seqhdr, body):
        """
        Process incoming messages.
        """
        typeid = nodeid_from_binary(body)
        requesthdr = struct_from_binary(ua.RequestHeader, body)
        _logger.debug('process_message %r %r', typeid, requesthdr)
        try:
            return await self._process_message(typeid, requesthdr, seqhdr, body)
        except ServiceError as e:
            status = ua.StatusCode(e.code)
            response = ua.ServiceFault()
            response.ResponseHeader.ServiceResult = status
            _logger.error("sending service fault response: %s (%s)", status.doc, status.name)
            self.send_response(requesthdr.RequestHandle, seqhdr, response)
            return True
        except ua.uaerrors.BadUserAccessDenied:
            if self.session:
                user = self.session.user
            else:
                user = 'Someone'
            _logger.warning("%s attempted to do something they are not permitted to do", user)
            response = ua.ServiceFault()
            response.ResponseHeader.ServiceResult = ua.StatusCode(ua.StatusCodes.BadUserAccessDenied)
            self.send_response(requesthdr.RequestHandle, seqhdr, response)
        except Exception:
            _logger.exception('Error while processing message')
            response = ua.ServiceFault()
            response.ResponseHeader.ServiceResult = ua.StatusCode(ua.StatusCodes.BadInternalError)
            self.send_response(requesthdr.RequestHandle, seqhdr, response)
            return True

    async def _process_message(self, typeid, requesthdr, seqhdr, body):
        if typeid in [ua.NodeId(ua.ObjectIds.CreateSessionRequest_Encoding_DefaultBinary),
                      ua.NodeId(ua.ObjectIds.CloseSessionRequest_Encoding_DefaultBinary),
                      ua.NodeId(ua.ObjectIds.ActivateSessionRequest_Encoding_DefaultBinary),
                      ua.NodeId(ua.ObjectIds.FindServersRequest_Encoding_DefaultBinary),
                      ua.NodeId(ua.ObjectIds.GetEndpointsRequest_Encoding_DefaultBinary)]:
            # The connection is first created without a user being attached, and then during activation the
            user = None
        elif self.session is None:
            _logger.warning("Received a request of type %d without an existing session", typeid.Identifier)
            raise ua.uaerrors.BadUserAccessDenied
        else:
            user = self.session.user
            if self._connection.security_policy.permissions is not None:
                if self._connection.security_policy.permissions.check_validity(user, typeid, body) is False:
                    raise ua.uaerrors.BadUserAccessDenied

        if typeid == ua.NodeId(ua.ObjectIds.CreateSessionRequest_Encoding_DefaultBinary):
            _logger.info("Create session request (%s)", user)
            params = struct_from_binary(ua.CreateSessionParameters, body)
            # create the session on server
            self.session = self.iserver.create_session(self.name, external=True)
            # get a session creation result to send back
            sessiondata = await self.session.create_session(params, sockname=self.sockname)
            response = ua.CreateSessionResponse()
            response.Parameters = sessiondata
            response.Parameters.ServerCertificate = self._connection.security_policy.host_certificate
            if self._connection.security_policy.peer_certificate is None:
                data = params.ClientNonce
            else:
                data = self._connection.security_policy.peer_certificate + params.ClientNonce
            response.Parameters.ServerSignature.Signature = \
                self._connection.security_policy.asymmetric_cryptography.signature(data)
            response.Parameters.ServerSignature.Algorithm = self._connection.security_policy.AsymmetricSignatureURI
            # _logger.info("sending create session response")
            self.send_response(requesthdr.RequestHandle, seqhdr, response)

        elif typeid == ua.NodeId(ua.ObjectIds.CloseSessionRequest_Encoding_DefaultBinary):
            _logger.info("Close session request (%s)", user)
            if self.session:
                deletesubs = ua.ua_binary.Primitives.Boolean.unpack(body)
                await self.session.close_session(deletesubs)
            else:
                _logger.info("Request to close non-existing session (%s)", user)

            response = ua.CloseSessionResponse()
            _logger.info("sending close session response (%s)", user)
            self.send_response(requesthdr.RequestHandle, seqhdr, response)

        elif typeid == ua.NodeId(ua.ObjectIds.ActivateSessionRequest_Encoding_DefaultBinary):
            _logger.info("Activate session request (%s)", user)
            params = struct_from_binary(ua.ActivateSessionParameters, body)
            if not self.session:
                _logger.info("request to activate non-existing session (%s)", user)
                raise ServiceError(ua.StatusCodes.BadSessionIdInvalid)
            if self._connection.security_policy.host_certificate is None:
                data = self.session.nonce
            else:
                data = self._connection.security_policy.host_certificate + self.session.nonce
            self._connection.security_policy.asymmetric_cryptography.verify(data, params.ClientSignature.Signature)
            result = self.session.activate_session(params, self._connection.security_policy.peer_certificate)
            response = ua.ActivateSessionResponse()
            response.Parameters = result
            # _logger.info("sending read response")
            self.send_response(requesthdr.RequestHandle, seqhdr, response)
        elif typeid == ua.NodeId(ua.ObjectIds.GetEndpointsRequest_Encoding_DefaultBinary):
            _logger.info("get endpoints request (%s)", user)
            params = struct_from_binary(ua.GetEndpointsParameters, body)
            endpoints = await self.iserver.get_endpoints(params, sockname=self.sockname)
            response = ua.GetEndpointsResponse()
            response.Endpoints = endpoints
            # _logger.info("sending get endpoints response")
            self.send_response(requesthdr.RequestHandle, seqhdr, response)

        elif typeid == ua.NodeId(ua.ObjectIds.FindServersRequest_Encoding_DefaultBinary):
            _logger.info("find servers request (%s)", user)
            params = struct_from_binary(ua.FindServersParameters, body)
            servers = self.iserver.find_servers(params)
            response = ua.FindServersResponse()
            response.Servers = servers
            # _logger.info("sending find servers response")
            self.send_response(requesthdr.RequestHandle, seqhdr, response)

        elif typeid == ua.NodeId(ua.ObjectIds.RegisterServerRequest_Encoding_DefaultBinary):
            _logger.info("register server request %s", user)
            serv = struct_from_binary(ua.RegisteredServer, body)
            self.iserver.register_server(serv)
            response = ua.RegisterServerResponse()
            # _logger.info("sending register server response")
            self.send_response(requesthdr.RequestHandle, seqhdr, response)

        elif typeid == ua.NodeId(ua.ObjectIds.RegisterServer2Request_Encoding_DefaultBinary):
            _logger.info("register server 2 request %s", user)
            params = struct_from_binary(ua.RegisterServer2Parameters, body)
            results = self.iserver.register_server2(params)
            response = ua.RegisterServer2Response()
            response.ConfigurationResults = results
            # _logger.info("sending register server 2 response")
            self.send_response(requesthdr.RequestHandle, seqhdr, response)
        elif typeid == ua.NodeId(ua.ObjectIds.CloseSecureChannelRequest_Encoding_DefaultBinary):
            _logger.info("close secure channel request (%s)", user)
            self._connection.close()
            response = ua.CloseSecureChannelResponse()
            self.send_response(requesthdr.RequestHandle, seqhdr, response)
            return False
        else:
            # All services that requere a active session
            if not self.session:
                _logger.info("Request service that need a session (%s)", user)
                raise ServiceError(ua.StatusCodes.BadSessionIdInvalid)
            if not self.session.is_activated():
                _logger.info("Request service that needs a activated session (%s)", user)
                raise ServiceError(ua.StatusCodes.BadSessionNotActivated)

            if typeid == ua.NodeId(ua.ObjectIds.ReadRequest_Encoding_DefaultBinary):
                _logger.info("Read request (%s)", user)
                params = struct_from_binary(ua.ReadParameters, body)
                results = await self.session.read(params)
                response = ua.ReadResponse()
                response.Results = results
                # _logger.info("sending read response")
                self.send_response(requesthdr.RequestHandle, seqhdr, response)

            elif typeid == ua.NodeId(ua.ObjectIds.WriteRequest_Encoding_DefaultBinary):
                _logger.info("Write request (%s)", user)
                params = struct_from_binary(ua.WriteParameters, body)
                results = await self.session.write(params)
                response = ua.WriteResponse()
                response.Results = results
                # _logger.info("sending write response")
                self.send_response(requesthdr.RequestHandle, seqhdr, response)

            elif typeid == ua.NodeId(ua.ObjectIds.BrowseRequest_Encoding_DefaultBinary):
                _logger.info("Browse request (%s)", user)
                params = struct_from_binary(ua.BrowseParameters, body)
                results = await self.session.browse(params)
                response = ua.BrowseResponse()
                response.Results = results
                # _logger.info("sending browse response")
                self.send_response(requesthdr.RequestHandle, seqhdr, response)

            elif typeid == ua.NodeId(ua.ObjectIds.TranslateBrowsePathsToNodeIdsRequest_Encoding_DefaultBinary):
                _logger.info("translate browsepaths to nodeids request (%s)", user)
                params = struct_from_binary(ua.TranslateBrowsePathsToNodeIdsParameters, body)
                paths = await self.session.translate_browsepaths_to_nodeids(params.BrowsePaths)
                response = ua.TranslateBrowsePathsToNodeIdsResponse()
                response.Results = paths
                # _logger.info("sending translate browsepaths to nodeids response")
                self.send_response(requesthdr.RequestHandle, seqhdr, response)

            elif typeid == ua.NodeId(ua.ObjectIds.AddNodesRequest_Encoding_DefaultBinary):
                _logger.info("add nodes request (%s)", user)
                params = struct_from_binary(ua.AddNodesParameters, body)
                results = await self.session.add_nodes(params.NodesToAdd)
                response = ua.AddNodesResponse()
                response.Results = results
                # _logger.info("sending add node response")
                self.send_response(requesthdr.RequestHandle, seqhdr, response)

            elif typeid == ua.NodeId(ua.ObjectIds.DeleteNodesRequest_Encoding_DefaultBinary):
                _logger.info("delete nodes request (%s)", user)
                params = struct_from_binary(ua.DeleteNodesParameters, body)
                results = await self.session.delete_nodes(params)
                response = ua.DeleteNodesResponse()
                response.Results = results
                # _logger.info("sending delete node response")
                self.send_response(requesthdr.RequestHandle, seqhdr, response)

            elif typeid == ua.NodeId(ua.ObjectIds.AddReferencesRequest_Encoding_DefaultBinary):
                _logger.info("add references request (%s)", user)
                params = struct_from_binary(ua.AddReferencesParameters, body)
                results = await self.session.add_references(params.ReferencesToAdd)
                response = ua.AddReferencesResponse()
                response.Results = results
                # _logger.info("sending add references response")
                self.send_response(requesthdr.RequestHandle, seqhdr, response)

            elif typeid == ua.NodeId(ua.ObjectIds.DeleteReferencesRequest_Encoding_DefaultBinary):
                _logger.info("delete references request (%s)", user)
                params = struct_from_binary(ua.DeleteReferencesParameters, body)
                results = await self.session.delete_references(params.ReferencesToDelete)
                response = ua.DeleteReferencesResponse()
                response.Parameters.Results = results
                # _logger.info("sending delete references response")
                self.send_response(requesthdr.RequestHandle, seqhdr, response)

            elif typeid == ua.NodeId(ua.ObjectIds.CreateSubscriptionRequest_Encoding_DefaultBinary):
                _logger.info("create subscription request (%s)", user)
                params = struct_from_binary(ua.CreateSubscriptionParameters, body)
                result = await self.session.create_subscription(params, callback=self.forward_publish_response)
                response = ua.CreateSubscriptionResponse()
                response.Parameters = result
                # _logger.info("sending create subscription response")
                self.send_response(requesthdr.RequestHandle, seqhdr, response)

            elif typeid == ua.NodeId(ua.ObjectIds.ModifySubscriptionRequest_Encoding_DefaultBinary):
                _logger.info("modify subscription request")
                params = struct_from_binary(ua.ModifySubscriptionParameters, body)

                result = self.session.modify_subscription(params, self.forward_publish_response)

                response = ua.ModifySubscriptionResponse()
                response.Parameters = result

                #_logger.info("sending modify subscription response")
                self.send_response(requesthdr.RequestHandle, seqhdr, response)

            elif typeid == ua.NodeId(ua.ObjectIds.DeleteSubscriptionsRequest_Encoding_DefaultBinary):
                _logger.info("delete subscriptions request (%s)", user)
                params = struct_from_binary(ua.DeleteSubscriptionsParameters, body)
                results = await self.session.delete_subscriptions(params.SubscriptionIds)
                response = ua.DeleteSubscriptionsResponse()
                response.Results = results
                # _logger.info("sending delete subscription response")
                self.send_response(requesthdr.RequestHandle, seqhdr, response)

            elif typeid == ua.NodeId(ua.ObjectIds.CreateMonitoredItemsRequest_Encoding_DefaultBinary):
                _logger.info("create monitored items request (%s)", user)
                params = struct_from_binary(ua.CreateMonitoredItemsParameters, body)
                results = await self.session.create_monitored_items(params)
                response = ua.CreateMonitoredItemsResponse()
                response.Results = results
                # _logger.info("sending create monitored items response")
                self.send_response(requesthdr.RequestHandle, seqhdr, response)

            elif typeid == ua.NodeId(ua.ObjectIds.ModifyMonitoredItemsRequest_Encoding_DefaultBinary):
                _logger.info("modify monitored items request (%s)", user)
                params = struct_from_binary(ua.ModifyMonitoredItemsParameters, body)
                results = await self.session.modify_monitored_items(params)
                response = ua.ModifyMonitoredItemsResponse()
                response.Results = results
                # _logger.info("sending modify monitored items response")
                self.send_response(requesthdr.RequestHandle, seqhdr, response)

            elif typeid == ua.NodeId(ua.ObjectIds.DeleteMonitoredItemsRequest_Encoding_DefaultBinary):
                _logger.info("delete monitored items request (%s)", user)
                params = struct_from_binary(ua.DeleteMonitoredItemsParameters, body)
                results = await self.session.delete_monitored_items(params)
                response = ua.DeleteMonitoredItemsResponse()
                response.Results = results
                # _logger.info("sending delete monitored items response")
                self.send_response(requesthdr.RequestHandle, seqhdr, response)

            elif typeid == ua.NodeId(ua.ObjectIds.HistoryReadRequest_Encoding_DefaultBinary):
                _logger.info("history read request (%s)", user)
                params = struct_from_binary(ua.HistoryReadParameters, body)
                results = await self.session.history_read(params)
                response = ua.HistoryReadResponse()
                response.Results = results
                # _logger.info("sending history read response")
                self.send_response(requesthdr.RequestHandle, seqhdr, response)

            elif typeid == ua.NodeId(ua.ObjectIds.RegisterNodesRequest_Encoding_DefaultBinary):
                _logger.info("register nodes request (%s)", user)
                params = struct_from_binary(ua.RegisterNodesParameters, body)
                _logger.info("Node registration not implemented")
                response = ua.RegisterNodesResponse()
                response.Parameters.RegisteredNodeIds = params.NodesToRegister
                # _logger.info("sending register nodes response")
                self.send_response(requesthdr.RequestHandle, seqhdr, response)

            elif typeid == ua.NodeId(ua.ObjectIds.UnregisterNodesRequest_Encoding_DefaultBinary):
                _logger.info("unregister nodes request (%s)", user)
                params = struct_from_binary(ua.UnregisterNodesParameters, body)
                response = ua.UnregisterNodesResponse()
                # _logger.info("sending unregister nodes response")
                self.send_response(requesthdr.RequestHandle, seqhdr, response)

            elif typeid == ua.NodeId(ua.ObjectIds.PublishRequest_Encoding_DefaultBinary):
                _logger.debug("publish request (%s)", user)
                if not self.session:
                    return False
                params = struct_from_binary(ua.PublishParameters, body)
                data = PublishRequestData(requesthdr=requesthdr, seqhdr=seqhdr)
                # Store the Publish Request (will be used to send publish answers from server)
                self._publish_requests.append(data)
                # If there is an enqueued result forward it immediately
                while self._publish_results:
                    result = self._publish_results.popleft()
                    if result.SubscriptionId not in self.session.subscription_service.active_subscription_ids:
                        # Discard the result if the subscription is no longer active
                        continue
                    await self.forward_publish_response(result)
                    break
                self.session.publish(params.SubscriptionAcknowledgements)
                # _logger.debug("publish forward to server")

            elif typeid == ua.NodeId(ua.ObjectIds.RepublishRequest_Encoding_DefaultBinary):
                _logger.info("re-publish request (%s)", user)
                params = struct_from_binary(ua.RepublishParameters, body)
                msg = self.session.republish(params)
                response = ua.RepublishResponse()
                response.NotificationMessage = msg
                self.send_response(requesthdr.RequestHandle, seqhdr, response)

            elif typeid == ua.NodeId(ua.ObjectIds.CallRequest_Encoding_DefaultBinary):
                _logger.info("call request (%s)", user)
                params = struct_from_binary(ua.CallParameters, body)
                results = await self.session.call(params.MethodsToCall)
                response = ua.CallResponse()
                response.Results = results
                self.send_response(requesthdr.RequestHandle, seqhdr, response)

            elif typeid == ua.NodeId(ua.ObjectIds.SetMonitoringModeRequest_Encoding_DefaultBinary):
                _logger.info("set monitoring mode request (%s)", user)
                params = struct_from_binary(ua.SetMonitoringModeParameters, body)
                # FIXME: Implement SetMonitoringMode
                # For now send dummy results to keep clients happy
                response = ua.SetMonitoringModeResponse()
                results = ua.SetMonitoringModeResult()
                ids = params.MonitoredItemIds
                statuses = [ua.StatusCode(ua.StatusCodes.Good) for node_id in ids]
                results.Results = statuses
                response.Parameters = results
                _logger.info("sending set monitoring mode response")
                self.send_response(requesthdr.RequestHandle, seqhdr, response)

            elif typeid == ua.NodeId(ua.ObjectIds.SetPublishingModeRequest_Encoding_DefaultBinary):
                _logger.info("set publishing mode request (%s)", user)
                params = struct_from_binary(ua.SetPublishingModeParameters, body)
                # FIXME: Implement SetPublishingMode
                # For now send dummy results to keep clients happy
                response = ua.SetPublishingModeResponse()
                results = ua.SetPublishingModeResult()
                ids = params.SubscriptionIds
                statuses = [ua.StatusCode(ua.StatusCodes.Good) for node_id in ids]
                results.Results = statuses
                response.Parameters = results
                _logger.info("sending set publishing mode response")
                self.send_response(requesthdr.RequestHandle, seqhdr, response)

            else:
                _logger.warning("Unknown message received %s (%s)", typeid, user)
                raise ServiceError(ua.StatusCodes.BadServiceUnsupported)

        return True

    async def close(self):
        """
        to be called when client has disconnected to ensure we really close
        everything we should
        """
        _logger.info("Cleanup client connection: %s", self.name)
        if self.session:
            await self.session.close_session(True)
