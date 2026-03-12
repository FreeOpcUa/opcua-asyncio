import copy
from collections.abc import Callable, Coroutine
from typing import TYPE_CHECKING, Any

import asyncua
from asyncua import ua

from ..ua.uaerrors import UaError
from .ua_utils import get_node_subtypes, is_subtype

if TYPE_CHECKING:
    from asyncua.common.node import Node


_BROWSE_MASK = ua.BrowseResultMask.NodeClass | ua.BrowseResultMask.ReferenceTypeId | ua.BrowseResultMask.BrowseName


class Event:
    """
    OPC UA Event object.
    This is class in inherited by the common event objects such as BaseEvent,
    other auto standard events and custom events
    Events are used to trigger events on server side and are
    sent to clients for every events from server

    Developer Warning:
    On server side the data type of attributes should be known, thus
    add properties using the add_property method!!!
    """

    def __init__(self, emitting_node: ua.NodeId | int = ua.ObjectIds.Server) -> None:
        self.server_handle: int | None = None
        self.select_clauses: list[ua.SimpleAttributeOperand] | None = None
        self.event_fields: list[ua.Variant] | None = None
        self.data_types: dict[str, ua.VariantType] = {}
        self.emitting_node: ua.NodeId
        if isinstance(emitting_node, ua.NodeId):
            self.emitting_node = emitting_node
        else:
            self.emitting_node = ua.NodeId(emitting_node)
        # save current attributes
        self.internal_properties = [*self.__dict__.keys(), "internal_properties"]

    def __str__(self) -> str:
        return "{0}({1})".format(
            self.__class__.__name__,
            [str(k) + ":" + str(v) for k, v in self.__dict__.items() if k not in self.internal_properties],
        )

    __repr__ = __str__

    def add_property(self, name: str, val: Any, datatype: ua.VariantType) -> None:
        setattr(self, name, val)
        self.data_types[name] = datatype

    def add_variable(self, name: str, val: Any, datatype: ua.VariantType) -> None:
        setattr(self, name, val)
        self.data_types[name] = datatype

    def get_event_props_as_fields_dict(self) -> dict[str, ua.Variant]:
        field_vars: dict[str, ua.Variant] = {}
        for key, value in vars(self).items():
            if not key.startswith("__") and key not in self.internal_properties:
                field_vars[key] = ua.Variant(value, self.data_types[key])
        return field_vars

    @staticmethod
    def from_field_dict(fields: dict[str, ua.Variant]) -> "Event":
        ev = Event()
        for k, v in fields.items():
            ev.add_property(k, v.Value, v.VariantType)
        return ev

    def to_event_fields_using_subscription_fields(
        self, select_clauses: list[ua.SimpleAttributeOperand]
    ) -> list[ua.Variant]:
        fields: list[ua.Variant] = []
        if self.select_clauses is None or self.event_fields is None:
            return fields
        for sattr in select_clauses:
            for idx, o_sattr in enumerate(self.select_clauses):
                if sattr.BrowsePath == o_sattr.BrowsePath and sattr.AttributeId == o_sattr.AttributeId:
                    fields.append(self.event_fields[idx])
                    break
        return fields

    def to_event_fields(self, select_clauses: list[ua.SimpleAttributeOperand]) -> list[ua.Variant]:
        fields: list[ua.Variant] = []
        for sattr in select_clauses:
            if len(sattr.BrowsePath) == 0:
                name = ua.AttributeIds(sattr.AttributeId).name
            else:
                name = self.browse_path_to_attribute_name(sattr.BrowsePath)
            try:
                val = getattr(self, name)
            except AttributeError:
                field = ua.Variant(None)
            else:
                if val is None:
                    field = ua.Variant(None)
                else:
                    field = ua.Variant(copy.deepcopy(val), self.data_types[name])
            fields.append(field)
        return fields

    @staticmethod
    def from_event_fields(select_clauses: list[ua.SimpleAttributeOperand], fields: list[ua.Variant]) -> "Event":
        ev = Event()
        ev.select_clauses = select_clauses
        ev.event_fields = fields
        for idx, sattr in enumerate(select_clauses):
            if len(sattr.BrowsePath) == 0:
                name = sattr.AttributeId.name
            else:
                name = Event.browse_path_to_attribute_name(sattr.BrowsePath)
            ev.add_property(name, fields[idx].Value, fields[idx].VariantType)
        return ev

    @staticmethod
    def browse_path_to_attribute_name(browsePath: list[ua.QualifiedName]) -> str:
        name = browsePath[0].Name
        iter_paths = iter(browsePath)
        next(iter_paths)
        for path in iter_paths:
            name += "/" + path.Name
        return name


