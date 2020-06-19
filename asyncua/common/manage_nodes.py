"""
High level functions to create nodes
"""
import logging
from asyncua import ua
from .instantiate_util import instantiate
from .node_factory import make_node

_logger = logging.getLogger(__name__)


def _parse_nodeid_qname(*args):
    try:
        if isinstance(args[0], int):
            nodeid = ua.NodeId(0, int(args[0]))
            qname = ua.QualifiedName(args[1], int(args[0]))
            return nodeid, qname
        if isinstance(args[0], ua.NodeId):
            nodeid = args[0]
        elif isinstance(args[0], str):
            nodeid = ua.NodeId.from_string(args[0])
        else:
            raise RuntimeError()
        if isinstance(args[1], ua.QualifiedName):
            qname = args[1]
        elif isinstance(args[1], str):
            qname = ua.QualifiedName.from_string(args[1])
        else:
            raise RuntimeError()
        return nodeid, qname
    except ua.UaError:
        raise
    except Exception as ex:
        raise TypeError(
            f"This method takes either a namespace index and a string as argument or a nodeid and a qualifiedname."
            f" Received arguments {args} and got exception {ex}"
        )


async def create_folder(parent, nodeid, bname):
    """
    create a child node folder
    arguments are nodeid, browsename
    or namespace index, name
    """
    nodeid, qname = _parse_nodeid_qname(nodeid, bname)
    return make_node(
        parent.server,
        await _create_object(parent.server, parent.nodeid, nodeid, qname, ua.ObjectIds.FolderType)
    )


async def create_object(parent, nodeid, bname, objecttype=None):
    """
    create a child node object
    arguments are nodeid, browsename, [objecttype]
    or namespace index, name, [objecttype]
    if objectype is given (a NodeId) then the type node is instantiated inclusive its child nodes
    """
    nodeid, qname = _parse_nodeid_qname(nodeid, bname)
    if objecttype is not None:
        objecttype = make_node(parent.server, objecttype)
        dname = ua.LocalizedText(qname.Name)
        nodes = await instantiate(parent, objecttype, nodeid, bname=qname, dname=dname)
        return nodes[0]
    else:
        return make_node(
            parent.server,
            await _create_object(parent.server, parent.nodeid, nodeid, qname, ua.ObjectIds.BaseObjectType)
        )


async def create_property(parent, nodeid, bname, val, varianttype=None, datatype=None):
    """
    create a child node property
    args are nodeid, browsename, value, [variant type]
    or idx, name, value, [variant type]
    """
    nodeid, qname = _parse_nodeid_qname(nodeid, bname)
    var = ua.Variant(val, varianttype)
    if datatype and isinstance(datatype, int):
        datatype = ua.NodeId(datatype, 0)
    if datatype and not isinstance(datatype, ua.NodeId):
        raise RuntimeError("datatype argument must be a nodeid or an int refering to a nodeid")
    return make_node(
        parent.server,
        await _create_variable(parent.server, parent.nodeid, nodeid, qname, var, datatype=datatype, isproperty=True)
    )


async def create_variable(parent, nodeid, bname, val, varianttype=None, datatype=None):
    """
    create a child node variable
    args are nodeid, browsename, value, [variant type], [data type]
    or idx, name, value, [variant type], [data type]
    """
    nodeid, qname = _parse_nodeid_qname(nodeid, bname)
    var = ua.Variant(val, varianttype)
    if datatype and isinstance(datatype, int):
        datatype = ua.NodeId(datatype, 0)
    if datatype and not isinstance(datatype, ua.NodeId):
        raise RuntimeError("datatype argument must be a nodeid or an int refering to a nodeid")

    return make_node(
        parent.server,
        await _create_variable(parent.server, parent.nodeid, nodeid, qname, var, datatype=datatype, isproperty=False)
    )


async def create_variable_type(parent, nodeid, bname, datatype):
    """
    Create a new variable type
    args are nodeid, browsename and datatype
    or idx, name and data type
    """
    nodeid, qname = _parse_nodeid_qname(nodeid, bname)
    if datatype and isinstance(datatype, int):
        datatype = ua.NodeId(datatype, 0)
    if datatype and not isinstance(datatype, ua.NodeId):
        raise RuntimeError(
            f"Data type argument must be a nodeid or an int refering to a nodeid, received: {datatype}")
    return make_node(
        parent.server,
        await _create_variable_type(parent.server, parent.nodeid, nodeid, qname, datatype)
    )


