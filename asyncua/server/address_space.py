from __future__ import annotations

import asyncio
import collections.abc
import dataclasses
import logging
import pickle
import shelve
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Dict, Union
    from collections.abc import Callable, Generator
    from asyncua.ua.uaprotocol_auto import (
        ObjectAttributes,
        DataTypeAttributes,
        ReferenceTypeAttributes,
        VariableTypeAttributes,
        VariableAttributes,
        ObjectTypeAttributes,
    )

    __TYPE_ATTRIBUTES = Union[
        DataTypeAttributes,
        ReferenceTypeAttributes,
        VariableTypeAttributes,
        VariableAttributes,
        ObjectTypeAttributes,
        ObjectAttributes,
    ]  # FIXME Check, if there are missing attribute types.

from asyncua import ua
from asyncua.crypto.permission_rules import User, UserRole


_logger = logging.getLogger(__name__)


class AttributeValue:
    """
    The class holds the value(s) of an attribute and callbacks.
    """

    def __init__(self, value: ua.DataValue):
        self.value: ua.DataValue | None = value
        self.value_callback: Callable[[ua.NodeId, ua.AttributeIds], ua.DataValue] | None = None
        self.value_setter: Callable[[NodeData, ua.AttributeIds, ua.DataValue], None] | None = None
        self.datachange_callbacks = {}

    def __str__(self) -> str:
        return f"AttributeValue({self.value})" if not self.value_callback else f"AttributeValue({self.value_callback})"

    __repr__ = __str__


class NodeData:
    """
    The class is internal to asyncua and holds all the information about a Node.
    """

    def __init__(self, nodeid: ua.NodeId):
        self.nodeid = nodeid
        self.attributes: Dict[ua.AttributeIds, AttributeValue] = {}
        self.references: list[ua.ReferenceDescription] = []
        self.call = None

    def __str__(self) -> str:
        return f"NodeData(id:{self.nodeid}, attrs:{self.attributes}, refs:{self.references})"

    __repr__ = __str__


class AttributeService:
    """
    This class implements the attribute service set defined in the opc ua standard.
    https://reference.opcfoundation.org/v104/Core/docs/Part4/5.10.1/
    """

    def __init__(self, aspace: AddressSpace):
        self.logger = logging.getLogger(__name__)
        self._aspace: AddressSpace = aspace

    def read(self, params: ua.ReadParameters) -> list[ua.DataValue]:
        # self.logger.debug("read %s", params)
        res: list[ua.DataValue] = []
        for readvalue in params.NodesToRead:
            res.append(self._aspace.read_attribute_value(readvalue.NodeId, readvalue.AttributeId))
        return res

    async def write(self, params: ua.WriteParameters, user: User = User(role=UserRole.Admin)) -> list[ua.StatusCode]:
        # self.logger.debug("write %s as user %s", params, user)
        res: list[ua.StatusCode] = []
        for writevalue in params.NodesToWrite:
            if user.role != UserRole.Admin:
                if writevalue.AttributeId != ua.AttributeIds.Value:
                    res.append(ua.StatusCode(ua.StatusCodes.BadUserAccessDenied))
                    continue
                al = self._aspace.read_attribute_value(writevalue.NodeId, ua.AttributeIds.AccessLevel)
                ual = self._aspace.read_attribute_value(writevalue.NodeId, ua.AttributeIds.UserAccessLevel)
                if (
                    al.StatusCode is None
                    or al.Value is None
                    or ual.Value is None
                    or not al.StatusCode.is_good()
                    or not ua.ua_binary.test_bit(al.Value.Value, ua.AccessLevel.CurrentWrite)
                    or not ua.ua_binary.test_bit(ual.Value.Value, ua.AccessLevel.CurrentWrite)
                ):
                    res.append(ua.StatusCode(ua.StatusCodes.BadUserAccessDenied))
                    continue
            if writevalue.AttributeId == ua.AttributeIds.Value and self._aspace.force_server_timestamp:
                dv = dataclasses.replace(
                    writevalue.Value, ServerTimestamp=datetime.now(timezone.utc), ServerPicoseconds=None
                )
            else:
                dv = writevalue.Value
            res.append(await self._aspace.write_attribute_value(writevalue.NodeId, writevalue.AttributeId, dv))
        return res


