"""
high level interface to subscriptions
"""

from __future__ import annotations

import asyncio
import collections.abc
import inspect
import logging
import math
from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, Any, Protocol, cast, overload

from asyncua import ua
from asyncua.client.ua_client import UaClient
from asyncua.common.ua_utils import copy_dataclass_attr

if TYPE_CHECKING:
    from asyncua.server.internal_session import InternalSession

from .events import Event, get_filter_from_event_type
from .node import Node


class SubscriptionItemData:
    """
    To store useful data from a monitored item.
    """

    def __init__(self):
        self.node = None
        self.client_handle = None
        self.server_handle = None
        self.attribute = None
        self.mfilter = None
        self.monitoring_mode = ua.MonitoringMode.Reporting
        self.sampling_interval = 0.0
        self.queue_size = 0
        self.discard_oldest = True


class DataChangeNotif:
    """
    To be send to clients for every datachange notification from server.
    """

    def __init__(self, subscription_data: SubscriptionItemData, monitored_item: ua.MonitoredItemNotification):
        self.monitored_item = monitored_item
        self.subscription_data = subscription_data

    def __str__(self):
        return f"DataChangeNotification({self.subscription_data}, {self.monitored_item})"

    __repr__ = __str__


class DataChangeNotificationHandler(Protocol):
    def datachange_notification(self, node: Node, val: Any, data: DataChangeNotif) -> None:
        """
        called for every datachange notification from server
        """
        ...


class EventNotificationHandler(Protocol):
    def event_notification(self, event: Event) -> None:
        """
        called for every event notification from server
        """
        ...


class StatusChangeNotificationHandler(Protocol):
    def status_change_notification(self, status: ua.StatusChangeNotification) -> None:
        """
        called for every status change notification from server
        """
        ...


class DataChangeNotificationHandlerAsync(Protocol):
    async def datachange_notification(self, node: Node, val: Any, data: DataChangeNotif) -> None:
        """
        called for every datachange notification from server
        """
        ...


class EventNotificationHandlerAsync(Protocol):
    async def event_notification(self, event: Event) -> None:
        """
        called for every event notification from server
        """
        ...


class StatusChangeNotificationHandlerAsync(Protocol):
    async def status_change_notification(self, status: ua.StatusChangeNotification) -> None:
        """
        called for every status change notification from server
        """
        ...


# Protocol type alias for subscription handlers receiving server notifications.
SubscriptionHandler = (
    DataChangeNotificationHandler
    | EventNotificationHandler
    | StatusChangeNotificationHandler
    | DataChangeNotificationHandlerAsync
    | EventNotificationHandlerAsync
    | StatusChangeNotificationHandlerAsync
)


def _make_monitored_item_request_from_data(data: SubscriptionItemData) -> ua.MonitoredItemCreateRequest:
    rv = ua.ReadValueId()
    rv.NodeId = data.node.nodeid
    rv.AttributeId = data.attribute
    mparams = ua.MonitoringParameters()
    mparams.ClientHandle = data.client_handle
    mparams.SamplingInterval = data.sampling_interval
    mparams.QueueSize = data.queue_size
    mparams.DiscardOldest = data.discard_oldest
    if data.mfilter:
        mparams.Filter = data.mfilter
    mir = ua.MonitoredItemCreateRequest()
    mir.ItemToMonitor = rv
    mir.MonitoringMode = data.monitoring_mode
    mir.RequestedParameters = mparams
    return mir


def _make_monitoring_parameters_request(
    new_queuesize: int,
    new_samp_time: ua.Duration,
    mod_filter: ua.MonitoringFilter | None,
    client_handle: ua.IntegerId,
) -> ua.MonitoringParameters:
    req_params = ua.MonitoringParameters()
    req_params.ClientHandle = client_handle
    req_params.QueueSize = new_queuesize
    req_params.Filter = mod_filter
    req_params.SamplingInterval = new_samp_time
    return req_params


def _normalize_nodes(nodes: Node | Iterable[Node]) -> tuple[list[Node], bool]:
    if isinstance(nodes, collections.abc.Iterable):
        return list(nodes), True
    return [nodes], False


