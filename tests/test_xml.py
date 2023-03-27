import uuid
import logging
import datetime
import pathlib
import pytest

from pytz import timezone

from asyncua import ua, Node, uamethod
from asyncua.common.structures104 import new_struct, new_struct_field
from asyncua.ua import uaerrors

_logger = logging.getLogger("asyncua.common.xmlimporter")
_logger.setLevel(logging.DEBUG)
_logger = logging.getLogger("asyncua.common.xmlparser")
_logger.setLevel(logging.DEBUG)

pytestmark = pytest.mark.asyncio

BASE_DIR = pathlib.Path(__file__).parent.absolute()
CUSTOM_NODES_XML_PATH = BASE_DIR / "custom_nodes.xml"
CUSTOM_NODES_NS_XML_PATH = BASE_DIR / "custom_nodesns.xml"
CUSTOM_NODES_NS_XML_PATH1 = BASE_DIR / "custom_nodesns_2.xml"
CUSTOM_NODES_NS_XML_PATH2 = BASE_DIR / "custom_nodesns_3.xml"
CUSTOM_NODES_NS_XML_PATH3 = BASE_DIR / "custom_nodesns_4.xml"
CUSTOM_NS_META_ADD_XML_PATH = BASE_DIR / "custom_ns_meta_add.xml"
CUSTOM_REQ_XML_PASS_PATH = BASE_DIR / "test_requirement_pass.xml"
CUSTOM_REQ_XML_FAIL_PATH = BASE_DIR / "test_requirement_fail.xml"
NODESET_DI = BASE_DIR / "Nodesets" / "Opc.Ua.Di.NodeSet2.xml"
NODESET_SCALES = BASE_DIR / "Nodesets" / "Opc.Ua.Scales.NodeSet2.xml"
NODESET_PACK = BASE_DIR / "Nodesets" / "Opc.Ua.PackML.NodeSet2.xml"
NODESET_TMC = BASE_DIR / "Nodesets" / "Opc.Ua.TMC.NodeSet2.xml"


@uamethod
def func(parent, value, string):
    return value * 2


async def test_xml_import(opc):
    nodes = await opc.opc.import_xml(CUSTOM_NODES_XML_PATH)
    o = opc.opc.nodes.objects
    v = await o.get_child(["1:MyXMLFolder", "1:MyXMLObject", "1:MyXMLVariable"])
    val = await v.read_value()
    assert "StringValue" == val
    node_path = ["Types", "DataTypes", "BaseDataType", "Enumeration", "1:MyEnum", "0:EnumStrings"]
    o = await opc.opc.nodes.root.get_child(node_path)
    assert 3 == len(await o.read_value())
    # Check if method is imported
    node_path = ["Types", "ObjectTypes", "BaseObjectType", "1:MyObjectType", "1:MyMethod"]
    o = await opc.opc.nodes.root.get_child(node_path)
    assert 4 == len(await o.get_referenced_nodes())
    # Check if InputArgs are imported and can be read
    node_path = ["Types", "ObjectTypes", "BaseObjectType", "1:MyObjectType", "1:MyMethod", "InputArguments"]
    o = await opc.opc.nodes.root.get_child(node_path)
    input_arg = (await o.read_data_value()).Value.Value[0]
    assert "Context" == input_arg.Name
    await opc.opc.delete_nodes([v])
    for nodeid in nodes:
        await opc.opc.delete_nodes([opc.opc.get_node(nodeid)])


async def test_xml_import_companion_specifications(opc):
    # if not already shift the new namespaces
    await opc.server.register_namespace("http://placeholder.toincrease.nsindex")
    # Test against some companion specifications
    nodes = await opc.opc.import_xml(NODESET_DI)
    nodes += await opc.opc.import_xml(NODESET_SCALES)
    if opc.opc == opc.server:
        # Only load in server testcase takes to long if the networklayer is involved
        nodes += await opc.opc.import_xml(NODESET_PACK)
        nodes += await opc.opc.import_xml(NODESET_TMC)
    for nodeid in nodes:
        await opc.opc.delete_nodes([opc.opc.get_node(nodeid)])


