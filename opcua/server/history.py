import asyncio
import logging
from typing import Coroutine
from datetime import timedelta
from datetime import datetime

from opcua import ua
from ..common import Subscription, Buffer

__all__ = ["HistoryManager", "HistoryStorageInterface", "HistoryDict"]


class UaNodeAlreadyHistorizedError(ua.UaError):
    pass


class HistoryStorageInterface:

    """
    Interface of a history backend.
    Must be implemented by backends
    """
    async def init(self):
        """
        Async. initialization.
        Has to be called once after creation.
        """
        raise NotImplementedError

    async def new_historized_node(self, node_id, period, count=0):
        """
        Called when a new node is to be historized
        Returns None
        """
        raise NotImplementedError

    async def save_node_value(self, node_id, datavalue):
        """
        Called when the value of a historized node has changed and should be saved in history
        Returns None
        """
        raise NotImplementedError

    async def read_node_history(self, node_id, start, end, nb_values):
        """
        Called when a client make a history read request for a node
        if start or end is missing then nb_values is used to limit query
        nb_values is the max number of values to read. Ignored if 0
        Start time and end time are inclusive
        Returns a list of DataValues and a continuation point which
        is None if all nodes are read or the SourceTimeStamp of the last rejected DataValue
        """
        raise NotImplementedError

    async def new_historized_event(self, source_id, evtypes, period, count=0):
        """
        Called when historization of events is enabled on server side
        Returns None
        """
        raise NotImplementedError

    async def save_event(self, event):
        """
        Called when a new event has been generated ans should be saved in history
        Returns None
        """
        raise NotImplementedError

    async def read_event_history(self, source_id, start, end, nb_values, evfilter):
        """
        Called when a client make a history read request for events
        Start time and end time are inclusive
        Returns a list of Events and a continuation point which
        is None if all events are read or the SourceTimeStamp of the last rejected event
        """
        raise NotImplementedError

    async def stop(self):
        """
        Called when the server shuts down
        Can be used to close database connections etc.
        """
        raise NotImplementedError


class HistoryDict(HistoryStorageInterface):
    """
    Very minimal history backend storing data in memory using a Python dictionary
    """

    def __init__(self):
        self._datachanges = {}
        self._datachanges_period = {}
        self._events = {}
        self._events_periods = {}
        self.logger = logging.getLogger(__name__)

    async def init(self):
        pass

    async def new_historized_node(self, node_id, period, count=0):
        if node_id in self._datachanges:
            raise UaNodeAlreadyHistorizedError(node_id)
        self._datachanges[node_id] = []
        self._datachanges_period[node_id] = period, count

    async def save_node_value(self, node_id, datavalue):
        data = self._datachanges[node_id]
        period, count = self._datachanges_period[node_id]
        data.append(datavalue)
        now = datetime.utcnow()
        if period:
            while len(data) and now - data[0].SourceTimestamp > period:
                data.pop(0)
        if count and len(data) > count:
            data.pop(0)

    async def read_node_history(self, node_id, start, end, nb_values):
        cont = None
        if node_id not in self._datachanges:
            self.logger.warning("Error attempt to read history for a node which is not historized")
            return [], cont
        else:
            if start is None:
                start = ua.get_win_epoch()
            if end is None:
                end = ua.get_win_epoch()
            if start == ua.get_win_epoch():
                results = [dv for dv in reversed(self._datachanges[node_id]) if start <= dv.SourceTimestamp]
            elif end == ua.get_win_epoch():
                results = [dv for dv in self._datachanges[node_id] if start <= dv.SourceTimestamp]
            elif start > end:
                results = [dv for dv in reversed(self._datachanges[node_id]) if end <= dv.SourceTimestamp <= start]

            else:
                results = [dv for dv in self._datachanges[node_id] if start <= dv.SourceTimestamp <= end]
            if nb_values and len(results) > nb_values:
                cont = results[nb_values + 1].SourceTimestamp
                results = results[:nb_values]
            return results, cont

    async def new_historized_event(self, source_id, evtypes, period, count=0):
        if source_id in self._events:
            raise UaNodeAlreadyHistorizedError(source_id)
        self._events[source_id] = []
        self._events_periods[source_id] = period, count

    async def save_event(self, event):
        evts = self._events[event.SourceNode]
        evts.append(event)
        period, count = self._events_periods[event.SourceNode]
        now = datetime.utcnow()
        if period:
            while len(evts) and now - evts[0].SourceTimestamp > period:
                evts.pop(0)
        if count and len(evts) > count:
            evts.pop(0)

    async def read_event_history(self, source_id, start, end, nb_values, evfilter):
        cont = None
        if source_id not in self._events:
            print("Error attempt to read event history for a node which does not historize events")
            return [], cont
        else:
            if start is None:
                start = ua.get_win_epoch()
            if end is None:
                end = ua.get_win_epoch()
            if start == ua.get_win_epoch():
                results = [ev for ev in reversed(self._events[source_id]) if start <= ev.Time]
            elif end == ua.get_win_epoch():
                results = [ev for ev in self._events[source_id] if start <= ev.Time]
            elif start > end:
                results = [ev for ev in reversed(self._events[source_id]) if end <= ev.Time <= start]

            else:
                results = [ev for ev in self._events[source_id] if start <= ev.Time <= end]
            if nb_values and len(results) > nb_values:
                cont = results[nb_values + 1].Time
                results = results[:nb_values]
            return results, cont

    async def stop(self):
        pass