async def create_reference_type(parent, nodeid, bname, symmetric=True, inversename=None):
    """
    Create a new reference type
    args are nodeid and browsename
    or idx and name
    """
    nodeid, qname = _parse_nodeid_qname(nodeid, bname)
    return make_node(
        parent.server,
        await _create_reference_type(parent.server, parent.nodeid, nodeid, qname, symmetric, inversename)
    )


async def create_object_type(parent, nodeid, bname):
    """
    Create a new object type to be instanciated in address space.
    arguments are nodeid, browsename
    or namespace index, name
    """
    nodeid, qname = _parse_nodeid_qname(nodeid, bname)
    return make_node(parent.server, await _create_object_type(parent.server, parent.nodeid, nodeid, qname))


async def create_method(parent, *args):
    """
    create a child method object
    This is only possible on server side!!
    args are nodeid, browsename, method_to_be_called, [input argument types], [output argument types]
    or idx, name, method_to_be_called, [input argument types], [output argument types]
    if argument types is specified, child nodes advertising what arguments the method uses and returns will be created
    a callback is a method accepting the nodeid of the parent as first argument and variants after.
    returns a list of variants
    """
    _logger.info('create_method %r', parent)
    nodeid, qname = _parse_nodeid_qname(*args[:2])
    callback = args[2]
    if len(args) > 3:
        inputs = args[3]
    else:
        inputs = []
    if len(args) > 4:
        outputs = args[4]
    else:
        outputs = []
    return make_node(parent.server, await _create_method(parent, nodeid, qname, callback, inputs, outputs))


async def _create_object(server, parentnodeid, nodeid, qname, objecttype):
    addnode = ua.AddNodesItem()
    addnode.RequestedNewNodeId = nodeid
    addnode.BrowseName = qname
    addnode.ParentNodeId = parentnodeid
    if await make_node(server, parentnodeid).get_type_definition() == ua.NodeId(ua.ObjectIds.FolderType):
        addnode.ReferenceTypeId = ua.NodeId(ua.ObjectIds.Organizes)
    else:
        addnode.ReferenceTypeId = ua.NodeId(ua.ObjectIds.HasComponent)
    addnode.NodeClass = ua.NodeClass.Object
    if isinstance(objecttype, int):
        addnode.TypeDefinition = ua.NodeId(objecttype)
    else:
        addnode.TypeDefinition = objecttype
    attrs = ua.ObjectAttributes()
    attrs.EventNotifier = 0
    attrs.Description = ua.LocalizedText(qname.Name)
    attrs.DisplayName = ua.LocalizedText(qname.Name)
    attrs.WriteMask = 0
    attrs.UserWriteMask = 0
    addnode.NodeAttributes = attrs
    results = await server.add_nodes([addnode])
    results[0].StatusCode.check()
    return results[0].AddedNodeId


async def _create_reference_type(server, parentnodeid, nodeid, qname, symmetric, inversename):
    addnode = ua.AddNodesItem()
    addnode.RequestedNewNodeId = nodeid
    addnode.BrowseName = qname
    addnode.NodeClass = ua.NodeClass.ReferenceType
    addnode.ParentNodeId = parentnodeid
    addnode.ReferenceTypeId = ua.NodeId(ua.ObjectIds.HasSubtype)
    attrs = ua.ReferenceTypeAttributes()
    attrs.IsAbstract = False
    attrs.Description = ua.LocalizedText(qname.Name)
    attrs.DisplayName = ua.LocalizedText(qname.Name)
    attrs.Symmetric = symmetric
    attrs.InverseName = ua.LocalizedText(inversename)
    attrs.UserWriteMask = 0
    addnode.NodeAttributes = attrs

    results = await server.add_nodes([addnode])
    results[0].StatusCode.check()
    return results[0].AddedNodeId


