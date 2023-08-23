"""
High level node object, to access node attribute
and browse address space
"""

import logging
from typing import Union

from asyncua import ua
from asyncua.common.session_interface import AbstractSession
from .ua_utils import value_to_datavalue

from .events import Event, get_filter_from_event_type
from .ua_utils import data_type_to_variant_type
from .manage_nodes import create_folder, create_object, create_object_type, create_variable, create_variable_type, \
    create_data_type, create_property, delete_nodes, create_method, create_reference_type
from .methods import call_method

_logger = logging.getLogger(__name__)


def _check_results(results, reqlen=1):
    if not len(results) == reqlen:
        raise ValueError(results)
    for r in results:
        r.check()


def _to_nodeid(nodeid):
    if isinstance(nodeid, int):
        return ua.TwoByteNodeId(nodeid)
    if isinstance(nodeid, Node):
        return nodeid.nodeid
    if isinstance(nodeid, ua.NodeId):
        return nodeid
    if type(nodeid) in (str, bytes):
        return ua.NodeId.from_string(nodeid)
    raise ua.UaError(f"Could not resolve '{nodeid}' to a type id")


class Node:
    """
    High level node object, to access node attribute,
    browse and populate address space.
    Node objects are useful as-is but they do not expose the entire
    OPC-UA protocol. Feel free to look at the code of this class and call
    directly UA services methods to optimize your code
    """
    def __init__(self, session: AbstractSession, nodeid: Union["Node", ua.NodeId, str, bytes, int]):
        self.session = session
        self.nodeid: ua.NodeId
        if isinstance(nodeid, Node):
            self.nodeid = nodeid.nodeid
        elif isinstance(nodeid, ua.NodeId):
            self.nodeid = nodeid
        elif type(nodeid) in (str, bytes):
            self.nodeid = ua.NodeId.from_string(nodeid)
        elif isinstance(nodeid, int):
            self.nodeid = ua.NodeId(nodeid, 0)
        else:
            raise ua.UaError(f"argument to node must be a NodeId object or a string" f" defining a nodeid found {nodeid} of type {type(nodeid)}")
        self.basenodeid = None

    def __eq__(self, other):
        if isinstance(other, Node) and self.nodeid == other.nodeid:
            return True
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return self.nodeid.to_string()

    def __repr__(self):
        return f"Node({self.nodeid})"

    def __hash__(self):
        return self.nodeid.__hash__()

    async def read_browse_name(self):
        """
        Get browse name of a node. A browse name is a QualifiedName object
        composed of a string(name) and a namespace index.
        """
        result = await self.read_attribute(ua.AttributeIds.BrowseName)
        return result.Value.Value

    async def read_display_name(self):
        """
        get DisplayName attribute of node
        """
        result = await self.read_attribute(ua.AttributeIds.DisplayName)
        return result.Value.Value

    async def read_data_type(self):
        """
        get data type of node as NodeId
        """
        result = await self.read_attribute(ua.AttributeIds.DataType)
        return result.Value.Value

    async def read_data_type_as_variant_type(self):
        """
        get data type of node as VariantType
        This only works if node is a variable, otherwise type
        may not be convertible to VariantType
        """
        result = await self.read_attribute(ua.AttributeIds.DataType)
        return await data_type_to_variant_type(Node(self.session, result.Value.Value))

    async def get_access_level(self):
        """
        Get the access level attribute of the node as a set of AccessLevel enum values.
        """
        result = await self.read_attribute(ua.AttributeIds.AccessLevel)
        return ua.AccessLevel.parse_bitfield(result.Value.Value)

    async def get_user_access_level(self):
        """
        Get the user access level attribute of the node as a set of AccessLevel enum values.
        """
        result = await self.read_attribute(ua.AttributeIds.UserAccessLevel)
        return ua.AccessLevel.parse_bitfield(result.Value.Value)

    async def read_event_notifier(self):
        """
        Get the event notifier attribute of the node as a set of EventNotifier enum values.
        """
        result = await self.read_attribute(ua.AttributeIds.EventNotifier)
        return ua.EventNotifier.parse_bitfield(result.Value.Value)

    async def set_event_notifier(self, values):
        """
        Set the event notifier attribute.

        :param values: an iterable of EventNotifier enum values.
        """
        event_notifier_bitfield = ua.EventNotifier.to_bitfield(values)
        await self.write_attribute(ua.AttributeIds.EventNotifier, ua.DataValue(ua.Variant(event_notifier_bitfield, ua.VariantType.Byte)))

    async def read_node_class(self):
        """
        get node class attribute of node
        """
        result = await self.read_attribute(ua.AttributeIds.NodeClass)
        return ua.NodeClass(result.Value.Value)

    async def read_data_type_definition(self):
        """
        read data type definition attribute of node
        only DataType nodes following spec >= 1.04 have that attribute
        """
        result = await self.read_attribute(ua.AttributeIds.DataTypeDefinition)
        return result.Value.Value

    async def write_data_type_definition(self, sdef: ua.DataTypeDefinition):
        """
        write data type definition attribute of node
        only DataType nodes following spec >= 1.04 have that attribute
        """
        v = ua.Variant(sdef, ua.VariantType.ExtensionObject)
        await self.write_attribute(ua.AttributeIds.DataTypeDefinition, ua.DataValue(v))

    async def read_description(self):
        """
        get description attribute class of node
        """
        result = await self.read_attribute(ua.AttributeIds.Description)
        return result.Value.Value

    async def read_value(self):
        """
        Get value of a node as a python type. Only variables ( and properties) have values.
        An exception will be generated for other node types.
        WARNING: on server side, this function returns a ref to object in ua database.
        Do not modify it if it is a mutable object unless you know what you are doing
        """
        result = await self.read_data_value()
        return result.Value.Value

    get_value = read_value  # legacy compatibility

    async def read_data_value(self, raise_on_bad_status=True):
        """
        Get value of a node as a DataValue object. Only variables (and properties) have values.
        An exception will be generated for other node types.
        DataValue contain a variable value as a variant as well as server and source timestamps
        """
        return await self.read_attribute(ua.AttributeIds.Value, None, raise_on_bad_status)

    async def write_array_dimensions(self, value):
        """
        Set attribute ArrayDimensions of node
        make sure it has the correct data type
        """
        v = ua.Variant(value, ua.VariantType.UInt32)
        await self.write_attribute(ua.AttributeIds.ArrayDimensions, ua.DataValue(v))

    async def read_array_dimensions(self):
        """
        Read and return ArrayDimensions attribute of node
        """
        res = await self.read_attribute(ua.AttributeIds.ArrayDimensions)
        return res.Value.Value

    async def write_value_rank(self, value):
        """
        Set attribute ValueRank of node
        """
        v = ua.Variant(value, ua.VariantType.Int32)
        await self.write_attribute(ua.AttributeIds.ValueRank, ua.DataValue(v))

    async def read_value_rank(self):
        """
        Read and return ValueRank attribute of node
        """
        res = await self.read_attribute(ua.AttributeIds.ValueRank)
        return ua.ValueRank(res.Value.Value)

    async def write_value(self, value, varianttype=None):
        """
        Write value of a node. Only variables(properties) have values.
        An exception will be generated for other node types.
        value argument is either:
        * a python built-in type, converted to opc-ua
        optionally using the variantype argument.
        * a ua.Variant, varianttype is then ignored
        * a ua.DataValue, you then have full control over data send to server
        WARNING: On server side, ref to object is directly saved in our UA db, if this is a mutable object
        and you modify it afterward, then the object in db will be modified without any
        data change event generated
        """
        dv = value_to_datavalue(value, varianttype)
        await self.write_attribute(ua.AttributeIds.Value, dv)

    set_data_value = write_value  # legacy compatibility
    set_value = write_value  # legacy compatibility

    async def set_writable(self, writable=True):
        """
        Set node as writable by clients.
        A node is always writable on server side.
        """
        if writable:
            await self.set_attr_bit(ua.AttributeIds.AccessLevel, ua.AccessLevel.CurrentWrite)
            await self.set_attr_bit(ua.AttributeIds.UserAccessLevel, ua.AccessLevel.CurrentWrite)
        else:
            await self.unset_attr_bit(ua.AttributeIds.AccessLevel, ua.AccessLevel.CurrentWrite)
            await self.unset_attr_bit(ua.AttributeIds.UserAccessLevel, ua.AccessLevel.CurrentWrite)

    async def set_attr_bit(self, attr, bit):
        dv = await self.read_attribute(attr)
        val = ua.ua_binary.set_bit(dv.Value.Value, bit)
        await self.write_attribute(attr, ua.DataValue(ua.Variant(val, dv.Value.VariantType)))

    async def unset_attr_bit(self, attr, bit):
        dv = await self.read_attribute(attr)
        val = ua.ua_binary.unset_bit(dv.Value.Value, bit)
        await self.write_attribute(attr, ua.DataValue(ua.Variant(val, dv.Value.VariantType)))

    def set_read_only(self):
        """
        Set a node as read-only for clients.
        A node is always writable on server side.
        """
        return self.set_writable(False)

    async def write_attribute(self, attributeid, datavalue, indexrange=None):
        """
        Set an attribute of a node
        attributeid is a member of ua.AttributeIds
        datavalue is a ua.DataValue object
        indexrange is a NumericRange (a string; e.g. "1" or "1:3".
            See https://reference.opcfoundation.org/v104/Core/docs/Part4/7.22/)
        """
        attr = ua.WriteValue()
        attr.NodeId = self.nodeid
        attr.AttributeId = attributeid
        attr.Value = datavalue
        attr.IndexRange = indexrange
        params = ua.WriteParameters()
        params.NodesToWrite = [attr]
        result = await self.session.write(params)
        result[0].check()

    async def write_params(self, params):
        result = await self.session.write(params)
        return result

    async def read_attribute(self, attr, indexrange=None, raise_on_bad_status=True):
        """
        Read one attribute of a node
        attributeid is a member of ua.AttributeIds
        indexrange is a NumericRange (a string; e.g. "1" or "1:3".
        result code from server is checked and an exception is raised in case of error
        """
        rv = ua.ReadValueId()
        rv.NodeId = self.nodeid
        rv.AttributeId = attr
        rv.IndexRange = indexrange
        params = ua.ReadParameters()
        params.NodesToRead.append(rv)
        result = await self.session.read(params)
        if raise_on_bad_status:
            result[0].StatusCode.check()
        return result[0]

    async def read_attributes(self, attrs):
        """
        Read several attributes of a node
        list of DataValue is returned
        """
        params = ua.ReadParameters()
        for attr in attrs:
            rv = ua.ReadValueId()
            rv.NodeId = self.nodeid
            rv.AttributeId = attr
            params.NodesToRead.append(rv)

        results = await self.session.read(params)
        return results

    async def read_params(self, params):
        result = await self.session.read(params)
        return result

    async def get_children(self, refs=ua.ObjectIds.HierarchicalReferences, nodeclassmask=ua.NodeClass.Unspecified):
        """
        Get all children of a node. By default hierarchical references and all node classes are returned.
        Other reference types may be given:
        References = 31
        NonHierarchicalReferences = 32
        HierarchicalReferences = 33
        HasChild = 34
        Organizes = 35
        HasEventSource = 36
        HasModellingRule = 37
        HasEncoding = 38
        HasDescription = 39
        HasTypeDefinition = 40
        GeneratesEvent = 41
        Aggregates = 44
        HasSubtype = 45
        HasProperty = 46
        HasComponent = 47
        HasNotifier = 48
        HasOrderedComponent = 49
        """
        return await self.get_referenced_nodes(refs, ua.BrowseDirection.Forward, nodeclassmask)

    def get_properties(self):
        """
        return properties of node.
        properties are child nodes with a reference of type HasProperty and a NodeClass of Variable
        COROUTINE
        """
        return self.get_children(refs=ua.ObjectIds.HasProperty, nodeclassmask=ua.NodeClass.Variable)

    def get_variables(self):
        """
        return variables of node.
        variables are child nodes with a reference of type HasComponent and a NodeClass of Variable
        """
        return self.get_children(refs=ua.ObjectIds.HasComponent, nodeclassmask=ua.NodeClass.Variable)

    def get_methods(self):
        """
        return methods of node.
        methods are child nodes with a reference of type HasComponent and a NodeClass of Method
        """
        return self.get_children(refs=ua.ObjectIds.HasComponent, nodeclassmask=ua.NodeClass.Method)

    async def get_children_descriptions(self, refs=ua.ObjectIds.HierarchicalReferences, nodeclassmask=ua.NodeClass.Unspecified, includesubtypes=True, result_mask=ua.BrowseResultMask.All):
        return await self.get_references(refs, ua.BrowseDirection.Forward, nodeclassmask, includesubtypes, result_mask)

    def get_encoding_refs(self):
        return self.get_referenced_nodes(ua.ObjectIds.HasEncoding, ua.BrowseDirection.Forward)

    def get_description_refs(self):
        return self.get_referenced_nodes(ua.ObjectIds.HasDescription, ua.BrowseDirection.Forward)

    async def get_references(self, refs=ua.ObjectIds.References, direction=ua.BrowseDirection.Both, nodeclassmask=ua.NodeClass.Unspecified, includesubtypes=True, result_mask=ua.BrowseResultMask.All):
        """
        returns references of the node based on specific filter defined with:

        refs = ObjectId of the Reference
        direction = Browse direction for references
        nodeclassmask = filter nodes based on specific class
        includesubtypes = If true subtypes of the reference (ref) are also included
        result_mask = define what results information are requested
        """
        desc = ua.BrowseDescription()
        desc.BrowseDirection = direction
        desc.ReferenceTypeId = _to_nodeid(refs)
        desc.IncludeSubtypes = includesubtypes
        desc.NodeClassMask = nodeclassmask
        desc.ResultMask = result_mask
        desc.NodeId = self.nodeid
        params = ua.BrowseParameters()
        params.View.Timestamp = ua.get_win_epoch()
        params.NodesToBrowse.append(desc)
        params.RequestedMaxReferencesPerNode = 0
        results = await self.session.browse(params)
        references = await self._browse_next(results)
        return references

    async def _browse_next(self, results):
        references = results[0].References
        while results[0].ContinuationPoint:
            params = ua.BrowseNextParameters()
            params.ContinuationPoints = [results[0].ContinuationPoint]
            params.ReleaseContinuationPoints = False
            results = await self.session.browse_next(params)
            references.extend(results[0].References)
        return references

    async def get_referenced_nodes(self, refs=ua.ObjectIds.References, direction=ua.BrowseDirection.Both, nodeclassmask=ua.NodeClass.Unspecified, includesubtypes=True):
        """
        returns referenced nodes based on specific filter
        Parameters are the same as for get_references

        """
        references = await self.get_references(refs, direction, nodeclassmask, includesubtypes)
        nodes = []
        for desc in references:
            node = Node(self.session, desc.NodeId)
            nodes.append(node)
        return nodes

    async def read_type_definition(self):
        """
        returns type definition of the node.
        """
        references = await self.get_references(refs=ua.ObjectIds.HasTypeDefinition, direction=ua.BrowseDirection.Forward)
        if len(references) == 0:
            return None
        return references[0].NodeId

    async def get_path(self, max_length=20, as_string=False):
        """
        Attempt to find path of node from root node and return it as a list of Nodes.
        There might several possible paths to a node, this function will return one
        Some nodes may be missing references, so this method may
        return an empty list
        Since address space may have circular references, a max length is specified

        """
        path = await self._get_path(max_length)
        path = [Node(self.session, ref.NodeId) for ref in path]
        path.append(self)
        if as_string:
            path = [(await el.read_browse_name()).to_string() for el in path]
        return path

    async def _get_path(self, max_length=20):
        """
        Attempt to find path of node from root node and return it as a list of Nodes.
        There might several possible paths to a node, this function will return one
        Some nodes may be missing references, so this method may
        return an empty list
        Since address space may have circular references, a max length is specified

        """
        path = []
        node = self
        while True:
            refs = await node.get_references(refs=ua.ObjectIds.HierarchicalReferences, direction=ua.BrowseDirection.Inverse)
            if len(refs) > 0:
                path.insert(0, refs[0])
                node = Node(self.session, refs[0].NodeId)
                if len(path) >= (max_length - 1):
                    return path
            else:
                return path

    async def get_parent(self):
        """
        returns parent of the node.
        A Node may have several parents, the first found is returned.
        This method uses reverse references, a node might be missing such a link,
        thus we will not find its parent.
        """
        refs = await self.get_references(refs=ua.ObjectIds.HierarchicalReferences, direction=ua.BrowseDirection.Inverse)
        if len(refs) > 0:
            return Node(self.session, refs[0].NodeId)
        return None

    async def get_child(self, path, return_all=False):
        """
        get a child specified by its path from this node.
        A path might be:
        * a string representing a qualified name.
        * a qualified name
        * a list of string
        * a list of qualified names
        """
        if type(path) not in (list, tuple):
            path = [path]
        rpath = self._make_relative_path(path)
        bpath = ua.BrowsePath()
        bpath.StartingNode = self.nodeid
        bpath.RelativePath = rpath
        result = await self.session.translate_browsepaths_to_nodeids([bpath])
        result = result[0]
        result.StatusCode.check()
        if return_all:
            return [Node(self.session, target.TargetId) for target in result.Targets]
        return Node(self.session, result.Targets[0].TargetId)

    async def get_children_by_path(self, paths, raise_on_partial_error=True):
        """
        get children specified by their paths from this node.
        A path might be:
        * a string representing a qualified name.
        * a qualified name
        * a list of string
        * a list of qualified names
        """
        bpaths = []
        for path in paths:
            if type(path) not in (list, tuple):
                path = [path]
            rpath = self._make_relative_path(path)
            bpath = ua.BrowsePath()
            bpath.StartingNode = self.nodeid
            bpath.RelativePath = rpath
            bpaths.append(bpath)

        results = await self.session.translate_browsepaths_to_nodeids(bpaths)
        try:
            if raise_on_partial_error:
                for result in results:
                    result.StatusCode.check()
        except ua.UaStatusCodeError:
            codes = [result.StatusCode.value for result in results]
            raise ua.UaStatusCodeErrors(codes)
        return [
            [Node(self.session, target.TargetId) for target in result.Targets]
            if result.StatusCode.is_good() else None
            for result in results
        ]

    def _make_relative_path(self, path):
        rpath = ua.RelativePath()
        for item in path:
            el = ua.RelativePathElement()
            el.ReferenceTypeId = ua.TwoByteNodeId(ua.ObjectIds.HierarchicalReferences)
            el.IsInverse = False
            el.IncludeSubtypes = True
            if isinstance(item, ua.QualifiedName):
                el.TargetName = item
            else:
                el.TargetName = ua.QualifiedName.from_string(item)
            rpath.Elements.append(el)
        return rpath

    async def read_raw_history(self, starttime=None, endtime=None, numvalues=0, return_bounds=True):
        """
        Read raw history of a node
        result code from server is checked and an exception is raised in case of error
        If numvalues is > 0 and number of events in period is > numvalues
        then result will be truncated
        """
        details = ua.ReadRawModifiedDetails()
        details.IsReadModified = False
        if starttime:
            details.StartTime = starttime
        else:
            details.StartTime = ua.get_win_epoch()
        if endtime:
            details.EndTime = endtime
        else:
            details.EndTime = ua.get_win_epoch()
        details.NumValuesPerNode = numvalues
        details.ReturnBounds = return_bounds
        history = []
        continuation_point = None
        while True:
            result = await self.history_read(details, continuation_point)
            result.StatusCode.check()
            continuation_point = result.ContinuationPoint
            history.extend(result.HistoryData.DataValues)
            # No more data available
            if continuation_point is None:
                break
            # No more data needed
            if numvalues > 0:
                break
        return history

    async def history_read(self, details, continuation_point=None):
        """
        Read raw history of a node, low-level function
        result code from server is checked and an exception is raised in case of error
        """
        valueid = ua.HistoryReadValueId()
        valueid.NodeId = self.nodeid
        valueid.IndexRange = ''
        valueid.ContinuationPoint = continuation_point
        params = ua.HistoryReadParameters()
        params.HistoryReadDetails = details
        params.TimestampsToReturn = ua.TimestampsToReturn.Both
        params.ReleaseContinuationPoints = False
        params.NodesToRead.append(valueid)
        return (await self.session.history_read(params))[0]

    async def read_event_history(self, starttime=None, endtime=None, numvalues=0, evtypes=ua.ObjectIds.BaseEventType):
        """
        Read event history of a source node
        result code from server is checked and an exception is raised in case of error
        If numvalues is > 0 and number of events in period is > numvalues
        then result will be truncated
        """
        details = ua.ReadEventDetails()
        if starttime:
            details.StartTime = starttime
        else:
            details.StartTime = ua.get_win_epoch()
        if endtime:
            details.EndTime = endtime
        else:
            details.EndTime = ua.get_win_epoch()
        details.NumValuesPerNode = numvalues
        if not isinstance(evtypes, (list, tuple)):
            evtypes = [evtypes]
        evtypes = [Node(self.session, evtype) for evtype in evtypes]
        evfilter = await get_filter_from_event_type(evtypes)
        details.Filter = evfilter
        result = await self.history_read_events(details)
        result.StatusCode.check()
        event_res = []
        for res in result.HistoryData.Events:
            event_res.append(Event.from_event_fields(evfilter.SelectClauses, res.EventFields))
        return event_res

    async def history_read_events(self, details):
        """
        Read event history of a node, low-level function
        result code from server is checked and an exception is raised in case of error
        """
        valueid = ua.HistoryReadValueId()
        valueid.NodeId = self.nodeid
        valueid.IndexRange = ''
        params = ua.HistoryReadParameters()
        params.HistoryReadDetails = details
        params.TimestampsToReturn = ua.TimestampsToReturn.Both
        params.ReleaseContinuationPoints = False
        params.NodesToRead.append(valueid)
        return (await self.session.history_read(params))[0]

    async def delete(self, delete_references=True, recursive=False):
        """
        Delete node from address space
        """
        nodes, results = await delete_nodes(self.session, [self], recursive, delete_references)
        for r in results:
            r.check()
        return nodes

    def _fill_delete_reference_item(self, rdesc, bidirectional=False):
        ditem = ua.DeleteReferencesItem()
        ditem.SourceNodeId = self.nodeid
        ditem.TargetNodeId = rdesc.NodeId
        ditem.ReferenceTypeId = rdesc.ReferenceTypeId
        ditem.IsForward = rdesc.IsForward
        ditem.DeleteBidirectional = bidirectional
        return ditem

    async def delete_reference(self, target, reftype, forward=True, bidirectional=True):
        """
        Delete given node's references from address space
        """
        known_refs = await self.get_references(reftype, includesubtypes=False)
        targetid = _to_nodeid(target)
        for r in known_refs:
            if r.NodeId == targetid and r.IsForward == forward:
                rdesc = r
                break
        else:
            raise ua.UaStatusCodeError(ua.StatusCodes.BadNotFound)
        ditem = self._fill_delete_reference_item(rdesc, bidirectional)
        (await self.session.delete_references([ditem]))[0].check()

    async def add_reference(self, target, reftype, forward=True, bidirectional=True):
        """
        Add reference to node
        """
        aitem = ua.AddReferencesItem()
        aitem.SourceNodeId = self.nodeid
        aitem.TargetNodeId = _to_nodeid(target)
        aitem.ReferenceTypeId = _to_nodeid(reftype)
        aitem.IsForward = forward
        params = [aitem]
        if bidirectional:
            aitem2 = ua.AddReferencesItem()
            aitem2.SourceNodeId = aitem.TargetNodeId
            aitem2.TargetNodeId = aitem.SourceNodeId
            aitem2.ReferenceTypeId = aitem.ReferenceTypeId
            aitem2.IsForward = not forward
            params.append(aitem2)
        results = await self.session.add_references(params)
        _check_results(results, len(params))

    async def set_modelling_rule(self, mandatory: bool):
        """
        Add a modelling rule reference to Node.
        When creating a new object type, its variable and child nodes will not
        be instantiated if they do not have modelling rule
        if mandatory is None, the modelling rule is removed
        """
        # remove all existing modelling rule
        rules = await self.get_references(ua.ObjectIds.HasModellingRule)
        await self.session.delete_references(list(map(self._fill_delete_reference_item, rules)))
        # add new modelling rule as requested
        if mandatory is not None:
            rule = ua.ObjectIds.ModellingRule_Mandatory if mandatory else ua.ObjectIds.ModellingRule_Optional
            await self.add_reference(rule, ua.ObjectIds.HasModellingRule, True, False)

    async def add_folder(self, nodeid, bname):
        return await create_folder(self, nodeid, bname)

    async def add_object(self, nodeid, bname, objecttype=None, instantiate_optional=True):
        return await create_object(self, nodeid, bname, objecttype, instantiate_optional)

    async def add_variable(self, nodeid, bname, val, varianttype=None, datatype=None):
        return await create_variable(self, nodeid, bname, val, varianttype, datatype)

    async def add_object_type(self, nodeid, bname):
        return await create_object_type(self, nodeid, bname)

    async def add_variable_type(self, nodeid, bname, datatype):
        return await create_variable_type(self, nodeid, bname, datatype)

    async def add_data_type(self, nodeid, bname, description=None):
        return await create_data_type(self, nodeid, bname, description=description)

    async def add_property(self, nodeid, bname, val, varianttype=None, datatype=None):
        return await create_property(self, nodeid, bname, val, varianttype, datatype)

    async def add_method(self, *args):
        return await create_method(self, *args)

    async def add_reference_type(self, nodeid, bname, symmetric=True, inversename=None):
        return await create_reference_type(self, nodeid, bname, symmetric, inversename)

    async def call_method(self, methodid, *args):
        return await call_method(self, methodid, *args)

    async def register(self):
        """
        Register node for faster read and write access (if supported by server)
        Rmw: This call modifies the nodeid of the node, the original nodeid is
        available as node.basenodeid
        """
        nodeid = (await self.session.register_nodes([self.nodeid]))[0]
        self.basenodeid = self.nodeid
        self.nodeid = nodeid

    async def unregister(self):
        if self.basenodeid is None:
            return
        await self.session.unregister_nodes([self.nodeid])
        self.nodeid = self.basenodeid
        self.basenodeid = None

    @staticmethod
    def new_node(session, nodeid: ua.NodeId):
        """
        Helper function to init nodes with out importing Node
        """
        return Node(session, nodeid)