async def test_xml_import_additional_ns(opc):
    # if not already shift the new namespaces
    await opc.server.register_namespace("http://placeholder.toincrease.nsindex")
    # "tests/custom_nodes.xml" isn't created with namespaces in mind, provide new test file
    # the ns=1 in to file now should be mapped to ns=2
    z = await opc.opc.import_xml(CUSTOM_NODES_NS_XML_PATH)
    ns = await opc.opc.get_namespace_index("http://examples.freeopcua.github.io/")
    o = opc.opc.nodes.objects
    o2 = await o.get_child([f"{ns}:MyBaseObject"])
    assert o2 is not None
    v1 = await o.get_child([f"{ns}:MyBaseObject", f"{ns}:MyVar"])
    assert v1 is not None
    r1 = (await o2.get_references(refs=ua.ObjectIds.HasComponent))[0]
    assert ns == r1.NodeId.NamespaceIndex
    r3 = (await v1.get_references(refs=ua.ObjectIds.HasComponent))[0]
    assert ns == r3.NodeId.NamespaceIndex
    for nodeid in z:
        await opc.opc.delete_nodes([opc.opc.get_node(nodeid)])


async def test_xml_import_ns_dependencies(opc):
    a = await opc.opc.import_xml(CUSTOM_NODES_NS_XML_PATH)
    b = await opc.opc.import_xml(CUSTOM_NODES_NS_XML_PATH1)
    c = await opc.opc.import_xml(CUSTOM_NODES_NS_XML_PATH2)
    d = await opc.opc.import_xml(CUSTOM_NODES_NS_XML_PATH3)
    ns = await opc.opc.get_namespace_index("http://examples.freeopcua.github.io/")
    ns2 = await opc.opc.get_namespace_index("http://examples.freeopcua.github.io/xmlfile_1/")
    ns3 = await opc.opc.get_namespace_index("http://examples.freeopcua.github.io/xmlfile_2/")
    ns4 = await opc.opc.get_namespace_index("http://examples.freeopcua.github.io/xmlfile_3/")
    o = opc.opc.nodes.objects
    o2 = await o.get_child([f"{ns}:MyBaseObject"])
    assert o2 is not None
    o3 = await o2.get_child([f"{ns2}:MySecondLevel"])
    assert o3 is not None
    o4 = await o3.get_child([f"{ns3}:MyThirdLevel"])
    assert o4 is not None
    o5 = await o4.get_child([f"{ns4}:MyForthLevel"])
    assert o5 is not None
    for imported_nodes in [a, b, c, d]:
        for nodeid in imported_nodes:
            await opc.opc.delete_nodes([opc.opc.get_node(nodeid)])


async def test_xml_method(opc, tmpdir):
    await opc.opc.register_namespace("foo")
    await opc.opc.register_namespace("bar")
    o = await opc.opc.nodes.objects.add_object(2, "xmlexportmethod")
    m = await o.add_method(2, "callme", func, [ua.VariantType.Double, ua.VariantType.String], [ua.VariantType.Float])
    # set an arg dimension to a list to test list export
    inputs = await m.get_child("InputArguments")
    val = await inputs.read_value()
    val[0].ArrayDimensions = [2, 2]
    desc = "My nce description"
    val[0].Description = ua.LocalizedText(desc)
    await inputs.write_value(val)
    # get all nodes and export
    nodes = [o, m]
    nodes.extend(await m.get_children())
    tmp_path = tmpdir.join("tmp_test_export.xml").strpath
    await opc.opc.export_xml(nodes, tmp_path, export_values=True)
    await opc.opc.delete_nodes(nodes)
    await opc.opc.import_xml(tmp_path)
    # now see if our nodes are here
    val = await inputs.read_value()
    assert 2 == len(val)
    assert [2, 2] == val[0].ArrayDimensions
    assert desc == val[0].Description.Text


async def test_xml_vars(opc, tmpdir):
    tmp_path = tmpdir.join("tmp_test_export-vars.xml").strpath
    await opc.opc.register_namespace("foo")
    await opc.opc.register_namespace("bar")
    o = await opc.opc.nodes.objects.add_object(2, "xmlexportobj")
    v = await o.add_variable(3, "myxmlvar", 6.78, ua.VariantType.Double)
    a = await o.add_variable(3, "myxmlvar-array", [6, 1], ua.VariantType.UInt16)
    a2 = await o.add_variable(3, "myxmlvar-2dim", [[1, 2], [3, 4]], ua.VariantType.UInt32)
    a3 = await o.add_variable(3, "myxmlvar-2dim2", [[]], ua.VariantType.ByteString)
    nodes = [o, v, a, a2, a3]
    await opc.opc.export_xml(nodes, tmp_path, export_values=True)
    await opc.opc.delete_nodes(nodes)
    await opc.opc.import_xml(tmp_path)
    assert 6.78 == await v.read_value()
    assert ua.NodeId(ua.ObjectIds.Double) == await v.read_data_type()
    assert ua.NodeId(ua.ObjectIds.UInt16) == await a.read_data_type()
    assert await a.read_value_rank() in (0, 1)
    assert [6, 1] == await a.read_value()
    assert [[1, 2], [3, 4]] == await a2.read_value()
    assert ua.NodeId(ua.ObjectIds.UInt32) == await a2.read_data_type()
    assert await a2.read_value_rank() in (0, 2)
    assert [2, 2] == (await a2.read_attribute(ua.AttributeIds.ArrayDimensions)).Value.Value
    # assert a3.read_value(), [[]])  # would require special code ...
    assert ua.NodeId(ua.ObjectIds.ByteString) == await a3.read_data_type()
    assert await a3.read_value_rank() in (0, 2)
    assert [1, 0] == (await a3.read_attribute(ua.AttributeIds.ArrayDimensions)).Value.Value