class ViewService:
    """
    This class implements the view service set defined in the opc ua standard.
    https://reference.opcfoundation.org/v104/Core/docs/Part4/5.8.1/
    """

    def __init__(self, aspace: AddressSpace):
        self.logger = logging.getLogger(__name__)
        self._aspace: AddressSpace = aspace

    def browse(self, params: ua.BrowseParameters) -> list[ua.BrowseResult]:
        # self.logger.debug("browse %s", params)
        res: list[ua.BrowseResult] = []
        for desc in params.NodesToBrowse:
            res.append(self._browse(desc))
        return res

    def _browse(self, desc: ua.BrowseDescription) -> ua.BrowseResult:
        res = ua.BrowseResult()
        if desc.NodeId not in self._aspace:
            res.StatusCode = ua.StatusCode(ua.StatusCodes.BadNodeIdInvalid)
            return res
        node = self._aspace[desc.NodeId]
        for ref in node.references:
            if not self._is_suitable_ref(desc, ref):
                continue
            res.References.append(ref)
        return res

    def _is_suitable_ref(self, desc: ua.BrowseDescription, ref: ua.ReferenceDescription) -> bool:
        if not self._suitable_direction(desc.BrowseDirection, ref.IsForward):
            # self.logger.debug("%s is not suitable due to direction", ref)
            return False
        if not self._suitable_reftype(desc.ReferenceTypeId, ref.ReferenceTypeId, desc.IncludeSubtypes):
            # self.logger.debug("%s is not suitable due to type", ref)
            return False
        if desc.NodeClassMask and ((desc.NodeClassMask & ref.NodeClass) == 0):
            # self.logger.debug("%s is not suitable due to class", ref)
            return False
        # self.logger.debug("%s is a suitable ref for desc %s", ref, desc)
        return True

    def _suitable_reftype(self, ref1: ua.NodeId, ref2: ua.NodeId, subtypes: bool) -> bool:
        if ref1 == ua.NodeId(ua.ObjectIds.Null):
            # If ReferenceTypeId is not specified in the BrowseDescription,
            # all References are returned and includeSubtypes is ignored.
            return True
        if ref1 == ref2:
            return True
        if subtypes and ref2 in self._get_sub_ref(ref1):
            return True
        return False

    def _get_sub_ref(self, ref: ua.NodeId) -> Generator[ua.NodeId, None, None]:
        nodedata = self._aspace.get(ref)
        if nodedata is not None:
            for ref_desc in nodedata.references:
                if ref_desc.ReferenceTypeId == ua.NodeId(ua.ObjectIds.HasSubtype) and ref_desc.IsForward:
                    yield ref_desc.NodeId
                    yield from self._get_sub_ref(ref_desc.NodeId)

    def _suitable_direction(self, direction: ua.BrowseDirection, isforward: bool) -> bool:
        if direction == ua.BrowseDirection.Both:
            return True
        if direction == ua.BrowseDirection.Forward and isforward:
            return True
        if direction == ua.BrowseDirection.Inverse and not isforward:
            return True
        return False

    def translate_browsepaths_to_nodeids(self, browsepaths: list[ua.BrowsePath]) -> list[ua.BrowsePathResult]:
        # self.logger.debug("translate browsepath: %s", browsepaths)
        results: list[ua.BrowsePathResult] = []
        for path in browsepaths:
            results.append(self._translate_browsepath_to_nodeid(path))
        return results

    def _translate_browsepath_to_nodeid(self, path: ua.BrowsePath) -> ua.BrowsePathResult:
        # self.logger.debug("looking at path: %s", path)
        res = ua.BrowsePathResult()
        if not path.RelativePath.Elements[-1].TargetName:
            # OPC UA Part 4: Services, 5.8.4 TranslateBrowsePathsToNodeIds
            # it's unclear if this the check should also handle empty strings
            res.StatusCode = ua.StatusCode(ua.StatusCodes.BadBrowseNameInvalid)
            return res
        if path.StartingNode not in self._aspace:
            res.StatusCode = ua.StatusCode(ua.StatusCodes.BadNodeIdInvalid)
            return res
        target_nodeids = self._navigate(path.StartingNode, path.RelativePath.Elements)
        if not target_nodeids:
            res.StatusCode = ua.StatusCode(ua.StatusCodes.BadNoMatch)
            return res
        for nodeid in target_nodeids:
            target = ua.BrowsePathTarget()
            target.TargetId = nodeid  # FIXME <<<< Type conflict
            target.RemainingPathIndex = ua.Index(4294967295)  # FIXME: magic number, why not Index.MAX?
            res.Targets.append(target)
        # FIXME: might need to order these one way or another
        return res

    def _navigate(self, start_nodeid: ua.NodeId, elements: list[ua.RelativePathElement]) -> list[ua.NodeId]:
        current_nodeids = [start_nodeid]
        for el in elements:
            new_currents = []
            for nodeid in current_nodeids:
                tmp_nodeids = self._find_elements_in_node(el, nodeid)
                new_currents.extend(tmp_nodeids)
            if not new_currents:
                self.logger.info("element %s was not found as child of node %s", el, current_nodeids)
                return []
            current_nodeids = new_currents
        return current_nodeids

    def _find_elements_in_node(self, el: ua.RelativePathElement, nodeid: ua.NodeId) -> list[ua.NodeId]:
        nodedata: NodeData = self._aspace[nodeid]
        nodeids: list[ua.NodeId] = []
        for ref in nodedata.references:
            if ref.BrowseName != el.TargetName:
                continue
            if ref.IsForward == el.IsInverse:
                continue
            if not self._suitable_reftype(el.ReferenceTypeId, ref.ReferenceTypeId, el.IncludeSubtypes):
                continue
            nodeids.append(ref.NodeId)
        return nodeids


