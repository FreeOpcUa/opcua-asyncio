"""
server side implementation of a subscription object
"""

import logging
import asyncio

from typing import Union, Iterable, Dict, List
from asyncua import ua
from .monitored_item_service import MonitoredItemService
from .address_space import AddressSpace


class InternalSubscription:
    """
    Server internal subscription.
    Runs the publication loop and stores the Publication Results until they are acknowledged.
    """

    def __init__(self, loop: asyncio.AbstractEventLoop, data: ua.CreateSubscriptionResult, aspace: AddressSpace,
                 callback=None, no_acks=False):
        """
        :param loop: Event loop instance
        :param data: Create Subscription Result
        :param aspace: Server Address Space
        :param callback: Callback for publishing
        :param no_acks: If true no acknowledging will be expected (for server internal subscriptions)
        """
        self.logger = logging.getLogger(__name__)
        self.loop: asyncio.AbstractEventLoop = loop
        self.data: ua.CreateSubscriptionResult = data
        self.pub_result_callback = callback
        self.monitored_item_srv = MonitoredItemService(self, aspace)
        self._triggered_datachanges: Dict[int, List[ua.MonitoredItemNotification]] = {}
        self._triggered_events: Dict[int, List[ua.EventFieldList]] = {}
        self._triggered_statuschanges: list = []
        self._notification_seq = 1
        self._not_acknowledged_results: Dict[int, ua.PublishResult] = {}
        self._startup = True
        self._keep_alive_count = 0
        self._publish_cycles_count = 0
        self._task = None
        self.no_acks = no_acks

    def __str__(self):
        return f"Subscription(id:{self.data.SubscriptionId})"

    async def start(self):
        self.logger.debug("starting subscription %s", self.data.SubscriptionId)
        if self.data.RevisedPublishingInterval > 0.0:
            self._task = self.loop.create_task(self._subscription_loop())

    async def stop(self):
        self.logger.info("stopping internal subscription %s", self.data.SubscriptionId)
        self._task.cancel()
        await self._task
        self._task = None
        self.monitored_item_srv.delete_all_monitored_items()

    def _trigger_publish(self):
        """
        Trigger immediate publication (if requested by the PublishingInterval).
        """
        if not self._task and self.data.RevisedPublishingInterval <= 0.0:
            # Publish immediately (as fast as possible)
            self.publish_results()

    async def _subscription_loop(self):
        """
        Start the publication loop running at the RevisedPublishingInterval.
        """
        try:
            while True:
                await asyncio.sleep(self.data.RevisedPublishingInterval / 1000.0)
                self.publish_results()
        except asyncio.CancelledError:
            self.logger.info('exiting _subscription_loop for %s', self.data.SubscriptionId)
            pass
        except Exception:
            # seems this except is necessary to log errors
            self.logger.exception("Exception in subscription loop")

    def has_published_results(self):
        if self._startup or self._triggered_datachanges or self._triggered_events:
            return True
        if self._keep_alive_count > self.data.RevisedMaxKeepAliveCount:
            self.logger.debug("keep alive count %s is > than max keep alive count %s, sending publish event",
                self._keep_alive_count, self.data.RevisedMaxKeepAliveCount)
            return True
        self._keep_alive_count += 1
        return False

    def publish_results(self):
        """
        Publish all enqueued data changes, events and status changes though the callback.
        """
        if self._publish_cycles_count > self.data.RevisedLifetimeCount:
            self.logger.warning("Subscription %s has expired, publish cycle count(%s) > lifetime count (%s)", self,
                self._publish_cycles_count, self.data.RevisedLifetimeCount)
            # FIXME this will never be send since we do not have publish request anyway
            self.monitored_item_srv.trigger_statuschange(ua.StatusCode(ua.StatusCodes.BadTimeout))
        result = None
        if self.has_published_results():
            if not self.no_acks:
                self._publish_cycles_count += 1
            result = self._pop_publish_result()
        if result is not None:
            #self.logger.info('publish_results for %s', self.data.SubscriptionId)
            # The callback can be:
            #    Subscription.publish_callback -> server internal subscription
            #    UaProcessor.forward_publish_response -> client subscription
            self.pub_result_callback(result)

    def _pop_publish_result(self) -> ua.PublishResult:
        """
        Return a `PublishResult` with all enqueued data changes, events and status changes.
        Clear all queues.
        """
        result = ua.PublishResult()
        result.SubscriptionId = self.data.SubscriptionId
        self._pop_triggered_datachanges(result)
        self._pop_triggered_events(result)
        self._pop_triggered_statuschanges(result)
        self._keep_alive_count = 0
        self._startup = False
        result.NotificationMessage.SequenceNumber = self._notification_seq
        if result.NotificationMessage.NotificationData and not self.no_acks:
            # Acknowledgement is only expected when the Subscription is for a client.
            self._notification_seq += 1
            self._not_acknowledged_results[result.NotificationMessage.SequenceNumber] = result
        result.MoreNotifications = False
        result.AvailableSequenceNumbers = list(self._not_acknowledged_results.keys())
        return result

    def _pop_triggered_datachanges(self, result: ua.PublishResult):
        """Append all enqueued data changes to the given `PublishResult` and clear the queue."""
        if self._triggered_datachanges:
            notif = ua.DataChangeNotification()
            notif.MonitoredItems = [item for sublist in self._triggered_datachanges.values() for item in sublist]
            self._triggered_datachanges = {}
            #self.logger.debug("sending datachanges notification with %s events", len(notif.MonitoredItems))
            result.NotificationMessage.NotificationData.append(notif)

    def _pop_triggered_events(self, result: ua.PublishResult):
        """Append all enqueued events to the given `PublishResult` and clear the queue."""
        if self._triggered_events:
            notif = ua.EventNotificationList()
            notif.Events = [item for sublist in self._triggered_events.values() for item in sublist]
            self._triggered_events = {}
            result.NotificationMessage.NotificationData.append(notif)
            #self.logger.debug("sending event notification with %s events", len(notif.Events))

    def _pop_triggered_statuschanges(self, result: ua.PublishResult):
        """Append all enqueued status changes to the given `PublishResult` and clear the queue."""
        if self._triggered_statuschanges:
            notif = ua.StatusChangeNotification()
            notif.Status = self._triggered_statuschanges.pop(0)
            result.NotificationMessage.NotificationData.append(notif)
            #self.logger.debug("sending event notification %s", notif.Status)

    def publish(self, acks: Iterable[int]):
        """
        Reset publish cycle count, acknowledge PublishResults.
        :param acks: Sequence number of the PublishResults to acknowledge
        """
        #self.logger.info("publish request with acks %s", acks)
        self._publish_cycles_count = 0
        for nb in acks:
            self._not_acknowledged_results.pop(nb, None)

    def republish(self, nb):
        #self.logger.info("re-publish request for ack %s in subscription %s", nb, self)
        notification_message = self._not_acknowledged_results.pop(nb, None)
        if notification_message:
            self.logger.info("re-publishing ack %s in subscription %s", nb, self)
            return notification_message
        self.logger.info("Error request to re-published non existing ack %s in subscription %s", nb, self)
        return ua.NotificationMessage()

    def enqueue_datachange_event(self, mid: int, eventdata: ua.MonitoredItemNotification, maxsize: int):
        """
        Enqueue a monitored item data change.
        :param mid: Monitored Item Id
        :param eventdata: Monitored Item Notification
        :param maxsize: Max queue size (0: No limit)
        """
        self._enqueue_event(mid, eventdata, maxsize, self._triggered_datachanges)

    def enqueue_event(self, mid: int, eventdata: ua.EventFieldList, maxsize: int):
        """
        Enqueue a event.
        :param mid: Monitored Item Id
        :param eventdata: Event Field List
        :param maxsize: Max queue size (0: No limit)
        """
        self._enqueue_event(mid, eventdata, maxsize, self._triggered_events)

    def enqueue_statuschange(self, code):
        """
        Enqueue a status change.
        :param code:
        """
        self._triggered_statuschanges.append(code)
        self._trigger_publish()

    def _enqueue_event(self, mid: int, eventdata: Union[ua.MonitoredItemNotification, ua.EventFieldList], size: int,
                       queue: dict):
        if mid not in queue:
            # New Monitored Item Id
            queue[mid] = [eventdata]
            self._trigger_publish()
            return
        if size != 0:
            # Limit queue size
            if len(queue[mid]) >= size:
                queue[mid].pop(0)
        queue[mid].append(eventdata)