async def test_xml_ns(opc, tmpdir):
    """
    This test is far too complicated but catches a lot of things...
    """
    ns_array = await opc.opc.get_namespace_array()
    if len(ns_array) < 3:
        await opc.opc.register_namespace("dummy_ns")
    ref_ns = await opc.opc.register_namespace("ref_namespace")
    new_ns = await opc.opc.register_namespace("my_new_namespace")
    bname_ns = await opc.opc.register_namespace("bname_namespace")
    o = await opc.opc.nodes.objects.add_object(0, "xmlns0")
    o50 = await opc.opc.nodes.objects.add_object(50, "xmlns20")
    o200 = await opc.opc.nodes.objects.add_object(200, "xmlns200")
    onew = await opc.opc.nodes.objects.add_object(new_ns, "xmlns_new")
    vnew = await onew.add_variable(new_ns, "xmlns_new_var", 9.99)
    o_no_export = await opc.opc.nodes.objects.add_object(ref_ns, "xmlns_parent")
    v_no_parent = await o_no_export.add_variable(new_ns, "xmlns_new_var_no_parent", 9.99)
    o_bname = await onew.add_object(f"ns={new_ns};i=4000", f"{bname_ns}:BNAME")
    nodes = [o, o50, o200, onew, vnew, v_no_parent, o_bname]
    tmp_path = tmpdir.join("tmp_test_export-ns.xml").strpath
    await opc.opc.export_xml(nodes, tmp_path, export_values=True)
    # delete node and change index og new_ns before re-importing
    await opc.opc.delete_nodes(nodes)
    ns_node = opc.opc.get_node(ua.NodeId(ua.ObjectIds.Server_NamespaceArray))
    nss = await ns_node.read_value()
    nss.remove("my_new_namespace")
    # nss.remove("ref_namespace")
    nss.remove("bname_namespace")
    await ns_node.write_value(nss)
    new_ns = await opc.opc.register_namespace("my_new_namespace_offsett")
    new_ns = await opc.opc.register_namespace("my_new_namespace")
    _ = await opc.opc.import_xml(tmp_path)
    for i in [o, o50, o200]:
        await i.read_browse_name()
    with pytest.raises(uaerrors.BadNodeIdUnknown):
        await onew.read_browse_name()
    # since my_new_namesspace2 is referenced byt a node it should have been reimported
    nss = await opc.opc.get_namespace_array()
    assert "bname_namespace" in nss
    # get index of namespaces after import
    new_ns = await opc.opc.register_namespace("my_new_namespace")
    bname_ns = await opc.opc.register_namespace("bname_namespace")

    nnode = Node(onew.session, ua.NodeId(Identifier=onew.nodeid.Identifier, NamespaceIndex=new_ns))
    await nnode.read_browse_name()
    vnew2 = (await nnode.get_children())[0]
    assert vnew2.nodeid.NamespaceIndex == new_ns


async def test_xml_float(opc, tmpdir):
    o = await opc.opc.nodes.objects.add_variable(2, "xmlfloat", 5.67)
    dtype = await o.read_data_type()
    dv = await o.read_data_value()
    tmp_path = tmpdir.join("tmp_test_export-float.xml").strpath
    await opc.opc.export_xml([o], tmp_path, export_values=True)
    await opc.opc.delete_nodes([o])
    new_nodes = await opc.opc.import_xml(tmp_path)
    o2 = opc.opc.get_node(new_nodes[0])
    assert o2 == o
    assert await o2.read_data_type() == dtype
    assert (await o2.read_data_value()).Value == dv.Value
    await opc.opc.delete_nodes([o, o2])


