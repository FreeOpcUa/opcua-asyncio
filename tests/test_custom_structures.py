import xml.etree.ElementTree as Et

import pytest

from asyncua import ua
from asyncua.common.structures import EnumType, StructGenerator, Struct
import asyncua.common.type_dictionary_builder
from asyncua.common.type_dictionary_builder import OPCTypeDictionaryBuilder, DataTypeDictionaryBuilder
from asyncua.common.type_dictionary_builder import get_ua_class, StructNode

port_num = 48540
ns_urn = 'http://test.freeopcua.github.io'


pytestmark = pytest.mark.asyncio


def to_camel_case(name):
    func = getattr(asyncua.common.type_dictionary_builder, '_to_camel_case')
    return func(name)


def reference_generator(source_id, target_id, reference_type, is_forward=True):
    func = getattr(asyncua.common.type_dictionary_builder, '_reference_generator')
    return func(source_id, target_id, reference_type, is_forward)


def set_up_test_tree():
    ext_head_attributes = {'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance', 'xmlns:tns': ns_urn,
                           'DefaultByteOrder': 'LittleEndian', 'xmlns:opc': 'http://opcfoundation.org/BinarySchema/',
                           'xmlns:ua': 'http://opcfoundation.org/UA/', 'TargetNamespace': ns_urn}

    test_etree = Et.ElementTree(Et.Element('opc:TypeDictionary', ext_head_attributes))
    name_space = Et.SubElement(test_etree.getroot(), 'opc:Import')
    name_space.attrib['Namespace'] = 'http://opcfoundation.org/UA/'
    return test_etree


@pytest.fixture(scope="function")
async def _srv(server):
    class Srv:
        pass
    srv = Srv()
    srv.srv = server
    srv.idx = await srv.srv.register_namespace(ns_urn)
    yield srv


@pytest.fixture
async def srv(_srv):
    _srv.test_etree = set_up_test_tree()
    _srv.opc_type_builder = OPCTypeDictionaryBuilder(ns_urn)
    _srv.dict_builder = DataTypeDictionaryBuilder(_srv.srv, _srv.idx, ns_urn, 'TestDict')
    await _srv.dict_builder.init()
    yield _srv


async def test_camel_case_1():
    case = 'TurtleActionlibShapeActionFeedback'
    result = to_camel_case('turtle_actionlib/ShapeActionFeedback')
    assert result == case


async def test_camel_case_2():
    case = 'HelloWorldFffD'
    result = to_camel_case('Hello#world+fff_**?&&d')
    assert result == case


async def test_opc_type_dict_process_type_opc(srv):
    case = 'opc:Boolean'
    result = getattr(srv.opc_type_builder, '_process_type')('Boolean')
    assert result == case


async def test_opc_type_dict_process_type_tns(srv):
    case = 'tns:CustomizedStruct'
    result = getattr(srv.opc_type_builder, '_process_type')('CustomizedStruct')
    assert result == case


async def test_opc_type_dict_append_struct_1(srv):
    case = {'BaseType': 'ua:ExtensionObject',
            'Name': 'CustomizedStruct'}
    result = srv.opc_type_builder.append_struct('CustomizedStruct')
    assert result.attrib == case


@pytest.mark.skip("Support for that feature currently removed")
async def test_opc_type_dict_append_struct_2(srv):
    case = {'BaseType': 'ua:ExtensionObject',
            'Name': 'CustomizedStruct'}
    result = srv.opc_type_builder.append_struct('customized_#?+`struct')
    assert result.attrib == case


async def test_opc_type_dict_add_field_1(srv):
    structure_name = 'CustomizedStruct'
    srv.opc_type_builder.append_struct(structure_name)
    srv.opc_type_builder.add_field(ua.VariantType.Boolean, 'id', structure_name)
    case = {'TypeName': 'opc:Boolean',
            'Name': 'id'}
    struct_dict = getattr(srv.opc_type_builder, '_structs_dict')
    result = list(struct_dict[structure_name])[0]
    assert result.attrib == case


