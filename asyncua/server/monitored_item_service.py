"""
server side implementation of a subscription object
"""

import logging
from asyncua import ua


class MonitoredItemData:
    def __init__(self):
        self.client_handle = None
        self.callback_handle = None
        self.monitored_item_id = None
        self.mode = None
        self.filter = None
        self.mvalue = MonitoredItemValues()
        self.where_clause_evaluator = None
        self.queue_size = 0


class MonitoredItemValues:
    def __init__(self):
        self.current_value = None
        self.old_value = None

    def set_current_value(self, cur_val):
        self.old_value = self.current_value
        self.current_value = cur_val

    def get_current_value(self):
        return self.current_value

    def get_old_value(self):
        return self.old_value


class MonitoredItemService:
    """
    Implements monitored item service for one subscription
    """

    def __init__(self, isub, aspace):
        self.logger = logging.getLogger(f"{__name__}.{isub.data.SubscriptionId}")
        self.isub = isub
        self.aspace = aspace
        self._monitored_items = {}
        self._monitored_events = {}
        self._monitored_datachange = {}
        self._monitored_item_counter = 111

    def __str__(self):
        return f"MonitoredItemService({self.isub.data.SubscriptionId})"

    def delete_all_monitored_items(self):
        self.delete_monitored_items([mdata.monitored_item_id for mdata in self._monitored_items.values()])

    async def create_monitored_items(self, params):
        results = []
        for item in params.ItemsToCreate:
            # with self._lock:
            if item.ItemToMonitor.AttributeId == ua.AttributeIds.EventNotifier:
                result = self._create_events_monitored_item(item)
            else:
                result = self._create_data_change_monitored_item(item)
            results.append(result)
        return results

    def modify_monitored_items(self, params):
        results = []
        for item in params.ItemsToModify:
            results.append(self._modify_monitored_item(item))
        return results

    def trigger_datachange(self, handle, nodeid, attr):
        self.logger.debug("triggering datachange for handle %s, nodeid %s, and attribute %s", handle, nodeid, attr)
        variant = self.aspace.get_attribute_value(nodeid, attr)
        self.datachange_callback(handle, variant)

    def _modify_monitored_item(self, params):
        for mdata in self._monitored_items.values():
            result = ua.MonitoredItemModifyResult()
            if mdata.monitored_item_id == params.MonitoredItemId:
                result.RevisedSamplingInterval = params.RequestedParameters.SamplingInterval
                result.RevisedQueueSize = params.RequestedParameters.QueueSize
                if params.RequestedParameters.Filter is not None:
                    mdata.filter = params.RequestedParameters.Filter
                mdata.queue_size = params.RequestedParameters.QueueSize
                return result
        result = ua.MonitoredItemModifyResult()
        result.StatusCode(ua.StatusCodes.BadMonitoredItemIdInvalid)
        return result

    def _commit_monitored_item(self, result, mdata):
        if result.StatusCode.is_good():
            self._monitored_items[result.MonitoredItemId] = mdata
            self._monitored_item_counter += 1

    def _make_monitored_item_common(self, params):
        result = ua.MonitoredItemCreateResult()
        result.RevisedSamplingInterval = self.isub.data.RevisedPublishingInterval
        result.RevisedQueueSize = params.RequestedParameters.QueueSize
        self._monitored_item_counter += 1
        result.MonitoredItemId = self._monitored_item_counter
        self.logger.debug("Creating MonitoredItem with id %s", result.MonitoredItemId)

        mdata = MonitoredItemData()
        mdata.mode = params.MonitoringMode
        mdata.client_handle = params.RequestedParameters.ClientHandle
        mdata.monitored_item_id = result.MonitoredItemId
        mdata.queue_size = params.RequestedParameters.QueueSize
        mdata.filter = params.RequestedParameters.Filter

        return result, mdata

    def _create_events_monitored_item(self, params):
        self.logger.info("request to subscribe to events for node %s and attribute %s", params.ItemToMonitor.NodeId,
                         params.ItemToMonitor.AttributeId)

        result, mdata = self._make_monitored_item_common(params)
        ev_notify_byte = self.aspace.get_attribute_value(params.ItemToMonitor.NodeId,
                                                         ua.AttributeIds.EventNotifier).Value.Value

        if ev_notify_byte is None or not ua.ua_binary.test_bit(ev_notify_byte, ua.EventNotifier.SubscribeToEvents):
            result.StatusCode = ua.StatusCode(ua.StatusCodes.BadServiceUnsupported)
            return result
        # result.FilterResult = ua.EventFilterResult()  # spec says we can ignore if not error
        mdata.where_clause_evaluator = WhereClauseEvaluator(self.logger, self.aspace, mdata.filter.WhereClause)
        self._commit_monitored_item(result, mdata)
        if params.ItemToMonitor.NodeId not in self._monitored_events:
            self._monitored_events[params.ItemToMonitor.NodeId] = []
        self._monitored_events[params.ItemToMonitor.NodeId].append(result.MonitoredItemId)
        return result

    def _create_data_change_monitored_item(self, params):
        self.logger.info("request to subscribe to datachange for node %s and attribute %s", params.ItemToMonitor.NodeId,
                         params.ItemToMonitor.AttributeId)

        result, mdata = self._make_monitored_item_common(params)
        result.FilterResult = params.RequestedParameters.Filter
        result.StatusCode, handle = self.aspace.add_datachange_callback(
            params.ItemToMonitor.NodeId, params.ItemToMonitor.AttributeId, self.datachange_callback)

        self.logger.debug("adding callback return status %s and handle %s", result.StatusCode, handle)
        mdata.callback_handle = handle
        self._commit_monitored_item(result, mdata)
        if result.StatusCode.is_good():
            self._monitored_datachange[handle] = result.MonitoredItemId
            # force data change event generation
            self.trigger_datachange(handle, params.ItemToMonitor.NodeId, params.ItemToMonitor.AttributeId)
        return result

    def delete_monitored_items(self, ids):
        self.logger.debug("delete monitored items %s", ids)
        # with self._lock:
        results = []
        for mid in ids:
            results.append(self._delete_monitored_items(mid))
        return results

    def _delete_monitored_items(self, mid):
        if mid not in self._monitored_items:
            return ua.StatusCode(ua.StatusCodes.BadMonitoredItemIdInvalid)
        for k, v in self._monitored_events.items():
            if mid in v:
                v.remove(mid)
                if not v:
                    self._monitored_events.pop(k)
                break
        for k, v in self._monitored_datachange.items():
            if v == mid:
                self.aspace.delete_datachange_callback(k)
                self._monitored_datachange.pop(k)
                break
        self._monitored_items.pop(mid)
        return ua.StatusCode()

    def datachange_callback(self, handle, value, error=None):
        if error:
            self.logger.info("subscription %s: datachange callback called with handle '%s' and error '%s'", self,
                             handle, error)
            self.trigger_statuschange(error)
        else:
            self.logger.info("subscription %s: datachange callback called with handle '%s' and value '%s'", self,
                             handle, value.Value)
            event = ua.MonitoredItemNotification()
            mid = self._monitored_datachange[handle]
            mdata = self._monitored_items[mid]
            mdata.mvalue.set_current_value(value.Value.Value)
            if mdata.filter:
                deadband_flag_pass = self.deadband_callback(mdata.mvalue, mdata.filter)
            else:
                deadband_flag_pass = True
            if deadband_flag_pass:
                event.ClientHandle = mdata.client_handle
                event.Value = value
                self.isub.enqueue_datachange_event(mid, event, mdata.queue_size)

    def deadband_callback(self, values, flt):
        if flt.DeadbandType == ua.DeadbandType.None_ or values.get_old_value() is None:
            return True
        if flt.DeadbandType == ua.DeadbandType.Absolute and \
                ((abs(values.get_current_value() - values.get_old_value())) > flt.DeadbandValue):
            return True
        if flt.DeadbandType == ua.DeadbandType.Percent:
            self.logger.warning("DeadbandType Percent is not implemented !")
            return True
        return False

    def trigger_event(self, event):
        if event.emitting_node not in self._monitored_events:
            self.logger.debug("%s has no subscription for events %s from node: %s", self, event, event.emitting_node)
            return False
        self.logger.debug("%s has subscription for events %s from node: %s", self, event, event.emitting_node)
        mids = self._monitored_events[event.emitting_node]
        for mid in mids:
            self._trigger_event(event, mid)
        return True

    def _trigger_event(self, event, mid):
        if mid not in self._monitored_items:
            self.logger.debug("Could not find monitored items for id %s for event %s in subscription %s", mid, event,
                              self)
            return
        mdata = self._monitored_items[mid]
        if not mdata.where_clause_evaluator.eval(event):
            self.logger.info("%s, %s, Event %s does not fit WhereClause, not generating event", self, mid, event)
            return
        fieldlist = ua.EventFieldList()
        fieldlist.ClientHandle = mdata.client_handle
        fieldlist.EventFields = event.to_event_fields(mdata.filter.SelectClauses)
        self.isub.enqueue_event(mid, fieldlist, mdata.queue_size)

    def trigger_statuschange(self, code):
        self.isub.enqueue_statuschange(code)