async def test_xml_bool(opc, tmpdir):
    o = await opc.opc.nodes.objects.add_variable(2, "xmlbool", True)
    await _test_xml_var_type(opc, tmpdir, o, "bool")
    await opc.opc.delete_nodes([o])


async def test_xml_string(opc, tmpdir):
    o = await opc.opc.nodes.objects.add_variable(2, "xmlstring", "mystring")
    await _test_xml_var_type(opc, tmpdir, o, "string")
    await opc.opc.delete_nodes([o])


async def test_xml_string_with_null_description(opc, tmpdir):
    o = await opc.opc.nodes.objects.add_variable(2, "xmlstring", "mystring")
    await o.write_attribute(ua.AttributeIds.Description, ua.DataValue(ua.Variant(ua.LocalizedText())))
    o2 = await _test_xml_var_type(opc, tmpdir, o, "string")
    assert await o.read_description() == await o2.read_description()
    await opc.opc.delete_nodes([o, o2])


async def test_xml_string_array(opc, tmpdir):
    o = await opc.opc.nodes.objects.add_variable(2, "xmlstringarray", ["mystring2", "mystring3"])
    node2 = await _test_xml_var_type(opc, tmpdir, o, "stringarray")
    _ = await node2.read_data_value()
    await opc.opc.delete_nodes([o, node2])


async def test_xml_guid(opc, tmpdir):
    o = await opc.opc.nodes.objects.add_variable(2, "xmlguid", uuid.uuid4())
    await _test_xml_var_type(opc, tmpdir, o, "guid")
    await opc.opc.delete_nodes([o])


async def test_xml_guid_array(opc, tmpdir):
    o = await opc.opc.nodes.objects.add_variable(2, "xmlguid", [uuid.uuid4(), uuid.uuid4()])
    await _test_xml_var_type(opc, tmpdir, o, "guid_array")
    await opc.opc.delete_nodes([o])


async def test_xml_datetime(opc, tmpdir):
    o = await opc.opc.nodes.objects.add_variable(3, "myxmlvar-dt", datetime.datetime.utcnow(), ua.VariantType.DateTime)
    await _test_xml_var_type(opc, tmpdir, o, "datetime")
    await opc.opc.delete_nodes([o])


async def test_xml_datetime_array(opc, tmpdir):
    o = await opc.opc.nodes.objects.add_variable(3, "myxmlvar-array", [
        datetime.datetime.now(),
        datetime.datetime.utcnow(),
        datetime.datetime.now(timezone("Asia/Tokyo"))
    ], ua.VariantType.DateTime)
    await _test_xml_var_type(opc, tmpdir, o, "datetime_array")
    await opc.opc.delete_nodes([o])


async def test_xml_qualifiedname(opc, tmpdir):
    o = await opc.opc.nodes.objects.add_variable(2, "xmlltext", ua.QualifiedName("mytext", 5))
    await _test_xml_var_type(opc, tmpdir, o, "qualified_name")
    await opc.opc.delete_nodes([o])


async def test_xml_qualifiedname_array(opc, tmpdir):
    o = await opc.opc.nodes.objects.add_variable(2, "xmlltext_array", [ua.QualifiedName("erert", 5), ua.QualifiedName("erert33", 6)])
    await _test_xml_var_type(opc, tmpdir, o, "qualified_name_array")
    await opc.opc.delete_nodes([o])


async def test_xml_xmlelement(opc, tmpdir):
    o = await opc.opc.nodes.objects.add_variable(2, "xmllxmlelement", ua.XmlElement("XMLElem"))
    await _test_xml_var_type(opc, tmpdir, o, "xmlelement")
    await opc.opc.delete_nodes([o])


async def test_xml_xmlelement_array(opc, tmpdir):
    o = await opc.opc.nodes.objects.add_variable(2, "xmllxmlelement_array", [ua.XmlElement("XMLElem1"), ua.XmlElement("XMLElem2")], ua.VariantType.XmlElement)
    await _test_xml_var_type(opc, tmpdir, o, "xmlelement_array")
    await opc.opc.delete_nodes([o])


async def test_xml_expanded_nodeid(opc, tmpdir):
    o = await opc.opc.nodes.objects.add_variable(2, "xmllexpandednodeid", ua.ExpandedNodeId(32, 1, None, "urn://testxml", 1))
    await _test_xml_var_type(opc, tmpdir, o, "expanded_nodeid")
    await opc.opc.delete_nodes([o])