async def _create_object_type(server, parentnodeid, nodeid, qname):
    addnode = ua.AddNodesItem()
    addnode.RequestedNewNodeId = nodeid
    addnode.BrowseName = qname
    addnode.ParentNodeId = parentnodeid
    addnode.ReferenceTypeId = ua.NodeId(ua.ObjectIds.HasSubtype)
    addnode.NodeClass = ua.NodeClass.ObjectType
    attrs = ua.ObjectTypeAttributes()
    attrs.IsAbstract = False
    attrs.Description = ua.LocalizedText(qname.Name)
    attrs.DisplayName = ua.LocalizedText(qname.Name)
    attrs.WriteMask = 0
    attrs.UserWriteMask = 0
    addnode.NodeAttributes = attrs
    results = await server.add_nodes([addnode])
    results[0].StatusCode.check()
    return results[0].AddedNodeId


async def _create_variable(server, parentnodeid, nodeid, qname, var, datatype=None, isproperty=False):
    addnode = ua.AddNodesItem()
    addnode.RequestedNewNodeId = nodeid
    addnode.BrowseName = qname
    addnode.NodeClass = ua.NodeClass.Variable
    addnode.ParentNodeId = parentnodeid
    if isproperty:
        addnode.ReferenceTypeId = ua.NodeId(ua.ObjectIds.HasProperty)
        addnode.TypeDefinition = ua.NodeId(ua.ObjectIds.PropertyType)
    else:
        addnode.ReferenceTypeId = ua.NodeId(ua.ObjectIds.HasComponent)
        addnode.TypeDefinition = ua.NodeId(ua.ObjectIds.BaseDataVariableType)
    attrs = ua.VariableAttributes()
    attrs.Description = ua.LocalizedText(qname.Name)
    attrs.DisplayName = ua.LocalizedText(qname.Name)
    if datatype:
        attrs.DataType = datatype
    else:
        attrs.DataType = _guess_datatype(var)

    attrs.Value = var
    if not isinstance(var.Value, (list, tuple)):
        attrs.ValueRank = ua.ValueRank.Scalar
    else:
        if var.Dimensions:
            attrs.ValueRank = len(var.Dimensions)
            attrs.ArrayDimensions = var.Dimensions
    attrs.WriteMask = 0
    attrs.UserWriteMask = 0
    attrs.Historizing = False
    attrs.AccessLevel = ua.AccessLevel.CurrentRead.mask
    attrs.UserAccessLevel = ua.AccessLevel.CurrentRead.mask
    addnode.NodeAttributes = attrs
    results = await server.add_nodes([addnode])
    results[0].StatusCode.check()
    return results[0].AddedNodeId


async def _create_variable_type(server, parentnodeid, nodeid, qname, datatype, value=None):
    addnode = ua.AddNodesItem()
    addnode.RequestedNewNodeId = nodeid
    addnode.BrowseName = qname
    addnode.NodeClass = ua.NodeClass.VariableType
    addnode.ParentNodeId = parentnodeid
    addnode.ReferenceTypeId = ua.NodeId(ua.ObjectIds.HasSubtype)
    # addnode.TypeDefinition = ua.NodeId(ua.ObjectIds.BaseDataVariableType)
    attrs = ua.VariableTypeAttributes()
    attrs.Description = ua.LocalizedText(qname.Name)
    attrs.DisplayName = ua.LocalizedText(qname.Name)
    attrs.DataType = datatype
    attrs.IsAbstract = False
    if value:
        attrs.Value = value
        if isinstance(value, (list, tuple)):
            attrs.ValueRank = ua.ValueRank.OneDimension
        else:
            attrs.ValueRank = ua.ValueRank.Scalar
    # attrs.ArrayDimensions = None
    attrs.WriteMask = 0
    attrs.UserWriteMask = 0
    addnode.NodeAttributes = attrs
    results = await server.add_nodes([addnode])
    results[0].StatusCode.check()
    return results[0].AddedNodeId


async def create_data_type(parent, nodeid, bname, description=None):
    """
    Create a new data type to be used in new variables, etc ..
    arguments are nodeid, browsename
    or namespace index, name
    """
    nodeid, qname = _parse_nodeid_qname(nodeid, bname)

    addnode = ua.AddNodesItem()
    addnode.RequestedNewNodeId = nodeid
    addnode.BrowseName = qname
    addnode.NodeClass = ua.NodeClass.DataType
    addnode.ParentNodeId = parent.nodeid
    addnode.ReferenceTypeId = ua.NodeId(ua.ObjectIds.HasSubtype)
    # addnode.TypeDefinition = ua.NodeId(ua.ObjectIds.BaseDataVariableType) # No type definition for types
    attrs = ua.DataTypeAttributes()
    if description is None:
        attrs.Description = ua.LocalizedText(qname.Name)
    else:
        attrs.Description = ua.LocalizedText(description)
    attrs.DisplayName = ua.LocalizedText(qname.Name)
    attrs.WriteMask = 0
    attrs.UserWriteMask = 0
    attrs.IsAbstract = False  # True mean they cannot be instanciated
    addnode.NodeAttributes = attrs
    results = await parent.server.add_nodes([addnode])
    results[0].StatusCode.check()
    return make_node(parent.server, results[0].AddedNodeId)


