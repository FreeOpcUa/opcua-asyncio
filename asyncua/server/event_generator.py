import logging
from datetime import datetime
import time
import uuid
from typing import Optional
import sys

from asyncua import ua
from ..common import events, event_objects, Node


class EventGenerator:
    """
    Create an event based on an event type. Per default is BaseEventType used.
    Object members are dynamically created from the base event type and send to
    client when evebt is triggered (see example code in source)

    Arguments to constructor are:
        server: The InternalSession object to use for query and event triggering
        source: The emiting source for the node, either an objectId, NodeId or a Node
        etype: The event type, either an objectId, a NodeId or a Node object
    """

    def __init__(self, isession):
        self.logger = logging.getLogger(__name__)
        self.isession = isession
        self.event: Optional[event_objects.BaseEvent] = None
        self.emitting_node: Optional[Node] = None

    async def init(self, etype=None, emitting_node=ua.ObjectIds.Server):
        node = None

        if isinstance(etype, event_objects.BaseEvent):
            self.event = etype
        elif isinstance(etype, Node):
            node = etype
        elif isinstance(etype, ua.NodeId):
            node = Node(self.isession, etype)
        else:
            node = Node(self.isession, ua.NodeId(etype))

        if node:
            self.event = await events.get_event_obj_from_type_node(node)

        if isinstance(emitting_node, Node):
            pass
        elif isinstance(emitting_node, ua.NodeId):
            emitting_node = Node(self.isession, emitting_node)
        else:
            emitting_node = Node(self.isession, ua.NodeId(emitting_node))

        self.event.emitting_node = emitting_node.nodeid
        if not self.event.SourceNode:
            self.event.SourceNode = emitting_node.nodeid
        if not self.event.SourceName:
            self.event.SourceName = (await Node(self.isession, self.event.SourceNode).get_browse_name()).Name

        await emitting_node.set_event_notifier([ua.EventNotifier.SubscribeToEvents])
        refs = []
        ref = ua.AddReferencesItem()
        ref.IsForward = True
        ref.ReferenceTypeId = ua.NodeId(ua.ObjectIds.GeneratesEvent)
        ref.SourceNodeId = emitting_node.nodeid
        ref.TargetNodeClass = ua.NodeClass.ObjectType
        ref.TargetNodeId = self.event.EventType
        refs.append(ref)
        results = await self.isession.add_references(refs)
        # result.StatusCode.check()

        self.emitting_node = emitting_node

    def __str__(self):
        return "EventGenerator(Type:{0}, Emitting Node:{1}, Time:{2}, Message: {3})".format(
            self.event.EventType, self.emitting_node, self.event.Time, self.event.Message)

    __repr__ = __str__

    async def trigger(self, time_attr=None, message=None):
        """
        Trigger the event. This will send a notification to all subscribed clients
        """
        self.event.EventId = ua.Variant(uuid.uuid4().hex.encode('utf-8'), ua.VariantType.ByteString)
        if time_attr:
            self.event.Time = time_attr
        else:
            self.event.Time = datetime.utcnow()
        self.event.ReceiveTime = datetime.utcnow()

        self.event.LocalTime = ua.uaprotocol_auto.TimeZoneDataType()
        if sys.version_info.major > 2:
            localtime = time.localtime(self.event.Time.timestamp())
            self.event.LocalTime.Offset = localtime.tm_gmtoff//60
        else:
            localtime = time.localtime(time.mktime(self.event.Time.timetuple()))
            self.event.LocalTime.Offset = -(time.altzone if localtime.tm_isdst else time.timezone)
        self.event.LocalTime.DaylightSavingInOffset = bool(localtime.tm_isdst != -1)

        if message:
            self.event.Message = ua.LocalizedText(message)
        elif not self.event.Message:
            self.event.Message = ua.LocalizedText(Node(self.isession, self.event.SourceNode).get_browse_name().Text)

        await self.isession.subscription_service.trigger_event(self.event)