class NodeManagementService:
    """
    This class implements the node management service set defined in the opc ua standard.
    https://reference.opcfoundation.org/v105/Core/docs/Part4/5.7.1/
    """

    def __init__(self, aspace: AddressSpace):
        self.logger = logging.getLogger(__name__)
        self._aspace: AddressSpace = aspace

    def add_nodes(
        self, addnodeitems: list[ua.AddNodesItem], user: User = User(role=UserRole.Admin)
    ) -> list[ua.AddNodesResult]:
        results: list[ua.AddNodesResult] = []
        for item in addnodeitems:
            results.append(self._add_node(item, user))
        return results

    def try_add_nodes(
        self, addnodeitems: list[ua.AddNodesItem], user: User = User(role=UserRole.Admin), check: bool = True
    ):
        for item in addnodeitems:
            ret = self._add_node(item, user, check=check)
            if not ret.StatusCode.is_good():
                yield item

    def _add_node(self, item: ua.AddNodesItem, user: User, check: bool = True) -> ua.AddNodesResult:
        # self.logger.debug("Adding node %s %s", item.RequestedNewNodeId, item.BrowseName)
        result = ua.AddNodesResult()

        if not user.role == UserRole.Admin:
            result.StatusCode = ua.StatusCode(ua.StatusCodes.BadUserAccessDenied)
            return result

        if item.RequestedNewNodeId.has_null_identifier():
            # If Identifier of requested NodeId is null we generate a new NodeId using
            # the namespace of the nodeid, this is an extention of the spec to allow
            # to requests the server to generate a new nodeid in a specified namespace
            # self.logger.debug("RequestedNewNodeId has null identifier, generating Identifier")
            item.RequestedNewNodeId = self._aspace.generate_nodeid(
                item.RequestedNewNodeId.NamespaceIndex
            )  # FIXME type conflict
        else:
            if item.RequestedNewNodeId in self._aspace:
                self.logger.warning("AddNodesItem: Requested NodeId %s already exists", item.RequestedNewNodeId)
                result.StatusCode = ua.StatusCode(ua.StatusCodes.BadNodeIdExists)
                return result

        if item.ParentNodeId.is_null():
            # self.logger.info("add_node: while adding node %s, requested parent node is null %s %s",
            # item.RequestedNewNodeId, item.ParentNodeId, item.ParentNodeId.is_null())
            if check:
                result.StatusCode = ua.StatusCode(ua.StatusCodes.BadParentNodeIdInvalid)
                return result

        parentdata = self._aspace.get(item.ParentNodeId)
        if parentdata is None and not item.ParentNodeId.is_null():
            self.logger.info(
                "add_node: while adding node %s, requested parent node %s does not exists",
                item.RequestedNewNodeId,
                item.ParentNodeId,
            )
            result.StatusCode = ua.StatusCode(ua.StatusCodes.BadParentNodeIdInvalid)
            return result

        if item.ParentNodeId in self._aspace:
            # check properties
            for ref in self._aspace[item.ParentNodeId].references:
                if ref.ReferenceTypeId == ua.NodeId(ua.ObjectIds.HasProperty):
                    if item.BrowseName.Name == ref.BrowseName.Name:
                        self.logger.warning(
                            "AddNodesItem: Requested Browsename %s"
                            " already exists in Parent Node. ParentID:%s --- "
                            "ItemId:%s",
                            item.BrowseName.Name,
                            item.ParentNodeId,
                            item.RequestedNewNodeId,
                        )
                        result.StatusCode = ua.StatusCode(ua.StatusCodes.BadBrowseNameDuplicated)
                        return result

        if not item.TypeDefinition.is_null() and item.TypeDefinition not in self._aspace:
            result.StatusCode = ua.StatusCode(ua.StatusCodes.BadTypeDefinitionInvalid)
            return result

        nodedata = NodeData(item.RequestedNewNodeId)

        self._add_node_attributes(nodedata, item, add_timestamps=check)

        # now add our node to db
        self._aspace[nodedata.nodeid] = nodedata

        if parentdata is not None:
            self._add_ref_from_parent(nodedata, item, parentdata)
            self._add_ref_to_parent(nodedata, item, parentdata)

        # add type definition
        if not item.TypeDefinition.is_null():
            self._add_type_definition(nodedata, item)

        result.StatusCode = ua.StatusCode()
        result.AddedNodeId = nodedata.nodeid

        return result

    def _add_node_attributes(self, nodedata: NodeData, item: ua.AddNodesItem, add_timestamps: bool):
        # add common attrs
        nodedata.attributes[ua.AttributeIds.NodeId] = AttributeValue(
            ua.DataValue(ua.Variant(nodedata.nodeid, ua.VariantType.NodeId))
        )
        nodedata.attributes[ua.AttributeIds.BrowseName] = AttributeValue(
            ua.DataValue(ua.Variant(item.BrowseName, ua.VariantType.QualifiedName))
        )
        nodedata.attributes[ua.AttributeIds.NodeClass] = AttributeValue(
            ua.DataValue(ua.Variant(item.NodeClass, ua.VariantType.Int32))
        )
        # add requested attrs
        self._add_nodeattributes(item.NodeAttributes, nodedata, add_timestamps)

    def _add_unique_reference(self, nodedata: NodeData, desc: ua.ReferenceDescription):
        for r in nodedata.references:
            if r.ReferenceTypeId == desc.ReferenceTypeId and r.NodeId == desc.NodeId:
                if r.IsForward != desc.IsForward:
                    self.logger.error("Cannot add conflicting reference %s ", str(desc))
                    return ua.StatusCode(ua.StatusCodes.BadReferenceNotAllowed)
                break  # ref already exists
        else:
            nodedata.references.append(desc)
        return ua.StatusCode()

    def _add_ref_from_parent(self, nodedata, item, parentdata):
        desc = ua.ReferenceDescription()
        desc.ReferenceTypeId = item.ReferenceTypeId
        desc.NodeId = nodedata.nodeid
        desc.NodeClass = item.NodeClass
        desc.BrowseName = item.BrowseName
        desc.DisplayName = item.NodeAttributes.DisplayName
        desc.TypeDefinition = item.TypeDefinition
        desc.IsForward = True  # FIXME in uaprotocol_auto.py
        self._add_unique_reference(parentdata, desc)  # FIXME return StatusCode is not evaluated

    def _add_ref_to_parent(self, nodedata: NodeData, item: ua.AddNodesItem, parentdata: NodeData):
        addref = ua.AddReferencesItem()
        addref.ReferenceTypeId = item.ReferenceTypeId
        addref.SourceNodeId = nodedata.nodeid
        addref.TargetNodeId = item.ParentNodeId
        addref.TargetNodeClass = parentdata.attributes[ua.AttributeIds.NodeClass].value.Value.Value  # type: ignore[union-attr]
        addref.IsForward = False  # FIXME in uaprotocol_auto.py
        self._add_reference_no_check(nodedata, addref)  # FIXME return StatusCode is not evaluated

    def _add_type_definition(self, nodedata: NodeData, item: ua.AddNodesItem):
        addref = ua.AddReferencesItem()
        addref.SourceNodeId = nodedata.nodeid
        addref.IsForward = True  # FIXME in uaprotocol_auto.py
        addref.ReferenceTypeId = ua.NodeId(ua.ObjectIds.HasTypeDefinition)
        addref.TargetNodeId = item.TypeDefinition
        addref.TargetNodeClass = ua.NodeClass.Unspecified
        self._add_reference_no_check(nodedata, addref)  # FIXME return StatusCode is not evaluated

    def delete_nodes(
        self, deletenodeitems: ua.DeleteNodesParameters, user: User = User(role=UserRole.Admin)
    ) -> list[ua.StatusCode]:
        results: list[ua.StatusCode] = []
        for item in deletenodeitems.NodesToDelete:
            results.append(self._delete_node(item, user))
        return results

    def _delete_node(self, item: ua.DeleteNodesItem, user: User) -> ua.StatusCode:
        if user.role != UserRole.Admin:
            return ua.StatusCode(ua.StatusCodes.BadUserAccessDenied)

        if item.NodeId not in self._aspace:
            self.logger.warning("DeleteNodesItem: NodeId %s does not exists", item.NodeId)
            return ua.StatusCode(ua.StatusCodes.BadNodeIdUnknown)

        if item.DeleteTargetReferences:
            for elem in self._aspace.keys():
                for rdesc in self._aspace[elem].references[:]:
                    if rdesc.NodeId == item.NodeId:
                        self._aspace[elem].references.remove(rdesc)

        self._delete_node_callbacks(self._aspace[item.NodeId])

        del self._aspace[item.NodeId]

        return ua.StatusCode()

    def _delete_node_callbacks(self, nodedata: NodeData):
        if ua.AttributeIds.Value in nodedata.attributes:
            for handle, callback in list(nodedata.attributes[ua.AttributeIds.Value].datachange_callbacks.items()):
                try:
                    callback(handle, None, ua.StatusCode(ua.StatusCodes.BadNodeIdUnknown))
                    self._aspace.delete_datachange_callback(handle)
                except Exception as ex:
                    self.logger.exception(
                        "Error calling delete node callback callback %s, %s, %s", nodedata, ua.AttributeIds.Value, ex
                    )

    def add_references(
        self, refs: list[ua.AddReferencesItem], user: User = User(role=UserRole.Admin)
    ):  # FIXME return type
        result = [self._add_reference(ref, user) for ref in refs]
        return result

    def try_add_references(self, refs: list[ua.AddReferencesItem], user: User = User(role=UserRole.Admin)):
        for ref in refs:
            if not self._add_reference(ref, user).is_good():
                yield ref

    def _add_reference(self, addref: ua.AddReferencesItem, user: User) -> ua.StatusCode:
        sourcedata = self._aspace.get(addref.SourceNodeId)
        if sourcedata is None:
            return ua.StatusCode(ua.StatusCodes.BadSourceNodeIdInvalid)
        if addref.TargetNodeId not in self._aspace:
            return ua.StatusCode(ua.StatusCodes.BadTargetNodeIdInvalid)
        if user.role != UserRole.Admin:
            return ua.StatusCode(ua.StatusCodes.BadUserAccessDenied)
        return self._add_reference_no_check(sourcedata, addref)

    def _add_reference_no_check(self, sourcedata: NodeData, addref: ua.AddReferencesItem) -> ua.StatusCode:
        rdesc = ua.ReferenceDescription()
        rdesc.ReferenceTypeId = addref.ReferenceTypeId
        rdesc.IsForward = addref.IsForward
        rdesc.NodeId = addref.TargetNodeId
        if addref.TargetNodeClass == ua.NodeClass.Unspecified:
            rdesc.NodeClass = self._aspace.read_attribute_value(  # type: ignore[union-attr]
                addref.TargetNodeId, ua.AttributeIds.NodeClass
            ).Value.Value
        else:
            rdesc.NodeClass = addref.TargetNodeClass
        bname = self._aspace.read_attribute_value(addref.TargetNodeId, ua.AttributeIds.BrowseName).Value.Value  # type: ignore[union-attr]

        if bname:
            rdesc.BrowseName = bname
        dname = self._aspace.read_attribute_value(addref.TargetNodeId, ua.AttributeIds.DisplayName).Value.Value  # type: ignore[union-attr]
        if dname:
            rdesc.DisplayName = dname
        return self._add_unique_reference(sourcedata, rdesc)

    def delete_references(
        self, refs: list[ua.DeleteReferencesItem], user: User = User(role=UserRole.Admin)
    ) -> list[ua.StatusCode]:
        result: list[ua.StatusCode] = []
        for ref in refs:
            result.append(self._delete_reference(ref, user))
        return result

    def _delete_unique_reference(self, item: ua.DeleteReferencesItem, invert: bool = False) -> ua.StatusCode:
        if invert:
            source, target, forward = item.TargetNodeId, item.SourceNodeId, not item.IsForward
        else:
            source, target, forward = item.SourceNodeId, item.TargetNodeId, item.IsForward
        for rdesc in self._aspace[source].references:
            if rdesc.NodeId == target and rdesc.ReferenceTypeId == item.ReferenceTypeId:
                if rdesc.IsForward == forward:
                    self._aspace[source].references.remove(rdesc)
                    return ua.StatusCode()
        return ua.StatusCode(ua.StatusCodes.BadNotFound)

    def _delete_reference(self, item: ua.DeleteReferencesItem, user: User) -> ua.StatusCode:
        if item.SourceNodeId not in self._aspace:
            return ua.StatusCode(ua.StatusCodes.BadSourceNodeIdInvalid)
        if item.TargetNodeId not in self._aspace:
            return ua.StatusCode(ua.StatusCodes.BadTargetNodeIdInvalid)
        if item.ReferenceTypeId not in self._aspace:
            return ua.StatusCode(ua.StatusCodes.BadReferenceTypeIdInvalid)
        if user.role != UserRole.Admin:
            return ua.StatusCode(ua.StatusCodes.BadUserAccessDenied)

        if item.DeleteBidirectional:
            self._delete_unique_reference(item, True)
        return self._delete_unique_reference(item)

    def _add_node_attr(
        self,
        attributes: __TYPE_ATTRIBUTES,
        nodedata: NodeData,
        name: str,
        vtype: ua.VariantType = None,
        add_timestamps: bool = False,
        is_array: bool = False,
    ):
        if attributes.SpecifiedAttributes & getattr(ua.NodeAttributesMask, name):
            dv = ua.DataValue(
                ua.Variant(getattr(attributes, name), vtype, is_array=is_array),
                SourceTimestamp=datetime.now(timezone.utc) if add_timestamps else None,
                ServerTimestamp=datetime.now(timezone.utc)
                if add_timestamps and self._aspace.force_server_timestamp
                else None,
            )
            nodedata.attributes[getattr(ua.AttributeIds, name)] = AttributeValue(dv)

    def _add_nodeattributes(self, node_attributes: __TYPE_ATTRIBUTES, nodedata: NodeData, add_timestamps: bool):
        self._add_node_attr(node_attributes, nodedata, "AccessLevel", ua.VariantType.Byte)
        self._add_node_attr(node_attributes, nodedata, "ArrayDimensions", ua.VariantType.UInt32, is_array=True)
        self._add_node_attr(node_attributes, nodedata, "BrowseName", ua.VariantType.QualifiedName)
        self._add_node_attr(node_attributes, nodedata, "ContainsNoLoops", ua.VariantType.Boolean)
        self._add_node_attr(node_attributes, nodedata, "DataType", ua.VariantType.NodeId)
        self._add_node_attr(node_attributes, nodedata, "Description", ua.VariantType.LocalizedText)
        self._add_node_attr(node_attributes, nodedata, "DisplayName", ua.VariantType.LocalizedText)
        self._add_node_attr(node_attributes, nodedata, "EventNotifier", ua.VariantType.Byte)
        self._add_node_attr(node_attributes, nodedata, "Executable", ua.VariantType.Boolean)
        self._add_node_attr(node_attributes, nodedata, "Historizing", ua.VariantType.Boolean)
        self._add_node_attr(node_attributes, nodedata, "InverseName", ua.VariantType.LocalizedText)
        self._add_node_attr(node_attributes, nodedata, "IsAbstract", ua.VariantType.Boolean)
        self._add_node_attr(node_attributes, nodedata, "MinimumSamplingInterval", ua.VariantType.Double)
        self._add_node_attr(node_attributes, nodedata, "NodeClass", ua.VariantType.Int32)
        self._add_node_attr(node_attributes, nodedata, "NodeId", ua.VariantType.NodeId)
        self._add_node_attr(node_attributes, nodedata, "Symmetric", ua.VariantType.Boolean)
        self._add_node_attr(node_attributes, nodedata, "UserAccessLevel", ua.VariantType.Byte)
        self._add_node_attr(node_attributes, nodedata, "UserExecutable", ua.VariantType.Boolean)
        self._add_node_attr(node_attributes, nodedata, "UserWriteMask", ua.VariantType.Byte)
        self._add_node_attr(node_attributes, nodedata, "ValueRank", ua.VariantType.Int32)
        self._add_node_attr(node_attributes, nodedata, "WriteMask", ua.VariantType.UInt32)
        self._add_node_attr(node_attributes, nodedata, "UserWriteMask", ua.VariantType.UInt32)
        self._add_node_attr(node_attributes, nodedata, "DataTypeDefinition", ua.VariantType.ExtensionObject)
        self._add_node_attr(node_attributes, nodedata, "Value", add_timestamps=add_timestamps)


