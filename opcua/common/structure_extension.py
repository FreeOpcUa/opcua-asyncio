from opcua import ua
from enum import Enum

import xml.etree.ElementTree as Et
import re

# Indicates which type should be OPC build in types
_ua_build_in_types = [ua_type for ua_type in ua.VariantType.__members__ if ua_type != 'ExtensionObject']


def _repl_func(m):
    """
    taken from
     https://stackoverflow.com/questions/1549641/how-to-capitalize-the-first-letter-of-each-word-in-a-string-python
     """
    return m.group(1) + m.group(2).upper()


def _to_camel_case(name):
    """
    Create python class name from an arbitrary string to CamelCase string
    e.g.                 actionlib/TestAction -> ActionlibTestAction
         turtle_actionlib/ShapeActionFeedback -> TurtleActionlibShapeActionFeedback
    """
    name = re.sub(r'[^a-zA-Z0-9]+', ' ', name)
    name = re.sub('(^|\s)(\S)', _repl_func, name)
    name = name.replace(' ', '')
    return name


class OPCTypeDictionaryBuilder:

    def __init__(self, idx_name):
        """
        :param idx_name: name of the name space
        types in dict is created as opc:xxx, otherwise as tns:xxx
        """
        head_attributes = {'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance', 'xmlns:tns': idx_name,
                           'DefaultByteOrder': 'LittleEndian', 'xmlns:opc': 'http://opcfoundation.org/BinarySchema/',
                           'xmlns:ua': 'http://opcfoundation.org/UA/', 'TargetNamespace': idx_name}

        self.etree = Et.ElementTree(Et.Element('opc:TypeDictionary', head_attributes))

        name_space = Et.SubElement(self.etree.getroot(), 'opc:Import')
        name_space.attrib['Namespace'] = 'http://opcfoundation.org/UA/'

        self._structs_dict = {}
        self._build_in_list = _ua_build_in_types
    
    def _process_type(self, type_name):
        if type_name in self._build_in_list:
            type_name = 'opc:' + type_name
        else:
            type_name = 'tns:' + _to_camel_case(type_name)
        return type_name

    def _add_field(self, type_name, variable_name, struct_name):
        type_name = self._process_type(type_name)
        field = Et.SubElement(self._structs_dict[struct_name], 'opc:Field')
        field.attrib['Name'] = variable_name
        field.attrib['TypeName'] = type_name

    def _add_array_field(self, type_name, variable_name, struct_name):
        type_name = self._process_type(type_name)
        array_len = 'NoOf' + variable_name
        field = Et.SubElement(self._structs_dict[struct_name], 'opc:Field')
        field.attrib['Name'] = array_len
        field.attrib['TypeName'] = 'opc:Int32'
        field = Et.SubElement(self._structs_dict[struct_name], 'opc:Field')
        field.attrib['Name'] = variable_name
        field.attrib['TypeName'] = type_name
        field.attrib['LengthField'] = array_len

    def add_field(self, type_name, variable_name, struct_name, is_array=False):
        if isinstance(type_name, Enum):
            type_name = type_name.name
        if is_array:
            self._add_array_field(type_name, variable_name, struct_name)
        else:
            self._add_field(type_name, variable_name, struct_name)

    def append_struct(self, name):
        appended_struct = Et.SubElement(self.etree.getroot(), 'opc:StructuredType')
        appended_struct.attrib['BaseType'] = 'ua:ExtensionObject'
        appended_struct.attrib['Name'] = _to_camel_case(name)
        self._structs_dict[name] = appended_struct
        return appended_struct

    def get_dict_value(self):
        self.indent(self.etree.getroot())
        # For debugging
        # Et.dump(self.etree.getroot())
        return Et.tostring(self.etree.getroot(), encoding='utf-8')

    def indent(self, elem, level=0):
        i = '\n' + level * '  '
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + '  '
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self.indent(elem, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i


def _reference_generator(source_id, target_id, reference_type, is_forward=True):
    ref = ua.AddReferencesItem()
    ref.IsForward = is_forward
    ref.ReferenceTypeId = reference_type
    ref.SourceNodeId = source_id
    ref.TargetNodeClass = ua.NodeClass.DataType
    ref.TargetNodeId = target_id
    return ref


class DataTypeDictionaryBuilder:

    def __init__(self, server, idx, idx_name, dict_name):
        self._server = server
        self._session_server = server.get_root_node().server
        self._idx = idx
        # Risk of bugs using a fixed number without checking
        self._id_counter = 8000
        self.dict_id = self._add_dictionary(dict_name)
        self._type_dictionary = OPCTypeDictionaryBuilder(idx_name)

    def _add_dictionary(self, name):
        dictionary_node_id = self._nodeid_generator()
        node = ua.AddNodesItem()
        node.RequestedNewNodeId = dictionary_node_id
        node.BrowseName = ua.QualifiedName(name, self._idx)
        node.NodeClass = ua.NodeClass.Variable
        node.ParentNodeId = ua.NodeId(ua.ObjectIds.OPCBinarySchema_TypeSystem, 0)
        node.ReferenceTypeId = ua.NodeId(ua.ObjectIds.HasComponent, 0)
        node.TypeDefinition = ua.NodeId(ua.ObjectIds.DataTypeDictionaryType, 0)
        attrs = ua.VariableAttributes()
        attrs.DisplayName = ua.LocalizedText(name)
        attrs.DataType = ua.NodeId(ua.ObjectIds.ByteString)
        # Value should be set after all data types created by calling set_dict_byte_string
        attrs.Value = ua.Variant(None, ua.VariantType.Null)
        attrs.ValueRank = -1
        node.NodeAttributes = attrs
        self._session_server.add_nodes([node])

        return dictionary_node_id

    def _nodeid_generator(self):
        self._id_counter += 1
        return ua.NodeId(self._id_counter, namespaceidx=self._idx, nodeidtype=ua.NodeIdType.Numeric)

    def _link_nodes(self, linked_obj_node_id, data_type_node_id, description_node_id):
        """link the three node by their node ids according to UA standard"""
        refs = [
                # add reverse reference to BaseDataType -> Structure
                _reference_generator(data_type_node_id, ua.NodeId(ua.ObjectIds.Structure, 0),
                                     ua.NodeId(ua.ObjectIds.HasSubtype, 0), False),
                # add reverse reference to created data type
                _reference_generator(linked_obj_node_id, data_type_node_id,
                                     ua.NodeId(ua.ObjectIds.HasEncoding, 0), False),
                # add HasDescription link to dictionary description
                _reference_generator(linked_obj_node_id, description_node_id,
                                     ua.NodeId(ua.ObjectIds.HasDescription, 0)),
                # add reverse HasDescription link
                _reference_generator(description_node_id, linked_obj_node_id,
                                     ua.NodeId(ua.ObjectIds.HasDescription, 0), False),
                # add link to the type definition node
                _reference_generator(linked_obj_node_id, ua.NodeId(ua.ObjectIds.DataTypeEncodingType, 0),
                                     ua.NodeId(ua.ObjectIds.HasTypeDefinition, 0)),
                # add has type definition link
                _reference_generator(description_node_id, ua.NodeId(ua.ObjectIds.DataTypeDescriptionType, 0),
                                     ua.NodeId(ua.ObjectIds.HasTypeDefinition, 0)),
                # add forward link of dict to description item
                _reference_generator(self.dict_id, description_node_id,
                                     ua.NodeId(ua.ObjectIds.HasComponent, 0)),
                # add reverse link to dictionary
                _reference_generator(description_node_id, self.dict_id,
                                     ua.NodeId(ua.ObjectIds.HasComponent, 0), False)]
        self._session_server.add_references(refs)

    def _create_data_type(self, type_name):
        name = _to_camel_case(type_name)
        # apply for new node id
        data_type_node_id = self._nodeid_generator()
        description_node_id = self._nodeid_generator()
        bind_obj_node_id = self._nodeid_generator()

        # create data type node
        dt_node = ua.AddNodesItem()
        dt_node.RequestedNewNodeId = data_type_node_id
        dt_node.BrowseName = ua.QualifiedName(name, self._idx)
        dt_node.NodeClass = ua.NodeClass.DataType
        dt_node.ParentNodeId = ua.NodeId(ua.ObjectIds.Structure, 0)
        dt_node.ReferenceTypeId = ua.NodeId(ua.ObjectIds.HasSubtype, 0)
        dt_attributes = ua.DataTypeAttributes()
        dt_attributes.DisplayName = ua.LocalizedText(type_name)
        dt_node.NodeAttributes = dt_attributes

        # create description node
        desc_node = ua.AddNodesItem()
        desc_node.RequestedNewNodeId = description_node_id
        desc_node.BrowseName = ua.QualifiedName(name, self._idx)
        desc_node.NodeClass = ua.NodeClass.Variable
        desc_node.ParentNodeId = self.dict_id
        desc_node.ReferenceTypeId = ua.NodeId(ua.ObjectIds.HasComponent, 0)
        desc_node.TypeDefinition = ua.NodeId(ua.ObjectIds.DataTypeDescriptionType, 0)
        desc_attributes = ua.VariableAttributes()
        desc_attributes.DisplayName = ua.LocalizedText(type_name)
        desc_attributes.DataType = ua.NodeId(ua.ObjectIds.String)
        desc_attributes.Value = ua.Variant(name, ua.VariantType.String)
        desc_attributes.ValueRank = -1
        desc_node.NodeAttributes = desc_attributes

        # create object node which the loaded python class should link to
        obj_node = ua.AddNodesItem()
        obj_node.RequestedNewNodeId = bind_obj_node_id
        obj_node.BrowseName = ua.QualifiedName('Default Binary', 0)
        obj_node.NodeClass = ua.NodeClass.Object
        obj_node.ParentNodeId = data_type_node_id
        obj_node.ReferenceTypeId = ua.NodeId(ua.ObjectIds.HasEncoding, 0)
        obj_node.TypeDefinition = ua.NodeId(ua.ObjectIds.DataTypeEncodingType, 0)
        obj_attributes = ua.ObjectAttributes()
        obj_attributes.DisplayName = ua.LocalizedText('Default Binary')
        obj_attributes.EventNotifier = 0
        obj_node.NodeAttributes = obj_attributes

        self._session_server.add_nodes([dt_node, desc_node, obj_node])
        self._link_nodes(bind_obj_node_id, data_type_node_id, description_node_id)

        self._type_dictionary.append_struct(type_name)
        return StructNode(self, data_type_node_id, type_name)

    def create_data_type(self, type_name):
        return self._create_data_type(type_name)

    def add_field(self, type_name, variable_name, struct_name, is_array=False):
        self._type_dictionary.add_field(type_name, variable_name, struct_name, is_array)

    def set_dict_byte_string(self):
        dict_node = self._server.get_node(self.dict_id)
        value = self._type_dictionary.get_dict_value()
        dict_node.set_value(value, ua.VariantType.ByteString)


class StructNode:

    def __init__(self, type_dict, data_type, name):
        self._type_dict = type_dict
        self.data_type = data_type
        self.name = name
        pass

    def add_field(self, type_name, field_name, is_array=False):
        # nested structure could directly use simple structure as field
        if isinstance(field_name, StructNode):
            field_name = field_name.name
        self._type_dict.add_field(field_name, type_name, self.name, is_array)


def get_ua_class(ua_class_name):
    return getattr(ua, _to_camel_case(ua_class_name))
