import xml.etree.ElementTree as ET
import collections


class Node_struct:

    def __init__(self):
        self.nodeId = None
        self.browseName = None
        self.isAbstract = True
        self.parentNodeId = None
        self.dataType = None
        self.displayName = None
        self.description = None
        self.references = []
        self.tag = None

    def __hash__(self):
        return hash(self.nodeId, self.browseName, self.isAbstract, self.parentNodeId, self.dataType, self.displayName,
                    self.description, self.references, self.tag)

    def __eq__(self, other):
        return (self.nodeId, self.browseName, self.isAbstract, self.parentNodeId, self.dataType, self.displayName,
                self.description, self.references, self.tag) == (
               other.nodeId, other.browseName, other.isAbstract, other.parentNodeId, other.dataType, other.displayName,
               other.description, other.references, other.tag)

    def __ne__(self, other):
        return not (self == other)


class Reference:
    def __init__(self):
        self.referenceType = None
        self.refId = None

    def __hash__(self):
        return hash(self.referenceType, self.refId)

    def __eq__(self, other):
        return (self.referenceType, self.refId) == (other.referenceType, other.refValue)

    def __ne__(self, other):
        return not (self == other)


class Model_Event:
    def __init__(self):
        self.structs = []

    def get_struct(self, nodeId):
        for struct in self.structs:
            if struct.nodeId == nodeId:
                return struct
        raise Exception("No struct with the Id: " + str(nodeId))


class Parser(object):
    nameSpace = "{http://opcfoundation.org/UA/2011/03/UANodeSet.xsd}"

    def __init__(self, path):
        self.path = path
        self.model = None

    def findNodeWithNodeId(self, root, nodeId):
        node = Node_struct()
        for child in root:
            if nodeId == child.attrib.get('NodeId'):
                # The xml-tag is the type of an xml-element e.g. <Reference> then tag is Reference. 
                # The tag also includes the namespace which needs to be removed 
                # e.g. '{http://opcfoundation.org/UA/2011/03/UANodeSet.xsd}Reference'
                node.tag = child.tag.split(self.nameSpace)[1]
                node.browseName = str(child.attrib.get('BrowseName'))
                node.nodeId = child.attrib.get('NodeId')
                node.isAbstract = child.attrib.get('IsAbstract')
                node.dataType = child.attrib.get('DataType')
                if node.dataType is None:
                    node.dataType = 'Variant'
                node.displayName = child.find(self.nameSpace + 'DisplayName').text
                if child.find(self.nameSpace + 'Description') is not None:
                    node.description = child.find(self.nameSpace + 'Description').text
                for ref in child.find(self.nameSpace + 'References').findall(self.nameSpace + 'Reference'):
                    reference = Reference()
                    reference.referenceType = ref.attrib.get('ReferenceType')
                    reference.refId = ref.text
                    if ref.attrib.get('IsForward') != None:
                        node.parentNodeId = reference.refId
                    node.references.append(reference)
        return node

    def checkNodeType(self, node):
        if (
                (node.tag == self.nameSpace + "UAObjectType") or
                (node.tag == self.nameSpace + "UAVariable") or
                (node.tag == self.nameSpace + "UAObject") or
                (node.tag == self.nameSpace + "UAMethod") or
                (node.tag == self.nameSpace + "UAVariableType")):
            return True

    def parse(self):
        print("Parsing: " + self.path)
        tree = ET.parse(self.path)
        root = tree.getroot()
        listEventType = {}
        for child in root:
            browseName = str(child.attrib.get('BrowseName'))
            if browseName.endswith("EventType") or browseName.endswith("ConditionType") or \
                    browseName.endswith("AlarmType"):
                if browseName == "EventType":
                    continue
                node = Node_struct()
                node.browseName = browseName.replace("Type", "")
                node.nodeId = child.attrib.get('NodeId')
                node.isAbstract = child.attrib.get('IsAbstract')
                node.displayName = child.find(self.nameSpace + 'DisplayName').text
                if child.find(self.nameSpace + 'Description') is not None:
                    node.description = child.find(self.nameSpace + 'Description').text
                for ref in child.find(self.nameSpace + 'References').findall(self.nameSpace + 'Reference'):
                    reference = Reference()
                    reference.referenceType = ref.attrib.get('ReferenceType')
                    reference.refId = ref.text
                    reference.refBrowseName = self.findNodeWithNodeId(root, reference.refId).browseName
                    reference.refDataType = self.findNodeWithNodeId(root, reference.refId).dataType
                    if ref.attrib.get('IsForward') is not None:
                        node.parentNodeId = reference.refId
                    # ReferenceType is 'HasProperty'  -> There is just a simple PropertyType
                    # ReferenceType is 'HasComponent' -> There is a VariableType with sub-properties
                    if reference.referenceType == 'HasComponent':
                        refs_node = self.findNodeWithNodeId(root, reference.refId)
                        if refs_node.tag != 'UAVariable':
                            continue
                        # Collect the sub-properties of the VariableType
                        for ref in refs_node.references:
                            if ref.referenceType == 'HasProperty':
                                child_ref_node = self.findNodeWithNodeId(root, ref.refId)
                                subReference = Reference()
                                subReference.referenceType = 'HasProperty'
                                subReference.refId = ref.refId
                                subReference.refBrowseName = refs_node.browseName + '/' + child_ref_node.browseName
                                subReference.refDataType = child_ref_node.dataType
                                node.references.append(subReference)
                    node.references.append(reference)
                listEventType.update({node.nodeId: node})

        return collections.OrderedDict(
            sorted(sorted(listEventType.items(), key=lambda t: t[0]), key=lambda u: len(u[0])))
