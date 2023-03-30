import logging

from asyncua import ua
from .node_factory import make_node


_logger = logging.getLogger(__name__)


async def copy_node(parent, node, nodeid=None, recursive=True):
    """
    Copy a node or node tree as child of parent node
    """
    rdesc = await _rdesc_from_node(parent, node)
    if nodeid is None:
        nodeid = ua.NodeId(NamespaceIndex=node.nodeid.NamespaceIndex)
    added_nodeids = await _copy_node(parent.session, parent.nodeid, rdesc, nodeid, recursive)
    return [make_node(parent.session, nid) for nid in added_nodeids]


async def _copy_node(session, parent_nodeid, rdesc, nodeid, recursive):
    addnode = ua.AddNodesItem()
    addnode.RequestedNewNodeId = nodeid
    addnode.BrowseName = rdesc.BrowseName
    addnode.ParentNodeId = parent_nodeid
    addnode.ReferenceTypeId = rdesc.ReferenceTypeId
    addnode.TypeDefinition = rdesc.TypeDefinition
    addnode.NodeClass = rdesc.NodeClass
    node_to_copy = make_node(session, rdesc.NodeId)
    attr_obj = getattr(ua, ua.NodeClass(rdesc.NodeClass).name + "Attributes")
    await _read_and_copy_attrs(node_to_copy, attr_obj(), addnode)
    res = (await session.add_nodes([addnode]))[0]
    added_nodes = [res.AddedNodeId]
    if recursive:
        descs = await node_to_copy.get_children_descriptions()
        for desc in descs:
            nodes = await _copy_node(session, res.AddedNodeId, desc,
                                     nodeid=ua.NodeId(NamespaceIndex=desc.NodeId.NamespaceIndex), recursive=True)
            added_nodes.extend(nodes)

    return added_nodes


async def _rdesc_from_node(parent, node):
    results = await node.read_attributes([
        ua.AttributeIds.NodeClass, ua.AttributeIds.BrowseName, ua.AttributeIds.DisplayName,
    ])
    nclass, qname, dname = [res.Value.Value for res in results]
    rdesc = ua.ReferenceDescription()
    rdesc.NodeId = node.nodeid
    rdesc.BrowseName = qname
    rdesc.DisplayName = dname
    rdesc.NodeClass = nclass
    if await parent.read_type_definition() == ua.NodeId(ua.ObjectIds.FolderType):
        rdesc.ReferenceTypeId = ua.NodeId(ua.ObjectIds.Organizes)
    else:
        rdesc.ReferenceTypeId = ua.NodeId(ua.ObjectIds.HasComponent)
    typedef = await node.read_type_definition()
    if typedef:
        rdesc.TypeDefinition = typedef
    return rdesc


async def _read_and_copy_attrs(node_type, struct, addnode):
    names = [name for name in struct.__dict__.keys() if not name.startswith("_") and name not in (
        "BodyLength", "TypeId", "SpecifiedAttributes", "Encoding", "IsAbstract", "EventNotifier",
    )]
    attrs = [getattr(ua.AttributeIds, name) for name in names]
    results = await node_type.read_attributes(attrs)
    for idx, name in enumerate(names):
        if results[idx].StatusCode.is_good():
            if name == "Value":
                setattr(struct, name, results[idx].Value)
            else:
                setattr(struct, name, results[idx].Value.Value)
        else:
            _logger.warning(f"Instantiate: while copying attributes from node type {str(node_type)},"
                           f" attribute {str(name)}, statuscode is {str(results[idx].StatusCode)}")
    addnode.NodeAttributes = struct
