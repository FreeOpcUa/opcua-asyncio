"""
Instantiate a new node and its child nodes from a node type.
"""

import logging

from typing import Union, List

from asyncua import ua
from .ua_utils import get_node_supertypes, is_child_present
from .copy_node_util import _rdesc_from_node, _read_and_copy_attrs
from .node_factory import make_node

_logger = logging.getLogger(__name__)


async def is_abstract(node_type) -> bool:
    result = await node_type.read_attribute(ua.AttributeIds.IsAbstract)
    return result.Value.Value


async def instantiate(parent, node_type, nodeid: ua.NodeId=None, bname: Union[str, ua.QualifiedName]=None, dname: ua.LocalizedText=None, idx: int=0, instantiate_optional: bool=True,
                      instantiate_optional_list: List[Union[str, ua.QualifiedName]]=None):
    """
    instantiate a node type under a parent node.
    nodeid and browse name of new node can be specified, or just namespace index
    If they exists children of the node type, such as components, variables and
    properties are also instantiated
    instantiate_optional: instantiate all optional nodes
    instantiate_optional_list: list of optinal nodes to instantiate
    """
    instante_list = []
    if instantiate_optional_list is not None:
        for optional in instantiate_optional_list:
            if isinstance(optional, ua.QualifiedName):
                instante_list.append(optional)
            else:
                instante_list.append(ua.QualifiedName.from_string(optional))
    rdesc = await _rdesc_from_node(parent, node_type)
    rdesc.TypeDefinition = node_type.nodeid
    if rdesc.NodeClass in (ua.NodeClass.DataType, ua.NodeClass.ReferenceType, ua.NodeClass.ObjectType, ua.NodeClass.ReferenceType):
        # Only some nodes can be abstract
        abstract = await is_abstract(node_type)
        if abstract:
            raise ua.UaError(f"InstantiationError NodeId: {node_type.nodeid} is abstract and cant be instantiated!")
    if nodeid is None:
        nodeid = ua.NodeId(NamespaceIndex=idx)  # will trigger automatic node generation in namespace idx
    if bname is None:
        bname = rdesc.BrowseName
    elif isinstance(bname, str):
        bname = ua.QualifiedName.from_string(bname)

    nodeids = await _instantiate_node(
        parent.session,
        make_node(parent.session, rdesc.NodeId),
        parent.nodeid,
        rdesc,
        nodeid,
        bname,
        dname=dname,
        instantiate_optional=instantiate_optional,
        instantiate_optional_list=instante_list)
    return [make_node(parent.session, nid) for nid in nodeids]


async def _instantiate_node(session,
                            node_type,
                            parentid,
                            rdesc,
                            nodeid,
                            bname,
                            dname=None,
                            recursive=True,
                            instantiate_optional=True,
                            instantiate_optional_list=None):
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
        _logger.error("Instantiate: Node class not supported: %s", rdesc.NodeClass)
        raise RuntimeError("Instantiate: Node class not supported")
    if dname is not None:
        addnode.NodeAttributes.DisplayName = dname

    res = (await session.add_nodes([addnode]))[0]
    added_nodes = [res.AddedNodeId]

    if recursive:
        parents = await get_node_supertypes(node_type, includeitself=True)
        node = make_node(session, res.AddedNodeId)
        for parent in parents:
            descs = await parent.get_children_descriptions()
            for c_rdesc in descs:
                # skip items that already exists, prefer the 'lowest' one in object hierarchy
                if not await is_child_present(node, c_rdesc.BrowseName):
                    c_node_type = make_node(session, c_rdesc.NodeId)
                    refs = await c_node_type.get_referenced_nodes(refs=ua.ObjectIds.HasModellingRule)
                    if not refs:
                        # spec says to ignore nodes without modelling rules
                        _logger.info("Instantiate: Skip node without modelling rule %s as part of %s",
                                    c_rdesc.BrowseName, addnode.BrowseName)
                        continue
                        # exclude nodes with optional ModellingRule if requested
                    if refs[0].nodeid in (ua.NodeId(ua.ObjectIds.ModellingRule_Optional), ua.NodeId(ua.ObjectIds.ModellingRule_OptionalPlaceholder)):
                        # instatiate optionals
                        if not instantiate_optional or c_rdesc.BrowseName not in instantiate_optional_list:
                            _logger.info("Instantiate: Skip optional node %s as part of %s", c_rdesc.BrowseName,
                                addnode.BrowseName)
                            continue
                    # if root node being instantiated has a String NodeId, create the children with a String NodeId
                    if res.AddedNodeId.NodeIdType is ua.NodeIdType.String:
                        inst_nodeid = res.AddedNodeId.Identifier + "." + c_rdesc.BrowseName.Name
                        nodeids = await _instantiate_node(
                            session,
                            c_node_type,
                            res.AddedNodeId,
                            c_rdesc,
                            nodeid=ua.NodeId(Identifier=inst_nodeid, NamespaceIndex=res.AddedNodeId.NamespaceIndex),
                            bname=c_rdesc.BrowseName,
                            instantiate_optional=instantiate_optional
                        )
                    else:
                        nodeids = await _instantiate_node(
                            session,
                            c_node_type,
                            res.AddedNodeId,
                            c_rdesc,
                            nodeid=ua.NodeId(NamespaceIndex=res.AddedNodeId.NamespaceIndex),
                            bname=c_rdesc.BrowseName,
                            instantiate_optional=instantiate_optional,
                            instantiate_optional_list=instantiate_optional_list
                        )
                    added_nodes.extend(nodeids)
    return added_nodes
