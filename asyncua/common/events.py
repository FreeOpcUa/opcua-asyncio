import copy

from asyncua import ua
import asyncua
from ..ua.uaerrors import UaError
from .ua_utils import get_node_subtypes

# byme
import json


class Event:
    """
    OPC UA Event object.
    This is class in inherited by the common event objects such as BaseEvent,
    other auto standard events and custom events
    Events are used to trigger events on server side and are
    sent to clients for every events from server

    Developper Warning:
    On server side the data type of attributes should be known, thus
    add properties using the add_property method!!!
    """

    def __init__(self, emitting_node=ua.ObjectIds.Server):
        self.server_handle = None
        self.select_clauses = None
        self.event_fields = None
        self.data_types = {}
        self.emitting_node = emitting_node
        if isinstance(emitting_node, ua.NodeId):
            self.emitting_node = emitting_node
        else:
            self.emitting_node = ua.NodeId(emitting_node)
        # save current attributes
        self.internal_properties = list(self.__dict__.keys())[:] + ["internal_properties"]

    def __str__(self):
        return "{0}({1})".format(
            self.__class__.__name__,
            [str(k) + ":" + str(v) for k, v in self.__dict__.items() if k not in self.internal_properties])

    __repr__ = __str__

    def add_property(self, name, val, datatype):
        """
        Add a property to event and store its data type
        """
        setattr(self, name, val)
        self.data_types[name] = datatype

    def add_variable(self, name, val, datatype):
        """
        Add a variable to event and store its data type
        variables are able to have properties as children
        """
        setattr(self, name, val)
        self.data_types[name] = datatype

    def get_event_props_as_fields_dict(self):
        """
        convert all properties and variables of the Event class to a dict of variants
        """
        field_vars = {}
        for key, value in vars(self).items():
            if not key.startswith("__") and key not in self.internal_properties:
                field_vars[key] = ua.Variant(value, self.data_types[key])
        return field_vars

    @staticmethod
    def from_field_dict(fields):
        """
        Create an Event object from a dict of name and variants
        """
        ev = Event()
        for k, v in fields.items():
            ev.add_property(k, v.Value, v.VariantType)
        return ev

    def to_event_fields_using_subscription_fields(self, select_clauses):
        """
        Using a new select_clauses and the original select_clauses
        used during subscription, return a field list
        """
        fields = []
        for sattr in select_clauses:
            for idx, o_sattr in enumerate(self.select_clauses):
                if sattr.BrowsePath == o_sattr.BrowsePath and sattr.AttributeId == o_sattr.AttributeId:
                    fields.append(self.event_fields[idx])
                    break
        return fields

    def to_event_fields(self, select_clauses):
        """
        return a field list using a select clause and the object properties
        """
        fields = []
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
    def from_event_fields(select_clauses, fields):
        """
        Instantiate an Event object from a select_clauses and fields
        """
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
    def browse_path_to_attribute_name(browsePath):
        name = browsePath[0].Name
        # Append the sub-property of a VariableType with '/'
        iter_paths = iter(browsePath)
        next(iter_paths)
        for path in iter_paths:
            name += '/' + path.Name
        return name


async def get_filter_from_event_type(eventtypes, objectslist=[]):
    evfilter = ua.EventFilter()
    evfilter.SelectClauses = await select_clauses_from_evtype(eventtypes, objectslist)

    # byme :BEGIN: Debug SelectClause
    with open('select_clause_SimpleAttributeOperands.json', 'w+') as sel_file:
        json_obj = {}
        for i, op in enumerate(evfilter.SelectClauses):
            json_obj['SimpleAttributeOperand' + str(i + 1)] = {
                "TypeDefinitionId": str(op.TypeDefinitionId),
                "BrowsePath": str(op.BrowsePath),
                "AttributeId": str(op.AttributeId),
                "IndexRange": str(op.IndexRange)
            }
        json.dump(json_obj, sel_file, indent=2)
    # byme :END:

    evfilter.WhereClause = await where_clause_from_evtype(eventtypes)
    # with open('where_clause_SimpleAttributeOperands.json', 'w+'):
    return evfilter


async def append_new_attribute_to_select_clauses(attribute, select_clauses, already_selected,
                                                 parent_browse_path):  # parent_variable):

    # byme
    browse_path = []
    if parent_browse_path:
        browse_path = parent_browse_path.copy()

    # browse_path = []
    # if parent_variable:
    #     browse_path.append(await parent_variable.read_browse_name())
    browse_path.append(await attribute.read_browse_name())
    string_path = '/'.join(map(str, browse_path))
    if string_path not in already_selected:
        already_selected[string_path] = string_path
        op = ua.SimpleAttributeOperand()
        op.AttributeId = ua.AttributeIds.Value
        op.BrowsePath = browse_path
        select_clauses.append(op)