async def _create_event_filter(
    server: InternalSession | UaClient,
    evtypes: Node | ua.NodeId | str | int | Iterable[Node | ua.NodeId | str | int],
    where_clause_generation: bool = True,
) -> ua.EventFilter:
    if isinstance(evtypes, int | str | ua.NodeId | Node):
        evtypes = [evtypes]
    event_types = [Node(server, evtype) for evtype in evtypes]  # type: ignore[union-attr]
    return await get_filter_from_event_type(event_types, where_clause_generation)


def _is_base_event_type(
    server: InternalSession | UaClient, evtypes: Node | ua.NodeId | str | int | Iterable[Node | ua.NodeId | str | int]
) -> bool:
    if not isinstance(evtypes, int | str | ua.NodeId | Node):
        return False
    return Node(server, evtypes).nodeid == ua.NodeId(ua.ObjectIds.BaseEventType)


def _create_deadband_filter(deadband_val: ua.Double, deadbandtype: ua.UInt32 = 1) -> ua.DataChangeFilter:
    deadband_filter = ua.DataChangeFilter()
    # Send notification when status or value changes.
    deadband_filter.Trigger = ua.DataChangeTrigger(1)
    deadband_filter.DeadbandType = deadbandtype
    # absolute float value or from 0 to 100 for percentage deadband
    deadband_filter.DeadbandValue = deadband_val
    return deadband_filter


def _create_subscription_item_data(
    server: InternalSession | UaClient, mi: ua.MonitoredItemCreateRequest
) -> SubscriptionItemData:
    data = SubscriptionItemData()
    data.client_handle = mi.RequestedParameters.ClientHandle
    data.node = Node(server, mi.ItemToMonitor.NodeId)
    data.attribute = mi.ItemToMonitor.AttributeId
    data.monitoring_mode = mi.MonitoringMode
    data.sampling_interval = mi.RequestedParameters.SamplingInterval
    data.queue_size = mi.RequestedParameters.QueueSize
    data.discard_oldest = mi.RequestedParameters.DiscardOldest
    # TODO: Either use the filter from request or from response.
    #  Here it uses from request, in modify it uses from response
    data.mfilter = mi.RequestedParameters.Filter
    return data


def _build_server_to_client_handle_map(monitored_items: dict[int, SubscriptionItemData]) -> dict[int, int]:
    return {value.server_handle: key for key, value in monitored_items.items()}


def _get_expected_samples_per_publish(
    publishing_interval: float, sampling_interval: ua.Duration, monitoring: ua.MonitoringMode
) -> int | None:
    if monitoring != ua.MonitoringMode.Reporting:
        return None
    if sampling_interval <= 0:
        return None
    if publishing_interval <= 0:
        return None

    expected_samples_per_publish = math.ceil(publishing_interval / sampling_interval)
    if expected_samples_per_publish <= 1:
        return None
    return expected_samples_per_publish


def _is_queue_size_potentially_too_small(queuesize: int, expected_samples_per_publish: int) -> bool:
    effective_queue_size = 1 if queuesize in (0, 1) else queuesize
    return effective_queue_size < expected_samples_per_publish


def _make_queue_warning_key(
    publishing_interval: float, sampling_interval: ua.Duration, queuesize: int
) -> tuple[float, float, int]:
    return (publishing_interval, float(sampling_interval), queuesize)


def _collect_datachange_handler_args(
    datachange: ua.DataChangeNotification,
    monitored_items: dict[int, SubscriptionItemData],
    logger: logging.Logger,
) -> list[tuple[Node, Any, DataChangeNotif]]:
    known_handles_args: list[tuple[Node, Any, DataChangeNotif]] = []
    for item in datachange.MonitoredItems:
        if item.ClientHandle not in monitored_items:
            logger.warning("Received a notification for unknown handle: %s", item.ClientHandle)
            continue
        data = monitored_items[item.ClientHandle]
        event_data = DataChangeNotif(data, item)
        # FIXME: Value can be None
        known_handles_args.append((data.node, item.Value.Value.Value, event_data))  # type: ignore[union-attr]
    return known_handles_args