class MethodService:
    """
    This class implements the method service set defined in the opc ua standard.
    https://reference.opcfoundation.org/v104/Core/docs/Part4/5.11.1/
    """

    def __init__(self, aspace: AddressSpace):
        self.logger = logging.getLogger(__name__)
        self._aspace: AddressSpace = aspace
        self._pool = ThreadPoolExecutor()

    def stop(self):
        self._pool.shutdown()

    async def call(self, methods):
        results = []
        for method in methods:
            res = await self._call(method)
            results.append(res)
        return results

    async def _call(self, method):
        self.logger.info("Calling: %s", method)
        res = ua.CallMethodResult()
        if method.ObjectId not in self._aspace or method.MethodId not in self._aspace:
            res.StatusCode = ua.StatusCode(ua.StatusCodes.BadNodeIdInvalid)
        else:
            node = self._aspace[method.MethodId]
            if node.call is None:
                res.StatusCode = ua.StatusCode(ua.StatusCodes.BadNothingToDo)
            else:
                try:
                    if method.InputArguments is None:
                        # An array value can also be None
                        method.InputArguments = []
                    result = await self._run_method(node.call, method.ObjectId, *method.InputArguments)
                except Exception:
                    self.logger.exception("Error executing method call %s, an exception was raised: ", method)
                    res.StatusCode = ua.StatusCode(ua.StatusCodes.BadUnexpectedError)
                else:
                    if isinstance(result, ua.CallMethodResult):
                        res = result
                    elif isinstance(result, ua.StatusCode):
                        res.StatusCode = result
                    else:
                        res.OutputArguments = result
                    while len(res.InputArgumentResults) < len(method.InputArguments):
                        res.InputArgumentResults.append(ua.StatusCode())
        return res

    async def _run_method(self, func, parent, *args):
        if asyncio.iscoroutinefunction(func):
            return await func(parent, *args)
        p = partial(func, parent, *args)
        res = await asyncio.get_event_loop().run_in_executor(self._pool, p)
        return res