async def test_opc_type_dict_add_field_2(srv):
    structure_name = 'CustomizedStruct'
    srv.opc_type_builder.append_struct(structure_name)
    srv.opc_type_builder.add_field('Boolean', 'id', structure_name)
    case = {'TypeName': 'opc:Boolean',
            'Name': 'id'}
    struct_dict = getattr(srv.opc_type_builder, '_structs_dict')
    result = list(struct_dict[structure_name])[0]
    assert result.attrib == case


async def test_opc_type_dict_add_field_3(srv):
    structure_name = 'CustomizedStruct'
    srv.opc_type_builder.append_struct(structure_name)
    srv.opc_type_builder.add_field(ua.VariantType.Boolean, 'id', structure_name, is_array=True)
    case = [{'TypeName': 'opc:Int32',
            'Name': 'NoOfid'},
            {'TypeName': 'opc:Boolean',
             'LengthField': 'NoOfid',
             'Name': 'id'}]
    struct_dict = getattr(srv.opc_type_builder, '_structs_dict')
    result = [item.attrib for item in list(struct_dict[structure_name])]
    assert result == case


async def test_opc_type_dict_get_dict_value(srv):
    structure_name = 'CustomizedStruct'
    srv.opc_type_builder.append_struct(structure_name)
    # external tree operation
    appended_struct = Et.SubElement(srv.test_etree.getroot(), 'opc:StructuredType')
    appended_struct.attrib['BaseType'] = 'ua:ExtensionObject'
    appended_struct.attrib['Name'] = to_camel_case(structure_name)

    srv.opc_type_builder.add_field(ua.VariantType.Boolean, 'id', structure_name)
    # external tree operation
    field = Et.SubElement(appended_struct, 'opc:Field')
    field.attrib['Name'] = 'id'
    field.attrib['TypeName'] = 'opc:Boolean'
    case = Et.tostring(srv.test_etree.getroot(), encoding='utf-8').decode("utf-8").replace(' ', '')
    result = srv.opc_type_builder.get_dict_value().decode("utf-8").replace(' ', '').replace('\n', '')
    assert result == case


async def test_reference_generator_1(srv):
    id1 = ua.NodeId(1, NamespaceIndex=2, NodeIdType=ua.NodeIdType.Numeric)
    id2 = ua.NodeId(2, NamespaceIndex=2, NodeIdType=ua.NodeIdType.Numeric)
    ref = ua.NodeId(ua.ObjectIds.HasEncoding, 0)
    result = reference_generator(id1, id2, ref)
    assert result.IsForward
    assert result.ReferenceTypeId == ref
    assert result.SourceNodeId == id1
    assert result.TargetNodeClass == ua.NodeClass.DataType
    assert result.TargetNodeId == id2


async def test_reference_generator_2(srv):
    id1 = ua.NodeId(1, NamespaceIndex=2, NodeIdType=ua.NodeIdType.Numeric)
    id2 = ua.NodeId(2, NamespaceIndex=2, NodeIdType=ua.NodeIdType.Numeric)
    ref = ua.NodeId(ua.ObjectIds.HasEncoding, 0)
    result = reference_generator(id1, id2, ref, False)
    assert not result.IsForward
    assert result.ReferenceTypeId == ref
    assert result.SourceNodeId == id1
    assert result.TargetNodeClass == ua.NodeClass.DataType
    assert result.TargetNodeId == id2


async def test_data_type_dict_general(srv):
    assert srv.dict_builder.dict_id is not None
    assert getattr(srv.dict_builder, '_type_dictionary') is not None


async def test_data_type_dict_add_dictionary(srv):
    add_dictionary = getattr(srv.dict_builder, '_add_dictionary')
    dict_name = 'TestDict'
    dict_node = srv.srv.get_node(await add_dictionary(dict_name))
    assert await dict_node.read_browse_name() == ua.QualifiedName(dict_name, srv.idx)
    assert await dict_node.read_node_class() == ua.NodeClass.Variable
    assert (await dict_node.get_parent()).nodeid == ua.NodeId(ua.ObjectIds.OPCBinarySchema_TypeSystem, 0)
    assert ua.NodeId(ua.ObjectIds.HasComponent, 0) == (await dict_node.get_references(refs=ua.ObjectIds.HasComponent))[0].ReferenceTypeId
    assert await dict_node.read_type_definition() == ua.NodeId(ua.ObjectIds.DataTypeDictionaryType, 0)
    assert await dict_node.read_display_name() == ua.LocalizedText(dict_name)
    assert await dict_node.read_data_type() == ua.NodeId(ua.ObjectIds.ByteString)
    assert await dict_node.read_value_rank() == -1