async def _dispatch_datachange_notifications(
    callback: Callable[[Node, Any, DataChangeNotif], Any],
    known_handles_args: list[tuple[Node, Any, DataChangeNotif]],
) -> None:
    tasks = []
    for args in known_handles_args:
        result = callback(*args)
        if inspect.isawaitable(result):
            tasks.append(result)
    if tasks:
        await asyncio.gather(*tasks)


async def _dispatch_event_notification(callback: Callable[[Event], Any], event: Event) -> None:
    result = callback(event)
    if inspect.isawaitable(result):
        await result


async def _dispatch_status_change_notification(
    callback: Callable[[ua.StatusChangeNotification], Any],
    status: ua.StatusChangeNotification,
) -> None:
    result = callback(status)
    if inspect.isawaitable(result):
        await result


def _build_event_from_notification(
    monitored_items: dict[int, SubscriptionItemData],
    event_notification: ua.EventFieldList,
    logger: logging.Logger,
) -> Event | None:
    if event_notification.ClientHandle not in monitored_items:
        logger.warning("Received a notification for unknown handle: %s", event_notification.ClientHandle)
        return None

    data = monitored_items[event_notification.ClientHandle]
    result = Event.from_event_fields(data.mfilter.SelectClauses, event_notification.EventFields)
    result.server_handle = data.server_handle
    return result


