"""
server side implementation of subscription service
"""

import logging

from opcua import ua
from .internal_subscription import InternalSubscription

__all__ = ["SubscriptionService"]


class SubscriptionService:
    """
    ToDo: check if locks need to be replaced by asyncio.Lock
    """

    def __init__(self, loop, aspace):
        self.logger = logging.getLogger(__name__)
        self.loop = loop
        self.aspace = aspace
        self.subscriptions = {}
        self._sub_id_counter = 77

    async def create_subscription(self, params, callback):
        self.logger.info("create subscription with callback: %s", callback)
        result = ua.CreateSubscriptionResult()
        result.RevisedPublishingInterval = params.RequestedPublishingInterval
        result.RevisedLifetimeCount = params.RequestedLifetimeCount
        result.RevisedMaxKeepAliveCount = params.RequestedMaxKeepAliveCount
        self._sub_id_counter += 1
        result.SubscriptionId = self._sub_id_counter

        sub = InternalSubscription(self, result, self.aspace, callback)
        await sub.start()
        self.subscriptions[result.SubscriptionId] = sub
        return result

    async def delete_subscriptions(self, ids):
        self.logger.info("delete subscriptions: %s", ids)
        res = []
        for i in ids:
            if i not in self.subscriptions:
                res.append(ua.StatusCode(ua.StatusCodes.BadSubscriptionIdInvalid))
            else:
                sub = self.subscriptions.pop(i)
                await sub.stop()
                res.append(ua.StatusCode())
        return res

    def publish(self, acks):
        self.logger.info("publish request with acks %s", acks)
        for subid, sub in self.subscriptions.items():
            sub.publish([ack.SequenceNumber for ack in acks if ack.SubscriptionId == subid])

    async def create_monitored_items(self, params):
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
            params.MonitoredItemIds)

    def republish(self, params):
        #with self._lock:
        if params.SubscriptionId not in self.subscriptions:
            # TODO: what should I do?
            return ua.NotificationMessage()
        return self.subscriptions[params.SubscriptionId].republish(params.RetransmitSequenceNumber)

    def trigger_event(self, event):
        for sub in self.subscriptions.values():
            sub.monitored_item_srv.trigger_event(event)
