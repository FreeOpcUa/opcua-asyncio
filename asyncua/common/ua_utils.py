"""
Useful methods and classes not belonging anywhere and depending on asyncua library
"""

import uuid
import logging
from datetime import datetime, timezone
from enum import Enum, IntEnum, IntFlag

from dateutil import parser  # type: ignore[attr-defined]

from asyncua import ua

_logger = logging.getLogger(__name__)


def value_to_datavalue(val, varianttype=None):
    """
    convert anything to a DataValue using varianttype
    """
    if isinstance(val, ua.DataValue):
        return val
    if isinstance(val, ua.Variant):
        return ua.DataValue(val, SourceTimestamp=datetime.now(timezone.utc))
    return ua.DataValue(ua.Variant(val, varianttype), SourceTimestamp=datetime.now(timezone.utc))


def val_to_string(val, truncate=False):
    """
    convert a python object or python-asyncua object to a string
    which should be easy to understand for human
    easy to modify, and not too hard to parse back ....not easy
    meant for UI or command lines
    if truncate is true then huge strings or bytes are truncated

    """
    if isinstance(val, (list, tuple)):
        res = []
        for v in val:
            res.append(val_to_string(v))
        return "[{}]".format(", ".join(res))

    if hasattr(val, "to_string"):
        val = val.to_string()
    elif isinstance(val, ua.StatusCode):
        val = val.name
    elif isinstance(val, (Enum, IntEnum, IntFlag)):
        val = val.name
    elif isinstance(val, ua.DataValue):
        val = variant_to_string(val.Value)
    elif isinstance(val, ua.XmlElement):
        val = val.Value
    elif isinstance(val, str):
        if truncate and len(val) > 100:
            val = val[:10] + "...." + val[-10:]
    elif isinstance(val, bytes):
        if truncate and len(val) > 100:
            val = val[:10].decode("utf-8", errors="replace") + "...." + val[-10:].decode("utf-8", errors="replace")
        else:
            val = val.decode("utf-8", errors="replace")
    elif isinstance(val, datetime):
        val = val.isoformat()
    elif isinstance(val, (int, float)):
        val = str(val)
    else:
        # FIXME: Some types are probably missing!
        val = str(val)
    return val


def variant_to_string(var):
    """
    convert a variant to a string which should be easy to understand for human
    easy to modify, and not too hard to parse back ....not easy
    meant for UI or command lines
    """
    return val_to_string(var.Value)


def string_to_val(string, vtype):
    """
    Convert back a string to a python or python-asyncua object
    Note: no error checking is done here, supplying null strings could raise exceptions (datetime and guid)
    """
    string = string.strip()
    if string.startswith("[") and string.endswith("]"):
        string = string[1:-1]
        var = []
        for s in string.split(","):
            s = s.strip()
            val = string_to_val(s, vtype)
            var.append(val)
        return var

    if vtype == ua.VariantType.Null:
        val = None
    elif vtype == ua.VariantType.Boolean:
        if string in ("True", "true", "on", "On", "1"):
            val = True
        else:
            val = False
    elif vtype in (ua.VariantType.SByte, ua.VariantType.Int16, ua.VariantType.Int32, ua.VariantType.Int64):
        if not string:
            val = 0
        else:
            val = int(string)
    elif vtype in (ua.VariantType.Byte, ua.VariantType.UInt16, ua.VariantType.UInt32, ua.VariantType.UInt64):
        if not string:
            val = 0
        else:
            val = int(string)
    elif vtype in (ua.VariantType.Float, ua.VariantType.Double):
        if not string:
            val = 0.0
        else:
            val = float(string)
    elif vtype == ua.VariantType.XmlElement:
        val = ua.XmlElement(string)
    elif vtype == ua.VariantType.String:
        val = string
    elif vtype == ua.VariantType.ByteString:
        val = string.encode()
    elif vtype in (ua.VariantType.NodeId, ua.VariantType.ExpandedNodeId):
        val = ua.NodeId.from_string(string)
    elif vtype == ua.VariantType.QualifiedName:
        val = ua.QualifiedName.from_string(string)
    elif vtype == ua.VariantType.DateTime:
        val = parser.parse(string)
    elif vtype == ua.VariantType.LocalizedText:
        val = ua.LocalizedText.from_string(string)
    elif vtype == ua.VariantType.StatusCode:
        val = ua.StatusCode(string)
    elif vtype == ua.VariantType.Guid:
        val = uuid.UUID(string)
    elif issubclass(vtype, Enum):
        enum_int = int(string.rsplit('_', 1)[1])
        val = vtype(enum_int)
    else:
        # FIXME: Some types are probably missing!
        raise NotImplementedError
    return val


def string_to_variant(string, vtype):
    """
    convert back a string to an ua.Variant
    """
    return ua.Variant(string_to_val(string, vtype), vtype)


async def get_node_children(node, nodes=None):
    """
    Get recursively all children of a node
    """
    if nodes is None:
        nodes = [node]
    for child in await node.get_children():
        nodes.append(child)
        await get_node_children(child, nodes)
    return nodes


