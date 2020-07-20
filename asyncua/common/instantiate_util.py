"""
Instantiate a new node and its child nodes from a node type.
"""

import logging

from asyncua import ua
from .ua_utils import get_node_supertypes, is_child_present
from .copy_node_util import _rdesc_from_node, _read_and_copy_attrs
from .node_factory import make_node

logger = logging.getLogger(__name__)


async def instantiate(parent, node_type, nodeid=None, bname=None, dname=None, idx=0, instantiate_optional=True):
    """
    instantiate a node type under a parent node.
    nodeid and browse name of new node can be specified, or just namespace index
    If they exists children of the node type, such as components, variables and
    properties are also instantiated
    """
    rdesc = await _rdesc_from_node(parent, node_type)
    rdesc.TypeDefinition = node_type.nodeid

    if nodeid is None:
        nodeid = ua.NodeId(namespaceidx=idx)  # will trigger automatic node generation in namespace idx
    if bname is None:
        bname = rdesc.BrowseName
    elif isinstance(bname, str):
        bname = ua.QualifiedName.from_string(bname)

    nodeids = await _instantiate_node(
        parent.server,
        make_node(parent.server, rdesc.NodeId),
        parent.nodeid,
        rdesc,
        nodeid,
        bname,
        dname=dname,
        instantiate_optional=instantiate_optional)
    return [make_node(parent.server, nid) for nid in nodeids]


async def _instantiate_node(server,
                            node_type,
                            parentid,
                            rdesc,
                            nodeid,
                            bname,
                            dname=None,
                            recursive=True,
                            instantiate_optional=True):
    """
    instantiate a node type under parent
    """
    addnode = ua.AddNodesItem()
    addnode.RequestedNewNodeId = nodeid
    addnode.BrowseName = bname
    addnode.ParentNodeId = parentid
    addnode.ReferenceTypeId = rdesc.ReferenceTypeId
    addnode.TypeDefinition = rdesc.TypeDefinition

    if rdesc.NodeClass in (ua.NodeClass.Object, ua.NodeClass.ObjectType):
        addnode.NodeClass = ua.NodeClass.Object
        await _read_and_copy_attrs(node_type, ua.ObjectAttributes(), addnode)

    elif rdesc.NodeClass in (ua.NodeClass.Variable, ua.NodeClass.VariableType):
        addnode.NodeClass = ua.NodeClass.Variable
        await _read_and_copy_attrs(node_type, ua.VariableAttributes(), addnode)
    elif rdesc.NodeClass in (ua.NodeClass.Method,):
        addnode.NodeClass = ua.NodeClass.Method
        await _read_and_copy_attrs(node_type, ua.MethodAttributes(), addnode)
    elif rdesc.NodeClass in (ua.NodeClass.DataType,):
        addnode.NodeClass = ua.NodeClass.DataType
        await _read_and_copy_attrs(node_type, ua.DataTypeAttributes(), addnode)
    else:
        logger.error("Instantiate: Node class not supported: %s", rdesc.NodeClass)
        raise RuntimeError("Instantiate: Node class not supported")
    if dname is not None:
        addnode.NodeAttributes.DisplayName = dname

    res = (await server.add_nodes([addnode]))[0]
    added_nodes = [res.AddedNodeId]

    if recursive:
        parents = await get_node_supertypes(node_type, includeitself=True)
        node = make_node(server, res.AddedNodeId)
        for parent in parents:
            descs = await parent.get_children_descriptions(includesubtypes=False)
            for c_rdesc in descs:
                # skip items that already exists, prefer the 'lowest' one in object hierarchy
                if not await is_child_present(node, c_rdesc.BrowseName):
                    c_node_type = make_node(server, c_rdesc.NodeId)
                    refs = await c_node_type.get_referenced_nodes(refs=ua.ObjectIds.HasModellingRule)
                    if not refs:
                        # spec says to ignore nodes without modelling rules
                        logger.info("Instantiate: Skip node without modelling rule %s as part of %s",
                                    c_rdesc.BrowseName, addnode.BrowseName)
                        continue
                        # exclude nodes with optional ModellingRule if requested
                    if not instantiate_optional or refs[0].nodeid == ua.NodeId(ua.ObjectIds.ModellingRule_Optional):
                        logger.info("Instantiate: Skip optional node %s as part of %s", c_rdesc.BrowseName,
                                    addnode.BrowseName)
                        continue
                    # if root node being instantiated has a String NodeId, create the children with a String NodeId
                    if res.AddedNodeId.NodeIdType is ua.NodeIdType.String:
                        inst_nodeid = res.AddedNodeId.Identifier + "." + c_rdesc.BrowseName.Name
                        nodeids = await _instantiate_node(
                            server,
                            c_node_type,
                            res.AddedNodeId,
                            c_rdesc,
                            nodeid=ua.NodeId(identifier=inst_nodeid, namespaceidx=res.AddedNodeId.NamespaceIndex),
                            bname=c_rdesc.BrowseName
                        )
                    else:
                        nodeids = await _instantiate_node(
                            server,
                            c_node_type,
                            res.AddedNodeId,
                            c_rdesc,
                            nodeid=ua.NodeId(namespaceidx=res.AddedNodeId.NamespaceIndex),
                            bname=c_rdesc.BrowseName
                        )
                    added_nodes.extend(nodeids)
    return added_nodes
