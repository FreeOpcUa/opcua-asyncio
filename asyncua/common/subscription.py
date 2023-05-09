"""
high level interface to subscriptions
"""
import asyncio
import logging
import collections.abc
from typing import Tuple, Union, List, Iterable, Optional
from asyncua.common.ua_utils import copy_dataclass_attr

from asyncua import ua
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


class DataChangeNotif:
    """
    To be send to clients for every datachange notification from server.
    """

    def __init__(
            self,
            subscription_data: SubscriptionItemData,
            monitored_item: ua.MonitoredItemNotification
        ):
        self.monitored_item = monitored_item
        self.subscription_data = subscription_data

    def __str__(self):
        return f"DataChangeNotification({self.subscription_data}, {self.monitored_item})"

    __repr__ = __str__


class SubHandler:
    """
    Subscription Handler. To receive events from server for a subscription
    This class is just a sample class. Whatever class having these methods can be used
    """

    def datachange_notification(self, node: Node, val, data: DataChangeNotif):
        """
        called for every datachange notification from server
        """
        pass

    def event_notification(self, event: ua.EventNotificationList):
        """
        called for every event notification from server
        """
        pass

    def status_change_notification(self, status: ua.StatusChangeNotification):
        """
        called for every status change notification from server
        """
        pass


class Subscription:
    """
    Subscription object returned by Server or Client objects.
    The object represent a subscription to an opc-ua server.
    This is a high level class, especially `subscribe_data_change` and `subscribe_events methods`.
    If more control is necessary look at code and/or use `create_monitored_items method`.
    :param server: `InternalSession` or `UAClient`
    """

    def __init__(self, server, params: ua.CreateSubscriptionParameters, handler: SubHandler):
        self.logger = logging.getLogger(__name__)
        self.server = server
        self._client_handle = 200
        self._handler: SubHandler = handler
        self.parameters: ua.CreateSubscriptionParameters = params  # move to data class
        self._monitored_items = {}
        self.subscription_id: Optional[int] = None

    async def init(self) -> ua.CreateSubscriptionResult:
        response = await self.server.create_subscription(
            self.parameters,
            callback=self.publish_callback
        )
        self.subscription_id = response.SubscriptionId  # move to data class
        self.logger.info("Subscription created %s", self.subscription_id)
        return response

    async def update(
        self,
        params: ua.ModifySubscriptionParameters
    ) -> ua.ModifySubscriptionResponse:
        response = await self.server.update_subscription(params)
        self.logger.info('Subscription updated %s', params.SubscriptionId)
        # update the self.parameters attr with the updated values
        copy_dataclass_attr(params, self.parameters)
        return response

    async def publish_callback(self, publish_result: ua.PublishResult):
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

    async def delete(self):
        """
        Delete subscription on server. This is automatically done by Client and Server classes on exit.
        """
        results = await self.server.delete_subscriptions([self.subscription_id])
        results[0].check()

    async def _call_datachange(self, datachange: ua.DataChangeNotification):
        if not hasattr(self._handler, "datachange_notification"):
            self.logger.error("DataChange subscription created but handler has no datachange_notification method")
            return

        known_handles_args: List[Tuple] = []
        for item in datachange.MonitoredItems:
            if item.ClientHandle not in self._monitored_items:
                self.logger.warning("Received a notification for unknown handle: %s", item.ClientHandle)
                continue
            data = self._monitored_items[item.ClientHandle]
            event_data = DataChangeNotif(data, item)
            # FIXME: Value can be None
            known_handles_args.append((data.node, item.Value.Value.Value, event_data))  # type: ignore[union-attr]

        try:
            tasks = [
                self._handler.datachange_notification(*args) for args in known_handles_args
            ]
            if asyncio.iscoroutinefunction(self._handler.datachange_notification):
                await asyncio.gather(*tasks)
        except Exception as ex:
            self.logger.exception("Exception calling data change handler. Error: %s", ex)

    async def _call_event(self, eventlist: ua.EventNotificationList):
        for event in eventlist.Events:
            if event.ClientHandle not in self._monitored_items:
                self.logger.warning("Received a notification for unknown handle: %s", event.ClientHandle)
                continue
            data = self._monitored_items[event.ClientHandle]
            result = Event.from_event_fields(data.mfilter.SelectClauses, event.EventFields)
            result.server_handle = data.server_handle
            if hasattr(self._handler, "event_notification"):
                try:
                    if asyncio.iscoroutinefunction(self._handler.event_notification):
                        await self._handler.event_notification(result)
                    else:
                        self._handler.event_notification(result)
                except Exception:
                    self.logger.exception("Exception calling event handler")
            else:
                self.logger.error("Event subscription created but handler has no event_notification method")

    async def _call_status(self, status: ua.StatusChangeNotification):
        if not hasattr(self._handler, "status_change_notification"):
            self.logger.error("DataChange subscription has no status_change_notification method")
            return
        try:
            if asyncio.iscoroutinefunction(self._handler.status_change_notification):
                await self._handler.status_change_notification(status)
            else:
                self._handler.status_change_notification(status)
        except Exception:
            self.logger.exception("Exception calling status change handler")

    async def subscribe_data_change(
        self,
        nodes: Union[Node, Iterable[Node]],
        attr: ua.AttributeIds = ua.AttributeIds.Value,
        queuesize: int = 0,
        monitoring=ua.MonitoringMode.Reporting,
        sampling_interval: ua.Duration = 0.0
    ) -> Union[int, List[Union[int, ua.StatusCode]]]:
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

    async def _create_eventfilter(self, evtypes: Union[ua.ObjectIds, List[ua.ObjectIds], ua.NodeId, List[ua.NodeId]], where_clause_generation: bool = True):
        if not isinstance(evtypes, (list, tuple)):
            evtypes = [evtypes]
        evtypes = [Node(self.server, evtype) for evtype in evtypes]  # type: ignore[union-attr]
        evfilter = await get_filter_from_event_type(evtypes, where_clause_generation) # type: ignore[union-attr]
        return evfilter

    async def subscribe_events(
        self,
        sourcenode: Node = ua.ObjectIds.Server,
        evtypes: Union[ua.ObjectIds, List[ua.ObjectIds], ua.NodeId, List[ua.NodeId]] = ua.ObjectIds.BaseEventType,
        evfilter: ua.EventFilter = None,
        queuesize: int = 0,
        where_clause_generation: bool = True
    ) -> int:
        """
        Subscribe to events from a node. Default node is Server node.
        In most servers the server node is the only one you can subscribe to.
        If evtypes is not provided, evtype defaults to BaseEventType.
        If evtypes is a list or tuple of custom event types, the events will be filtered to the supplied types.
        A handle (integer value) is returned which can be used to modify/cancel the subscription.

        :param sourcenode: Node
        :param evtypes: ua.ObjectIds or ua.NodeId
        :param evfilter: ua.EventFilter which provides the SelectClauses and WhereClause
        :param queuesize: 0 for default queue size, 1 for minimum queue size, n for FIFO queue,
        MaxUInt32 for max queue size
        :param where_clause_generation: No where_clause generation when no eventfilter is provided. Need for TwinCAT, Codesys
        :return: Handle for changing/cancelling of the subscription
        """
        sourcenode = Node(self.server, sourcenode)
        if evfilter is None:
            if type(evtypes) not in (list, tuple) and evtypes == ua.ObjectIds.BaseEventType:
                # Remove where clause for base event type, for servers that have problems with long WhereClauses.
                # Also because BaseEventType wants every event we can ommit it. Issue: #1205
                where_clause_generation = False
            evfilter = await self._create_eventfilter(evtypes, where_clause_generation)
        return await self._subscribe(sourcenode, ua.AttributeIds.EventNotifier, evfilter, queuesize=queuesize)  # type: ignore

    async def subscribe_alarms_and_conditions(
        self,
        sourcenode: Node = ua.ObjectIds.Server,
        evtypes: Union[ua.ObjectIds, List[ua.ObjectIds], ua.NodeId, List[ua.NodeId]] = ua.ObjectIds.ConditionType,
        evfilter: ua.EventFilter = None,
        queuesize: int = 0
    ) -> int:
        """
        Subscribe to alarm and condition events from a node. Default node is Server node.
        In many servers the server node is the only one you can subscribe to.
        If evtypes is not provided, evtype defaults to ConditionType.
        If evtypes is a list or tuple of custom event types, the events will be filtered to the supplied types.
        A handle (integer value) is returned which can be used to modify/cancel the subscription.

        :param sourcenode: Node
        :param evtypes: ua.ObjectIds or ua.NodeId
        :param evfilter: ua.EventFilter which provides the SelectClauses and WhereClause
        :param queuesize: 0 for default queue size, 1 for minimum queue size, n for FIFO queue,
        MaxUInt32 for max queue size
        :return: Handle for changing/cancelling of the subscription
        """
        sourcenode = Node(self.server, sourcenode)
        if evfilter is None:
            evfilter = await self._create_eventfilter(evtypes)
        # Add SimpleAttribute for NodeId if missing.
        matches = [a for a in evfilter.SelectClauses if a.AttributeId == ua.AttributeIds.NodeId]
        if not matches:
            conditionIdOperand = ua.SimpleAttributeOperand()
            conditionIdOperand.TypeDefinitionId = ua.NodeId(ua.ObjectIds.ConditionType)
            conditionIdOperand.AttributeId = ua.AttributeIds.NodeId
            evfilter.SelectClauses.append(conditionIdOperand)
        return await self._subscribe(sourcenode, ua.AttributeIds.EventNotifier, evfilter, queuesize=queuesize)  # type: ignore

    async def _subscribe(
        self,
        nodes: Union[Node, Iterable[Node]],
        attr = ua.AttributeIds.Value,
        mfilter: ua.MonitoringFilter = None,
        queuesize: int = 0,
        monitoring: ua.MonitoringMode = ua.MonitoringMode.Reporting,
        sampling_interval: ua.Duration = 0.0
    ) -> Union[int, List[Union[int, ua.StatusCode]]]:
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
            mir = self._make_monitored_item_request(
                node, attr, mfilter, queuesize, monitoring, sampling_interval
            )
            mirs.append(mir)
        # Await MonitoredItemCreateResult
        mids = await self.create_monitored_items(mirs)
        if is_list:
            # Return results for multiple nodes
            return mids
        # Check and return result for single node (raise `UaStatusCodeError` if subscription failed)
        if type(mids[0]) == ua.StatusCode:
            mids[0].check()
        return mids[0]  # type: ignore

    def _make_monitored_item_request(
            self,
            node: Node,
            attr,
            mfilter,
            queuesize,
            monitoring,
            sampling_interval
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

    async def create_monitored_items(self, monitored_items: List[ua.MonitoredItemCreateRequest]) -> List[Union[int, ua.StatusCode]]:
        """
        low level method to have full control over subscription parameters.
        Client handle must be unique since it will be used as key for internal registration of data.
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
            # TODO: Either use the filter from request or from response.
            #  Here it uses from request, in modify it uses from response
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

    async def unsubscribe(self, handle: Union[int, List[int]]):
        """
        Unsubscribe from datachange or events using the handle returned while subscribing.
        If you delete the subscription, you do not need to unsubscribe.
        :param handle: The handle that was returned when subscribing to the node/nodes
        """
        handles: List[int] = [handle] if isinstance(handle, int) else handle
        if not handles:
            return
        params = ua.DeleteMonitoredItemsParameters()
        params.SubscriptionId = self.subscription_id
        params.MonitoredItemIds = handles
        results = await self.server.delete_monitored_items(params)
        results[0].check()
        handle_map = {v.server_handle: k for k, v in self._monitored_items.items()}
        for handle in handles:
            if handle in handle_map:
                del self._monitored_items[handle_map[handle]]

    async def modify_monitored_item(self, handle: int, new_samp_time: ua.Duration, new_queuesize: int = 0, mod_filter_val: int = -1):
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
            raise ValueError('The monitored item was not found.')
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
            mod_filter: ua.DataChangeFilter,
            client_handle: ua.IntegerId
        ):
        req_params = ua.MonitoringParameters()
        req_params.ClientHandle = client_handle
        req_params.QueueSize = new_queuesize
        req_params.Filter = mod_filter
        req_params.SamplingInterval = new_samp_time
        return req_params

    def deadband_monitor(
            self,
            var: Union[Node, Iterable[Node]],
            deadband_val: ua.Double,
            deadbandtype: ua.UInt32 = 1,
            queuesize: int = 0,
            attr: ua.AttributeIds = ua.AttributeIds.Value
        ):
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
        return self._subscribe(var, attr, deadband_filter, queuesize)

    async def set_monitoring_mode(self, monitoring: ua.MonitoringMode) -> ua.uatypes.StatusCode:
        """
        The monitoring mode parameter is used
        to enable/disable the sampling of MonitoredItems
        (Samples don't queue on the server side)

        :param monitoring: The monitoring mode to apply
        :return: Return a Set Monitoring Mode Result
        """
        node_handles = []
        for mi in self._monitored_items.values():
            node_handles.append(mi.server_handle)

        params = ua.SetMonitoringModeParameters()
        params.SubscriptionId = self.subscription_id
        params.MonitoredItemIds = node_handles
        params.MonitoringMode = monitoring
        return await self.server.set_monitoring_mode(params)

    async def set_publishing_mode(self, publishing: bool) -> ua.uatypes.StatusCode:
        """
        Disable publishing of NotificationMessages for the subscription,
        but doesn't discontinue the sending of keep-alive Messages,
        nor change the monitoring mode.

        :param publishing: The publishing mode to apply
        :return: Return a Set Publishing Mode Result
        """
        self.logger.info("set_publishing_mode")
        params = ua.SetPublishingModeParameters()
        params.SubscriptionIds = [self.subscription_id]  # type: ignore
        params.PublishingEnabled = publishing
        result = await self.server.set_publishing_mode(params)
        if result[0].is_good():
            self.parameters.PublishingEnabled = publishing
        return result
