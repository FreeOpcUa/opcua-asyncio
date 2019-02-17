"""
high level interface to subscriptions
"""
import asyncio
import logging
import collections
from typing import Union

from opcua import ua
from .events import Event, get_filter_from_event_type
from .node import Node

__all__ = ["Subscription"]


class SubHandler:
    """
    Subscription Handler. To receive events from server for a subscription
    This class is just a sample class. Whatever class having these methods can be used
    """

    def data_change(self, handle, node, val, attr):
        """
        Deprecated, use datachange_notification
        """
        pass

    def datachange_notification(self, node, val, data):
        """
        called for every datachange notification from server
        """
        pass

    def event_notification(self, event):
        """
        called for every event notification from server
        """
        pass

    def status_change_notification(self, status):
        """
        called for every status change notification from server
        """
        pass


class SubscriptionItemData:
    """
    To store useful data from a monitored item
    """
    def __init__(self):
        self.node = None
        self.client_handle = None
        self.server_handle = None
        self.attribute = None
        self.mfilter = None


class DataChangeNotif:
    """
    To be send to clients for every datachange notification from server
    """
    def __init__(self, subscription_data, monitored_item):
        self.monitored_item = monitored_item
        self.subscription_data = subscription_data

    def __str__(self):
        return "DataChangeNotification({0}, {1})".format(self.subscription_data, self.monitored_item)
    __repr__ = __str__


