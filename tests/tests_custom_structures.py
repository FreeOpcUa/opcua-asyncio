import unittest
import logging
import xml.etree.ElementTree as Et
from opcua import ua, Server
import opcua.common.type_dictionary_buider
from opcua.common.type_dictionary_buider import OPCTypeDictionaryBuilder, DataTypeDictionaryBuilder
from opcua.common.type_dictionary_buider import get_ua_class, StructNode

port_num = 48540
idx_name = 'http://test.freeopcua.github.io'


def to_camel_case(name):
    func = getattr(opcua.common.type_dictionary_buider, '_to_camel_case')
    return func(name)


def reference_generator(source_id, target_id, reference_type, is_forward=True):
    func = getattr(opcua.common.type_dictionary_buider, '_reference_generator')
    return func(source_id, target_id, reference_type, is_forward)


def set_up_test_tree():
    ext_head_attributes = {'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance', 'xmlns:tns': idx_name,
                           'DefaultByteOrder': 'LittleEndian', 'xmlns:opc': 'http://opcfoundation.org/BinarySchema/',
                           'xmlns:ua': 'http://opcfoundation.org/UA/', 'TargetNamespace': idx_name}

    test_etree = Et.ElementTree(Et.Element('opc:TypeDictionary', ext_head_attributes))
    name_space = Et.SubElement(test_etree.getroot(), 'opc:Import')
    name_space.attrib['Namespace'] = 'http://opcfoundation.org/UA/'
    return test_etree


class TypeDictionaryBuilderTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.srv = Server()
        cls.srv.set_endpoint('opc.tcp://127.0.0.1:{0:d}'.format(port_num))
        cls.idx = cls.srv.register_namespace(idx_name)
        cls.srv.start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.stop()

    def setUp(self):
        self.test_etree = set_up_test_tree()
        self.opc_type_builder = OPCTypeDictionaryBuilder(idx_name)
        self.dict_builder = DataTypeDictionaryBuilder(self.srv, self.idx, idx_name, 'TestDict')
        self.init_counter = getattr(self.dict_builder, '_id_counter')

    def tearDown(self):
        curr_counter = getattr(self.dict_builder, '_id_counter')
        trash_nodes = []
        for counter in range(self.init_counter, curr_counter + 1):
            trash_nodes.append(self.srv.get_node('ns={0};i={1}'.format(self.idx, str(counter))))
        self.srv.delete_nodes(trash_nodes)

    def test_camel_case_1(self):
        case = 'TurtleActionlibShapeActionFeedback'
        result = to_camel_case('turtle_actionlib/ShapeActionFeedback')
        self.assertEquals(result, case)

    def test_camel_case_2(self):
        case = 'HelloWorldFffD'
        result = to_camel_case('Hello#world+fff_**?&&d')
        self.assertEquals(result, case)

    def test_opc_type_dict_process_type_opc(self):
        case = 'opc:Boolean'
        result = getattr(self.opc_type_builder, '_process_type')('Boolean')
        self.assertEquals(result, case)

    def test_opc_type_dict_process_type_tns(self):
        case = 'tns:CustomizedStruct'
        result = getattr(self.opc_type_builder, '_process_type')('CustomizedStruct')
        self.assertEquals(result, case)

    def test_opc_type_dict_append_struct_1(self):
        case = {'BaseType': 'ua:ExtensionObject',
                'Name': 'CustomizedStruct'}
        result = self.opc_type_builder.append_struct('CustomizedStruct')
        self.assertEquals(result.attrib, case)

    def test_opc_type_dict_append_struct_2(self):
        case = {'BaseType': 'ua:ExtensionObject',
                'Name': 'CustomizedStruct'}
        result = self.opc_type_builder.append_struct('customized_#?+`struct')
        self.assertEquals(result.attrib, case)

    def test_opc_type_dict_add_field_1(self):
        structure_name = 'CustomizedStruct'
        self.opc_type_builder.append_struct(structure_name)
        self.opc_type_builder.add_field(ua.VariantType.Boolean, 'id', structure_name)
        case = {'TypeName': 'opc:Boolean',
                'Name': 'id'}
        struct_dict = getattr(self.opc_type_builder, '_structs_dict')
        result = list(struct_dict[structure_name])[0]
        self.assertEquals(result.attrib, case)

    def test_opc_type_dict_add_field_2(self):
        structure_name = 'CustomizedStruct'
        self.opc_type_builder.append_struct(structure_name)
        self.opc_type_builder.add_field('Boolean', 'id', structure_name)
        case = {'TypeName': 'opc:Boolean',
                'Name': 'id'}
        struct_dict = getattr(self.opc_type_builder, '_structs_dict')
        result = list(struct_dict[structure_name])[0]
        self.assertEquals(result.attrib, case)

    def test_opc_type_dict_add_field_3(self):
        structure_name = 'CustomizedStruct'
        self.opc_type_builder.append_struct(structure_name)
        self.opc_type_builder.add_field(ua.VariantType.Boolean, 'id', structure_name, is_array=True)
        case = [{'TypeName': 'opc:Int32',
                'Name': 'NoOfid'},
                {'TypeName': 'opc:Boolean',
                 'LengthField': 'NoOfid',
                 'Name': 'id'}]
        struct_dict = getattr(self.opc_type_builder, '_structs_dict')
        result = [item.attrib for item in list(struct_dict[structure_name])]
        self.assertItemsEqual(result, case)

    def test_opc_type_dict_get_dict_value(self):
        structure_name = 'CustomizedStruct'
        self.opc_type_builder.append_struct(structure_name)
        # external tree operation
        appended_struct = Et.SubElement(self.test_etree.getroot(), 'opc:StructuredType')
        appended_struct.attrib['BaseType'] = 'ua:ExtensionObject'
        appended_struct.attrib['Name'] = to_camel_case(structure_name)

        self.opc_type_builder.add_field(ua.VariantType.Boolean, 'id', structure_name)
        # external tree operation
        field = Et.SubElement(appended_struct, 'opc:Field')
        field.attrib['Name'] = 'id'
        field.attrib['TypeName'] = 'opc:Boolean'
        case = Et.tostring(self.test_etree.getroot(), encoding='utf-8').replace(' ', '')
        result = self.opc_type_builder.get_dict_value().replace(' ', '').replace('\n', '')
        self.assertEqual(result, case)

    def test_reference_generator_1(self):
        id1 = ua.NodeId(1, namespaceidx=2, nodeidtype=ua.NodeIdType.Numeric)
        id2 = ua.NodeId(2, namespaceidx=2, nodeidtype=ua.NodeIdType.Numeric)
        ref = ua.NodeId(ua.ObjectIds.HasEncoding, 0)
        result = reference_generator(id1, id2, ref)
        self.assertTrue(result.IsForward)
        self.assertEqual(result.ReferenceTypeId, ref)
        self.assertEqual(result.SourceNodeId, id1)
        self.assertEqual(result.TargetNodeClass, ua.NodeClass.DataType)
        self.assertEqual(result.TargetNodeId, id2)

    def test_reference_generator_2(self):
        id1 = ua.NodeId(1, namespaceidx=2, nodeidtype=ua.NodeIdType.Numeric)
        id2 = ua.NodeId(2, namespaceidx=2, nodeidtype=ua.NodeIdType.Numeric)
        ref = ua.NodeId(ua.ObjectIds.HasEncoding, 0)
        result = reference_generator(id1, id2, ref, False)
        self.assertFalse(result.IsForward)
        self.assertEqual(result.ReferenceTypeId, ref)
        self.assertEqual(result.SourceNodeId, id1)
        self.assertEqual(result.TargetNodeClass, ua.NodeClass.DataType)
        self.assertEqual(result.TargetNodeId, id2)

    def test_data_type_dict_general(self):
        self.assertIsNotNone(self.dict_builder.dict_id)
        self.assertIsNotNone(getattr(self.dict_builder, '_type_dictionary'))

    def test_data_type_dict_nodeid_generator(self):
        nodeid_generator = getattr(self.dict_builder, '_nodeid_generator')
        result = nodeid_generator()
        self.assertTrue(isinstance(result, ua.NodeId))
        self.assertTrue(str(result.Identifier).isdigit())
        self.assertEqual(result.NamespaceIndex, self.idx)
        setattr(self.dict_builder, '_id_counter', self.init_counter)

    def test_data_type_dict_add_dictionary(self):
        add_dictionary = getattr(self.dict_builder, '_add_dictionary')
        dict_name = 'TestDict'
        dict_node = self.srv.get_node(add_dictionary(dict_name))
        self.assertEqual(dict_node.get_browse_name(), ua.QualifiedName(dict_name, self.idx))
        self.assertEqual(dict_node.get_node_class(), ua.NodeClass.Variable)
        self.assertEqual(dict_node.get_parent().nodeid, ua.NodeId(ua.ObjectIds.OPCBinarySchema_TypeSystem, 0))
        self.assertEqual(ua.NodeId(ua.ObjectIds.HasComponent, 0),
                         dict_node.get_references(refs=ua.ObjectIds.HasComponent)[0].ReferenceTypeId)
        self.assertEqual(dict_node.get_type_definition(), ua.NodeId(ua.ObjectIds.DataTypeDictionaryType, 0))
        self.assertEqual(dict_node.get_display_name(), ua.LocalizedText(dict_name))
        self.assertEqual(dict_node.get_data_type(), ua.NodeId(ua.ObjectIds.ByteString))
        self.assertEqual(dict_node.get_value_rank(), -1)

    def test_data_type_dict_create_data_type(self):
        type_name = 'CustomizedStruct'
        created_type = self.dict_builder.create_data_type(type_name)
        self.assertTrue(isinstance(created_type, StructNode))
        # Test data type node
        type_node = self.srv.get_node(created_type.data_type)
        self.assertEqual(type_node.get_browse_name(), ua.QualifiedName(type_name, self.idx))
        self.assertEqual(type_node.get_node_class(), ua.NodeClass.DataType)
        self.assertEqual(type_node.get_parent().nodeid, ua.NodeId(ua.ObjectIds.Structure, 0))
        self.assertEqual(ua.NodeId(ua.ObjectIds.HasSubtype, 0),
                         type_node.get_references(refs=ua.ObjectIds.HasSubtype)[0].ReferenceTypeId)
        self.assertEqual(type_node.get_display_name(), ua.LocalizedText(type_name))

        # Test description node
        desc_node = self.srv.get_node(self.dict_builder.dict_id).get_children()[0]
        self.assertEqual(desc_node.get_browse_name(), ua.QualifiedName(type_name, self.idx))
        self.assertEqual(desc_node.get_node_class(), ua.NodeClass.Variable)
        self.assertEqual(desc_node.get_parent().nodeid, self.dict_builder.dict_id)
        self.assertEqual(ua.NodeId(ua.ObjectIds.HasComponent, 0),
                         desc_node.get_references(refs=ua.ObjectIds.HasComponent)[0].ReferenceTypeId)
        self.assertEqual(desc_node.get_type_definition(), ua.NodeId(ua.ObjectIds.DataTypeDescriptionType, 0))

        self.assertEqual(desc_node.get_display_name(), ua.LocalizedText(type_name))
        self.assertEqual(desc_node.get_data_type(), ua.NodeId(ua.ObjectIds.String))
        self.assertEqual(desc_node.get_value(), type_name)
        self.assertEqual(desc_node.get_value_rank(), -1)

        # Test object node
        obj_node = type_node.get_children(refs=ua.ObjectIds.HasEncoding)[0]
        self.assertEqual(obj_node.get_browse_name(), ua.QualifiedName('Default Binary', 0))
        self.assertEqual(obj_node.get_node_class(), ua.NodeClass.Object)
        self.assertEqual(obj_node.get_references(refs=ua.ObjectIds.HasEncoding)[0].NodeId, type_node.nodeid)
        self.assertEqual(ua.NodeId(ua.ObjectIds.HasEncoding, 0),
                         obj_node.get_references(refs=ua.ObjectIds.HasEncoding)[0].ReferenceTypeId)
        self.assertEqual(obj_node.get_type_definition(), ua.NodeId(ua.ObjectIds.DataTypeEncodingType, 0))
        self.assertEqual(obj_node.get_display_name(), ua.LocalizedText('Default Binary'))
        self.assertEqual(len(obj_node.get_event_notifier()), 0)

        # Test links, three were tested above
        struct_node = self.srv.get_node(ua.NodeId(ua.ObjectIds.Structure, 0))
        struct_children = struct_node.get_children(refs=ua.ObjectIds.HasSubtype)
        self.assertTrue(type_node in struct_children)
        dict_node = self.srv.get_node(self.dict_builder.dict_id)
        dict_children = dict_node.get_children(refs=ua.ObjectIds.HasComponent)
        self.assertTrue(desc_node in dict_children)
        self.assertTrue(obj_node in type_node.get_children(ua.ObjectIds.HasEncoding))
        self.assertTrue(desc_node in obj_node.get_children(refs=ua.ObjectIds.HasDescription))
        self.assertEqual(obj_node.nodeid, desc_node.get_references(refs=ua.ObjectIds.HasDescription,
                                                                   direction=ua.BrowseDirection.Inverse)[0].NodeId)

    def test_data_type_dict_set_dict_byte_string(self):
        structure_name = 'CustomizedStruct'
        self.dict_builder.create_data_type(structure_name)
        self.dict_builder.add_field(ua.VariantType.Int32, 'id', structure_name)
        self.dict_builder.set_dict_byte_string()
        # external tree operation
        appended_struct = Et.SubElement(self.test_etree.getroot(), 'opc:StructuredType')
        appended_struct.attrib['BaseType'] = 'ua:ExtensionObject'
        appended_struct.attrib['Name'] = to_camel_case(structure_name)

        # external tree operation
        field = Et.SubElement(appended_struct, 'opc:Field')
        field.attrib['Name'] = 'id'
        field.attrib['TypeName'] = 'opc:Int32'
        case = Et.tostring(self.test_etree.getroot(), encoding='utf-8').replace(' ', '')
        result = self.srv.get_node(self.dict_builder.dict_id).get_value().replace(' ', '').replace('\n', '')
        self.assertEqual(result, case)

    def test_data_type_dict_add_field_1(self):
        struct_name = 'CustomizedStruct'
        self.dict_builder.create_data_type(struct_name)
        self.dict_builder.add_field(ua.VariantType.Int32, 'id', struct_name)
        self.dict_builder.set_dict_byte_string()
        self.srv.load_type_definitions()
        struct = get_ua_class(struct_name)
        self.assertEqual(struct.ua_types[0][0], 'id')
        self.assertEqual(struct.ua_types[0][1], 'Int32')
        struct_instance = struct()
        self.assertEqual(struct_instance.id, 0)

    def test_data_type_dict_add_field_2(self):
        struct_name = 'AnotherCustomizedStruct'
        self.dict_builder.create_data_type(struct_name)
        self.dict_builder.add_field(ua.VariantType.Int32, 'id', struct_name, is_array=True)
        self.dict_builder.set_dict_byte_string()
        self.srv.load_type_definitions()
        struct = get_ua_class(struct_name)
        self.assertEqual(struct.ua_types[0][0], 'id')
        self.assertEqual(struct.ua_types[0][1], 'ListOfInt32')
        struct_instance = struct()
        self.assertTrue(isinstance(struct_instance.id, list))

    def test_struct_node_general(self):
        struct_name = 'CustomizedStruct'
        struct_node = self.dict_builder.create_data_type(struct_name)
        self.assertEqual(getattr(struct_node, '_type_dict'), self.dict_builder)
        self.assertTrue(isinstance(struct_node.data_type, ua.NodeId))
        self.assertEqual(struct_node.name, struct_name)

    def test_struct_node_add_field(self):
        struct_name = 'CustomizedStruct'
        struct_node = self.dict_builder.create_data_type(struct_name)
        struct_node.add_field('id', ua.VariantType.Int32)
        self.dict_builder.set_dict_byte_string()
        self.srv.load_type_definitions()
        struct = get_ua_class(struct_name)
        self.assertEqual(struct.ua_types[0][0], 'id')
        self.assertEqual(struct.ua_types[0][1], 'Int32')
        struct_instance = struct()
        self.assertEqual(struct_instance.id, 0)

    def test_get_ua_class_1(self):
        struct_name = 'CustomizedStruct'
        struct_node = self.dict_builder.create_data_type(struct_name)
        struct_node.add_field('id', ua.VariantType.Int32)
        self.dict_builder.set_dict_byte_string()
        self.srv.load_type_definitions()
        try:
            self.assertIsNotNone(get_ua_class(struct_name))
        except AttributeError:
            pass

    def test_get_ua_class_2(self):
        struct_name = '*c*u_stom-ized&Stru#ct'
        struct_node = self.dict_builder.create_data_type(struct_name)
        struct_node.add_field('id', ua.VariantType.Int32)
        self.dict_builder.set_dict_byte_string()
        self.srv.load_type_definitions()
        try:
            self.assertIsNotNone(get_ua_class(struct_name))
        except AttributeError:
            pass

    def test_functional_basic(self):
        basic_struct_name = 'basic_structure'
        basic_struct = self.dict_builder.create_data_type(basic_struct_name)
        basic_struct.add_field('ID', ua.VariantType.Int32)
        basic_struct.add_field('Gender', ua.VariantType.Boolean)
        basic_struct.add_field('Comments', ua.VariantType.String)

        self.dict_builder.set_dict_byte_string()
        self.srv.load_type_definitions()

        basic_var = self.srv.nodes.objects.add_variable(ua.NodeId(namespaceidx=self.idx), 'BasicStruct',
                                                        ua.Variant(None, ua.VariantType.Null),
                                                        datatype=basic_struct.data_type)

        basic_msg = get_ua_class(basic_struct_name)()
        basic_msg.ID = 3
        basic_msg.Gender = True
        basic_msg.Comments = 'Test string'
        basic_var.set_value(basic_msg)

        basic_result = basic_var.get_value()
        self.assertEqual(basic_result, basic_msg)

    def test_functional_advance(self):
        basic_struct_name = 'basic_structure'
        basic_struct = self.dict_builder.create_data_type(basic_struct_name)
        basic_struct.add_field('ID', ua.VariantType.Int32)
        basic_struct.add_field('Gender', ua.VariantType.Boolean)
        basic_struct.add_field('Comments', ua.VariantType.String)

        nested_struct_name = 'nested_structure'
        nested_struct = self.dict_builder.create_data_type(nested_struct_name)
        nested_struct.add_field('Name', ua.VariantType.String)
        nested_struct.add_field('Surname', ua.VariantType.String)
        nested_struct.add_field('Stuff', basic_struct)

        self.dict_builder.set_dict_byte_string()
        self.srv.load_type_definitions()

        basic_var = self.srv.nodes.objects.add_variable(ua.NodeId(namespaceidx=self.idx), 'BasicStruct',
                                                        ua.Variant(None, ua.VariantType.Null),
                                                        datatype=basic_struct.data_type)

        basic_msg = get_ua_class(basic_struct_name)()
        basic_msg.ID = 3
        basic_msg.Gender = True
        basic_msg.Comments = 'Test string'
        basic_var.set_value(basic_msg)

        nested_var = self.srv.nodes.objects.add_variable(ua.NodeId(namespaceidx=self.idx), 'NestedStruct',
                                                         ua.Variant(None, ua.VariantType.Null),
                                                         datatype=nested_struct.data_type)

        nested_msg = get_ua_class(nested_struct_name)()
        nested_msg.Stuff = basic_msg
        nested_msg.Name = 'Max'
        nested_msg.Surname = 'Karl'
        nested_var.set_value(nested_msg)

        basic_result = basic_var.get_value()
        self.assertEqual(basic_result, basic_msg)
        nested_result = nested_var.get_value()
        self.assertEqual(nested_result, nested_msg)


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    unittest.main(verbosity=3)
