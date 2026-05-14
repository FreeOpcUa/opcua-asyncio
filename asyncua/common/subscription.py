"""
high level interface to subscriptions
"""

from __future__ import annotations

import asyncio
import collections.abc
import inspect
import logging
import time
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol, overload

from asyncua import ua
from asyncua.client.ua_session import UaSession
from asyncua.common.ua_utils import copy_dataclass_attr
from asyncua.ua.uaerrors import BadMessageNotAvailable

if TYPE_CHECKING:
    from asyncua.server.internal_session import InternalSession

from .events import Event, get_filter_from_event_type
from .node import Node


class SubscriptionItemData:
    """
    To store useful data from a monitored item.

    The queuesize / monitoring_mode / sampling_interval fields are captured so the
    Subscription can be re-created on the server after a reconnect.
    """

    def __init__(self) -> None:
        self.node: Node | None = None
        self.client_handle: int | None = None
        self.server_handle: int | None = None
        self.attribute: ua.AttributeIds | None = None
        self.mfilter: ua.MonitoringFilter | ua.EventFilter | None = None
        self.queuesize: int = 0
        self.monitoring_mode: ua.MonitoringMode = ua.MonitoringMode.Reporting
        self.sampling_interval: ua.Duration = 0.0


class DataChangeNotif:
    """
    To be send to clients for every datachange notification from server.
    """

    def __init__(self, subscription_data: SubscriptionItemData, monitored_item: ua.MonitoredItemNotification) -> None:
        self.monitored_item = monitored_item
        self.subscription_data = subscription_data

    def __str__(self) -> str:
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


SubscriptionHandler = (
    DataChangeNotificationHandler
    | EventNotificationHandler
    | StatusChangeNotificationHandler
    | DataChangeNotificationHandlerAsync
    | EventNotificationHandlerAsync
    | StatusChangeNotificationHandlerAsync
)

"""
Protocol class representing subscription handlers to receive events from server.
"""


@dataclass(frozen=True)
class DataChangeEvent:
    """A single monitored-item data change, yielded by Subscription's async iterator."""

    node: Node
    value: Any
    data: DataChangeNotif


@dataclass(frozen=True)
class OpcEvent:
    """An OPC UA event firing, yielded by Subscription's async iterator."""

    event: Event


@dataclass(frozen=True)
class StatusChangeEvent:
    """A server-side subscription status change, yielded by Subscription's async iterator.

    `notification.Status` is the `StatusCode`; `notification.DiagnosticInfo` carries the
    server's diagnostic data when available.
    """

    notification: ua.StatusChangeNotification


SubEvent = DataChangeEvent | OpcEvent | StatusChangeEvent


class OverflowPolicy(str, Enum):
    """Behavior when the iterator-mode Subscription queue is full."""

    DROP_OLDEST = "drop_oldest"  # pop front, push new — keeps most recent state
    DROP_NEWEST = "drop_newest"  # discard incoming notification
    WARN = "warn"  # log a warning AND drop the newest
    DISCONNECT = "disconnect"  # force a reconnect via the supervisor