async def test_xml_expanded_nodeid_array(opc, tmpdir):
    o = await opc.opc.nodes.objects.add_variable(2, "xmllexpandednodeid_array", [ua.ExpandedNodeId(32, 1, None, "urn://testxml", 1), ua.ExpandedNodeId(33, 5, None, "urn://testxml2", 2)])
    await _test_xml_var_type(opc, tmpdir, o, "expanded_nodeid_array")
    await opc.opc.delete_nodes([o])


async def test_xml_bytestring(opc, tmpdir):
    o = await opc.opc.nodes.objects.add_variable(2, "xmlltext", "mytext".encode("utf8"), ua.VariantType.ByteString)
    await _test_xml_var_type(opc, tmpdir, o, "bytestring")
    await opc.opc.delete_nodes([o])


async def test_xml_statuscode(opc, tmpdir):
    o = await opc.opc.nodes.objects.add_variable(2, "xmllstatuscode", ua.StatusCode(value=ua.StatusCodes.BadNodeIdInvalid))
    await _test_xml_var_type(opc, tmpdir, o, "statuscode")
    await opc.opc.delete_nodes([o])


async def test_xml_statuscode_array(opc, tmpdir):
    o = await opc.opc.nodes.objects.add_variable(2, "xmllstatuscode_array", [ua.StatusCode(value=ua.StatusCodes.BadNodeIdInvalid), ua.StatusCode(value=ua.StatusCodes.BadNodeIdExists)])
    await _test_xml_var_type(opc, tmpdir, o, "statuscode_array")
    await opc.opc.delete_nodes([o])


async def test_xml_bytestring_array(opc, tmpdir):
    o = await opc.opc.nodes.objects.add_variable(2, "xmlltext_array",
                                                 ["mytext".encode("utf8"), "errsadf".encode("utf8")],
                                                 ua.VariantType.ByteString)
    await _test_xml_var_type(opc, tmpdir, o, "bytestring_array")
    await opc.opc.delete_nodes([o])


async def test_xml_localizedtext(opc, tmpdir):
    o = await opc.opc.nodes.objects.add_variable(2, "xmlltext", ua.LocalizedText("mytext"))
    await _test_xml_var_type(opc, tmpdir, o, "localized_text")
    await opc.opc.delete_nodes([o])


async def test_xml_localizedtext_with_locale(opc, tmpdir):
    o = await opc.opc.nodes.objects.add_variable(2, "xmlltext", ua.LocalizedText("mytext", "en-US"))
    await _test_xml_var_type(opc, tmpdir, o, "localized_text")
    await opc.opc.delete_nodes([o])


async def test_xml_localizedtext_array(opc, tmpdir):
    o = await opc.opc.nodes.objects.add_variable(2, "xmlltext_array",
                                                 [ua.LocalizedText("erert"), ua.LocalizedText("erert33")])
    await _test_xml_var_type(opc, tmpdir, o, "localized_text_array")
    await opc.opc.delete_nodes([o])


async def test_xml_localizedtext_array_with_locale(opc, tmpdir):
    o = await opc.opc.nodes.objects.add_variable(2, "xmlltext_array",
                                                 [ua.LocalizedText(Text="erert", Locale="en"),
                                                  ua.LocalizedText(Text="erert33", Locale="de")])
    await _test_xml_var_type(opc, tmpdir, o, "localized_text_array")
    await opc.opc.delete_nodes([o])


async def test_xml_nodeid(opc, tmpdir):
    o = await opc.opc.nodes.objects.add_variable(2, "xmlnodeid", ua.NodeId("mytext", 1))
    await _test_xml_var_type(opc, tmpdir, o, "nodeid")
    await opc.opc.delete_nodes([o])


async def test_xml_ext_obj(opc, tmpdir):
    arg = ua.Argument()
    arg.DataType = ua.NodeId(ua.ObjectIds.Float)
    arg.Description = ua.LocalizedText("Nice description")
    arg.ArrayDimensions = [1, 2, 3]
    arg.Name = "MyArg"
    node = await opc.opc.nodes.objects.add_variable(2, "xmlexportobj2", arg)
    node2 = await _test_xml_var_type(opc, tmpdir, node, "ext_obj", test_equality=False)
    arg2 = await node2.read_value()
    assert arg.Name == arg2.Name
    assert arg.ArrayDimensions == arg2.ArrayDimensions
    assert arg.Description == arg2.Description
    assert arg.DataType == arg2.DataType
    await opc.opc.delete_nodes([node, node2])