class Subscription:
    """
    Subscription object returned by Server or Client objects.
    The object represent a subscription to an opc-ua server.
    This is a high level class, especially `subscribe_data_change` and `subscribe_events methods`.
    If more control is necessary look at code and/or use `create_monitored_items method`.
    :param server: `InternalSession` or `UaClient`
    """

    def __init__(
        self,
        server: InternalSession | UaClient,
        params: ua.CreateSubscriptionParameters,
        handler: SubscriptionHandler,
    ):
        self.logger = logging.getLogger(__name__)
        self.server: InternalSession | UaClient = server
        self._client_handle = 200
        self._handler: SubscriptionHandler = handler
        self.parameters: ua.CreateSubscriptionParameters = params  # move to data class
        self._monitored_items: dict[int, SubscriptionItemData] = {}
        self._queue_sizing_warnings_emitted: set[tuple[float, float, int]] = set()
        self.subscription_id: int | None = None

    def _warn_if_potential_queue_overflow(
        self, queuesize: int, monitoring: ua.MonitoringMode, sampling_interval: ua.Duration
    ) -> None:
        """
        Emit a best-effort warning when queue settings are likely too small.

        This helper compares requested `sampling_interval` against the subscription
        `RequestedPublishingInterval` and estimates how many samples can arrive
        within one publish cycle: ``ceil(publishing_interval / sampling_interval)``.
        If the effective queue size (where OPC UA ``queueSize`` values 0 and 1 are
        treated as a single-slot queue) is smaller than that estimate, this method
        logs a warning about potential overflow and possible data loss.

        Notes:
        - This is a heuristic, not a protocol guarantee. Real overflow behavior
          depends on source change rate, deadband/filtering, server internals, and
          network latency.
        - Warnings are de-duplicated per setting tuple to avoid log spam.
        - Only applies to monitored items in ``Reporting`` mode.
        """
        publishing_interval = float(self.parameters.RequestedPublishingInterval or 0.0)
        expected_samples_per_publish = _get_expected_samples_per_publish(
            publishing_interval, sampling_interval, monitoring
        )
        if expected_samples_per_publish is None:
            return

        if not _is_queue_size_potentially_too_small(queuesize, expected_samples_per_publish):
            return

        warning_key = _make_queue_warning_key(publishing_interval, sampling_interval, queuesize)
        if warning_key in self._queue_sizing_warnings_emitted:
            return
        self._queue_sizing_warnings_emitted.add(warning_key)

        self.logger.warning(
            "Potential monitored item queue overflow: publishing interval %.1f ms and sampling interval %.1f ms can produce up to %s samples per publish cycle, but queue_size=%s. Consider increasing queue_size or adjusting sampling/publishing intervals.",
            publishing_interval,
            sampling_interval,
            expected_samples_per_publish,
            queuesize,
        )

    async def init(self) -> ua.CreateSubscriptionResult:
        response = await self.server.create_subscription(self.parameters, callback=self.publish_callback)
        self.subscription_id = response.SubscriptionId  # move to data class
        self.logger.info("Subscription created %s", self.subscription_id)
        return response

    async def update(self, params: ua.ModifySubscriptionParameters) -> ua.ModifySubscriptionResult:
        if not isinstance(self.server, UaClient):
            raise ua.uaerrors.UaError(f"update() is not supported in {self.server}.")
        response = await self.server.update_subscription(params)
        self.logger.info("Subscription updated %s", params.SubscriptionId)
        # update the self.parameters attr with the updated values
        copy_dataclass_attr(params, self.parameters)
        return response

    async def publish_callback(self, publish_result: ua.PublishResult) -> None:
        """
        Handle `PublishResult` callback.
        """
        self.logger.info("Publish callback called with result: %s", publish_result)
        if publish_result.NotificationMessage.NotificationData is not None:
            for notif in publish_result.NotificationMessage.NotificationData:
                if isinstance(notif, ua.DataChangeNotification):
                    await self._call_datachange(notif)
                elif isinstance(notif, ua.EventNotificationList):
                    await self._call_event(notif)
                elif isinstance(notif, ua.StatusChangeNotification):
                    await self._call_status(notif)
                else:
                    self.logger.warning("Notification type not supported yet for notification %s", notif)

    async def delete(self) -> None:
        """
        Delete subscription on server. This is automatically done by Client and Server classes on exit.
        """
        results = await self.server.delete_subscriptions([self.subscription_id])
        results[0].check()
        self.subscription_id = None
        self._monitored_items.clear()

    async def recreate(self) -> tuple[int, int]:
        if not isinstance(self.server, UaClient):
            raise ua.uaerrors.UaError(f"recreate() is not supported in {self.server}.")
        if self.subscription_id is None:
            raise ua.uaerrors.UaError("Cannot recreate subscription without a valid subscription id")

        old_subscription_id = self.subscription_id
        monitored_items_snapshot = list(self._monitored_items.values())
        self.server._subscription_callbacks.pop(old_subscription_id, None)
        self.server._last_publish_sequence_numbers.pop(old_subscription_id, None)
        self.server._subscription_watchdog_states.pop(old_subscription_id, None)

        response = await self.server.create_subscription(self.parameters, callback=self.publish_callback)
        self.subscription_id = response.SubscriptionId

        if monitored_items_snapshot:
            requests = [
                _make_monitored_item_request_from_data(data)
                for data in sorted(monitored_items_snapshot, key=lambda item: item.client_handle)
            ]
            self._monitored_items.clear()
            await self.create_monitored_items(requests)

        self.logger.warning("Subscription recreated from %s to %s", old_subscription_id, self.subscription_id)
        return old_subscription_id, self.subscription_id

    async def _call_datachange(self, datachange: ua.DataChangeNotification) -> None:
        if not hasattr(self._handler, "datachange_notification"):
            self.logger.error("DataChange subscription created but handler has no datachange_notification method")
            return

        known_handles_args = _collect_datachange_handler_args(datachange, self._monitored_items, self.logger)
        callback = cast(Callable[[Node, Any, DataChangeNotif], Any], self._handler.datachange_notification)

        try:
            await _dispatch_datachange_notifications(callback, known_handles_args)
        except Exception as ex:
            self.logger.exception("Exception calling data change handler. Error: %s", ex)

    async def _call_event(self, eventlist: ua.EventNotificationList) -> None:
        for event_notification in eventlist.Events:
            result = _build_event_from_notification(self._monitored_items, event_notification, self.logger)
            if result is None:
                continue
            if hasattr(self._handler, "event_notification"):
                callback = cast(Callable[[Event], Any], self._handler.event_notification)
                try:
                    await _dispatch_event_notification(callback, result)
                except Exception:
                    self.logger.exception("Exception calling event handler")
            else:
                self.logger.error("Event subscription created but handler has no event_notification method")

    async def _call_status(self, status: ua.StatusChangeNotification) -> None:
        if not hasattr(self._handler, "status_change_notification"):
            self.logger.error("DataChange subscription has no status_change_notification method")
            return
        callback = cast(Callable[[ua.StatusChangeNotification], Any], self._handler.status_change_notification)
        try:
            await _dispatch_status_change_notification(callback, status)
        except Exception:
            self.logger.exception("Exception calling status change handler")

    @overload
    async def subscribe_data_change(
        self,
        nodes: Node,
        attr: ua.AttributeIds = ua.AttributeIds.Value,
        queuesize: int = 0,
        monitoring=ua.MonitoringMode.Reporting,
        sampling_interval: ua.Duration = 0.0,
    ) -> int: ...

    @overload
    async def subscribe_data_change(
        self,
        nodes: Node | Iterable[Node],
        attr: ua.AttributeIds = ua.AttributeIds.Value,
        queuesize: int = 0,
        monitoring=ua.MonitoringMode.Reporting,
        sampling_interval: ua.Duration = 0.0,
    ) -> list[int | ua.StatusCode]: ...

    async def subscribe_data_change(
        self,
        nodes: Node | Iterable[Node],
        attr: ua.AttributeIds = ua.AttributeIds.Value,
        queuesize: int = 0,
        monitoring=ua.MonitoringMode.Reporting,
        sampling_interval: ua.Duration = 50.0,
    ) -> int | list[int | ua.StatusCode]:
        """
        Subscribe to data change events of one or multiple nodes.
        The default attribute used for the subscription is `Value`.
        Return value is a handle which can be used to modify/cancel the subscription.
        The handle is an integer value for single Nodes. If the creation of the subscription fails an
        `UaStatusCodeError` is raised.
        If multiple Nodes are supplied, a List of integers or ua.StatusCode objects is returned. A list of
        StatusCode objects are returned to indicate that the subscription has failed (no exception will be
        raised in this case).
        If more control is necessary the `create_monitored_items` method can be used directly.

        :param nodes: One Node or an Iterable of Nodes
        :param attr: The Node attribute you want to subscribe to
        :param queuesize: 0 or 1 for default queue size (shall be 1 - no queuing), n for FIFO queue
        :param sampling_interval: ua.Duration
        :return: Handle for changing/cancelling of the subscription
        """
        return await self._subscribe(
            nodes, attr, queuesize=queuesize, monitoring=monitoring, sampling_interval=sampling_interval
        )

    async def subscribe_events(
        self,
        sourcenode: Node | ua.NodeId | str | int = ua.ObjectIds.Server,
        evtypes: Node | ua.NodeId | str | int | Iterable[Node | ua.NodeId | str | int] = ua.ObjectIds.BaseEventType,
        evfilter: ua.EventFilter | None = None,
        queuesize: int = 0,
        where_clause_generation: bool = True,
    ) -> int:
        """
        Subscribe to events from a node. Default node is Server node.
        In most servers the server node is the only one you can subscribe to.
        If evtypes is not provided, evtype defaults to BaseEventType.
        If evtypes is a list or tuple of custom event types, the events will be filtered to the supplied types.
        A handle (integer value) is returned which can be used to modify/cancel the subscription.

        :param sourcenode: int, str, ua.NodeId or Node
        :param evtypes: ua.ObjectIds, str, ua.NodeId or Node
        :param evfilter: ua.EventFilter which provides the SelectClauses and WhereClause
        :param queuesize: 0 for default queue size, 1 for minimum queue size, n for FIFO queue,
        MaxUInt32 for max queue size
        :param where_clause_generation: No where_clause generation when no eventfilter is provided. Need for TwinCAT, Codesys
        :return: Handle for changing/cancelling of the subscription
        """
        sourcenode = Node(self.server, sourcenode)
        if evfilter is None:
            if _is_base_event_type(self.server, evtypes):
                # Remove where clause for base event type, for servers that have problems with long WhereClauses.
                # Also because BaseEventType wants every event we can ommit it. Issue: #1205
                where_clause_generation = False
            evfilter = await _create_event_filter(self.server, evtypes, where_clause_generation)
        return await self._subscribe(sourcenode, ua.AttributeIds.EventNotifier, evfilter, queuesize=queuesize)  # type: ignore

    async def subscribe_alarms_and_conditions(
        self,
        sourcenode: Node | ua.NodeId | str | int = ua.ObjectIds.Server,
        evtypes: Node | ua.NodeId | str | int | Iterable[Node | ua.NodeId | str | int] = ua.ObjectIds.ConditionType,
        evfilter: ua.EventFilter | None = None,
        queuesize: int = 0,
    ) -> int:
        """
        Subscribe to alarm and condition events from a node. Default node is Server node.
        In many servers the server node is the only one you can subscribe to.
        If evtypes is not provided, evtype defaults to ConditionType.
        If evtypes is a list or tuple of custom event types, the events will be filtered to the supplied types.
        A handle (integer value) is returned which can be used to modify/cancel the subscription.

        :param sourcenode: int, str, ua.NodeId or Node
        :param evtypes: ua.ObjectIds, str, ua.NodeId or Node
        :param evfilter: ua.EventFilter which provides the SelectClauses and WhereClause
        :param queuesize: 0 for default queue size, 1 for minimum queue size, n for FIFO queue,
        MaxUInt32 for max queue size
        :return: Handle for changing/cancelling of the subscription
        """
        return await self.subscribe_events(sourcenode, evtypes, evfilter, queuesize)

    @overload
    async def _subscribe(
        self,
        nodes: Node,
        attr=ua.AttributeIds.Value,
        mfilter: ua.MonitoringFilter | None = None,
        queuesize: int = 0,
        monitoring: ua.MonitoringMode = ua.MonitoringMode.Reporting,
        sampling_interval: ua.Duration = 0.0,
    ) -> int: ...

    @overload
    async def _subscribe(
        self,
        nodes: Iterable[Node],
        attr=ua.AttributeIds.Value,
        mfilter: ua.MonitoringFilter | None = None,
        queuesize: int = 0,
        monitoring: ua.MonitoringMode = ua.MonitoringMode.Reporting,
        sampling_interval: ua.Duration = 0.0,
    ) -> list[int | ua.StatusCode]: ...

    async def _subscribe(
        self,
        nodes: Node | Iterable[Node],
        attr=ua.AttributeIds.Value,
        mfilter: ua.MonitoringFilter | None = None,
        queuesize: int = 0,
        monitoring: ua.MonitoringMode = ua.MonitoringMode.Reporting,
        sampling_interval: ua.Duration = 0.0,
    ) -> int | list[int | ua.StatusCode]:
        """
        Private low level method for subscribing.
        :param nodes: One Node or an Iterable of Nodes.
        :param attr: ua.AttributeId which shall be subscribed
        :param mfilter: ua.MonitoringFilter which shall be applied
        :param queuesize: queue size
        :param monitoring: ua.MonitoringMode
        :param sampling_interval: ua.Duration
        :return: Integer handle or if multiple Nodes were given a List of Integer handles/ua.StatusCode
        """
        nodes, is_list = _normalize_nodes(nodes)
        # Create List of MonitoredItemCreateRequest
        mirs = []
        for node in nodes:
            mir = self._make_monitored_item_request(node, attr, mfilter, queuesize, monitoring, sampling_interval)
            mirs.append(mir)
        # Await MonitoredItemCreateResult
        mids = await self.create_monitored_items(mirs)
        if is_list:
            # Return results for multiple nodes
            return mids
        # Check and return result for single node (raise `UaStatusCodeError` if subscription failed)
        if isinstance(mids[0], ua.StatusCode):
            mids[0].check()
        return mids[0]  # type: ignore

    def _make_monitored_item_request(
        self, node: Node, attr, mfilter, queuesize, monitoring, sampling_interval
    ) -> ua.MonitoredItemCreateRequest:
        self._warn_if_potential_queue_overflow(queuesize, monitoring, sampling_interval)
        rv = ua.ReadValueId()
        rv.NodeId = node.nodeid
        rv.AttributeId = attr
        # rv.IndexRange //We leave it null, then the entire array is returned
        mparams = ua.MonitoringParameters()
        self._client_handle += 1
        mparams.ClientHandle = self._client_handle
        mparams.SamplingInterval = sampling_interval
        mparams.QueueSize = queuesize
        mparams.DiscardOldest = True
        if mfilter:
            mparams.Filter = mfilter
        mir = ua.MonitoredItemCreateRequest()
        mir.ItemToMonitor = rv
        mir.MonitoringMode = monitoring
        mir.RequestedParameters = mparams
        return mir

    async def create_monitored_items(
        self, monitored_items: Iterable[ua.MonitoredItemCreateRequest]
    ) -> list[int | ua.StatusCode]:
        """
        low level method to have full control over subscription parameters.
        Client handle must be unique since it will be used as key for internal registration of data.
        """
        params = ua.CreateMonitoredItemsParameters()
        params.SubscriptionId = self.subscription_id
        params.ItemsToCreate = list(monitored_items)
        params.TimestampsToReturn = ua.TimestampsToReturn.Both
        # insert monitored item into map to avoid notification arrive before result return
        # server_handle is left as None in purpose as we don't get it yet.
        for mi in monitored_items:
            self._monitored_items[mi.RequestedParameters.ClientHandle] = _create_subscription_item_data(self.server, mi)
        results = await self.server.create_monitored_items(params)
        mids = []
        # process result, add server_handle, or remove it if failed
        for idx, result in enumerate(results):
            mi = params.ItemsToCreate[idx]
            if not result.StatusCode.is_good():
                del self._monitored_items[mi.RequestedParameters.ClientHandle]
                mids.append(result.StatusCode)
                continue
            data = self._monitored_items[mi.RequestedParameters.ClientHandle]
            data.server_handle = result.MonitoredItemId
            mids.append(result.MonitoredItemId)
        return mids

    async def unsubscribe(self, handle: int | Iterable[int]) -> None:
        """
        Unsubscribe from datachange or events using the handle returned while subscribing.
        If you delete the subscription, you do not need to unsubscribe.
        :param handle: The handle that was returned when subscribing to the node/nodes
        """
        handles: Iterable[int] = [handle] if isinstance(handle, int) else handle
        if not handles:
            return
        if self.subscription_id is None:
            raise ua.UaStatusCodeError(ua.StatusCodes.BadSubscriptionIdInvalid)
        params = ua.DeleteMonitoredItemsParameters()
        params.SubscriptionId = self.subscription_id
        params.MonitoredItemIds = list(handles)
        results = await self.server.delete_monitored_items(params)
        results[0].check()
        handle_map = _build_server_to_client_handle_map(self._monitored_items)
        for handle in handles:
            if handle in handle_map:
                del self._monitored_items[handle_map[handle]]

    async def modify_monitored_item(
        self, handle: int, new_samp_time: ua.Duration, new_queuesize: int = 0, mod_filter_val: int = -1
    ) -> list[ua.MonitoredItemModifyResult]:
        """
        Modify a monitored item.
        :param handle: Handle returned when originally subscribing
        :param new_samp_time: New wanted sample time
        :param new_queuesize: New wanted queuesize, default is 0
        :param mod_filter_val: New deadband filter value
        :return: Return a Modify Monitored Item Result
        """
        # Find the monitored item in the monitored item registry.
        item_to_change = next(item for item in self._monitored_items.values() if item.server_handle == handle)
        if not item_to_change:
            raise ValueError("The monitored item was not found.")
        if mod_filter_val is None:
            mod_filter = None
        elif mod_filter_val < 0:
            mod_filter = item_to_change.mfilter
        else:
            mod_filter = _create_deadband_filter(mod_filter_val, 1)

        self._warn_if_potential_queue_overflow(new_queuesize, item_to_change.monitoring_mode, new_samp_time)

        modif_item = ua.MonitoredItemModifyRequest()
        modif_item.MonitoredItemId = handle
        modif_item.RequestedParameters = _make_monitoring_parameters_request(
            new_queuesize, new_samp_time, mod_filter, item_to_change.client_handle
        )
        params = ua.ModifyMonitoredItemsParameters()
        params.SubscriptionId = self.subscription_id
        params.ItemsToModify.append(modif_item)
        results = await self.server.modify_monitored_items(params)
        item_to_change.mfilter = results[0].FilterResult
        return results

    @overload
    async def deadband_monitor(
        self,
        var: Node,
        deadband_val: ua.Double,
        deadbandtype: ua.UInt32 = 1,
        queuesize: int = 0,
        attr: ua.AttributeIds = ua.AttributeIds.Value,
    ) -> int: ...

    @overload
    async def deadband_monitor(
        self,
        var: Iterable[Node],
        deadband_val: ua.Double,
        deadbandtype: ua.UInt32 = 1,
        queuesize: int = 0,
        attr: ua.AttributeIds = ua.AttributeIds.Value,
    ) -> list[int | ua.StatusCode]: ...

    async def deadband_monitor(
        self,
        var: Node | Iterable[Node],
        deadband_val: ua.Double,
        deadbandtype: ua.UInt32 = 1,
        queuesize: int = 0,
        attr: ua.AttributeIds = ua.AttributeIds.Value,
    ) -> int | list[int | ua.StatusCode]:
        """
        Method to create a subscription with a Deadband Value.
        Default deadband value type is absolute.
        Return a handle which can be used to unsubscribe
        :param var: Variable to which you want to subscribe
        :param deadband_val: Absolute float value
        :param deadbandtype: Default value is 1 (absolute), change to 2 for percentage deadband
        :param queuesize: Wanted queue size, default is 1
        :param attr: Attribute ID
        """
        deadband_filter = _create_deadband_filter(deadband_val, deadbandtype)
        return await self._subscribe(var, attr, deadband_filter, queuesize)

    async def set_monitoring_mode(self, monitoring: ua.MonitoringMode) -> list[ua.uatypes.StatusCode]:
        """
        The monitoring mode parameter is used
        to enable/disable the sampling of MonitoredItems
        (Samples don't queue on the server side)

        :param monitoring: The monitoring mode to apply
        :return: Return a Set Monitoring Mode Result
        """
        if not isinstance(self.server, UaClient):
            raise ua.uaerrors.UaError(f"set_monitoring_mode() is not supported in {self.server}.")
        node_handles = []
        for mi in self._monitored_items.values():
            node_handles.append(mi.server_handle)

        params = ua.SetMonitoringModeParameters()
        params.SubscriptionId = self.subscription_id
        params.MonitoredItemIds = node_handles
        params.MonitoringMode = monitoring
        return await self.server.set_monitoring_mode(params)

    async def set_publishing_mode(self, publishing: bool) -> list[ua.uatypes.StatusCode]:
        """
        Disable publishing of NotificationMessages for the subscription,
        but doesn't discontinue the sending of keep-alive Messages,
        nor change the monitoring mode.

        :param publishing: The publishing mode to apply
        :return: Return a Set Publishing Mode Result
        """
        self.logger.info("set_publishing_mode")
        if not isinstance(self.server, UaClient):
            raise ua.uaerrors.UaError(f"set_publishing_mode() is not supported in {self.server}.")
        params = ua.SetPublishingModeParameters()
        params.SubscriptionIds = [self.subscription_id]  # type: ignore
        params.PublishingEnabled = publishing
        result = await self.server.set_publishing_mode(params)
        if result[0].is_good():
            self.parameters.PublishingEnabled = publishing
        return result