class Subscription:
    """
    Subscription object returned by Server or Client objects.
    The object represent a subscription to an opc-ua server.
    This is a high level class, especially `subscribe_data_change` and `subscribe_events methods`.
    If more control is necessary look at code and/or use `create_monitored_items method`.
    :param server: `InternalSession` or `UaSession`
    """

    def __init__(
        self,
        server: InternalSession | UaSession,
        params: ua.CreateSubscriptionParameters,
        handler: SubscriptionHandler | None = None,
        *,
        queue_maxsize: int = 1000,
        overflow: OverflowPolicy = OverflowPolicy.DROP_OLDEST,
    ) -> None:
        self.logger = logging.getLogger(__name__)
        self.server: InternalSession | UaSession = server
        self._client_handle = 200
        # Legacy callback path: events are dispatched to handler methods.
        # New iterator path: events are pushed into _event_queue and consumed
        # via `async for ev in sub`. Exactly one path is active at a time —
        # picking the handler arg vs leaving it None at construction.
        self._handler: SubscriptionHandler | None = handler
        # Queue is created eagerly in iterator mode so publish_callback can
        # start filling it before the consumer iterates.
        self._event_queue: asyncio.Queue[SubEvent | None] | None = (
            None if handler is not None else asyncio.Queue(maxsize=queue_maxsize)
        )
        self._queue_maxsize = queue_maxsize
        self._overflow = overflow
        self.parameters: ua.CreateSubscriptionParameters = params  # move to data class
        self._monitored_items: dict[int, SubscriptionItemData] = {}
        self.subscription_id: int | None = None
        # Tracks whether the user explicitly deleted this subscription, so the
        # auto-reconnect supervisor can skip re-creating dead subscriptions.
        self._deleted: bool = False
        # Monotonic timestamp of the last publish response we received for this
        # subscription. Used by the stale-subscription watchdog to detect a
        # subscription that's gone dead on the server side without the transport
        # going down. `None` means no notification has arrived yet.
        self.last_publish_at: float | None = None
        self.last_sequence_number: int | None = None
        # Hook the watchdog (set by Client.create_subscription) uses to force
        # a full reconnect cycle when overflow=DISCONNECT fires.
        self._on_overflow_disconnect: Any = None
        # Keep strong refs to in-flight dispatch tasks so the GC can't cancel
        # them while they're still running user-handler code.
        self._dispatch_tasks: set[asyncio.Task[None]] = set()

    async def init(self) -> ua.CreateSubscriptionResult:
        response = await self.server.create_subscription(self.parameters, callback=self.publish_callback)
        self.subscription_id = response.SubscriptionId  # move to data class
        self.logger.info("Subscription created %s", self.subscription_id)
        return response

    async def update(self, params: ua.ModifySubscriptionParameters) -> ua.ModifySubscriptionResult:
        if not isinstance(self.server, UaSession):
            raise ua.uaerrors.UaError(f"update() is not supported in {self.server}.")
        response = await self.server.update_subscription(params)
        self.logger.info("Subscription updated %s", params.SubscriptionId)
        # update the self.parameters attr with the updated values
        copy_dataclass_attr(params, self.parameters)
        return response

    async def publish_callback(self, publish_result: ua.PublishResult) -> None:
        """
        Handle a `PublishResult` from the publish loop.

        This stays cheap and synchronous-feeling: notifications are exploded
        into typed `SubEvent` instances, and each is delivered without
        awaiting user code. The publish loop never blocks on a slow consumer.
        """
        self.logger.info("Publish callback called with result: %s", publish_result)
        self.last_publish_at = time.monotonic()
        if publish_result.NotificationMessage.NotificationData is None:
            return
        self.last_sequence_number = int(publish_result.NotificationMessage.SequenceNumber)
        for event in self._explode_notifications(publish_result.NotificationMessage.NotificationData):
            self._deliver(event)

    def _explode_notifications(self, notification_data: Iterable[Any]) -> Iterable[SubEvent]:
        """Translate server `NotificationData` items into typed `SubEvent`s."""
        for notif in notification_data:
            if isinstance(notif, ua.DataChangeNotification):
                yield from self._explode_datachange(notif)
            elif isinstance(notif, ua.EventNotificationList):
                yield from self._explode_events(notif)
            elif isinstance(notif, ua.StatusChangeNotification):
                yield StatusChangeEvent(notification=notif)
            else:
                self.logger.warning("Notification type not supported yet for notification %s", notif)

    def _explode_datachange(self, datachange: ua.DataChangeNotification) -> Iterable[DataChangeEvent]:
        for item in datachange.MonitoredItems:
            data = self._monitored_items.get(item.ClientHandle)
            if data is None or data.node is None:
                self.logger.warning("Received a notification for unknown handle: %s", item.ClientHandle)
                continue
            event_data = DataChangeNotif(data, item)
            # Value can be None on some server responses; preserve the raw
            # behavior of master here.
            value = item.Value.Value.Value if item.Value and item.Value.Value else None  # type: ignore[union-attr]
            yield DataChangeEvent(node=data.node, value=value, data=event_data)

    def _explode_events(self, eventlist: ua.EventNotificationList) -> Iterable[OpcEvent]:
        for event in eventlist.Events:
            data = self._monitored_items.get(event.ClientHandle)
            if data is None:
                self.logger.warning("Received event for unknown handle: %s", event.ClientHandle)
                continue
            if data.mfilter is None or not hasattr(data.mfilter, "SelectClauses"):
                self.logger.warning(
                    "Received event notification but monitored item has no event filter: %s", event.ClientHandle
                )
                continue
            result = Event.from_event_fields(data.mfilter.SelectClauses, event.EventFields)  # type: ignore[union-attr]
            result.server_handle = data.server_handle
            yield OpcEvent(event=result)

    def _deliver(self, event: SubEvent) -> None:
        """Deliver one event to either the iterator queue or the legacy handler.

        Either path is non-blocking: the iterator path uses `put_nowait` (with
        the configured overflow policy), and the handler path schedules a task
        so the publish loop doesn't await user code.
        """
        if self._event_queue is not None:
            try:
                self._event_queue.put_nowait(event)
                return
            except asyncio.QueueFull:
                self._handle_overflow(event)
                return
        if self._handler is not None:
            task = asyncio.create_task(self._dispatch_to_handler(event))
            self._dispatch_tasks.add(task)
            task.add_done_callback(self._dispatch_tasks.discard)

    def _handle_overflow(self, event: SubEvent) -> None:
        """Apply the configured overflow policy when the iterator queue is full."""
        assert self._event_queue is not None
        if self._overflow is OverflowPolicy.DROP_OLDEST:
            try:
                self._event_queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
            else:
                try:
                    self._event_queue.put_nowait(event)
                except asyncio.QueueFull:
                    pass
        elif self._overflow is OverflowPolicy.WARN:
            self.logger.warning("Subscription %s event queue full; dropping event", self.subscription_id)
        elif self._overflow is OverflowPolicy.DISCONNECT:
            self.logger.error("Subscription %s event queue full; forcing reconnect", self.subscription_id)
            if callable(self._on_overflow_disconnect):
                try:
                    self._on_overflow_disconnect()
                except Exception:
                    self.logger.exception("overflow-disconnect hook raised")
        # DROP_NEWEST: do nothing — the new event is discarded.

    async def _dispatch_to_handler(self, event: SubEvent) -> None:
        """Call the right legacy handler method for `event`, in its own task."""
        if self._handler is None:
            return
        try:
            if isinstance(event, DataChangeEvent):
                method = getattr(self._handler, "datachange_notification", None)
                if method is None:
                    self.logger.error(
                        "DataChange subscription created but handler has no datachange_notification method"
                    )
                    return
                if inspect.iscoroutinefunction(method):
                    await method(event.node, event.value, event.data)
                else:
                    method(event.node, event.value, event.data)
            elif isinstance(event, OpcEvent):
                method = getattr(self._handler, "event_notification", None)
                if method is None:
                    self.logger.error("Event subscription created but handler has no event_notification method")
                    return
                if inspect.iscoroutinefunction(method):
                    await method(event.event)
                else:
                    method(event.event)
            elif isinstance(event, StatusChangeEvent):
                method = getattr(self._handler, "status_change_notification", None)
                if method is None:
                    self.logger.error("DataChange subscription has no status_change_notification method")
                    return
                if inspect.iscoroutinefunction(method):
                    await method(event.notification)
                else:
                    method(event.notification)
        except Exception:
            self.logger.exception("Exception calling subscription handler")

    # --- async iterator / context-manager API ------------------------------

    async def __aenter__(self) -> Subscription:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object,
    ) -> None:
        await self.delete()

    def __aiter__(self) -> Subscription:
        if self._handler is not None:
            raise RuntimeError(
                "Subscription is in handler mode; create it without a handler to use the async iterator API"
            )
        if self._event_queue is None:
            self._event_queue = asyncio.Queue(maxsize=self._queue_maxsize)
        return self

    async def __anext__(self) -> SubEvent:
        if self._event_queue is None:
            self._event_queue = asyncio.Queue(maxsize=self._queue_maxsize)
        item = await self._event_queue.get()
        if item is None:
            raise StopAsyncIteration
        return item

    async def next_event(self, timeout: float | None = None) -> SubEvent | None:
        """Return the next event, or None on timeout. Counterpart to `__anext__`.

        Returns None if `timeout` elapses; raises `StopAsyncIteration` if the
        subscription has been closed and the queue is drained.
        """
        if self._event_queue is None:
            self._event_queue = asyncio.Queue(maxsize=self._queue_maxsize)
        try:
            if timeout is None:
                item = await self._event_queue.get()
            else:
                item = await asyncio.wait_for(self._event_queue.get(), timeout)
        except asyncio.TimeoutError:
            return None
        if item is None:
            raise StopAsyncIteration
        return item

    async def delete(self) -> None:
        """
        Delete subscription on server. This is automatically done by Client and Server classes on exit.
        """
        if self.subscription_id is None:
            self._deleted = True
            self._close_iterator()
            return
        try:
            results = await self.server.delete_subscriptions([self.subscription_id])
            results[0].check()
        except (ConnectionError, OSError, asyncio.TimeoutError):
            self.logger.info("delete_subscriptions: transport unavailable; local cleanup only")
        finally:
            self._deleted = True
            self._close_iterator()

    def _close_iterator(self) -> None:
        """Push the sentinel so any active `async for ev in sub` loop ends."""
        if self._event_queue is None:
            return
        try:
            self._event_queue.put_nowait(None)
        except asyncio.QueueFull:
            # Drop the front so the sentinel definitely lands. Any in-flight
            # events already in the queue are dropped — we're shutting down.
            try:
                self._event_queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
            try:
                self._event_queue.put_nowait(None)
            except asyncio.QueueFull:
                pass

    def is_stale(self, margin: float) -> bool:
        if self._deleted or self.subscription_id is None or self.last_publish_at is None:
            return False
        interval_s = self.parameters.RequestedPublishingInterval / 1000.0
        keepalive = max(int(self.parameters.RequestedMaxKeepAliveCount or 1), 1)
        stale_after = max(interval_s * keepalive * margin, 1.0)
        return (time.monotonic() - self.last_publish_at) >= stale_after

    async def restore(self) -> None:
        if self._deleted or self.subscription_id is None or not isinstance(self.server, UaSession):
            await self.recreate()
            return
        params = ua.TransferSubscriptionsParameters()
        params.SubscriptionIds = [self.subscription_id]
        params.SendInitialValues = False
        try:
            results = await self.server.transfer_subscriptions(params)
        except Exception:
            self.logger.info("transfer_subscriptions failed; falling back to recreate", exc_info=True)
            await self.recreate()
            return
        result = results[0] if results else None
        if result is None or not result.StatusCode.is_good():
            self.logger.info(
                "transfer_subscriptions returned %s; falling back to recreate",
                result.StatusCode if result else "no result",
            )
            await self.recreate()
            return
        self.server._subscription_callbacks[self.subscription_id] = self.publish_callback
        if not await self._republish_gaps(result.AvailableSequenceNumbers):
            self.logger.info("republish could not fill gap for sub %s; recreating", self.subscription_id)
            await self.recreate()
            return
        self.last_publish_at = time.monotonic()

    async def _republish_gaps(self, available: list[int]) -> bool:
        if not isinstance(self.server, UaSession) or self.subscription_id is None:
            return True
        target = max(available) if available else (self.last_sequence_number or 0)
        seq = (self.last_sequence_number or 0) + 1
        while True:
            try:
                msg = await self.server.republish(self.subscription_id, seq)
            except BadMessageNotAvailable:
                break
            except Exception:
                self.logger.warning("republish failed for sub %s seq %s", self.subscription_id, seq, exc_info=True)
                return False
            await self.publish_callback(ua.PublishResult(self.subscription_id, NotificationMessage=msg))
            seq += 1
        return (self.last_sequence_number or 0) >= target

    async def recreate(self) -> None:
        """
        Re-create this subscription and its monitored items on the server.

        Used by the auto-reconnect supervisor (after the connection has been
        restored — the server-side subscription is gone) and by the
        stale-subscription watchdog (transport is still up but the server has
        dropped this subscription). Client handles are preserved so existing
        notification routing keeps working.
        """
        if self._deleted:
            return
        saved_items = list(self._monitored_items.values())
        old_subscription_id = self.subscription_id
        self._monitored_items.clear()
        self.subscription_id = None
        # Reset liveness clock so the watchdog doesn't immediately flag the
        # newly-recreated subscription before the first publish arrives.
        self.last_publish_at = time.monotonic()

        if old_subscription_id is not None and isinstance(self.server, UaSession):
            # Drop the dead callback registration. Server-side delete is best
            # effort and may fail (BadNoSubscription / BadSessionClosed) — we
            # don't care, the local cleanup is what matters here.
            self.server._subscription_callbacks.pop(old_subscription_id, None)
            try:
                await self.server.delete_subscriptions([old_subscription_id])
            except Exception:
                self.logger.debug("best-effort delete of old sub %s failed", old_subscription_id, exc_info=True)

        await self.init()

        if not saved_items:
            return

        mirs: list[ua.MonitoredItemCreateRequest] = []
        for item in saved_items:
            if item.node is None or item.attribute is None or item.client_handle is None:
                self.logger.warning("Skipping monitored item with missing fields during recreate")
                continue
            rv = ua.ReadValueId()
            rv.NodeId = item.node.nodeid
            rv.AttributeId = item.attribute
            mparams = ua.MonitoringParameters()
            mparams.ClientHandle = item.client_handle
            mparams.SamplingInterval = item.sampling_interval
            mparams.QueueSize = item.queuesize
            mparams.DiscardOldest = True
            if item.mfilter is not None:
                mparams.Filter = item.mfilter
            mir = ua.MonitoredItemCreateRequest()
            mir.ItemToMonitor = rv
            mir.MonitoringMode = item.monitoring_mode
            mir.RequestedParameters = mparams
            mirs.append(mir)
            # Restore the entry into _monitored_items so that any notifications
            # arriving between create_monitored_items and its server response are
            # still routed correctly.
            self._monitored_items[item.client_handle] = item

        if not mirs:
            return
        params = ua.CreateMonitoredItemsParameters()
        params.SubscriptionId = self.subscription_id
        params.ItemsToCreate = mirs
        params.TimestampsToReturn = ua.TimestampsToReturn.Both
        results = await self.server.create_monitored_items(params)
        for idx, result in enumerate(results):
            mi = params.ItemsToCreate[idx]
            assert mi.RequestedParameters.ClientHandle is not None
            item = self._monitored_items.get(mi.RequestedParameters.ClientHandle)
            if item is None:
                continue
            if not result.StatusCode.is_good():
                self.logger.warning(
                    "Failed to re-create monitored item (client_handle=%s): %s",
                    mi.RequestedParameters.ClientHandle,
                    result.StatusCode,
                )
                del self._monitored_items[mi.RequestedParameters.ClientHandle]
                continue
            item.server_handle = result.MonitoredItemId

    @overload
    async def subscribe_data_change(
        self,
        nodes: Node,
        attr: ua.AttributeIds = ua.AttributeIds.Value,
        queuesize: int = 0,
        monitoring: ua.MonitoringMode = ua.MonitoringMode.Reporting,
        sampling_interval: ua.Duration = 0.0,
    ) -> int: ...

    @overload
    async def subscribe_data_change(
        self,
        nodes: Node | Iterable[Node],
        attr: ua.AttributeIds = ua.AttributeIds.Value,
        queuesize: int = 0,
        monitoring: ua.MonitoringMode = ua.MonitoringMode.Reporting,
        sampling_interval: ua.Duration = 0.0,
    ) -> list[int | ua.StatusCode]: ...

    async def subscribe_data_change(
        self,
        nodes: Node | Iterable[Node],
        attr: ua.AttributeIds = ua.AttributeIds.Value,
        queuesize: int = 0,
        monitoring: ua.MonitoringMode = ua.MonitoringMode.Reporting,
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

    async def _create_eventfilter(
        self,
        evtypes: Node | ua.NodeId | str | int | Iterable[Node | ua.NodeId | str | int],
        where_clause_generation: bool = True,
    ) -> ua.EventFilter:
        if isinstance(evtypes, int | str | ua.NodeId | Node):
            evtypes = [evtypes]
        evtypes = [Node(self.server, evtype) for evtype in evtypes]  # type: ignore[union-attr]
        evfilter = await get_filter_from_event_type(evtypes, where_clause_generation)  # type: ignore[union-attr]
        return evfilter

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
            if isinstance(evtypes, int | str | ua.NodeId | Node) and Node(self.server, evtypes).nodeid == ua.NodeId(
                ua.ObjectIds.BaseEventType
            ):
                # Remove where clause for base event type, for servers that have problems with long WhereClauses.
                # Also because BaseEventType wants every event we can ommit it. Issue: #1205
                where_clause_generation = False
            evfilter = await self._create_eventfilter(evtypes, where_clause_generation)
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
        attr: ua.AttributeIds = ua.AttributeIds.Value,
        mfilter: ua.MonitoringFilter | None = None,
        queuesize: int = 0,
        monitoring: ua.MonitoringMode = ua.MonitoringMode.Reporting,
        sampling_interval: ua.Duration = 0.0,
    ) -> int: ...

    @overload
    async def _subscribe(
        self,
        nodes: Iterable[Node],
        attr: ua.AttributeIds = ua.AttributeIds.Value,
        mfilter: ua.MonitoringFilter | None = None,
        queuesize: int = 0,
        monitoring: ua.MonitoringMode = ua.MonitoringMode.Reporting,
        sampling_interval: ua.Duration = 0.0,
    ) -> list[int | ua.StatusCode]: ...

    async def _subscribe(
        self,
        nodes: Node | Iterable[Node],
        attr: ua.AttributeIds = ua.AttributeIds.Value,
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
        is_list = True
        if isinstance(nodes, collections.abc.Iterable):
            nodes = list(nodes)
        else:
            nodes = [nodes]
            is_list = False
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
        self,
        node: Node,
        attr: ua.AttributeIds,
        mfilter: ua.MonitoringFilter | None,
        queuesize: int,
        monitoring: ua.MonitoringMode,
        sampling_interval: ua.Duration,
    ) -> ua.MonitoredItemCreateRequest:
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
            data = SubscriptionItemData()
            data.client_handle = mi.RequestedParameters.ClientHandle
            data.node = Node(self.server, mi.ItemToMonitor.NodeId)
            data.attribute = mi.ItemToMonitor.AttributeId
            # TODO: Either use the filter from request or from response.
            #  Here it uses from request, in modify it uses from response
            data.mfilter = mi.RequestedParameters.Filter
            data.queuesize = mi.RequestedParameters.QueueSize
            data.monitoring_mode = mi.MonitoringMode
            data.sampling_interval = mi.RequestedParameters.SamplingInterval
            self._monitored_items[mi.RequestedParameters.ClientHandle] = data
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
        params = ua.DeleteMonitoredItemsParameters()
        params.SubscriptionId = self.subscription_id
        params.MonitoredItemIds = list(handles)
        results = await self.server.delete_monitored_items(params)
        results[0].check()
        handle_map = {v.server_handle: k for k, v in self._monitored_items.items()}
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
            mod_filter = ua.DataChangeFilter()
            # send notification when status or value change
            mod_filter.Trigger = ua.DataChangeTrigger(1)
            mod_filter.DeadbandType = 1
            # absolute float value or from 0 to 100 for percentage deadband
            mod_filter.DeadbandValue = mod_filter_val
        modif_item = ua.MonitoredItemModifyRequest()
        modif_item.MonitoredItemId = handle
        modif_item.RequestedParameters = self._modify_monitored_item_request(
            new_queuesize, new_samp_time, mod_filter, item_to_change.client_handle
        )
        params = ua.ModifyMonitoredItemsParameters()
        params.SubscriptionId = self.subscription_id
        params.ItemsToModify.append(modif_item)
        results = await self.server.modify_monitored_items(params)
        item_to_change.mfilter = results[0].FilterResult
        return results

    def _modify_monitored_item_request(
        self,
        new_queuesize: int,
        new_samp_time: ua.Duration,
        mod_filter: ua.DataChangeFilter | None,
        client_handle: ua.IntegerId,
    ) -> ua.MonitoringParameters:
        req_params = ua.MonitoringParameters()
        req_params.ClientHandle = client_handle
        req_params.QueueSize = new_queuesize
        req_params.Filter = mod_filter
        req_params.SamplingInterval = new_samp_time
        return req_params

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
        deadband_filter = ua.DataChangeFilter()
        # send notification when status or value change
        deadband_filter.Trigger = ua.DataChangeTrigger(1)
        deadband_filter.DeadbandType = deadbandtype
        # absolute float value or from 0 to 100 for percentage deadband
        deadband_filter.DeadbandValue = deadband_val
        return await self._subscribe(var, attr, deadband_filter, queuesize)

    async def set_monitoring_mode(self, monitoring: ua.MonitoringMode) -> list[ua.uatypes.StatusCode]:
        """
        The monitoring mode parameter is used
        to enable/disable the sampling of MonitoredItems
        (Samples don't queue on the server side)

        :param monitoring: The monitoring mode to apply
        :return: Return a Set Monitoring Mode Result
        """
        if not isinstance(self.server, UaSession):
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
        if not isinstance(self.server, UaSession):
            raise ua.uaerrors.UaError(f"set_publishing_mode() is not supported in {self.server}.")
        params = ua.SetPublishingModeParameters()
        params.SubscriptionIds = [self.subscription_id]  # type: ignore
        params.PublishingEnabled = publishing
        result = await self.server.set_publishing_mode(params)
        if result[0].is_good():
            self.parameters.PublishingEnabled = publishing
        return result