async def _create_method(parent, nodeid, qname, callback, inputs, outputs):
    addnode = ua.AddNodesItem()
    addnode.RequestedNewNodeId = nodeid
    addnode.BrowseName = qname
    addnode.NodeClass = ua.NodeClass.Method
    addnode.ParentNodeId = parent.nodeid
    addnode.ReferenceTypeId = ua.NodeId(ua.ObjectIds.HasComponent)
    # node.TypeDefinition = ua.NodeId(ua.ObjectIds.BaseObjectType)
    attrs = ua.MethodAttributes()
    attrs.Description = ua.LocalizedText(qname.Name)
    attrs.DisplayName = ua.LocalizedText(qname.Name)
    attrs.WriteMask = 0
    attrs.UserWriteMask = 0
    attrs.Executable = True
    attrs.UserExecutable = True
    addnode.NodeAttributes = attrs
    results = await parent.server.add_nodes([addnode])
    results[0].StatusCode.check()
    method = make_node(parent.server, results[0].AddedNodeId)
    if inputs:
        await create_property(
            method,
            ua.NodeId(namespaceidx=method.nodeid.NamespaceIndex),
            ua.QualifiedName("InputArguments", 0),
            [_vtype_to_argument(vtype) for vtype in inputs],
            varianttype=ua.VariantType.ExtensionObject,
            datatype=ua.ObjectIds.Argument
        )
    if outputs:
        await create_property(
            method,
            ua.NodeId(namespaceidx=method.nodeid.NamespaceIndex),
            ua.QualifiedName("OutputArguments", 0),
            [_vtype_to_argument(vtype) for vtype in outputs],
            varianttype=ua.VariantType.ExtensionObject,
            datatype=ua.ObjectIds.Argument
        )
    if hasattr(parent.server, "add_method_callback"):
        parent.server.add_method_callback(method.nodeid, callback)
    return results[0].AddedNodeId


def _vtype_to_argument(vtype):
    if isinstance(vtype, ua.Argument):
        return vtype
    arg = ua.Argument()
    if isinstance(vtype, ua.VariantType):
        arg.DataType = ua.NodeId(vtype.value)
    else:
        arg.DataType = ua.NodeId(vtype)
    return arg


def _guess_datatype(variant):
    if variant.VariantType == ua.VariantType.ExtensionObject:
        if variant.Value is None:
            raise ua.UaError("Cannot guess DataType from Null ExtensionObject")
        if type(variant.Value) in (list, tuple):
            if len(variant.Value) == 0:
                raise ua.UaError("Cannot guess DataType from Null ExtensionObject")
            extobj = variant.Value[0]
        else:
            extobj = variant.Value
        classname = extobj.__class__.__name__
        if not hasattr(ua.ObjectIds, classname):
            raise ua.UaError(f"Cannot guess DataType of {variant} of python type {type(variant)}")
        return ua.NodeId(getattr(ua.ObjectIds, classname))
    else:
        return ua.NodeId(getattr(ua.ObjectIds, variant.VariantType.name))


async def delete_nodes(server, nodes, recursive=False, delete_target_references=True):
    """
    Delete specified nodes. Optionally delete recursively all nodes with a
    downward hierachic references to the node
    return the list of deleted node and the result
    """
    nodestodelete = []
    if recursive:
        nodes += await _add_childs(nodes)
    for mynode in nodes:
        it = ua.DeleteNodesItem()
        it.NodeId = mynode.nodeid
        it.DeleteTargetReferences = delete_target_references
        nodestodelete.append(it)
    params = ua.DeleteNodesParameters()
    params.NodesToDelete = nodestodelete
    return nodes, await server.delete_nodes(params)


async def _add_childs(nodes):
    results = []
    for mynode in nodes:
        results += await _add_childs(await mynode.get_children())
        results += [mynode]
    return results
