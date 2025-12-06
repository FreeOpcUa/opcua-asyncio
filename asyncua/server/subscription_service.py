"""
server side implementation of subscription service
"""

import asyncio
import logging
from collections.abc import Iterable

from asyncua import ua
from asyncua.common import uamethod, utils

from .address_space import AddressSpace
from .internal_subscription import InternalSubscription


class SubscriptionService:
    """
    Manages subscriptions on the server side.
    There is one `SubscriptionService` instance for every `Server`/`InternalServer`.
    """

    def __init__(self, aspace: AddressSpace):
        self.logger = logging.getLogger(__name__)
        self.aspace: AddressSpace = aspace
        self.subscriptions: dict[int, InternalSubscription] = {}
        self._sub_id_counter = 77
        self.standard_events = {}
        self._conditions = {}

    async def create_subscription(self, params, callback, session_id, request_callback=None):
        self.logger.info("create subscription")
        result = ua.CreateSubscriptionResult()
        result.RevisedPublishingInterval = params.RequestedPublishingInterval
        result.RevisedLifetimeCount = params.RequestedLifetimeCount
        result.RevisedMaxKeepAliveCount = params.RequestedMaxKeepAliveCount
        self._sub_id_counter += 1
        result.SubscriptionId = self._sub_id_counter
        internal_sub = InternalSubscription(
            result,
            self.aspace,
            callback,
            session_id,
            request_callback=request_callback,
            delete_callback=lambda: self.subscriptions.pop(result.SubscriptionId, None),
        )
        await internal_sub.start()
        self.subscriptions[result.SubscriptionId] = internal_sub
        return result

    def modify_subscription(self, params):
        # Requested params are ignored, result = params set during create_subscription.
        self.logger.info("modify subscription")
        result = ua.ModifySubscriptionResult()
        try:
            sub = self.subscriptions[params.SubscriptionId]
            result.RevisedPublishingInterval = sub.data.RevisedPublishingInterval
            result.RevisedLifetimeCount = sub.data.RevisedLifetimeCount
            result.RevisedMaxKeepAliveCount = sub.data.RevisedMaxKeepAliveCount

            return result
        except KeyError:
            raise utils.ServiceError(ua.StatusCodes.BadSubscriptionIdInvalid)

    async def delete_subscriptions(self, ids):
        self.logger.info("delete subscriptions: %s", ids)
        res = []
        existing_subs = []
        for i in ids:
            sub = self.subscriptions.pop(i, None)
            if sub is None:
                res.append(ua.StatusCode(ua.StatusCodes.BadSubscriptionIdInvalid))
            else:
                existing_subs.append(sub)
                res.append(ua.StatusCode())
        stop_results = await asyncio.gather(*[sub.stop() for sub in existing_subs], return_exceptions=True)
        for stop_result in stop_results:
            if isinstance(res, Exception):
                self.logger.warning("Exception while stopping subscription", exc_info=stop_result)
        return res

    def publish(self, acks: Iterable[ua.SubscriptionAcknowledgement]):
        self.logger.info("publish request with acks %s", acks)
        for subid, sub in self.subscriptions.items():
            sub.publish([ack.SequenceNumber for ack in acks if ack.SubscriptionId == subid])

    async def create_monitored_items(self, params: ua.CreateMonitoredItemsParameters):
        self.logger.info("create monitored items")
        if params.SubscriptionId not in self.subscriptions:
            res = []
            for _ in params.ItemsToCreate:
                response = ua.MonitoredItemCreateResult()
                response.StatusCode = ua.StatusCode(ua.StatusCodes.BadSubscriptionIdInvalid)
                res.append(response)
            return res
        return await self.subscriptions[params.SubscriptionId].monitored_item_srv.create_monitored_items(params)

    def modify_monitored_items(self, params):
        self.logger.info("modify monitored items")
        if params.SubscriptionId not in self.subscriptions:
            res = []
            for _ in params.ItemsToModify:
                result = ua.MonitoredItemModifyResult()
                result.StatusCode = ua.StatusCode(ua.StatusCodes.BadSubscriptionIdInvalid)
                res.append(result)
            return res
        return self.subscriptions[params.SubscriptionId].monitored_item_srv.modify_monitored_items(params)

    def delete_monitored_items(self, params):
        self.logger.info("delete monitored items")
        if params.SubscriptionId not in self.subscriptions:
            res = []
            for _ in params.MonitoredItemIds:
                res.append(ua.StatusCode(ua.StatusCodes.BadSubscriptionIdInvalid))
            return res
        return self.subscriptions[params.SubscriptionId].monitored_item_srv.delete_monitored_items(
            params.MonitoredItemIds
        )

    def republish(self, params):
        if params.SubscriptionId not in self.subscriptions:
            # TODO: what should I do?
            return ua.NotificationMessage()
        return self.subscriptions[params.SubscriptionId].republish(params.RetransmitSequenceNumber)

    async def trigger_event(self, event, subscription_id=None):
        if hasattr(event, "Retain") and hasattr(event, "NodeId"):
            if event.Retain:
                self._conditions[event.NodeId] = event
            elif event.NodeId in self._conditions:
                del self._conditions[event.NodeId]
        if subscription_id is not None:
            if subscription_id in self.subscriptions:
                await self.subscriptions[subscription_id].monitored_item_srv.trigger_event(event)
        else:
            for sub in self.subscriptions.values():
                await sub.monitored_item_srv.trigger_event(event)

    @uamethod
    async def condition_refresh(self, parent, subscription_id, mid=None) -> ua.StatusCode | None:
        if subscription_id not in self.subscriptions:
            return ua.StatusCode(ua.StatusCodes.BadSubscriptionIdInvalid)
        sub = self.subscriptions[subscription_id]
        if mid is not None and mid not in sub.monitored_item_srv._monitored_items:
            return ua.StatusCode(ua.StatusCodes.BadMonitoredItemIdInvalid)
        if ua.ObjectIds.RefreshStartEventType in self.standard_events:
            await self.standard_events[ua.ObjectIds.RefreshStartEventType].trigger(subscription_id=subscription_id)
        for event in self._conditions.values():
            await sub.monitored_item_srv.trigger_event(event, mid)
        if ua.ObjectIds.RefreshEndEventType in self.standard_events:
            await self.standard_events[ua.ObjectIds.RefreshEndEventType].trigger(subscription_id=subscription_id)
        return None  # FIXME: really not sure this is correct, but this is the original behaviour