async def test_data_type_dict_create_data_type(srv):
    type_name = 'CustomizedStruct2'
    created_type = await srv.dict_builder.create_data_type(type_name)
    assert isinstance(created_type, StructNode)
    # Test data type node
    type_node = srv.srv.get_node(created_type.data_type)
    assert await type_node.read_browse_name() == ua.QualifiedName(type_name, srv.idx)
    assert await type_node.read_node_class() == ua.NodeClass.DataType
    assert (await type_node.get_parent()).nodeid == ua.NodeId(ua.ObjectIds.Structure, 0)
    assert ua.NodeId(ua.ObjectIds.HasSubtype, 0) == (await type_node.get_references(refs=ua.ObjectIds.HasSubtype))[0].ReferenceTypeId
    assert await type_node.read_display_name() == ua.LocalizedText(type_name)

    # Test description node
    n = srv.srv.get_node(srv.dict_builder.dict_id)
    desc_node = await n.get_child(f"{srv.dict_builder._idx}:{type_name}")
    assert await desc_node.read_browse_name() == ua.QualifiedName(type_name, srv.idx)
    assert await desc_node.read_node_class() == ua.NodeClass.Variable
    assert (await desc_node.get_parent()).nodeid == srv.dict_builder.dict_id
    assert ua.NodeId(ua.ObjectIds.HasComponent, 0) == (await desc_node.get_references(refs=ua.ObjectIds.HasComponent))[0].ReferenceTypeId
    assert await desc_node.read_type_definition() == ua.NodeId(ua.ObjectIds.DataTypeDescriptionType, 0)

    assert await desc_node.read_display_name() == ua.LocalizedText(type_name)
    assert await desc_node.read_data_type() == ua.NodeId(ua.ObjectIds.String)
    assert await desc_node.read_value() == type_name
    assert await desc_node.read_value_rank() == -1

    # Test object node
    obj_node = (await type_node.get_children(refs=ua.ObjectIds.HasEncoding))[0]
    assert await obj_node.read_browse_name() == ua.QualifiedName('Default Binary', 0)
    assert await obj_node.read_node_class() == ua.NodeClass.Object
    assert (await obj_node.get_references(refs=ua.ObjectIds.HasEncoding))[0].NodeId == type_node.nodeid
    assert ua.NodeId(ua.ObjectIds.HasEncoding, 0) == (await obj_node.get_references(refs=ua.ObjectIds.HasEncoding))[0].ReferenceTypeId
    assert await obj_node.read_type_definition() == ua.NodeId(ua.ObjectIds.DataTypeEncodingType, 0)
    assert await obj_node.read_display_name() == ua.LocalizedText('Default Binary')
    assert len(await obj_node.read_event_notifier()) == 0

    # Test links, three were tested above
    struct_node = srv.srv.get_node(ua.NodeId(ua.ObjectIds.Structure, 0))
    struct_children = await struct_node.get_children(refs=ua.ObjectIds.HasSubtype)
    assert type_node in struct_children
    dict_node = srv.srv.get_node(srv.dict_builder.dict_id)
    dict_children = await dict_node.get_children(refs=ua.ObjectIds.HasComponent)
    assert desc_node in dict_children
    assert obj_node in await type_node.get_children(ua.ObjectIds.HasEncoding)
    assert desc_node in await obj_node.get_children(refs=ua.ObjectIds.HasDescription)
    assert obj_node.nodeid == (await desc_node.get_references(refs=ua.ObjectIds.HasDescription, direction=ua.BrowseDirection.Inverse))[0].NodeId