async def test_xml_ext_obj_array(opc, tmpdir):
    arg = ua.Argument()
    arg.DataType = ua.NodeId(ua.ObjectIds.Float)
    arg.Description = ua.LocalizedText("Nice description")
    arg.ArrayDimensions = [1, 2, 3]
    arg.Name = "MyArg"
    arg2 = ua.Argument()
    arg2.DataType = ua.NodeId(ua.ObjectIds.Int32)
    arg2.Description = ua.LocalizedText("Nice description2")
    arg2.ArrayDimensions = [4, 5, 6]
    arg2.Name = "MyArg2"
    args = [arg, arg2]
    node = await opc.opc.nodes.objects.add_variable(2, "xmlexportobj2", args)
    node2 = await _test_xml_var_type(opc, tmpdir, node, "ext_obj_array", test_equality=False)
    read_args = await node2.read_value()
    for i, arg in enumerate(read_args):
        assert args[i].Name == read_args[i].Name
        assert args[i].ArrayDimensions == read_args[i].ArrayDimensions
        assert args[i].Description == read_args[i].Description
        assert args[i].DataType == read_args[i].DataType
    await opc.opc.delete_nodes([node, node2])


async def test_xml_enum(opc, tmpdir):
    o = await opc.opc.nodes.objects.add_variable(2, "xmlenum", 0, varianttype=ua.VariantType.Int32,
                                                 datatype=ua.ObjectIds.ApplicationType)
    await _test_xml_var_type(opc, tmpdir, o, "enum")
    await opc.opc.delete_nodes([o])


async def test_xml_enumvalues(opc, tmpdir):
    o = await opc.opc.nodes.objects.add_variable(2, "xmlenumvalues", 0, varianttype=ua.VariantType.UInt32,
                                                 datatype=ua.ObjectIds.AttributeWriteMask)
    await _test_xml_var_type(opc, tmpdir, o, "enumvalues")
    await opc.opc.delete_nodes([o])


async def test_xml_custom_uint32(opc, tmpdir):
    # t = opc.opc.nodes. create_custom_data_type(2, 'MyCustomUint32', ua.ObjectIds.UInt32)
    t = await opc.opc.get_node(ua.ObjectIds.UInt32).add_data_type(2, 'MyCustomUint32')
    o = await opc.opc.nodes.objects.add_variable(2, "xmlcustomunit32", 0, varianttype=ua.VariantType.UInt32,
                                                 datatype=t.nodeid)
    await _test_xml_var_type(opc, tmpdir, o, "cuint32")
    await opc.opc.delete_nodes([o, t])


async def test_xml_var_nillable(opc):
    xml = """
    <UANodeSet xmlns="http://opcfoundation.org/UA/2011/03/UANodeSet.xsd" xmlns:uax="http://opcfoundation.org/UA/2008/02/Types.xsd" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
      <NamespaceUris>
      </NamespaceUris>
      <Aliases>
        <Alias Alias="Boolean">i=1</Alias>
        <Alias Alias="String">i=12</Alias>
        <Alias Alias="HasTypeDefinition">i=40</Alias>
        <Alias Alias="HasComponent">i=47</Alias>
      </Aliases>
      <UAVariable BrowseName="2:xmlstring" DataType="String" NodeId="ns=2;s=test_xml.string.nillabel" ParentNodeId="i=85">
        <DisplayName>xmlstring</DisplayName>
        <Description>xmlstring</Description>
        <References>
          <Reference IsForward="false" ReferenceType="HasComponent">i=85</Reference>
          <Reference ReferenceType="HasTypeDefinition">i=63</Reference>
        </References>
        <Value>
            <uax:String></uax:String>
        </Value>
      </UAVariable>

     <UAVariable BrowseName="2:xmlbool" DataType="Boolean" NodeId="ns=2;s=test_xml.bool.nillabel" ParentNodeId="i=85">
        <DisplayName>xmlbool</DisplayName>
        <Description>xmlbool</Description>
        <References>
          <Reference IsForward="false" ReferenceType="HasComponent">i=85</Reference>
          <Reference ReferenceType="HasTypeDefinition">i=63</Reference>
        </References>
        <Value>
          <uax:Boolean></uax:Boolean>
        </Value>
      </UAVariable>

    </UANodeSet>
    """
    _ = await opc.opc.import_xml(xmlstring=xml)
    var_string = opc.opc.get_node(ua.NodeId('test_xml.string.nillabel', 2))
    var_bool = opc.opc.get_node(ua.NodeId('test_xml.bool.nillabel', 2))
    assert await var_string.read_value() is None
    assert await var_bool.read_value() is None
    await opc.opc.delete_nodes([var_string, var_bool])