class SubHandler:
    def __init__(self, storage):
        self.storage = storage
        self.loop = asyncio.get_event_loop()

    def datachange_notification(self, node, val, data):
        self.loop.create_task(
            self.storage.save_node_value(node.nodeid, data.monitored_item.Value)
        )

    def event_notification(self, event):
        self.loop.create_task(
            self.storage.save_event(event)
        )


class HistoryManager:
    def __init__(self, iserver):
        self.logger = logging.getLogger(__name__)
        self.iserver = iserver
        self.storage = HistoryDict()
        self._sub = None
        self._handlers = {}

    async def init(self):
        await self.storage.init()

    def set_storage(self, storage):
        """
        set the desired HistoryStorageInterface which History Manager will use for historizing
        """
        self.storage = storage

    async def _create_subscription(self, handler):
        params = ua.CreateSubscriptionParameters()
        params.RequestedPublishingInterval = 10
        params.RequestedLifetimeCount = 3000
        params.RequestedMaxKeepAliveCount = 10000
        params.MaxNotificationsPerPublish = 0
        params.PublishingEnabled = True
        params.Priority = 0
        subscription = Subscription(self.iserver.isession, params, handler)
        await subscription.init()
        return subscription

    async def historize_data_change(self, node, period=timedelta(days=7), count=0):
        """
        Subscribe to the nodes' data changes and store the data in the active storage.
        """
        if not self._sub:
            self._sub = await self._create_subscription(SubHandler(self.storage))
        if node in self._handlers:
            raise ua.UaError("Node {0} is already historized".format(node))
        await self.storage.new_historized_node(node.nodeid, period, count)
        handler = await self._sub.subscribe_data_change(node)
        self._handlers[node] = handler

    async def historize_event(self, source, period=timedelta(days=7), count=0):
        """
        Subscribe to the source nodes' events and store the data in the active storage.

        SQL Implementation
        The default is to historize every event type the source generates, custom event properties are included. At
        this time there is no way to historize a specific event type. The user software can filter out events which are
        not desired when reading.

        Note that adding custom events to a source node AFTER historizing has been activated is not supported at this
        time (in SQL history there will be no columns in the SQL table for the new event properties). For SQL The table
        must be deleted manually so that a new table with the custom event fields can be created.
        """
        if not self._sub:
            self._sub = await self._create_subscription(SubHandler(self.storage))
        if source in self._handlers:
            raise ua.UaError("Events from {0} are already historized".format(source))

        # get list of all event types that the source node generates; change this to only historize specific events
        event_types = await source.get_referenced_nodes(ua.ObjectIds.GeneratesEvent)

        await self.storage.new_historized_event(source.nodeid, event_types, period, count)

        handler = await self._sub.subscribe_events(source, event_types)
        self._handlers[source] = handler

    async def dehistorize(self, node):
        """
        Remove subscription to the node/source which is being historized

        SQL Implementation
        Only the subscriptions is removed. The historical data remains.
        """
        if node in self._handlers:
            await self._sub.unsubscribe(self._handlers[node])
            del(self._handlers[node])
        else:
            self.logger.error("History Manager isn't subscribed to %s", node)

    async def read_history(self, params):
        """
        Read history for a node
        This is the part AttributeService, but implemented as its own service
        since it requires more logic than other attribute service methods
        """
        results = []

        for rv in params.NodesToRead:
            res = await self._read_history(params.HistoryReadDetails, rv)
            results.append(res)
        return results

    async def _read_history(self, details, rv):
        """
        determine if the history read is for a data changes or events; then read the history for that node
        """
        result = ua.HistoryReadResult()
        if isinstance(details, ua.ReadRawModifiedDetails):
            if details.IsReadModified:
                result.HistoryData = ua.HistoryModifiedData()
                # we do not support modified history by design so we return what we have
            else:
                result.HistoryData = ua.HistoryData()
            dv, cont = await self._read_datavalue_history(rv, details)
            result.HistoryData.DataValues = dv
            result.ContinuationPoint = cont

        elif isinstance(details, ua.ReadEventDetails):
            result.HistoryData = ua.HistoryEvent()
            # FIXME: filter is a cumbersome type, maybe transform it something easier
            # to handle for storage
            ev, cont = await self._read_event_history(rv, details)
            result.HistoryData.Events = ev
            result.ContinuationPoint = cont

        else:
            # we do not currently support the other types, clients can process data themselves
            result.StatusCode = ua.StatusCode(ua.StatusCodes.BadNotImplemented)
        return result

    async def _read_datavalue_history(self, rv, details):
        starttime = details.StartTime
        if rv.ContinuationPoint:
            # Spec says we should ignore details if cont point is present
            # but they also say we can use cont point as timestamp to enable stateless
            # implementation. This is contradictory, so we assume details is
            # send correctly with continuation point
            starttime = ua.ua_binary.Primitives.DateTime.unpack(Buffer(rv.ContinuationPoint))

        dv, cont = await self.storage.read_node_history(rv.NodeId,
                                                  starttime,
                                                  details.EndTime,
                                                  details.NumValuesPerNode)
        if cont:
            cont = ua.ua_binary.Primitives.DateTime.pack(cont)
        # rv.IndexRange
        # rv.DataEncoding # xml or binary, seems spec say we can ignore that one
        return dv, cont

    async def _read_event_history(self, rv, details):
        starttime = details.StartTime
        if rv.ContinuationPoint:
            # Spec says we should ignore details if cont point is present
            # but they also say we can use cont point as timestamp to enable stateless
            # implementation. This is contradictory, so we assume details is
            # send correctly with continuation point
            starttime = ua.ua_binary.Primitives.DateTime.unpack(Buffer(rv.ContinuationPoint))

        evts, cont = await self.storage.read_event_history(rv.NodeId,
                                                     starttime,
                                                     details.EndTime,
                                                     details.NumValuesPerNode,
                                                     details.Filter)
        results = []
        for ev in evts:
            field_list = ua.HistoryEventFieldList()
            field_list.EventFields = ev.to_event_fields(details.Filter.SelectClauses)
            results.append(field_list)
        if cont:
            cont = ua.ua_binary.Primitives.DateTime.pack(cont)
        return results, cont

    def update_history(self, params):
        """
        Update history for a node
        This is the part AttributeService, but implemented as its own service
        since it requires more logic than other attribute service methods
        """
        results = []
        for _ in params.HistoryUpdateDetails:
            result = ua.HistoryUpdateResult()
            # we do not accept to rewrite history
            result.StatusCode = ua.StatusCode(ua.StatusCodes.BadNotWritable)
            results.append(results)
        return results

    def stop(self) -> Coroutine:
        """
        call stop methods of active storage interface whenever the server is stopped
        """
        return self.storage.stop()