async def test_data_type_dict_set_dict_byte_string(srv):
    structure_name = 'CustomizedStruct'
    await srv.dict_builder.create_data_type(structure_name)
    srv.dict_builder.add_field(ua.VariantType.Int32, 'id', structure_name)
    await srv.dict_builder.set_dict_byte_string()
    # external tree operation
    appended_struct = Et.SubElement(srv.test_etree.getroot(), 'opc:StructuredType')
    appended_struct.attrib['BaseType'] = 'ua:ExtensionObject'
    appended_struct.attrib['Name'] = to_camel_case(structure_name)

    # external tree operation
    field = Et.SubElement(appended_struct, 'opc:Field')
    field.attrib['Name'] = 'id'
    field.attrib['TypeName'] = 'opc:Int32'
    case = Et.tostring(srv.test_etree.getroot(), encoding='utf-8').decode("utf-8").replace(' ', '')
    result = (await srv.srv.get_node(srv.dict_builder.dict_id).read_value()).decode("utf-8").replace(' ', '').replace('\n', '')
    assert result == case


async def test_data_type_dict_add_field_1(srv):
    struct_name = 'CustomizedStruct'
    await srv.dict_builder.create_data_type(struct_name)
    srv.dict_builder.add_field(ua.VariantType.Int32, 'id', struct_name)
    await srv.dict_builder.set_dict_byte_string()
    await srv.srv.load_type_definitions()
    struct = get_ua_class(struct_name)
    struct_instance = struct()
    assert struct_instance.id == 0


async def test_data_type_dict_add_field_2(srv):
    struct_name = 'AnotherCustomizedStruct'
    await srv.dict_builder.create_data_type(struct_name)
    srv.dict_builder.add_field(ua.VariantType.Int32, 'id', struct_name, is_array=True)
    await srv.dict_builder.set_dict_byte_string()
    await srv.srv.load_type_definitions()
    struct = get_ua_class(struct_name)
    struct_instance = struct()
    assert isinstance(struct_instance.id, list)


async def test_struct_node_general(srv):
    struct_name = 'CustomizedStruct'
    struct_node = await srv.dict_builder.create_data_type(struct_name)
    assert getattr(struct_node, '_type_dict'), srv.dict_builder
    assert isinstance(struct_node.data_type, ua.NodeId)
    assert struct_node.name == struct_name


async def test_struct_node_add_field(srv):
    struct_name = 'CustomizedStruct'
    struct_node = await srv.dict_builder.create_data_type(struct_name)
    struct_node.add_field('id', ua.VariantType.Int32)
    await srv.dict_builder.set_dict_byte_string()
    await srv.srv.load_type_definitions()
    struct = get_ua_class(struct_name)
    struct_instance = struct()
    assert struct_instance.id == 0


async def test_get_ua_class_1(srv):
    struct_name = 'CustomizedStruct'
    struct_node = await srv.dict_builder.create_data_type(struct_name)
    struct_node.add_field('id', ua.VariantType.Int32)
    await srv.dict_builder.set_dict_byte_string()
    await srv.srv.load_type_definitions()
    try:
        assert get_ua_class(struct_name) is not None
    except AttributeError:
        pass


@pytest.mark.skip("Support for that feature currently removed")
async def test_get_ua_class_2(srv):
    struct_name = '*c*u_stom-ized&Stru#ct'
    struct_node = await srv.dict_builder.create_data_type(struct_name)
    struct_node.add_field('id', ua.VariantType.Int32)
    await srv.dict_builder.set_dict_byte_string()
    await srv.srv.load_type_definitions()
    try:
        assert get_ua_class(struct_name) is not None
    except AttributeError:
        pass


async def test_functional_basic(srv):
    basic_struct_name = 'basic_structure'
    basic_struct = await srv.dict_builder.create_data_type(basic_struct_name)
    basic_struct.add_field('ID', ua.VariantType.Int32)
    basic_struct.add_field('Gender', ua.VariantType.Boolean)
    basic_struct.add_field('Comments', ua.VariantType.String)

    await srv.dict_builder.set_dict_byte_string()
    await srv.srv.load_type_definitions()

    basic_var = await srv.srv.nodes.objects.add_variable(ua.NodeId(NamespaceIndex=srv.idx), 'BasicStruct',
                                                    ua.Variant(None, ua.VariantType.Null),
                                                    datatype=basic_struct.data_type)

    basic_msg = get_ua_class(basic_struct_name)()
    basic_msg.ID = 3
    basic_msg.Gender = True
    basic_msg.Comments = 'Test string'
    await basic_var.write_value(basic_msg)

    basic_result = await basic_var.read_value()
    assert basic_result == basic_msg
    await srv.srv.delete_nodes([basic_var])


