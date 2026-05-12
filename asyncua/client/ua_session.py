"""
OPC-UA Session: session-scoped state and services.

A `UaSession` owns the session lifecycle (CreateSession/ActivateSession/CloseSession),
the authentication token, the publish loop, and all session-scoped service calls
defined in `AbstractSession`. It uses a `UaClient` only as a transport.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from collections.abc import Callable
from enum import Enum
from typing import TYPE_CHECKING, Any

from asyncua import ua
from asyncua.common.session_interface import AbstractSession
from asyncua.common.utils import Buffer
from asyncua.ua.ua_binary import struct_from_binary
from asyncua.ua.uaerrors import (
    BadNoSubscription,
    BadSessionClosed,
    BadTimeout,
    BadUserAccessDenied,
    UaStructParsingError,
)

if TYPE_CHECKING:
    from asyncua.client.ua_client import UaClient


_logger = logging.getLogger(__name__)


class SessionState(str, Enum):
    NEW = "new"
    CREATING = "creating"
    CREATED = "created"
    ACTIVATING = "activating"
    ACTIVATED = "activated"
    CLOSING = "closing"
    CLOSED = "closed"


class UaSession(AbstractSession):
    """
    Owns the OPC-UA session: authentication token, publish loop, subscription
    callbacks, and the AbstractSession service set. Uses a `UaClient` for
    transport-level RPC.
    """

    def __init__(self, client: UaClient) -> None:
        self.logger = logging.getLogger(f"{__name__}.UaSession")
        self._client = client
        self.authentication_token: ua.NodeId = ua.NodeId()
        self._state: SessionState = SessionState.NEW
        self._subscription_callbacks: dict[int, Callable[..., Any]] = {}
        self._publish_task: asyncio.Task[None] | None = None
        self._closing: bool = False

    @property
    def state(self) -> SessionState:
        return self._state

    def _set_state(self, target: SessionState) -> None:
        """Set state. Callers know the right transition; no validation here."""
        self._state = target

    async def _send_request(
        self,
        request: Any,
        timeout: float = 1,
        message_type: ua.MessageType = ua.MessageType.SecureMessage,
    ) -> Buffer:
        return await self._client._send_request(request, timeout, message_type)

    async def create_session(self, parameters: ua.CreateSessionParameters) -> ua.CreateSessionResult:
        if self._client.protocol is None:
            raise ConnectionError("Connection is not open")
        self.logger.info("create_session")
        self._closing = False
        self._client.protocol.closed = False
        self._set_state(SessionState.CREATING)
        try:
            request = ua.CreateSessionRequest()
            request.Parameters = parameters
            data = await self._send_request(request)
            response = struct_from_binary(ua.CreateSessionResponse, data)
            self.logger.debug(response)
            response.ResponseHeader.ServiceResult.check()
        except BaseException:
            self._set_state(SessionState.NEW)
            raise
        self.authentication_token = response.Parameters.AuthenticationToken
        self._client.protocol.authentication_token = self.authentication_token
        self._set_state(SessionState.CREATED)
        return response.Parameters

    async def activate_session(self, parameters: ua.ActivateSessionParameters) -> ua.ActivateSessionResult:
        self.logger.info("activate_session")
        previous_state = self._state
        self._set_state(SessionState.ACTIVATING)
        try:
            request = ua.ActivateSessionRequest()
            request.Parameters = parameters
            data = await self._send_request(request)
            response = struct_from_binary(ua.ActivateSessionResponse, data)
            self.logger.debug(response)
            response.ResponseHeader.ServiceResult.check()
        except BaseException:
            # Roll back to whichever state we were in (CREATED or ACTIVATED)
            self._state = previous_state
            raise
        self._set_state(SessionState.ACTIVATED)
        return response.Parameters

    async def close_session(self, delete_subscriptions: bool) -> None:
        self.logger.info("close_session")
        if self._state in (SessionState.CLOSED, SessionState.CLOSING):
            return
        if self._state is SessionState.NEW:
            self._set_state(SessionState.CLOSED)
            return
        if not self._client.protocol:
            self.logger.warning("close_session but connection wasn't established")
            self._set_state(SessionState.CLOSING)
            self._set_state(SessionState.CLOSED)
            return
        self._client.protocol.closed = True
        self._closing = True
        if self._publish_task and not self._publish_task.done():
            self._publish_task.cancel()
        from .ua_client import UASocketProtocol

        self._set_state(SessionState.CLOSING)
        if self._client.protocol.state == UASocketProtocol.CLOSED:
            self.logger.warning("close_session was called but connection is closed")
            self._set_state(SessionState.CLOSED)
            return
        try:
            request = ua.CloseSessionRequest()
            request.DeleteSubscriptions = delete_subscriptions
            data = await self._send_request(request)
            response = struct_from_binary(ua.CloseSessionResponse, data)
            try:
                response.ResponseHeader.ServiceResult.check()
            except BadSessionClosed:
                # Closing the session with open publish requests leads to BadSessionClosed responses;
                # ignore it.
                pass
            except BadUserAccessDenied:
                # Older versions of asyncua didn't allow closing non-activated sessions; ignore it.
                pass
        finally:
            self._set_state(SessionState.CLOSED)

    # --- View Service Set ---

    async def browse(self, parameters: ua.BrowseParameters) -> list[ua.BrowseResult]:
        self.logger.info("browse")
        request = ua.BrowseRequest()
        request.Parameters = parameters
        data = await self._send_request(request)
        response = struct_from_binary(ua.BrowseResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def browse_next(self, parameters: ua.BrowseNextParameters) -> list[ua.BrowseResult]:
        self.logger.debug("browse next")
        request = ua.BrowseNextRequest()
        request.Parameters = parameters
        data = await self._send_request(request)
        response = struct_from_binary(ua.BrowseNextResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Parameters.Results

    async def translate_browsepaths_to_nodeids(self, browse_paths: list[ua.BrowsePath]) -> list[ua.BrowsePathResult]:
        self.logger.debug("translate_browsepath_to_nodeid")
        request = ua.TranslateBrowsePathsToNodeIdsRequest()
        request.Parameters.BrowsePaths = browse_paths
        data = await self._send_request(request)
        response = struct_from_binary(ua.TranslateBrowsePathsToNodeIdsResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def register_nodes(self, nodes: list[ua.NodeId]) -> list[ua.NodeId]:
        self.logger.info("register_nodes")
        request = ua.RegisterNodesRequest()
        request.Parameters.NodesToRegister = nodes
        data = await self._send_request(request)
        response = struct_from_binary(ua.RegisterNodesResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Parameters.RegisteredNodeIds

    async def unregister_nodes(self, nodes: list[ua.NodeId]) -> None:
        self.logger.info("unregister_nodes")
        request = ua.UnregisterNodesRequest()
        request.Parameters.NodesToUnregister = nodes
        data = await self._send_request(request)
        response = struct_from_binary(ua.UnregisterNodesResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()

    # --- Attribute Service Set ---

    async def read(self, parameters: ua.ReadParameters) -> list[ua.DataValue]:
        self.logger.debug("read")
        request = ua.ReadRequest()
        request.Parameters = parameters
        data = await self._send_request(request)
        response = struct_from_binary(ua.ReadResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def write(self, params: ua.WriteParameters) -> list[ua.StatusCode]:
        self.logger.debug("write")
        request = ua.WriteRequest()
        request.Parameters = params
        data = await self._send_request(request)
        response = struct_from_binary(ua.WriteResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def history_read(self, params: ua.HistoryReadParameters) -> list[ua.HistoryReadResult]:
        self.logger.info("history_read")
        request = ua.HistoryReadRequest()
        request.Parameters = params
        data = await self._send_request(request)
        response = struct_from_binary(ua.HistoryReadResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def read_attributes(self, nodeids: list[ua.NodeId], attr: ua.AttributeIds) -> list[ua.DataValue]:
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

    async def write_attributes(
        self,
        nodeids: list[ua.NodeId],
        datavalues: list[ua.DataValue],
        attributeid: ua.AttributeIds = ua.AttributeIds.Value,
    ) -> list[ua.StatusCode]:
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

    # --- NodeManagement Service Set ---

    async def add_nodes(self, nodestoadd: list[ua.AddNodesItem]) -> list[ua.AddNodesResult]:
        self.logger.info("add_nodes")
        request = ua.AddNodesRequest()
        request.Parameters.NodesToAdd = nodestoadd
        data = await self._send_request(request)
        response = struct_from_binary(ua.AddNodesResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def add_references(self, refs: list[ua.AddReferencesItem]) -> list[ua.StatusCode]:
        self.logger.info("add_references")
        request = ua.AddReferencesRequest()
        request.Parameters.ReferencesToAdd = refs
        data = await self._send_request(request)
        response = struct_from_binary(ua.AddReferencesResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def delete_references(self, refs: list[ua.DeleteReferencesItem]) -> list[ua.StatusCode]:
        self.logger.info("delete")
        request = ua.DeleteReferencesRequest()
        request.Parameters.ReferencesToDelete = refs
        data = await self._send_request(request)
        response = struct_from_binary(ua.DeleteReferencesResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Parameters.Results

    async def delete_nodes(self, params: ua.DeleteNodesParameters) -> list[ua.StatusCode]:
        self.logger.info("delete_nodes")
        request = ua.DeleteNodesRequest()
        request.Parameters = params
        data = await self._send_request(request)
        response = struct_from_binary(ua.DeleteNodesResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    # --- Method Service Set ---

    async def call(self, methodstocall: list[ua.CallMethodRequest]) -> list[ua.CallMethodResult]:
        request = ua.CallRequest()
        request.Parameters.MethodsToCall = methodstocall
        data = await self._send_request(request)
        response = struct_from_binary(ua.CallResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    # --- Subscription Service Set ---

    async def create_subscription(  # type: ignore[override]
        self, params: ua.CreateSubscriptionParameters, callback: Callable[..., Any]
    ) -> ua.CreateSubscriptionResult:
        self.logger.debug("create_subscription")
        request = ua.CreateSubscriptionRequest()
        request.Parameters = params
        data = await self._send_request(request)
        response = struct_from_binary(ua.CreateSubscriptionResponse, data)
        response.ResponseHeader.ServiceResult.check()
        self._subscription_callbacks[response.Parameters.SubscriptionId] = callback
        self.logger.info("create_subscription success SubscriptionId %s", response.Parameters.SubscriptionId)
        if not self._publish_task or self._publish_task.done():
            self._publish_task = asyncio.create_task(self._publish_loop())
        return response.Parameters

    async def update_subscription(self, params: ua.ModifySubscriptionParameters) -> ua.ModifySubscriptionResult:
        request = ua.ModifySubscriptionRequest()
        request.Parameters = params
        data = await self._send_request(request)
        response = struct_from_binary(ua.ModifySubscriptionResponse, data)
        response.ResponseHeader.ServiceResult.check()
        self.logger.info("update_subscription success SubscriptionId %s", params.SubscriptionId)
        return response.Parameters

    modify_subscription = update_subscription  # legacy support

    async def delete_subscriptions(self, subscription_ids: list[int]) -> list[ua.StatusCode]:  # type: ignore[override]
        self.logger.debug("delete_subscriptions %r", subscription_ids)
        ids = [int(sid) for sid in subscription_ids]
        request = ua.DeleteSubscriptionsRequest()
        request.Parameters.SubscriptionIds = ids
        data = await self._send_request(request)
        response = struct_from_binary(ua.DeleteSubscriptionsResponse, data)
        response.ResponseHeader.ServiceResult.check()
        # Only drop the local callback for ids the server confirmed deleted.
        # If the server reported a Bad status for an id, leave the registration
        # in place so the caller can decide what to do.
        for sid, status in zip(ids, response.Results):
            if status.is_good():
                self._subscription_callbacks.pop(sid, None)
            else:
                self.logger.warning("delete_subscriptions failed for %s: %s", sid, status)
        return response.Results

    async def transfer_subscriptions(self, params: ua.TransferSubscriptionsParameters) -> list[ua.TransferResult]:
        self.logger.info("transfer_subscriptions %s", list(params.SubscriptionIds))
        request = ua.TransferSubscriptionsRequest()
        request.Parameters = params
        data = await self._send_request(request)
        response = struct_from_binary(ua.TransferSubscriptionsResponse, data)
        response.ResponseHeader.ServiceResult.check()
        return response.Parameters.Results

    async def republish(self, subscription_id: int, retransmit_sequence_number: int) -> ua.NotificationMessage:
        self.logger.debug("republish sub=%s seq=%s", subscription_id, retransmit_sequence_number)
        request = ua.RepublishRequest()
        request.Parameters.SubscriptionId = subscription_id
        request.Parameters.RetransmitSequenceNumber = retransmit_sequence_number
        data = await self._send_request(request)
        response = struct_from_binary(ua.RepublishResponse, data)
        response.ResponseHeader.ServiceResult.check()
        return response.NotificationMessage

    async def inform_subscriptions(self, status: ua.StatusCode) -> None:
        """Inform all current subscriptions with a status code."""
        status_message = ua.StatusChangeNotification(Status=status)
        notification_message = ua.NotificationMessage(NotificationData=[status_message])  # type: ignore[list-item]
        for subid, callback in self._subscription_callbacks.items():
            try:
                parameters = ua.PublishResult(subid, NotificationMessage=notification_message)
                if inspect.iscoroutinefunction(callback):
                    await callback(parameters)
                else:
                    callback(parameters)
            except Exception:
                self.logger.exception("Exception while calling user callback")

    async def publish(self, acks: list[ua.SubscriptionAcknowledgement]) -> ua.PublishResponse:
        """Send a PublishRequest to the server."""
        self.logger.debug("publish %r", acks)
        request = ua.PublishRequest()
        request.Parameters.SubscriptionAcknowledgements = acks if acks else []
        data = await self._send_request(request, timeout=0)
        try:
            response = struct_from_binary(ua.PublishResponse, data)
        except Exception as ex:
            self.logger.exception("Error parsing notification from server")
            raise UaStructParsingError from ex
        return response

    async def _publish_loop(self) -> None:
        """
        Send PublishRequests in a loop and forward `PublishResult` to the matching subscription callback.
        """
        ack: ua.SubscriptionAcknowledgement | None = None
        while not self._closing:
            try:
                response = await self.publish([ack] if ack else [])
            except BadTimeout:
                ack = None
                continue
            except BadNoSubscription:
                self.logger.info("BadNoSubscription received, ignoring because it's probably valid.")
                return
            except UaStructParsingError:
                ack = None
                continue
            subscription_id = response.Parameters.SubscriptionId
            if not subscription_id:
                # Spec Part 4 - Section 5.13.5 "Publish": value 0 means no Subscriptions
                return
            callback = self._subscription_callbacks.get(subscription_id)
            if callback is None:
                self.logger.warning(
                    "Received data for unknown subscription %s active are %s",
                    subscription_id,
                    self._subscription_callbacks.keys(),
                )
            else:
                try:
                    if inspect.iscoroutinefunction(callback):
                        await callback(response.Parameters)
                    else:
                        callback(response.Parameters)
                except Exception:
                    self.logger.exception("Exception while calling user callback")
            if response.Parameters.NotificationMessage.NotificationData:
                ack = ua.SubscriptionAcknowledgement()
                ack.SubscriptionId = subscription_id
                ack.SequenceNumber = response.Parameters.NotificationMessage.SequenceNumber
            else:
                ack = None

    # --- MonitoredItem Service Set ---

    async def create_monitored_items(
        self, params: ua.CreateMonitoredItemsParameters
    ) -> list[ua.MonitoredItemCreateResult]:
        self.logger.info("create_monitored_items")
        request = ua.CreateMonitoredItemsRequest()
        request.Parameters = params
        data = await self._send_request(request)
        response = struct_from_binary(ua.CreateMonitoredItemsResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def delete_monitored_items(self, params: ua.DeleteMonitoredItemsParameters) -> list[ua.StatusCode]:
        self.logger.info("delete_monitored_items")
        request = ua.DeleteMonitoredItemsRequest()
        request.Parameters = params
        data = await self._send_request(request)
        response = struct_from_binary(ua.DeleteMonitoredItemsResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def modify_monitored_items(
        self, params: ua.ModifyMonitoredItemsParameters
    ) -> list[ua.MonitoredItemModifyResult]:
        self.logger.info("modify_monitored_items")
        request = ua.ModifyMonitoredItemsRequest()
        request.Parameters = params
        data = await self._send_request(request)
        response = struct_from_binary(ua.ModifyMonitoredItemsResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Results

    async def set_monitoring_mode(self, params: ua.SetMonitoringModeParameters) -> list[ua.uatypes.StatusCode]:
        self.logger.info("set_monitoring_mode")
        request = ua.SetMonitoringModeRequest()
        request.Parameters = params
        data = await self._send_request(request)
        response = struct_from_binary(ua.SetMonitoringModeResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Parameters.Results

    async def set_publishing_mode(self, params: ua.SetPublishingModeParameters) -> list[ua.uatypes.StatusCode]:
        self.logger.info("set_publishing_mode")
        request = ua.SetPublishingModeRequest()
        request.Parameters = params
        data = await self._send_request(request)
        response = struct_from_binary(ua.SetPublishingModeResponse, data)
        self.logger.debug(response)
        response.ResponseHeader.ServiceResult.check()
        return response.Parameters.Results