async def get_filter_from_event_type(eventtypes: list["Node"], where_clause_generation: bool = True) -> ua.EventFilter:
    evfilter = ua.EventFilter()
    evfilter.SelectClauses = await select_clauses_from_evtype(eventtypes)
    if where_clause_generation:
        evfilter.WhereClause = await where_clause_from_evtype(eventtypes)
    return evfilter


async def _append_new_attribute_to_select_clauses(
    select_clauses: list[ua.SimpleAttributeOperand],
    already_selected: dict[str, str],
    browse_path: list[ua.QualifiedName],
) -> None:
    string_path = "/".join(map(str, browse_path))
    if string_path not in already_selected:
        already_selected[string_path] = string_path
        op = ua.SimpleAttributeOperand()
        op.AttributeId = ua.AttributeIds.Value
        op.BrowsePath = browse_path
        op.TypeDefinitionId = ua.NodeId(ua.ObjectIds.BaseEventType)
        select_clauses.append(op)


async def _select_clause_from_childs(
    child: "Node",
    refs: list[ua.ReferenceDescription],
    select_clauses: list[ua.SimpleAttributeOperand],
    already_selected: dict[str, str],
    browse_path: list[ua.QualifiedName],
) -> None:
    for ref in refs:
        if ref.NodeClass == ua.NodeClass.Variable:
            if ref.ReferenceTypeId == ua.ObjectIds.HasProperty:
                await _append_new_attribute_to_select_clauses(
                    select_clauses, already_selected, [*browse_path, ref.BrowseName]
                )
            else:
                await _append_new_attribute_to_select_clauses(
                    select_clauses, already_selected, [*browse_path, ref.BrowseName]
                )
                var = child.new_node(child.session, ref.NodeId)
                refs = await var.get_references(
                    ua.ObjectIds.Aggregates,
                    ua.BrowseDirection.Forward,
                    ua.NodeClass.Object | ua.NodeClass.Variable,
                    True,
                    _BROWSE_MASK,
                )
                await _select_clause_from_childs(
                    var, refs, select_clauses, already_selected, [*browse_path, ref.BrowseName]
                )
        elif ref.NodeClass == ua.NodeClass.Object:
            obj = child.new_node(child.session, ref.NodeId)
            refs = await obj.get_references(
                ua.ObjectIds.Aggregates,
                ua.BrowseDirection.Forward,
                ua.NodeClass.Object | ua.NodeClass.Variable,
                True,
                _BROWSE_MASK,
            )
            await _select_clause_from_childs(
                obj, refs, select_clauses, already_selected, [*browse_path, ref.BrowseName]
            )


async def select_clauses_from_evtype(
    evtypes: list["Node"],
) -> list[ua.SimpleAttributeOperand]:
    select_clauses: list[ua.SimpleAttributeOperand] = []
    already_selected: dict[str, str] = {}
    add_condition_id = False
    for evtype in evtypes:
        if not add_condition_id and await is_subtype(evtype, ua.NodeId(ua.ObjectIds.ConditionType)):
            add_condition_id = True
        refs = await select_event_attributes_from_type_node(
            evtype,
            lambda n: n.get_references(
                ua.ObjectIds.Aggregates,
                ua.BrowseDirection.Forward,
                ua.NodeClass.Object | ua.NodeClass.Variable,
                True,
                _BROWSE_MASK,
            ),
        )
        if refs:
            await _select_clause_from_childs(evtype, refs, select_clauses, already_selected, [])
    if add_condition_id:
        op = ua.SimpleAttributeOperand()
        op.AttributeId = ua.AttributeIds.NodeId
        op.TypeDefinitionId = ua.NodeId(ua.ObjectIds.ConditionType)
        select_clauses.append(op)
    return select_clauses


async def where_clause_from_evtype(evtypes: list["Node"]) -> ua.ContentFilter:
    cf = ua.ContentFilter()
    el = ua.ContentFilterElement()

    op = ua.SimpleAttributeOperand()
    op.BrowsePath.append(ua.QualifiedName("EventType", 0))
    op.AttributeId = ua.AttributeIds.Value
    op.TypeDefinitionId = ua.NodeId(ua.ObjectIds.BaseEventType)
    el.FilterOperands.append(op)

    subtypes: list[ua.NodeId] = []
    for evtype in evtypes:
        for st in await get_node_subtypes(evtype):
            subtypes.append(st.nodeid)
    subtypes = list(set(subtypes))
    for subtypeid in subtypes:
        op = ua.LiteralOperand(Value=ua.Variant(subtypeid))
        el.FilterOperands.append(op)
    el.FilterOperator = ua.FilterOperator.InList
    cf.Elements.append(el)
    return cf