class AddressSpace:
    """
    The address space object stores all the nodes of the OPC-UA server and helper methods.
    The methods are thread safe

    https://reference.opcfoundation.org/Core/docs/Part3/
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.force_server_timestamp: bool = True
        self._nodes: Dict[ua.NodeId, NodeData] = {}
        self._datachange_callback_counter = 200
        self._handle_to_attribute_map: Dict[int, tuple[ua.NodeId, ua.AttributeIds]] = {}
        self._default_idx = 2
        self._nodeid_counter = {0: 20000, 1: 2000}

    def __getitem__(self, nodeid: ua.NodeId) -> NodeData:
        return self._nodes.__getitem__(nodeid)

    def get(self, nodeid: ua.NodeId) -> Union[NodeData, None]:
        return self._nodes.get(
            nodeid, None
        )  # Fixme This is another behaviour than __getitem__ where an KeyError exception is thrown, right?

    def __setitem__(self, nodeid: ua.NodeId, value: NodeData):
        return self._nodes.__setitem__(nodeid, value)

    def __contains__(self, nodeid: ua.NodeId) -> bool:
        return self._nodes.__contains__(nodeid)

    def __delitem__(self, nodeid: ua.NodeId):
        self._nodes.__delitem__(nodeid)

    def generate_nodeid(self, idx: Union[int, None] = None) -> ua.NodeId:
        if idx is None:
            idx = self._default_idx
        if idx in self._nodeid_counter:
            self._nodeid_counter[idx] += 1
        else:
            # get the biggest identifier number from the existed nodes in address space
            identifier_list = sorted(  # type: ignore
                [
                    nodeid.Identifier
                    for nodeid in self._nodes.keys()
                    if nodeid.NamespaceIndex == idx
                    and nodeid.NodeIdType in (ua.NodeIdType.Numeric, ua.NodeIdType.TwoByte, ua.NodeIdType.FourByte)
                ]
            )
            if identifier_list:
                self._nodeid_counter[idx] = identifier_list[-1]
            else:
                self._nodeid_counter[idx] = 1
        nodeid = ua.NodeId(self._nodeid_counter[idx], idx)
        while True:
            if nodeid in self._nodes:
                nodeid = self.generate_nodeid(idx)
            else:
                return nodeid

    def keys(self):
        return self._nodes.keys()

    def clear(self):
        """Delete all nodes in address space"""
        self._nodes.clear()

    def dump(self, path):
        """
        Dump address space as binary to file; note that server must be stopped for this method to work
        DO NOT DUMP AN ADDRESS SPACE WHICH IS USING A SHELF (load_aspace_shelf), ONLY CACHED NODES WILL GET DUMPED!
        """
        self.__prepare_nodes_for_dump()

        with open(path, "wb") as f:
            pickle.dump(self._nodes, f, pickle.HIGHEST_PROTOCOL)

    def __prepare_nodes_for_dump(self):
        """
        Removes unserialisable data from nodes.
        * function calls
        """
        for nodeid, ndata in self._nodes.items():
            # if the node has a reference to a method call, remove it so the object can be serialized
            if ndata.call is not None:
                self._nodes[nodeid].call = None

    def load(self, path):
        """
        Load address space from a binary file, overwriting everything in the current address space
        """
        with open(path, "rb") as f:
            self._nodes = pickle.load(f)

    def make_aspace_shelf(self, path: Path):
        """
        Make a shelf for containing the nodes from the standard address space; this is typically only done on first
        start of the server. Subsequent server starts will load the shelf, nodes are then moved to a cache
        by the LazyLoadingDict class when they are accessed. Saving data back to the shelf
        is currently NOT supported, it is only used for the default OPC UA standard address space

        Note: Intended for slow devices, such as Raspberry Pi, to greatly improve start up time
        """
        with shelve.open(str(path), "n", protocol=pickle.HIGHEST_PROTOCOL) as s:
            for nodeid, ndata in self._nodes.items():
                s[nodeid.to_string()] = ndata

    def load_aspace_shelf(self, path: Path):
        """
        Load the standard address space nodes from a python shelve via LazyLoadingDict as needed.
        The dump() method can no longer be used if the address space is being loaded from a shelf

        Note: Intended for slow devices, such as Raspberry Pi, to greatly improve start up time
        """

        class LazyLoadingDict(collections.abc.MutableMapping):
            """
            Special dict that only loads nodes as they are accessed. If a node is accessed it gets copied from the
            shelf to the cache dict. All user nodes are saved in the cache ONLY. Saving data back to the shelf
            is currently NOT supported
            """

            def __init__(self, source: shelve.Shelf):
                self.source: shelve.Shelf = source  # python shelf
                self.cache = {}  # internal dict

            def __getitem__(self, key):
                # try to get the item (node) from the cache, if it isn't there get it from the shelf
                try:
                    return self.cache[key]
                except KeyError:
                    node = self.cache[key] = self.source[key.to_string()]
                    return node

            def __setitem__(self, key, value):
                # add a new item to the cache; if this item is in the shelf it is not updated
                self.cache[key] = value

            def __contains__(self, key):
                return key in self.cache or key.to_string() in self.source

            def __delitem__(self, key):
                # only deleting items from the cache is allowed
                del self.cache[key]

            def __iter__(self):
                # only the cache can be iterated over
                return iter(self.cache.keys())

            def __len__(self):
                # only returns the length of items in the cache, not unaccessed items in the shelf
                return len(self.cache)

        self._nodes = LazyLoadingDict(shelve.open(str(path), "r"))

    def read_attribute_value(self, nodeid: ua.NodeId, attr: ua.AttributeIds) -> ua.DataValue:
        # self.logger.debug("get attr val: %s %s", nodeid, attr)
        if nodeid not in self._nodes:
            dv = ua.DataValue(StatusCode_=ua.StatusCode(ua.StatusCodes.BadNodeIdUnknown))
            return dv
        node = self._nodes[nodeid]
        if attr not in node.attributes:
            dv = ua.DataValue(StatusCode_=ua.StatusCode(ua.StatusCodes.BadAttributeIdInvalid))
            return dv
        attval = node.attributes[attr]
        # TODO: async support by using asyncio.iscoroutinefunction()
        if attval.value_callback:
            return attval.value_callback(nodeid, attr)
        return attval.value  # type: ignore[return-value] # .value must be filled

    async def write_attribute_value(
        self, nodeid: ua.NodeId, attr: ua.AttributeIds, value: ua.DataValue
    ) -> ua.StatusCode:
        # self.logger.debug("set attr val: %s %s %s", nodeid, attr, value)
        node = self._nodes.get(nodeid, None)
        if node is None:
            return ua.StatusCode(ua.StatusCodes.BadNodeIdUnknown)
        attval = node.attributes.get(attr, None)
        if attval is None:
            return ua.StatusCode(ua.StatusCodes.BadAttributeIdInvalid)
        if value.StatusCode is not None and value.StatusCode.is_bad():
            # https://reference.opcfoundation.org/v104/Core/docs/Part4/7.7.1/
            # If the StatusCode indicates an error then the value is to be ignored and the Server shall set it to null.
            value = dataclasses.replace(value, Value=ua.Variant(None, ua.VariantType.Null))
        elif not self._is_expected_variant_type(value, attval, node):
            # Only check datatype if no bad StatusCode is set
            return ua.StatusCode(ua.StatusCodes.BadTypeMismatch)

        if attval.value_setter is not None:
            attval.value_setter(node, attr, value)
        else:
            attval.value = value
            attval.value_callback = None

        for k, v in attval.datachange_callbacks.items():
            try:
                await v(k, value)
            except Exception as ex:
                self.logger.exception("Error calling datachange callback %s, %s, %s", k, v, ex)

        return ua.StatusCode()

    def _is_expected_variant_type(self, value: ua.DataValue, attval: AttributeValue, node: NodeData) -> bool:
        if attval.value is None:
            return True  # None data value can be overwritten anytime.

        # FIXME Type hinting reveals that it is possible that Value (Optional) is None which would raise an exception
        vtype = attval.value.Value.VariantType  # type: ignore[union-attr]
        if vtype == ua.VariantType.Null:
            # Node had a null value, many nodes are initialized with that value
            # we should check what the real type is
            dtype = node.attributes[ua.AttributeIds.DataType].value.Value.Value  # type: ignore[union-attr]
            if dtype.NamespaceIndex == 0 and dtype.Identifier <= 25:
                vtype = ua.VariantType(dtype.Identifier)
            else:
                # FIXME: should find the correct variant type given data type but
                # this is a bit complicaed so trusting the first write
                return True
        if value.Value.VariantType == vtype:  # type: ignore[union-attr]
            return True
        _logger.warning(
            "Write refused: Variant: %s with type %s does not have expected type: %s",
            value.Value,
            value.Value.VariantType if value.Value else None,
            attval.value.Value.VariantType if attval.value.Value else None,
        )
        return False

    def set_attribute_value_callback(
        self,
        nodeid: ua.NodeId,
        attr: ua.AttributeIds,
        callback: Callable[[ua.NodeId, ua.AttributeIds], ua.DataValue],
    ) -> ua.StatusCode:
        node = self._nodes.get(nodeid, None)
        if node is None:
            return ua.StatusCode(ua.StatusCodes.BadNodeIdUnknown)
        attval = node.attributes.get(attr, None)
        if attval is None:
            return ua.StatusCode(ua.StatusCodes.BadAttributeIdInvalid)

        attval.value = None
        attval.value_callback = callback

        # Note: It does not trigger the datachange_callbacks unlike write_attribute_value.

        return ua.StatusCode()

    def set_attribute_value_setter(
        self,
        nodeid: ua.NodeId,
        attr: ua.AttributeIds,
        setter: Callable[[NodeData, ua.AttributeIds], ua.DataValue],
    ) -> ua.StatusCode:
        node = self._nodes.get(nodeid, None)
        if node is None:
            return ua.StatusCode(ua.StatusCodes.BadNodeIdUnknown)
        attval = node.attributes.get(attr, None)
        if attval is None:
            return ua.StatusCode(ua.StatusCodes.BadAttributeIdInvalid)
        attval.value_setter = setter
        return ua.StatusCode()

    def add_datachange_callback(
        self, nodeid: ua.NodeId, attr: ua.AttributeIds, callback: Callable
    ) -> tuple[ua.StatusCode, int]:
        # self.logger.debug("set attr callback: %s %s %s", nodeid, attr, callback)
        if nodeid not in self._nodes:
            return ua.StatusCode(ua.StatusCodes.BadNodeIdUnknown), 0
        node = self._nodes[nodeid]
        if attr not in node.attributes:
            return ua.StatusCode(ua.StatusCodes.BadAttributeIdInvalid), 0
        attval = node.attributes[attr]
        self._datachange_callback_counter += 1
        handle = self._datachange_callback_counter
        attval.datachange_callbacks[handle] = callback
        self._handle_to_attribute_map[handle] = (nodeid, attr)
        return ua.StatusCode(), handle

    def delete_datachange_callback(self, handle: int):
        if handle in self._handle_to_attribute_map:
            nodeid, attr = self._handle_to_attribute_map.pop(handle)
            self._nodes[nodeid].attributes[attr].datachange_callbacks.pop(handle)

    def add_method_callback(self, methodid: ua.NodeId, callback: Callable):
        node = self._nodes[methodid]
        node.call = callback