async def _test_xml_var_type(opc, tmpdir, node: Node, typename: str, test_equality: bool = True):
    dtype = await node.read_data_type()
    dv = await node.read_data_value()
    rank = await node.read_value_rank()
    dim = await node.read_array_dimensions()
    nclass = await node.read_node_class()
    tmp_path = tmpdir.join(f"tmp_test_export-{typename}.xml").strpath
    await opc.opc.export_xml([node], tmp_path, export_values=True)
    await opc.opc.delete_nodes([node])
    new_nodes = await opc.opc.import_xml(tmp_path)
    node2 = opc.opc.get_node(new_nodes[0])
    assert node == node
    assert dtype == await node2.read_data_type()
    if test_equality:
        _logger.debug(node, dv, node2, await node2.read_value())
        _ = await node2.read_value()
        assert dv.Value == (await node2.read_data_value()).Value
    assert rank == await node2.read_value_rank()
    assert dim == await node2.read_array_dimensions()
    assert nclass == await node2.read_node_class()
    return node2


async def test_xml_byte(opc, tmpdir):
    o = await opc.opc.nodes.objects.add_variable(2, "byte", 255, ua.VariantType.Byte)
    dtype = await o.read_data_type()
    dv = await o.read_data_value()
    tmp_path = tmpdir.join("export-byte.xml").strpath
    await opc.opc.export_xml([o], tmp_path, export_values=True)
    await opc.opc.delete_nodes([o])
    new_nodes = await opc.opc.import_xml(tmp_path)
    o2 = opc.opc.get_node(new_nodes[0])
    assert o == o2
    assert dtype == await o2.read_data_type()
    assert dv.Value == (await o2.read_data_value()).Value
    await opc.opc.delete_nodes([o2])


async def test_xml_union(opc, tmpdir):
    idx = 4
    o, _ = await new_struct(opc.opc, idx, "MyUnionStruct2", [
        new_struct_field("MyString", ua.VariantType.String),
        new_struct_field("MyInt64", ua.VariantType.Int64),
    ], is_union=True)
    tmp_path = tmpdir.join("export-union.xml").strpath
    await opc.opc.export_xml([o], tmp_path, export_values=True)
    await opc.opc.delete_nodes([o])
    new_nodes = await opc.opc.import_xml(tmp_path)
    o2 = opc.opc.get_node(new_nodes[0])
    assert o == o2
    await opc.opc.load_data_type_definitions()
    t = ua.MyUnionStruct2()
    t.MyString = "abc"
    assert t.MyString == "abc"
    assert t.MyInt64 is None


async def test_xml_struct_optional(opc, tmpdir):
    idx = 4
    o, _ = await new_struct(opc.opc, idx, "MyOptionalStruct2", [
        new_struct_field("MyString", ua.VariantType.String, optional=True),
        new_struct_field("MyInt64", ua.VariantType.Int64, optional=True),
    ])
    tmp_path = tmpdir.join("export-optional.xml").strpath
    await opc.opc.export_xml([o], tmp_path, export_values=True)
    await opc.opc.delete_nodes([o])
    new_nodes = await opc.opc.import_xml(tmp_path)
    o2 = opc.opc.get_node(new_nodes[0])
    assert o == o2
    await opc.opc.load_data_type_definitions()
    t = ua.MyOptionalStruct2()
    t.MyInt64 = 5
    assert t.MyString is None
    assert t.MyInt64 == 5


async def test_xml_struct_with_value(opc, tmpdir):
    idx = 4
    my_struct, _ = await new_struct(opc.opc, idx, "MyStructWithValue", [
        new_struct_field("int_value", ua.VariantType.Int64, optional=False),
    ])
    await opc.opc.load_data_type_definitions()
    valnode = await opc.opc.nodes.objects.add_variable(idx, "my_struct", ua.Variant(ua.MyStructWithValue(), ua.VariantType.ExtensionObject))

    new_value = ua.MyStructWithValue()
    new_value.int_value = 14
    await valnode.write_value(ua.Variant(new_value, ua.VariantType.ExtensionObject))

    tmp_path = tmpdir.join("export-struct-with-value.xml").strpath
    await opc.opc.export_xml([my_struct, valnode], tmp_path, export_values=True)
    await opc.opc.delete_nodes([my_struct, valnode])
    new_nodes = await opc.opc.import_xml(tmp_path)
    imported_my_struct = opc.opc.get_node(new_nodes[0])
    imported_valnode = opc.opc.get_node(new_nodes[1])
    assert my_struct == imported_my_struct
    assert valnode == imported_valnode
    await opc.opc.load_data_type_definitions()

    value = await valnode.read_value()
    imported_value = await imported_valnode.read_value()
    assert value == imported_value