async def test_functional_advance(srv):
    basic_struct_name = 'basic_structure'
    basic_struct = await srv.dict_builder.create_data_type(basic_struct_name)
    basic_struct.add_field('ID', ua.VariantType.Int32)
    basic_struct.add_field('Gender', ua.VariantType.Boolean)
    basic_struct.add_field('Comments', ua.VariantType.String)

    nested_struct_name = 'nested_structure'
    nested_struct = await srv.dict_builder.create_data_type(nested_struct_name)
    nested_struct.add_field('Name', ua.VariantType.String)
    nested_struct.add_field('Surname', ua.VariantType.String)
    nested_struct.add_field('Stuff', basic_struct)

    await srv.dict_builder.set_dict_byte_string()
    await srv.srv.load_type_definitions()

    basic_var = await srv.srv.nodes.objects.add_variable(ua.NodeId(NamespaceIndex=srv.idx), 'BasicStruct',
                                                    ua.Variant(None, ua.VariantType.ExtensionObject),
                                                    datatype=basic_struct.data_type)

    basic_msg = get_ua_class(basic_struct_name)()
    basic_msg.ID = 3
    basic_msg.Gender = True
    basic_msg.Comments = 'Test string'
    await basic_var.write_value(basic_msg)

    nested_var = await srv.srv.nodes.objects.add_variable(ua.NodeId(NamespaceIndex=srv.idx), 'NestedStruct',
                                                     ua.Variant(None, ua.VariantType.ExtensionObject),
                                                     datatype=nested_struct.data_type)

    nested_msg = get_ua_class(nested_struct_name)()
    nested_msg.Stuff = basic_msg
    nested_msg.Name = 'Max'
    nested_msg.Surname = 'Karl'
    await nested_var.write_value(nested_msg)

    basic_result = await basic_var.read_value()
    assert basic_result == basic_msg
    nested_result = await nested_var.read_value()
    assert nested_result == nested_msg
    await srv.srv.delete_nodes([basic_var, nested_var])


async def test_bitfields(srv):
    # We use a bsd file from a server dict, because we only provide bitsets for backwards compatibility
    xmlpath = "tests/custom_extension_with_optional_fields.xml"
    structs_dict = {}
    c = StructGenerator()
    c.make_model_from_file(xmlpath)
    c.get_python_classes(structs_dict)
    for m in c.model:
        if type(m) in (Struct, EnumType):
            m.typeid = ua.NodeId(m.name, 1)
            ua.register_extension_object(m.name, m.typeid, structs_dict[m.name])
            c.set_typeid(m.name, m.typeid.to_string())
    await srv.dict_builder.set_dict_byte_string()
    await srv.srv.load_type_definitions()
    v = ua.ProcessValueType(name='XXX')
    bitfield_var = await srv.srv.nodes.objects.add_variable(
        ua.NodeId(NamespaceIndex=srv.idx), 'BitFieldSetsTest',
        ua.Variant(None, ua.VariantType.ExtensionObject),
        datatype=ua.NodeId('ProcessValueType', 1)
    )
    await bitfield_var.write_value(v)
    bit_res = await bitfield_var.read_value()
    assert v.cavityId is None
    assert v.description is None
    assert v == bit_res
    v.cavityId = ua.UInt16(123)
    await bitfield_var.write_value(v)
    bit_res = await bitfield_var.read_value()
    assert v == bit_res
    assert bit_res.description is None
    assert bit_res.cavityId is not None
    v.description = '1234'
    v.cavityId = None
    await bitfield_var.write_value(v)
    bit_res = await bitfield_var.read_value()
    assert v == bit_res
    assert bit_res.description is not None
    assert bit_res.cavityId is None
    v.description = 'test'
    v.cavityId = ua.UInt16(44)
    await bitfield_var.write_value(v)
    bit_res = await bitfield_var.read_value()
    assert v == bit_res
    assert bit_res.description is not None
    assert bit_res.cavityId is not None