class Subscription:
    """
    Subscription object returned by Server or Client objects.
    The object represent a subscription to an opc-ua server.
    This is a high level class, especially subscribe_data_change
    and subscribe_events methods. If more control is necessary look at
    code and/or use create_monitored_items method.
    :param server: `InternalSession` or `UAClient`
    """

    def __init__(self, server, params, handler):
        self.loop = asyncio.get_event_loop()
        self.logger = logging.getLogger(__name__)
        self.server = server
        self._client_handle = 200
        self._handler = handler
        self.parameters = params  # move to data class
        self._monitored_items = {}
        self.subscription_id = None

    async def init(self):
        response = await self.server.create_subscription(self.parameters, self.publish_callback)
        self.subscription_id = response.SubscriptionId  # move to data class
        self.logger.info('Subscription created %s', self.subscription_id)
        # Send a publish request so the server has one in its queue
        # Servers should always be able to handle at least on extra publish request per subscriptions
        self.loop.create_task(self.server.publish())

    async def delete(self):
        """
        Delete subscription on server. This is automatically done by Client and Server classes on exit
        """
        results = await self.server.delete_subscriptions([self.subscription_id])
        results[0].check()

    def publish_callback(self, publishresult: ua.PublishResult):
        self.logger.info("Publish callback called with result: %s", publishresult)
        if self.subscription_id is None:
            self.subscription_id = publishresult.SubscriptionId

        if publishresult.NotificationMessage.NotificationData is not None:
            for notif in publishresult.NotificationMessage.NotificationData:
                if isinstance(notif, ua.DataChangeNotification):
                    self._call_datachange(notif)
                elif isinstance(notif, ua.EventNotificationList):
                    self._call_event(notif)
                elif isinstance(notif, ua.StatusChangeNotification):
                    self._call_status(notif)
                else:
                    self.logger.warning("Notification type not supported yet for notification %s", notif)
        else:
            self.logger.warning("NotificationMessage is None.")

        ack = ua.SubscriptionAcknowledgement()
        ack.SubscriptionId = self.subscription_id
        ack.SequenceNumber = publishresult.NotificationMessage.SequenceNumber
        self.loop.create_task(self.server.publish([ack]))

    def _call_datachange(self, datachange: ua.DataChangeNotification):
        for item in datachange.MonitoredItems:
            if item.ClientHandle not in self._monitored_items:
                self.logger.warning("Received a notification for unknown handle: %s", item.ClientHandle)
                continue
            data = self._monitored_items[item.ClientHandle]
            if hasattr(self._handler, "datachange_notification"):
                event_data = DataChangeNotif(data, item)
                try:
                    self._handler.datachange_notification(data.node, item.Value.Value.Value, event_data)
                except Exception:
                    self.logger.exception("Exception calling data change handler")
            elif hasattr(self._handler, "data_change"):  # deprecated API
                self.logger.warning("data_change method is deprecated, use datachange_notification")
                try:
                    self._handler.data_change(data.server_handle, data.node, item.Value.Value.Value, data.attribute)
                except Exception:
                    self.logger.exception("Exception calling deprecated data change handler")
            else:
                self.logger.error("DataChange subscription created but handler has no datachange_notification method")

    def _call_event(self, eventlist: ua.EventNotificationList):
        for event in eventlist.Events:
            data = self._monitored_items[event.ClientHandle]
            result = Event.from_event_fields(data.mfilter.SelectClauses, event.EventFields)
            result.server_handle = data.server_handle
            if hasattr(self._handler, "event_notification"):
                try:
                    self._handler.event_notification(result)
                except Exception:
                    self.logger.exception("Exception calling event handler")
            elif hasattr(self._handler, "event"):  # depcrecated API
                try:
                    self._handler.event(data.server_handle, result)
                except Exception:
                    self.logger.exception("Exception calling deprecated event handler")
            else:
                self.logger.error("Event subscription created but handler has no event_notification method")

    def _call_status(self, status: ua.StatusChangeNotification):
        try:
            self._handler.status_change_notification(status.Status)
        except Exception:
            self.logger.exception("Exception calling status change handler")

    def subscribe_data_change(self, nodes, attr=ua.AttributeIds.Value, queuesize=0):
        """
        COROUTINE
        Subscribe for data change events for a node or list of nodes.
        default attribute is Value.
        Return a handle which can be used to unsubscribe
        If more control is necessary use create_monitored_items method
        """
        return self._subscribe(nodes, attr, queuesize=queuesize)

    async def subscribe_events(self, sourcenode=ua.ObjectIds.Server, evtypes=ua.ObjectIds.BaseEventType, evfilter=None,
            queuesize=0):
        """
        Subscribe to events from a node. Default node is Server node.
        In most servers the server node is the only one you can subscribe to.
        if evtypes is not provided, evtype defaults to BaseEventType
        if evtypes is a list or tuple of custom event types, the events will be filtered to the supplied types
        Return a handle which can be used to unsubscribe
        """
        sourcenode = Node(self.server, sourcenode)
        if evfilter is None:
            if not type(evtypes) in (list, tuple):
                evtypes = [evtypes]
            evtypes = [Node(self.server, evtype) for evtype in evtypes]
            evfilter = await get_filter_from_event_type(evtypes)
        return await self._subscribe(sourcenode, ua.AttributeIds.EventNotifier, evfilter, queuesize=queuesize)

    async def _subscribe(self, nodes, attr, mfilter=None, queuesize=0):
        is_list = True
        if isinstance(nodes, collections.Iterable):
            nodes = list(nodes)
        else:
            nodes = [nodes]
            is_list = False
        mirs = []
        for node in nodes:
            mir = self._make_monitored_item_request(node, attr, mfilter, queuesize)
            mirs.append(mir)
        mids = await self.create_monitored_items(mirs)
        if is_list:
            return mids
        if type(mids[0]) == ua.StatusCode:
            mids[0].check()
        return mids[0]

    def _make_monitored_item_request(self, node, attr, mfilter, queuesize):
        rv = ua.ReadValueId()
        rv.NodeId = node.nodeid
        rv.AttributeId = attr
        # rv.IndexRange //We leave it null, then the entire array is returned
        mparams = ua.MonitoringParameters()
        self._client_handle += 1
        mparams.ClientHandle = self._client_handle
        mparams.SamplingInterval = self.parameters.RequestedPublishingInterval
        mparams.QueueSize = queuesize
        mparams.DiscardOldest = True
        if mfilter:
            mparams.Filter = mfilter
        mir = ua.MonitoredItemCreateRequest()
        mir.ItemToMonitor = rv
        mir.MonitoringMode = ua.MonitoringMode.Reporting
        mir.RequestedParameters = mparams
        return mir

    async def create_monitored_items(self, monitored_items):
        """
        low level method to have full control over subscription parameters
        Client handle must be unique since it will be used as key for internal registration of data
        """
        params = ua.CreateMonitoredItemsParameters()
        params.SubscriptionId = self.subscription_id
        params.ItemsToCreate = monitored_items
        params.TimestampsToReturn = ua.TimestampsToReturn.Both
        # insert monitored item into map to avoid notification arrive before result return
        # server_handle is left as None in purpose as we don't get it yet.
        for mi in monitored_items:
            data = SubscriptionItemData()
            data.client_handle = mi.RequestedParameters.ClientHandle
            data.node = Node(self.server, mi.ItemToMonitor.NodeId)
            data.attribute = mi.ItemToMonitor.AttributeId
            #TODO: Either use the filter from request or from response. Here it uses from request, in modify it uses from response
            data.mfilter = mi.RequestedParameters.Filter
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

    async def unsubscribe(self, handle):
        """
        unsubscribe to datachange or events using the handle returned while subscribing
        if you delete subscription, you do not need to unsubscribe
        """
        params = ua.DeleteMonitoredItemsParameters()
        params.SubscriptionId = self.subscription_id
        params.MonitoredItemIds = [handle]
        results = await self.server.delete_monitored_items(params)
        results[0].check()
        for k, v in self._monitored_items.items():
            if v.server_handle == handle:
                del(self._monitored_items[k])
                return

    async def modify_monitored_item(self, handle, new_samp_time, new_queuesize=0, mod_filter_val=-1):
        """
        Modify a monitored item.
        :param handle: Handle returned when originally subscribing
        :param new_samp_time: New wanted sample time
        :param new_queuesize: New wanted queuesize, default is 0
        :param mod_filter_val: New deadband filter value
        :return: Return a Modify Monitored Item Result
        """
        for monitored_item_index in self._monitored_items:
            if self._monitored_items[monitored_item_index].server_handle == handle:
                item_to_change = self._monitored_items[monitored_item_index]
                break
        if mod_filter_val is None:
            mod_filter = None
        elif mod_filter_val < 0:
            mod_filter = item_to_change.mfilter
        else:
            mod_filter = ua.DataChangeFilter()
            mod_filter.Trigger = ua.DataChangeTrigger(1)  # send notification when status or value change
            mod_filter.DeadbandType = 1
            mod_filter.DeadbandValue = mod_filter_val  # absolute float value or from 0 to 100 for percentage deadband
        modif_item = ua.MonitoredItemModifyRequest()
        modif_item.MonitoredItemId = handle
        modif_item.RequestedParameters = self._modify_monitored_item_request(new_queuesize, new_samp_time,
                                                                             mod_filter, item_to_change.client_handle)
        params = ua.ModifyMonitoredItemsParameters()
        params.SubscriptionId = self.subscription_id
        params.ItemsToModify.append(modif_item)
        results = await self.server.modify_monitored_items(params)
        item_to_change.mfilter = results[0].FilterResult
        return results

    def _modify_monitored_item_request(self, new_queuesize, new_samp_time, mod_filter, client_handle):
        req_params = ua.MonitoringParameters()
        req_params.ClientHandle = client_handle
        req_params.QueueSize = new_queuesize
        req_params.Filter = mod_filter
        req_params.SamplingInterval = new_samp_time
        return req_params

    def deadband_monitor(self, var, deadband_val, deadbandtype=1, queuesize=0, attr=ua.AttributeIds.Value):
        """
        Method to create a subscription with a Deadband Value.
        Default deadband value type is absolute.
        Return a handle which can be used to unsubscribe
        :param var: Variable to which you want to subscribe
        :param deadband_val: Absolute float value
        :param deadbandtype: Default value is 1 (absolute), change to 2 for percentage deadband
        :param queuesize: Wanted queue size, default is 1
        """
        deadband_filter = ua.DataChangeFilter()
        deadband_filter.Trigger = ua.DataChangeTrigger(1)  # send notification when status or value change
        deadband_filter.DeadbandType = deadbandtype
        deadband_filter.DeadbandValue = deadband_val  # absolute float value or from 0 to 100 for percentage deadband
        return self._subscribe(var, attr, deadband_filter, queuesize)