async def select_clauses_from_evtype(evtypes, objectslist):
    select_clauses = []
    already_selected = {}
    for evtype in evtypes:
        selected_clauses_part = []  # byme
        for property in await get_event_properties_from_type_node(evtype):
            await append_new_attribute_to_select_clauses(property, selected_clauses_part, already_selected, None)
        for variable in await get_event_variables_from_type_node(evtype):
            await append_new_attribute_to_select_clauses(variable, selected_clauses_part, already_selected, None)
            for subproperty in await variable.get_properties():
                variable_browse_name = await variable.read_browse_name()
                await append_new_attribute_to_select_clauses(subproperty, selected_clauses_part, already_selected,
                                                             [variable_browse_name])  # byme here was just variable
        # byme :BEGIN: BEWARE self coded (monkeypatch)  # byme critical point for subtypes -> Namespace and Index were set to 0 !
        #                                               -> Request of MonitoredItems with false TypeId

        select_clauses += selected_clauses_part

        # append all properties and variables of a evtype's object and its subobjects
        async def append_from_evtype_object(obj, parent_browse_path):
            selected_clauses_obj = []
            obj_browse_path = parent_browse_path.copy()
            obj_browse_path.append(await obj.read_browse_name())

            for property in await get_event_properties_from_type_node(obj):
                await append_new_attribute_to_select_clauses(property, selected_clauses_obj, already_selected,
                                                             obj_browse_path)
            for variable in await get_event_variables_from_type_node(obj):
                await append_new_attribute_to_select_clauses(variable, selected_clauses_obj, already_selected,
                                                             obj_browse_path)
                for subproperty in await variable.get_properties():
                    variable_browse_name = await variable.read_browse_name()
                    variable_browse_path = obj_browse_path.copy()
                    variable_browse_path.append(variable_browse_name)
                    await append_new_attribute_to_select_clauses(subproperty, selected_clauses_obj, already_selected,
                                                                 variable_browse_path)

            # set the TypeDefinitionId to Objects NodeId
            for subclause in selected_clauses_obj:
                subclause.TypeDefinitionId = obj.nodeid

            # object can have objects as attributes
            for subobj in await get_event_objects_from_type_node(obj):
                if objectslist:
                    # add if the object is specified in list
                    subobj_browse_name = await subobj.read_browse_name()
                    if subobj_browse_name.to_string() in objectslist:
                        selected_clauses_obj += await append_from_evtype_object(subobj, obj_browse_path)
                else:
                    # add all
                    selected_clauses_obj += await append_from_evtype_object(subobj, obj_browse_path)


            return selected_clauses_obj

        # evtype can have objects
        for evtype_object in await get_event_objects_from_type_node(evtype):
            if objectslist:
                # add if the object is specified in list
                obj_browse_name = await evtype_object.read_browse_name()
                if obj_browse_name.to_string() in objectslist:
                    select_clauses += await append_from_evtype_object(evtype_object, [])
            else:
                # add all
                select_clauses += await append_from_evtype_object(evtype_object, [])

        # set the TypeDefinitionId to evtype's NodeId
        for clause in select_clauses:
            clause.TypeDefinitionId = evtype.nodeid

        # byme :END:

    return select_clauses


async def where_clause_from_evtype(evtypes):
    cf = ua.ContentFilter()
    el = ua.ContentFilterElement()
    # operands can be ElementOperand, LiteralOperand, AttributeOperand, SimpleAttribute
    # Create a clause where the generate event type property EventType
    # must be a subtype of events in evtypes argument

    # the first operand is the attribute event type
    op = ua.SimpleAttributeOperand()
    # op.TypeDefinitionId = evtype.nodeid  # byme critical point for subtypes -> Namespace and Index were set to 0 !
    #                                       -> Request of MonitoredItems with false TypeId
    # byme :BEGIN: fix TypeDefinitionId for SimpleAttributeOperand
    # FIXME list behaviour is dodgy
    if isinstance(evtypes, list):
        op.TypeDefinitionId = evtypes[0].nodeid
    else:
        op.TypeDefinitionId = evtypes.nodeid
    # byme :END:

    op.BrowsePath.append(ua.QualifiedName("EventType", 0))
    op.AttributeId = ua.AttributeIds.Value
    el.FilterOperands.append(op)
    # now create a list of all subtypes we want to accept
    subtypes = []
    for evtype in evtypes:
        for st in await get_node_subtypes(evtype):
            subtypes.append(st.nodeid)
    subtypes = list(set(subtypes))  # remove duplicates
    for subtypeid in subtypes:
        op = ua.LiteralOperand()
        op.Value = ua.Variant(subtypeid)
        el.FilterOperands.append(op)

    el.FilterOperator = ua.FilterOperator.InList
    cf.Elements.append(el)
    return cf