async def select_event_attributes_from_type_node(
    node: "Node",
    attributeSelector: Callable[["Node"], Coroutine[Any, Any, list[Any]]],
) -> list[Any] | None:
    attributes: list[Any] = []
    curr_node = node
    while True:
        attributes.extend(await attributeSelector(curr_node))
        if curr_node.nodeid == ua.NodeId(ua.ObjectIds.BaseEventType):
            break
        parents = await curr_node.get_referenced_nodes(
            refs=ua.ObjectIds.HasSubtype, direction=ua.BrowseDirection.Inverse
        )
        if len(parents) != 1:
            return None
        curr_node = parents[0]
    return attributes


async def get_event_properties_from_type_node(node: "Node") -> list[Any] | None:
    return await select_event_attributes_from_type_node(node, lambda n: n.get_properties())


async def get_event_variables_from_type_node(node: "Node") -> list[Any] | None:
    return await select_event_attributes_from_type_node(node, lambda n: n.get_variables())


async def get_event_objects_from_type_node(node: "Node") -> list[Any] | None:
    return await select_event_attributes_from_type_node(
        node, lambda n: n.get_children(refs=ua.ObjectIds.HasComponent, nodeclassmask=ua.NodeClass.Object)
    )


async def get_event_obj_from_type_node(node: "Node") -> Event:
    if node.nodeid.NamespaceIndex == 0:
        if node.nodeid.Identifier in asyncua.common.event_objects.IMPLEMENTED_EVENTS:
            return asyncua.common.event_objects.IMPLEMENTED_EVENTS[node.nodeid.Identifier]()  # type: ignore[index]

    parent_nodeid, parent_eventtype = await _find_parent_eventtype(node)

    class CustomEvent(parent_eventtype):  # type: ignore[valid-type]
        def __init__(self) -> None:
            parent_eventtype.__init__(self)
            self.EventType = node.nodeid

        async def _add_new_property(self, property: "Node", parent_variable: "Node | None") -> None:
            name = (await property.read_browse_name()).Name
            if parent_variable:
                parent_name = (await parent_variable.read_browse_name()).Name
                name = f"{parent_name}/{name}"
            val = await property.read_data_value()
            if val.Value is not None:
                self.add_property(name, val.Value.Value, val.Value.VariantType)

        async def _add_new_variable(self, variable: "Node") -> None:
            name = (await variable.read_browse_name()).Name
            val = await variable.read_data_value()
            if val.Value is not None:
                self.add_variable(name, val.Value.Value, await variable.read_data_type_as_variant_type())

        async def init(self) -> None:
            curr_node = node
            while curr_node.nodeid != parent_nodeid:
                for prop in await curr_node.get_properties():
                    await self._add_new_property(prop, None)
                for var in await curr_node.get_variables():
                    await self._add_new_variable(var)
                    for prop in await var.get_properties():
                        await self._add_new_property(prop, var)
                parents = await curr_node.get_referenced_nodes(
                    refs=ua.ObjectIds.HasSubtype, direction=ua.BrowseDirection.Inverse
                )
                if len(parents) != 1:
                    raise UaError("Parent of event type could not be found")
                curr_node = parents[0]

            self._freeze = True

    ce = CustomEvent()
    await ce.init()
    return ce


async def _find_parent_eventtype(node: "Node") -> tuple[ua.NodeId, type[Event]]:
    """ """
    parents = await node.get_referenced_nodes(refs=ua.ObjectIds.HasSubtype, direction=ua.BrowseDirection.Inverse)
    if len(parents) != 1:
        raise UaError("Parent of event type could not be found")
    if parents[0].nodeid.NamespaceIndex == 0:
        if parents[0].nodeid.Identifier in asyncua.common.event_objects.IMPLEMENTED_EVENTS:
            return parents[0].nodeid, asyncua.common.event_objects.IMPLEMENTED_EVENTS[parents[0].nodeid.Identifier]  # type: ignore[index]
    return await _find_parent_eventtype(parents[0])