async def test_xml_struct_in_struct_with_value(opc, tmpdir):
    idx = 4
    inner_struct, _ = await new_struct(opc.opc, idx, "MyInnerStruct", [
        new_struct_field("int_value", ua.VariantType.Int64, optional=False),
    ])
    outer_struct, _ = await new_struct(opc.opc, idx, "MyOuterStruct", [
        new_struct_field("inner_struct_value", inner_struct, optional=False),
    ])
    await opc.opc.load_data_type_definitions()
    valnode = await opc.opc.nodes.objects.add_variable(idx, "my_outer_struct", ua.Variant(ua.MyOuterStruct(), ua.VariantType.ExtensionObject))

    new_value = ua.MyOuterStruct()
    new_value.inner_struct_value.int_value = 42
    await valnode.write_value(ua.Variant(new_value, ua.VariantType.ExtensionObject))

    tmp_path = tmpdir.join("export-struct-in-struct-with-value.xml").strpath
    await opc.opc.export_xml([outer_struct, inner_struct, valnode], tmp_path, export_values=True)
    await opc.opc.delete_nodes([outer_struct, inner_struct, valnode])
    new_nodes = await opc.opc.import_xml(tmp_path)
    imported_outer_struct = opc.opc.get_node(new_nodes[0])
    imported_inner_struct = opc.opc.get_node(new_nodes[1])
    imported_valnode = opc.opc.get_node(new_nodes[2])
    assert outer_struct == imported_outer_struct
    assert inner_struct == imported_inner_struct
    await opc.opc.load_data_type_definitions()

    value = await valnode.read_value()
    imported_value = await imported_valnode.read_value()
    assert value == imported_value


async def test_basetype_alias(opc):
    idx = 4
    # Alias double
    _ = await opc.opc.get_node(ua.NodeId(11)).add_data_type(ua.NodeId(NamespaceIndex=idx), '4:MyDouble')
    await opc.opc.load_data_type_definitions()
    assert ua.MyDouble(4.0) == ua.Double(4.0)


async def test_xml_required_models_fail(opc):
    with pytest.raises(ValueError):
        await opc.opc.import_xml(CUSTOM_REQ_XML_FAIL_PATH)


async def test_xml_required_models_pass(opc):
    await opc.opc.import_xml(CUSTOM_REQ_XML_PASS_PATH)
    # check if missing namespace infos are added
    urn = "http://yourorganisation.org/testenum104/"
    idx = await opc.opc.register_namespace(urn)
    o = await opc.opc.nodes.namespaces.get_child([f"{idx}:{urn}"])
    assert await (await o.get_child("NamespaceUri")).read_value() == urn
    assert await (await o.get_child("NamespaceVersion")).read_value() == "1.0.0"
    dt = await (await o.get_child("NamespacePublicationDate")).read_value()
    assert dt.year == 2020
    assert dt.month == 8
    assert dt.day == 11


async def test_disable_xml_export_without_value(opc, tmpdir):
    # Test that a value of a node is not exportet when export_values = False
    o = await opc.opc.nodes.objects.add_variable(2, "byte_no_val", 255, ua.VariantType.Byte)
    dtype = await o.read_data_type()
    dv = await o.read_data_value()
    tmp_path = tmpdir.join("export-byte.xml").strpath
    await opc.opc.export_xml([o], tmp_path, export_values=False)
    await opc.opc.delete_nodes([o])
    new_nodes = await opc.opc.import_xml(tmp_path)
    o2 = opc.opc.get_node(new_nodes[0])
    assert o == o2
    assert dtype == await o2.read_data_type()
    v = await o2.read_data_value()
    assert dv.Value != v.Value
    assert v.Value.Value is None
    await opc.opc.delete_nodes([o2])

async def test_xml_namespace_meta_add(opc):
    with pytest.raises(ValueError):
        await opc.opc.get_namespace_index("http://foobar.org/struct_optional/")
    await opc.opc.import_xml(CUSTOM_NS_META_ADD_XML_PATH)
    assert await opc.opc.get_namespace_index("http://foobar.org/struct_optional/") > 0