class WhereClauseEvaluator:
    def __init__(self, logger, aspace, whereclause):
        self.logger = logger
        self.elements = whereclause.Elements
        self._aspace = aspace

    def eval(self, event):
        if not self.elements:
            return True
        # spec says we should only evaluate first element, which may use other elements
        try:
            res = self._eval_el(0, event)
        except Exception as ex:
            self.logger.exception("Exception while evaluating WhereClause %s for event %s: %s", self.elements, event,
                                  ex)
            return False
        return res

    def _eval_el(self, index, event):
        el = self.elements[index]
        # ops = [self._eval_op(op, event) for op in el.FilterOperands]
        ops = el.FilterOperands  # just to make code more readable
        if el.FilterOperator == ua.FilterOperator.Equals:
            return self._eval_op(ops[0], event) == self._eval_el(ops[1], event)
        if el.FilterOperator == ua.FilterOperator.IsNull:
            return self._eval_op(ops[0], event) is None  # FIXME: might be too strict
        if el.FilterOperator == ua.FilterOperator.GreaterThan:
            return self._eval_op(ops[0], event) > self._eval_el(ops[1], event)
        if el.FilterOperator == ua.FilterOperator.LessThan:
            return self._eval_op(ops[0], event) < self._eval_el(ops[1], event)
        if el.FilterOperator == ua.FilterOperator.GreaterThanOrEqual:
            return self._eval_op(ops[0], event) >= self._eval_el(ops[1], event)
        if el.FilterOperator == ua.FilterOperator.LessThanOrEqual:
            return self._eval_op(ops[0], event) <= self._eval_el(ops[1], event)
        if el.FilterOperator == ua.FilterOperator.Like:
            return self._like_operator(self._eval_op(ops[0], event), self._eval_el(ops[1], event))
        if el.FilterOperator == ua.FilterOperator.Not:
            return not self._eval_op(ops[0], event)
        if el.FilterOperator == ua.FilterOperator.Between:
            return self._eval_el(ops[2], event) >= self._eval_op(ops[0], event) >= self._eval_el(ops[1], event)
        if el.FilterOperator == ua.FilterOperator.InList:
            return self._eval_op(ops[0], event) in [self._eval_op(op, event) for op in ops[1:]]
        if el.FilterOperator == ua.FilterOperator.And:
            self.elements(ops[0].Index)
            return self._eval_op(ops[0], event) and self._eval_op(ops[1], event)
        if el.FilterOperator == ua.FilterOperator.Or:
            return self._eval_op(ops[0], event) or self._eval_el(ops[1], event)
        if el.FilterOperator == ua.FilterOperator.Cast:
            self.logger.warn("Cast operand not implemented, assuming True")
            return True
        if el.FilterOperator == ua.FilterOperator.OfType:
            return event.EventType == self._eval_op(ops[0], event)
        # TODO: implement missing operators
        self.logger.warning("WhereClause not implemented for element: %s", el)
        raise NotImplementedError

    def _like_operator(self, string, pattern):
        raise NotImplementedError

    def _eval_op(self, op, event):
        # seems spec says we should return Null if issues
        if isinstance(op, ua.ElementOperand):
            return self._eval_el(op.Index, event)
        if isinstance(op, ua.AttributeOperand):
            if op.BrowsePath:
                return getattr(event, op.BrowsePath.Elements[0].TargetName.Name)
            return self._aspace.get_attribute_value(event.EventType, op.AttributeId).Value.Value
            # FIXME: check, this is probably broken
        if isinstance(op, ua.SimpleAttributeOperand):
            if op.BrowsePath:
                # we only support depth of 1
                return getattr(event, op.BrowsePath[0].Name)
            # TODO: write code for index range.... but doe it make any sense
            return self._aspace.get_attribute_value(event.EventType, op.AttributeId).Value.Value
        if isinstance(op, ua.LiteralOperand):
            return op.Value.Value
        self.logger.warning("Where clause element % is not of a known type", op)
        raise NotImplementedError