async def get_node_subtypes(node, nodes=None):
    if nodes is None:
        nodes = [node]
    for child in await node.get_children(refs=ua.ObjectIds.HasSubtype):
        nodes.append(child)
        await get_node_subtypes(child, nodes)
    return nodes


async def get_node_supertypes(node, includeitself=False, skipbase=True):
    """
    return get all subtype parents of node recursive
    :param node: can be an ua.Node or ua.NodeId
    :param includeitself: include also node to the list
    :param skipbase don't include the toplevel one
    :returns list of ua.Node, top parent first
    """
    parents = []
    if includeitself:
        parents.append(node)
    parents.extend(await _get_node_supertypes(node))
    if skipbase and len(parents) > 1:
        parents = parents[:-1]
    return parents


async def _get_node_supertypes(node):
    """
    recursive implementation of get_node_derived_from_types
    """
    basetypes = []
    parent = await get_node_supertype(node)
    if parent:
        basetypes.append(parent)
        basetypes.extend(await _get_node_supertypes(parent))

    return basetypes


async def get_node_supertype(node):
    """
    return node supertype or None
    """
    supertypes = await node.get_referenced_nodes(
        refs=ua.ObjectIds.HasSubtype, direction=ua.BrowseDirection.Inverse
    )
    if supertypes:
        return supertypes[0]
    return None


async def is_subtype(node, supertype):
    """
    return if a node is a subtype of a specified nodeid
    """
    while node:
        if node.nodeid == supertype:
            return True
        node = await get_node_supertype(node)
    return False


async def is_child_present(node, browsename):
    """
    return if a browsename is present a child from the provide node
    :param node: node wherein to find the browsename
    :param browsename: browsename to search
    :returns returns True if the browsename is present else False
    """
    child_descs = await node.get_children_descriptions()
    for child_desc in child_descs:
        if child_desc.BrowseName == browsename:
            return True
    return False


async def data_type_to_variant_type(dtype_node):
    """
    Given a Node datatype, find out the variant type to encode
    data. This is not exactly straightforward...
    """
    base = await get_base_data_type(dtype_node)
    if base.nodeid.Identifier == 29:
        # we have an enumeration, value is an Int32
        return ua.VariantType.Int32
    elif base.nodeid.Identifier in [24, 26, 27, 28]:
        # BaseDataType, Number, Integer, UInteger -> Variant
        return ua.VariantType.Variant
    return ua.VariantType(base.nodeid.Identifier)


async def get_base_data_type(datatype):
    """
    Looks up the base datatype of the provided datatype Node
    The base datatype is either:
    A primitive type (ns=0, i<=21) or a complex one (ns=0 i>21 and i<30) like Enum and Struct.

    Args:
        datatype: NodeId of a datype of a variable
    Returns:
        NodeId of datatype base or None in case base datype can not be determined
    """
    base = datatype
    while base:
        if base.nodeid.NamespaceIndex == 0 and isinstance(base.nodeid.Identifier, int) and base.nodeid.Identifier < 30:
            return base
        base = await get_node_supertype(base)
    raise ua.UaError(f"Datatype must be a subtype of builtin types {str(datatype)}")


async def get_nodes_of_namespace(server, namespaces=None):
    """
    Get the nodes of one or more namespaces .
    Args:
        server: opc ua server to use
        namespaces: list of string uri or int indexes of the namespace to export
    Returns:
        List of nodes that are part of the provided namespaces
    """
    if namespaces is None:
        namespaces = []
    ns_available = await server.get_namespace_array()

    if not namespaces:
        namespaces = ns_available[1:]
    elif isinstance(namespaces, (str, int)):
        namespaces = [namespaces]

    # make sure all namespace are indexes (if needed, convert strings to indexes)
    namespace_indexes = [n if isinstance(n, int) else ns_available.index(n) for n in namespaces]

    # filter node is based on the provided namespaces and convert the nodeid to a node
    nodes = [
        server.get_node(nodeid) for nodeid in server.iserver.aspace.keys()
        if nodeid.NamespaceIndex != 0 and nodeid.NamespaceIndex in namespace_indexes
    ]
    return nodes


def get_default_value(uatype):
    if isinstance(uatype, ua.VariantType):
        return ua.get_default_value(uatype)
    if hasattr(ua.VariantType, uatype):
        return ua.get_default_value(getattr(ua.VariantType, uatype))
    return getattr(ua, uatype)()


def data_type_to_string(dtype):
    # we could just display browse name of node, but it requires a query
    if dtype.NamespaceIndex == 0 and dtype.Identifier in ua.ObjectIdNames:
        string = ua.ObjectIdNames[dtype.Identifier]
    else:
        string = dtype.to_string()
    return string


def copy_dataclass_attr(dc_source, dc_dest) -> None:
    """
    Copy the common attributes of dc_source to dc_dest
    """
    common_params = set(vars(dc_source)) & set(vars(dc_dest))
    for c in common_params:
        setattr(dc_dest, c, getattr(dc_source, c))
