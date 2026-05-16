from __future__ import annotations

import collections
import xml.etree.ElementTree as ET
from typing import Any


class Node_struct:
    def __init__(self) -> None:
        self.nodeId: str | None = None
        self.browseName: str | None = None
        self.isAbstract: str | None = "true"
        self.parentNodeId: str | None = None
        self.dataType: str | None = None
        self.displayName: str | None = None
        self.description: str | None = None
        self.references: list[Reference] = []
        self.tag: str | None = None

    def __hash__(self) -> int:
        return hash(
            (
                self.nodeId,
                self.browseName,
                self.isAbstract,
                self.parentNodeId,
                self.dataType,
                self.displayName,
                self.description,
                tuple(self.references),
                self.tag,
            )
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Node_struct):
            return NotImplemented
        return (
            self.nodeId,
            self.browseName,
            self.isAbstract,
            self.parentNodeId,
            self.dataType,
            self.displayName,
            self.description,
            self.references,
            self.tag,
        ) == (
            other.nodeId,
            other.browseName,
            other.isAbstract,
            other.parentNodeId,
            other.dataType,
            other.displayName,
            other.description,
            other.references,
            other.tag,
        )

    def __ne__(self, other: object) -> bool:
        return not (self == other)


class Reference:
    def __init__(self) -> None:
        self.referenceType: str | None = None
        self.refId: str | None = None
        self.refBrowseName: str | None = None
        self.refDataType: str | None = None

    def __hash__(self) -> int:
        return hash((self.referenceType, self.refId))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Reference):
            return NotImplemented
        return (self.referenceType, self.refId) == (other.referenceType, other.refId)

    def __ne__(self, other: object) -> bool:
        return not (self == other)


class Model_Event:
    def __init__(self) -> None:
        self.structs: list[Node_struct] = []

    def get_struct(self, nodeId: str) -> Node_struct:
        for struct in self.structs:
            if struct.nodeId == nodeId:
                return struct
        raise Exception("No struct with the Id: " + str(nodeId))


class Parser:
    nameSpace = "{http://opcfoundation.org/UA/2011/03/UANodeSet.xsd}"

    def __init__(self, path: str) -> None:
        self.path = path
        self.model: Model_Event | None = None

    def findNodeWithNodeId(self, root: ET.Element, nodeId: str | None) -> Node_struct:
        node = Node_struct()
        for child in root:
            if nodeId == child.attrib.get("NodeId"):
                # The xml-tag is the type of an xml-element e.g. <Reference> then tag is Reference.
                # The tag also includes the namespace which needs to be removed
                # e.g. '{http://opcfoundation.org/UA/2011/03/UANodeSet.xsd}Reference'
                node.tag = child.tag.split(self.nameSpace)[1]
                node.browseName = str(child.attrib.get("BrowseName"))
                node.nodeId = child.attrib.get("NodeId")
                node.isAbstract = child.attrib.get("IsAbstract")
                node.dataType = child.attrib.get("DataType")
                if node.dataType is None:
                    node.dataType = "Variant"
                dn = child.find(self.nameSpace + "DisplayName")
                node.displayName = dn.text if dn is not None else None
                desc = child.find(self.nameSpace + "Description")
                if desc is not None:
                    node.description = desc.text
                refs_el = child.find(self.nameSpace + "References")
                if refs_el is not None:
                    for ref in refs_el.findall(self.nameSpace + "Reference"):
                        reference = Reference()
                        reference.referenceType = ref.attrib.get("ReferenceType")
                        reference.refId = ref.text
                        if ref.attrib.get("IsForward") is not None:
                            node.parentNodeId = reference.refId
                        node.references.append(reference)
        return node

    def checkNodeType(self, node: Node_struct) -> bool:
        if (
            (node.tag == self.nameSpace + "UAObjectType")
            or (node.tag == self.nameSpace + "UAVariable")
            or (node.tag == self.nameSpace + "UAObject")
            or (node.tag == self.nameSpace + "UAMethod")
            or (node.tag == self.nameSpace + "UAVariableType")
        ):
            return True
        return False

    def parse(self) -> dict[str | None, Node_struct]:
        print("Parsing: " + self.path)
        tree = ET.parse(self.path)
        root = tree.getroot()
        listEventType: dict[str | None, Node_struct] = {}
        for child in root:
            browseName = str(child.attrib.get("BrowseName"))
            if (
                browseName.endswith("EventType")
                or browseName.endswith("ConditionType")
                or browseName.endswith("AlarmType")
            ):
                if browseName == "EventType":
                    continue
                node = Node_struct()
                node.browseName = browseName.replace("Type", "")
                node.nodeId = child.attrib.get("NodeId")
                node.isAbstract = child.attrib.get("IsAbstract")
                dn = child.find(self.nameSpace + "DisplayName")
                node.displayName = dn.text if dn is not None else None
                desc = child.find(self.nameSpace + "Description")
                if desc is not None:
                    node.description = desc.text
                refs_el = child.find(self.nameSpace + "References")
                if refs_el is None:
                    listEventType[node.nodeId] = node
                    continue
                for ref in refs_el.findall(self.nameSpace + "Reference"):
                    reference = Reference()
                    reference.referenceType = ref.attrib.get("ReferenceType")
                    reference.refId = ref.text
                    reference.refBrowseName = self.findNodeWithNodeId(root, reference.refId).browseName
                    reference.refDataType = self.findNodeWithNodeId(root, reference.refId).dataType
                    if ref.attrib.get("IsForward") is not None:
                        node.parentNodeId = reference.refId
                    # ReferenceType is 'HasProperty'  -> There is just a simple PropertyType
                    # ReferenceType is 'HasComponent' -> There is a VariableType with sub-properties
                    if reference.referenceType == "HasComponent":
                        refs_node = self.findNodeWithNodeId(root, reference.refId)
                        if refs_node.tag != "UAVariable":
                            continue
                        # Collect the sub-properties of the VariableType
                        for ref_ in refs_node.references:
                            if ref_.referenceType == "HasProperty":
                                child_ref_node = self.findNodeWithNodeId(root, ref_.refId)
                                subReference = Reference()
                                subReference.referenceType = "HasProperty"
                                subReference.refId = ref_.refId
                                subReference.refBrowseName = (
                                    f"{refs_node.browseName}/{child_ref_node.browseName}"
                                )
                                subReference.refDataType = child_ref_node.dataType
                                node.references.append(subReference)
                    node.references.append(reference)
                listEventType[node.nodeId] = node

        return collections.OrderedDict(
            sorted(sorted(listEventType.items(), key=lambda t: t[0] or ""), key=lambda u: len(u[0] or ""))
        )