async def select_event_attributes_from_type_node(node, attributeSelector):
    attributes = []
    curr_node = node
    while True:
        attributes.extend(await attributeSelector(curr_node))
        if curr_node.nodeid.Identifier == ua.ObjectIds.BaseEventType:
            break
        parents = await curr_node.get_referenced_nodes(
            refs=ua.ObjectIds.HasSubtype, direction=ua.BrowseDirection.Inverse, includesubtypes=True
        )
        # byme :BEGIN: objects of EventTypes have no HasSubtype reference
        #  -> identify parent with ref = HasComponent; nodeclass = Object
        if len(parents) != 1:  # curr_node is not a Subtype but a ObjectType or Object
            parents = await curr_node.get_referenced_nodes(
                refs=ua.ObjectIds.HasComponent, nodeclassmask=ua.NodeClass.ObjectType + ua.NodeClass.Object,
                direction=ua.BrowseDirection.Inverse, includesubtypes=True
            )
            if len(parents) != 1:  # Something went wrong
                return None

            # don't browse further backwards for ObjectTypes and Objects of a EventType
            # adding attributes of objects is handled moving down the tree in
            # select_clauses_from_evtype()
            break
        # byme :END:

        curr_node = parents[0]
    return attributes


async def get_event_properties_from_type_node(node):
    return await select_event_attributes_from_type_node(node, lambda n: n.get_properties())


async def get_event_variables_from_type_node(node):
    return await select_event_attributes_from_type_node(node, lambda n: n.get_variables())


# byme :BEGIN: fix selecting Variables and properties of a EventType wrapped in an object
async def get_event_objects_from_type_node(node):
    # ObjectType not included, because we are subscibing to it
    # TODO possibly there are usecases where ObjectTypes should get included here too
    #  (but this could be subtypes, which are already handled, so maybe not worth mentioning)
    return await select_event_attributes_from_type_node(
        node, lambda n: n.get_children(refs=ua.ObjectIds.HasComponent, nodeclassmask=ua.NodeClass.Object)
    )
# byme :END:


async def get_event_obj_from_type_node(node):
    """
    return an Event object from an event type node
    """
    if node.nodeid.NamespaceIndex == 0:
        if node.nodeid.Identifier in asyncua.common.event_objects.IMPLEMENTED_EVENTS.keys():
            return asyncua.common.event_objects.IMPLEMENTED_EVENTS[node.nodeid.Identifier]()

    parent_identifier, parent_eventtype = await _find_parent_eventtype(node)

    class CustomEvent(parent_eventtype):

        def __init__(self):
            parent_eventtype.__init__(self)
            self.EventType = node.nodeid

        async def _add_new_property(self, property, parent_variable):
            name = (await property.read_browse_name()).Name
            if parent_variable:
                parent_name = (await parent_variable.read_browse_name()).Name
                name = f'{parent_name}/{name}'
            val = await property.read_data_value()
            self.add_property(name, val.Value.Value, val.Value.VariantType)

        async def _add_new_variable(self, variable):
            name = (await variable.read_browse_name()).Name
            val = await variable.read_data_value()
            self.add_variable(name, val.Value.Value, await variable.read_data_type_as_variant_type())

        async def init(self):
            curr_node = node
            while curr_node.nodeid.Identifier != parent_identifier:
                for prop in await curr_node.get_properties():
                    await self._add_new_property(prop, None)
                for var in await curr_node.get_variables():
                    await self._add_new_variable(var)
                    # Add the sub-properties of the VariableType
                    for prop in await var.get_properties():
                        await self._add_new_property(prop, var)
                parents = await curr_node.get_referenced_nodes(refs=ua.ObjectIds.HasSubtype,
                                                               direction=ua.BrowseDirection.Inverse,
                                                               includesubtypes=True)
                if len(parents) != 1:  # Something went wrong
                    raise UaError("Parent of event type could not be found")
                curr_node = parents[0]

            self._freeze = True

    ce = CustomEvent()
    await ce.init()
    return ce


async def _find_parent_eventtype(node):
    """
    """
    parents = await node.get_referenced_nodes(refs=ua.ObjectIds.HasSubtype, direction=ua.BrowseDirection.Inverse,
                                              includesubtypes=True)

    if len(parents) != 1:  # Something went wrong
        raise UaError("Parent of event type could not be found")
    if parents[0].nodeid.NamespaceIndex == 0:
        if parents[0].nodeid.Identifier in asyncua.common.event_objects.IMPLEMENTED_EVENTS.keys():
            return parents[0].nodeid.Identifier, asyncua.common.event_objects.IMPLEMENTED_EVENTS[
                parents[0].nodeid.Identifier]
    return await _find_parent_eventtype(parents[0])
