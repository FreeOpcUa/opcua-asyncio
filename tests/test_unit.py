# encoding: utf-8
# ! /usr/bin/env python
"""
Simple unit test that do not need to setup a server or a client
"""

import io
import os
import uuid
import pytest
import logging
from datetime import datetime

from asyncua import ua
from asyncua.ua.ua_binary import extensionobject_from_binary
from asyncua.ua.ua_binary import extensionobject_to_binary
from asyncua.ua.ua_binary import nodeid_to_binary, variant_to_binary, _reshape, variant_from_binary, nodeid_from_binary
from asyncua.ua.ua_binary import struct_to_binary, struct_from_binary
from asyncua.ua import flatten, get_shape
from asyncua.server.monitored_item_service import WhereClauseEvaluator
from asyncua.common.event_objects import BaseEvent
from asyncua.common.ua_utils import string_to_val, val_to_string
from asyncua.ua.uatypes import _MaskEnum
from asyncua.common.structures import StructGenerator
from asyncua.common.connection import MessageChunk

EXAMPLE_BSD_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "example.bsd"))


def test_variant_array_none():
    v = ua.Variant(None, varianttype=ua.VariantType.Int32, is_array=True)
    data = variant_to_binary(v)
    v2 = variant_from_binary(ua.utils.Buffer(data))
    assert v == v2
    assert v2.is_array

    v = ua.Variant(None, varianttype=ua.VariantType.Null, is_array=True)
    data = variant_to_binary(v)
    v2 = variant_from_binary(ua.utils.Buffer(data))
    assert v == v2
    assert v2.is_array


def test_variant_empty_list():
    v = ua.Variant([], varianttype=ua.VariantType.Int32, is_array=True)
    data = variant_to_binary(v)
    v2 = variant_from_binary(ua.utils.Buffer(data))
    assert v == v2
    assert v2.is_array


def test_custom_structs(tmpdir):
    c = StructGenerator()
    c.make_model_from_file(EXAMPLE_BSD_PATH)
    output_path = tmpdir.join("test_custom_structs.py").strpath
    c.save_to_file(output_path)
    ns = {}
    with open(output_path) as s:
        exec(s.read(), ns)
    # test with default values
    v = ns["ScalarValueDataType"]()
    data = struct_to_binary(v)
    v2 = struct_from_binary(ns["ScalarValueDataType"], ua.utils.Buffer(data))

    # set some values
    v = ns["ScalarValueDataType"]()
    v.SbyteValue = 1
    v.ByteValue = 2
    v.Int16Value = 3
    v.UInt16Value = 4
    v.Int32Value = 5
    v.UInt32Value = 6
    v.Int64Value = 7
    v.UInt64Value = 8
    v.FloatValue = 9.0
    v.DoubleValue = 10.0
    v.StringValue = "elleven"
    v.DateTimeValue = datetime.utcnow()
    # self.GuidValue = uuid.uudib"14"
    v.ByteStringValue = b"fifteen"
    v.XmlElementValue = ua.XmlElement("<toto>titi</toto>")
    v.NodeIdValue = ua.NodeId.from_string("ns=4;i=9999")
    # self.ExpandedNodeIdValue =
    # self.QualifiedNameValue =
    # self.LocalizedTextValue =
    # self.StatusCodeValue =
    # self.VariantValue =
    # self.EnumerationValue =
    # self.StructureValue =
    # self.Number =
    # self.Integer =
    # self.UInteger =

    data = struct_to_binary(v)
    v2 = struct_from_binary(ns["ScalarValueDataType"], ua.utils.Buffer(data))
    assert v.NodeIdValue == v2.NodeIdValue


def test_custom_structs_array(tmpdir):
    c = StructGenerator()
    c.make_model_from_file(EXAMPLE_BSD_PATH)
    ns = {}
    output_path = tmpdir.join("test_custom_structs_array.py").strpath
    c.save_to_file(output_path)
    with open(output_path) as s:
        exec(s.read(), ns)

    # test with default values
    v = ns["ArrayValueDataType"]()
    data = struct_to_binary(v)
    v2 = struct_from_binary(ns["ArrayValueDataType"], ua.utils.Buffer(data))

    # set some values
    v = ns["ArrayValueDataType"]()
    v.SbyteValue = [1]
    v.ByteValue = [2]
    v.Int16Value = [3]
    v.UInt16Value = [4]
    v.Int32Value = [5]
    v.UInt32Value = [6]
    v.Int64Value = [7]
    v.UInt64Value = [8]
    v.FloatValue = [9.0]
    v.DoubleValue = [10.0]
    v.StringValue = ["elleven"]
    v.DateTimeValue = [datetime.utcnow()]
    # self.GuidValue = uuid.uudib"14"
    v.ByteStringValue = [b"fifteen", b"sixteen"]
    v.XmlElementValue = [ua.XmlElement("<toto>titi</toto>")]
    v.NodeIdValue = [ua.NodeId.from_string("ns=4;i=9999"), ua.NodeId.from_string("i=6")]
    data = struct_to_binary(v)
    v2 = struct_from_binary(ns["ArrayValueDataType"], ua.utils.Buffer(data))
    assert v.NodeIdValue == v2.NodeIdValue
    # print(v2.NodeIdValue)


def test_nodeid_nsu():
    n = ua.NodeId(100, 2)
    n.NamespaceUri = "http://freeopcua/tests"
    n.ServerIndex = 4
    data = nodeid_to_binary(n)
    n2 = nodeid_from_binary(ua.utils.Buffer(data))
    assert n == n2
    n3 = ua.NodeId.from_string(n.to_string())
    assert n == n3


def test_nodeid_ordering():
    a = ua.NodeId(2000, 1)
    b = ua.NodeId(3000, 1)
    c = ua.NodeId(20, 0)
    d = ua.NodeId("tititu", 1)
    e = ua.NodeId("aaaaa", 1)
    f = ua.NodeId("aaaaa", 2)
    g = ua.NodeId(uuid.uuid4(), 1)
    h = ua.TwoByteNodeId(2001)
    i = ua.NodeId(b"lkjkl", 1, ua.NodeIdType.ByteString)
    j = ua.NodeId(b"aaa", 5, ua.NodeIdType.ByteString)

    mylist = [a, b, c, d, e, f, g, h, i, j]
    mylist.sort()
    expected = [h, c, a, b, e, d, f, g, i, j]
    assert mylist == expected


def test_string_to_variant_int():
    s_arr_uint = "[1, 2, 3, 4]"
    arr_uint = [1, 2, 3, 4]
    assert arr_uint == string_to_val(s_arr_uint, ua.VariantType.UInt32)
    assert arr_uint == string_to_val(s_arr_uint, ua.VariantType.UInt16)
    assert s_arr_uint == val_to_string(arr_uint)


def test_string_to_variant_float():
    s_arr_float = "[1.1, 2.1, 3, 4.0]"
    arr_float = [1.1, 2.1, 3, 4.0]
    s_float = "1.9"
    assert 1.9 == string_to_val(s_float, ua.VariantType.Float)
    assert s_arr_float == val_to_string(arr_float)


def test_string_to_variant_datetime_string():
    s_arr_datetime = "[2014-05-6, 2016-10-3]"
    arr_string = ['2014-05-6', '2016-10-3']
    arr_datetime = [datetime(2014, 5, 6), datetime(2016, 10, 3)]
    assert s_arr_datetime == val_to_string(arr_string)
    assert arr_string == string_to_val(s_arr_datetime, ua.VariantType.String)
    assert arr_datetime == string_to_val(s_arr_datetime, ua.VariantType.DateTime)


def test_string_to_variant_nodeid():
    s_arr_nodeid = "[ns=2;i=56, i=45]"
    arr_nodeid = [ua.NodeId.from_string("ns=2;i=56"), ua.NodeId.from_string("i=45")]
    assert arr_nodeid == string_to_val(s_arr_nodeid, ua.VariantType.NodeId)


def test_string_to_variant_status_code():
    s_statuscode = "Good"
    statuscode = ua.StatusCode(ua.StatusCodes.Good)
    s_statuscode2 = "Uncertain"
    statuscode2 = ua.StatusCode(ua.StatusCodes.Uncertain)
    assert statuscode == string_to_val(s_statuscode, ua.VariantType.StatusCode)
    assert statuscode2 == string_to_val(s_statuscode2, ua.VariantType.StatusCode)


def test_status_code_to_string():
    # serialize a status code and deserialize it, name and doc resolution should work just fine
    statuscode = ua.StatusCode(ua.StatusCodes.BadNotConnected)
    statuscode2 = struct_from_binary(ua.StatusCode, io.BytesIO(struct_to_binary(ua.StatusCode(ua.StatusCodes.BadNotConnected))))

    assert statuscode == statuscode2
    assert statuscode.value == statuscode2.value

    # properties that are not serialized should still translate properly
    assert statuscode.name == statuscode2.name
    assert statuscode.doc == statuscode2.doc


def test_string_to_variant_qname():
    string = "2:name"
    obj = ua.QualifiedName("name", 2)
    assert obj == string_to_val(string, ua.VariantType.QualifiedName)
    assert string == val_to_string(obj)


def test_string_to_variant_localized_text():
    string = "_This is my nøåæ"
    obj = ua.LocalizedText(string)
    assert obj == string_to_val(string, ua.VariantType.LocalizedText)
    assert string == val_to_string(obj)


def test_string_to_variant_localized_text_with_locale():
    locale = "cs-CZ"
    string = "Moje jméno"
    string_repr = f"LocalizedText(Encoding:3, Locale:{locale}, Text:{string})"
    obj = ua.LocalizedText(string, locale)
    assert obj == string_to_val(string_repr, ua.VariantType.LocalizedText)
    assert string_repr == val_to_string(obj)


def test_string_to_variant_localized_text_with_none1():
    locale = "en-US"
    string = ""
    string_repr = f"LocalizedText(Encoding:1, Locale:{locale}, Text:{string})"
    obj = ua.LocalizedText(string, locale)
    obj2 = ua.LocalizedText(string)
    assert obj == string_to_val(string_repr, ua.VariantType.LocalizedText)
    assert obj2 == string_to_val(string, ua.VariantType.LocalizedText)
    assert "" == val_to_string(obj)


def test_string_to_variant_localized_text_with_none2():
    locale = None
    string = "my name is ..."
    string_repr = f"LocalizedText(Encoding:2, Locale:{locale}, Text:{string})"
    obj = ua.LocalizedText(string, locale)
    assert obj == string_to_val(string_repr, ua.VariantType.LocalizedText)
    assert obj == string_to_val(string, ua.VariantType.LocalizedText)
    assert string == val_to_string(obj)


def test_string_to_val_xml_element():
    string = "<p> titi toto </p>"
    obj = ua.XmlElement(string)
    assert obj == string_to_val(string, ua.VariantType.XmlElement)
    assert string == val_to_string(obj)
    b = struct_to_binary(obj)
    obj2 = struct_from_binary(ua.XmlElement, ua.utils.Buffer(b))
    assert obj == obj2


def test_variant_dimensions():
    l = [[[1.0, 1.0, 1.0, 1.0], [2.0, 2.0, 2.0, 2.0], [3.0, 3.0, 3.0, 3.0]], [[5.0, 5.0, 5.0, 5.0], [7.0, 8.0, 9.0, 01.0], [1.0, 1.0, 1.0, 1.0]]]
    v = ua.Variant(l)
    assert [2, 3, 4] == v.Dimensions
    v2 = variant_from_binary(ua.utils.Buffer(variant_to_binary(v)))
    assert v == v2
    assert v.Dimensions == v2.Dimensions

    # very special case
    l = [[[], [], []], [[], [], []]]
    v = ua.Variant(l, ua.VariantType.UInt32)
    assert [2, 3, 0] == v.Dimensions
    v2 = variant_from_binary(ua.utils.Buffer(variant_to_binary(v)))
    assert v.Dimensions == v2.Dimensions
    assert v == v2


def test_flatten():
    l = [[[1.0, 1.0, 1.0, 1.0], [1.0, 1.0, 1.0, 1.0], [1.0, 1.0, 1.0, 1.0]], [[1.0, 1.0, 1.0, 1.0], [1.0, 1.0, 1.0, 1.0], [1.0, 1.0, 1.0, 1.0]]]
    l2 = flatten(l)
    dims = get_shape(l)
    assert [2, 3, 4] == dims
    assert l != l2

    l3 = _reshape(l2, (2, 3, 4))
    assert l == l3

    l = [[[], [], []], [[], [], []]]
    l2 = flatten(l)
    dims = get_shape(l)
    assert dims == [2, 3, 0]

    l = [1, 2, 3, 4]
    l2 = flatten(l)
    dims = get_shape(l)
    assert dims == [4]
    assert l == l2


def test_custom_variant():
    with pytest.raises(ua.UaError):
        v = ua.Variant(b"ljsdfljds", ua.VariantTypeCustom(89))
    v = ua.Variant(b"ljsdfljds", ua.VariantTypeCustom(61))
    v2 = variant_from_binary(ua.utils.Buffer(variant_to_binary(v)))
    assert v.VariantType == v2.VariantType
    assert v == v2


def test_custom_variant_array():
    v = ua.Variant([b"ljsdfljds", b"lkjsdljksdf"], ua.VariantTypeCustom(40))
    v2 = variant_from_binary(ua.utils.Buffer(variant_to_binary(v)))
    assert v.VariantType == v2.VariantType
    assert v == v2


def test_guid():
    v = ua.Variant(uuid.uuid4(), ua.VariantType.Guid)
    v2 = variant_from_binary(ua.utils.Buffer(variant_to_binary(v)))
    assert v.VariantType == v2.VariantType
    assert v == v2


def test_nodeid():
    nid = ua.NodeId()
    assert nid.NodeIdType == ua.NodeIdType.TwoByte
    nid = ua.NodeId(446, 3, ua.NodeIdType.FourByte)
    assert nid.NodeIdType == ua.NodeIdType.FourByte
    d = nodeid_to_binary(nid)
    new_nid = nodeid_from_binary(io.BytesIO(d))
    assert new_nid == nid
    assert new_nid.NodeIdType == ua.NodeIdType.FourByte
    assert new_nid.Identifier == 446
    assert new_nid.NamespaceIndex == 3

    tb = ua.TwoByteNodeId(53)
    fb = ua.FourByteNodeId(53)
    n = ua.NumericNodeId(53)
    n1 = ua.NumericNodeId(53, 0)
    s1 = ua.StringNodeId("53", 0)
    bs = ua.ByteStringNodeId(b"53", 0)
    gid = uuid.uuid4()
    g = ua.ByteStringNodeId(str(gid), 0)
    guid = ua.GuidNodeId(gid)
    assert tb == fb
    assert tb == n
    assert tb == n1
    assert n1 == fb
    assert g != guid
    assert tb == nodeid_from_binary(ua.utils.Buffer(nodeid_to_binary(tb)))
    assert fb == nodeid_from_binary(ua.utils.Buffer(nodeid_to_binary(fb)))
    assert n == nodeid_from_binary(ua.utils.Buffer(nodeid_to_binary(n)))
    assert s1 == nodeid_from_binary(ua.utils.Buffer(nodeid_to_binary(s1)))
    assert bs == nodeid_from_binary(ua.utils.Buffer(nodeid_to_binary(bs)))
    assert guid == nodeid_from_binary(ua.utils.Buffer(nodeid_to_binary(guid)))


def test_nodeid_string():
    nid0 = ua.NodeId(45)
    assert nid0 == ua.NodeId.from_string("i=45")
    assert nid0 == ua.NodeId.from_string("ns=0;i=45")
    nid = ua.NodeId(45, 10)
    assert nid == ua.NodeId.from_string("i=45; ns=10")
    assert nid != ua.NodeId.from_string("i=45; ns=11")
    assert nid != ua.NodeId.from_string("i=5; ns=10")
    # not sure the next one is correct...
    assert nid == ua.NodeId.from_string("i=45; ns=10; srv=serverid")
    nid1 = ua.NodeId("myid.mynodeid", 7)
    assert nid1 == ua.NodeId.from_string("ns=7; s=myid.mynodeid")
    # with pytest.raises(ua.UaError):
    # nid1 = ua.NodeId(7, "myid.mynodeid")
    # with pytest.raises(ua.UaError):
    # nid1 = ua.StringNodeId(1, 2)


def test_bad_string():
    with pytest.raises(ua.UaStringParsingError):
        ua.NodeId.from_string("ns=r;s=yu")
    with pytest.raises(ua.UaStringParsingError):
        ua.NodeId.from_string("i=r;ns=1")
    with pytest.raises(ua.UaStringParsingError):
        ua.NodeId.from_string("ns=1")
    with pytest.raises(ua.UaError):
        ua.QualifiedName.from_string("i:yu")
    with pytest.raises(ua.UaError):
        ua.QualifiedName.from_string("i:::yu")


def test_expandednodeid():
    nid = ua.ExpandedNodeId()
    assert nid.NodeIdType == ua.NodeIdType.TwoByte
    nid2 = nodeid_from_binary(ua.utils.Buffer(nodeid_to_binary(nid)))
    assert nid == nid2


def test_null_guid():
    n = ua.NodeId(b'000000', 0, nodeidtype=ua.NodeIdType.Guid)
    n = ua.NodeId(uuid.UUID('00000000-0000-0000-0000-000000000000'), 0, nodeidtype=ua.NodeIdType.Guid)
    assert n.is_null()
    assert n.has_null_identifier()

    n = ua.NodeId(b'000000', 1, nodeidtype=ua.NodeIdType.Guid)
    n = ua.NodeId(uuid.UUID('00000000-0000-0000-0000-000000000000'), 1, nodeidtype=ua.NodeIdType.Guid)
    assert not n.is_null()
    assert n.has_null_identifier()

    n = ua.NodeId(uuid.UUID('00000000-0000-0000-0000-000001000000'), 1, nodeidtype=ua.NodeIdType.Guid)
    assert not n.is_null()
    assert not n.has_null_identifier()


def test_null_string():
    v = ua.Variant(None, ua.VariantType.String)
    b = variant_to_binary(v)
    v2 = variant_from_binary(ua.utils.Buffer(b))
    assert v.Value == v2.Value
    v = ua.Variant("", ua.VariantType.String)
    b = variant_to_binary(v)
    v2 = variant_from_binary(ua.utils.Buffer(b))
    assert v.Value == v2.Value


def test_extension_object():
    obj = ua.UserNameIdentityToken()
    obj.UserName = "admin"
    obj.Password = b"pass"
    obj2 = extensionobject_from_binary(ua.utils.Buffer(extensionobject_to_binary(obj)))
    assert type(obj) == type(obj2)
    assert obj.UserName == obj2.UserName
    assert obj.Password == obj2.Password
    v1 = ua.Variant(obj)
    v2 = variant_from_binary(ua.utils.Buffer(variant_to_binary(v1)))
    assert type(v1) == type(v2)
    assert v1.VariantType == v2.VariantType


def test_unknown_extension_object():
    obj = ua.ExtensionObject()
    obj.Body = b'example of data in custom format'
    obj.TypeId = ua.NodeId.from_string('ns=3;i=42')
    data = ua.utils.Buffer(extensionobject_to_binary(obj))
    obj2 = extensionobject_from_binary(data)
    assert type(obj2) == ua.ExtensionObject
    assert obj2.TypeId == obj.TypeId
    assert obj2.Body == b'example of data in custom format'


def test_datetime():
    now = datetime.utcnow()
    epch = ua.datetime_to_win_epoch(now)
    dt = ua.win_epoch_to_datetime(epch)
    assert now == dt
    # python's datetime has a range from Jan 1, 0001 to the end of year 9999
    # windows' filetime has a range from Jan 1, 1601 to approx. year 30828
    # let's test an overlapping range [Jan 1, 1601 - Dec 31, 9999]
    dt = datetime(1601, 1, 1)
    assert ua.win_epoch_to_datetime(ua.datetime_to_win_epoch(dt)) == dt
    dt = datetime(9999, 12, 31, 23, 59, 59)
    assert ua.win_epoch_to_datetime(ua.datetime_to_win_epoch(dt)) == dt
    epch = 128930364000001000
    dt = ua.win_epoch_to_datetime(epch)
    epch2 = ua.datetime_to_win_epoch(dt)
    assert epch == epch2
    epch = 0
    assert ua.datetime_to_win_epoch(ua.win_epoch_to_datetime(epch)) == epch


def test_equal_nodeid():
    nid1 = ua.NodeId(999, 2)
    nid2 = ua.NodeId(999, 2)
    assert nid1 == nid2
    assert id(nid1) != id(nid2)


def test_zero_nodeid():
    assert ua.NodeId() == ua.NodeId(0, 0)
    assert ua.NodeId() == ua.NodeId.from_string('ns=0;i=0;')


def test_string_nodeid():
    nid = ua.NodeId('titi', 1)
    assert nid.NamespaceIndex == 1
    assert nid.Identifier == 'titi'
    assert nid.NodeIdType == ua.NodeIdType.String


def test_unicode_string_nodeid():
    nid = ua.NodeId('hëllò', 1)
    assert nid.NamespaceIndex == 1
    assert nid.Identifier == 'hëllò'
    assert nid.NodeIdType == ua.NodeIdType.String
    d = nodeid_to_binary(nid)
    new_nid = nodeid_from_binary(io.BytesIO(d))
    assert new_nid == nid
    assert new_nid.Identifier == 'hëllò'
    assert new_nid.NodeIdType == ua.NodeIdType.String


def test_numeric_nodeid():
    nid = ua.NodeId(999, 2)
    assert nid.NamespaceIndex == 2
    assert nid.Identifier == 999
    assert nid.NodeIdType == ua.NodeIdType.Numeric


def test_qualifiedstring_nodeid():
    nid = ua.NodeId.from_string('ns=2;s=PLC1.Manufacturer;')
    assert nid.NamespaceIndex == 2
    assert nid.Identifier == 'PLC1.Manufacturer'


def test_strrepr_nodeid():
    nid = ua.NodeId.from_string('ns=2;s=PLC1.Manufacturer;')
    assert nid.to_string() == 'ns=2;s=PLC1.Manufacturer'
    # assert repr(nid) == 'ns=2;s=PLC1.Manufacturer;'


def test_qualified_name():
    qn = ua.QualifiedName('qname', 2)
    assert qn.NamespaceIndex == 2
    assert qn.Name == 'qname'
    assert qn.to_string() == '2:qname'


def test_datavalue():
    dv = ua.DataValue(123)
    assert dv.Value == ua.Variant(123)
    assert type(dv.Value) == ua.Variant
    dv = ua.DataValue('abc')
    assert dv.Value == ua.Variant('abc')
    now = datetime.utcnow()
    dv.SourceTimestamp = now


def test_variant():
    dv = ua.Variant(True, ua.VariantType.Boolean)
    assert dv.Value == True
    assert type(dv.Value) == bool
    now = datetime.utcnow()
    v = ua.Variant(now)
    assert v.Value == now
    assert v.VariantType == ua.VariantType.DateTime
    v2 = variant_from_binary(ua.utils.Buffer(variant_to_binary(v)))
    assert v.Value == v2.Value
    assert v.VariantType == v2.VariantType
    # commonity method:
    assert v == ua.Variant(v)


def test_variant_array():
    v = ua.Variant([1, 2, 3, 4, 5])
    assert v.Value[1] == 2
    # assert v.VarianType, ua.VariantType.Int64) # we do not care, we should aonly test for sutff that matter
    v2 = variant_from_binary(ua.utils.Buffer(variant_to_binary(v)))
    assert v.Value == v2.Value
    assert v.VariantType == v2.VariantType

    now = datetime.utcnow()
    v = ua.Variant([now])
    assert v.Value[0] == now
    assert v.VariantType == ua.VariantType.DateTime
    v2 = variant_from_binary(ua.utils.Buffer(variant_to_binary(v)))
    assert v.Value == v2.Value
    assert v.VariantType == v2.VariantType


def test_variant_array_dim():
    v = ua.Variant([1, 2, 3, 4, 5, 6], dimensions=[2, 3])
    assert v.Value[1] == 2
    v2 = variant_from_binary(ua.utils.Buffer(variant_to_binary(v)))
    assert _reshape(v.Value, (2, 3)) == v2.Value
    assert v.VariantType == v2.VariantType
    assert v.Dimensions == v2.Dimensions
    assert v2.Dimensions == [2, 3]


def test_text():
    t1 = ua.LocalizedText('Root')
    t2 = ua.LocalizedText('Root')
    t3 = ua.LocalizedText('root')
    assert t1 == t2
    assert t1 != t3
    t4 = struct_from_binary(ua.LocalizedText, ua.utils.Buffer(struct_to_binary(t1)))
    assert t1 == t4


def test_text_with_locale():
    t0 = ua.LocalizedText('Root')
    t1 = ua.LocalizedText('Root', 'de-AT')
    t2 = ua.LocalizedText('Root', 'de-AT')
    t3 = ua.LocalizedText('Root', 'de-DE')
    t4 = ua.LocalizedText(locale='de-DE')
    t5 = ua.LocalizedText(locale='de-DE')
    assert t0 != t1
    assert t1 == t2
    assert t1 != t3
    assert t3 != t4
    assert t4 == t5
    t6 = struct_from_binary(ua.LocalizedText, ua.utils.Buffer(struct_to_binary(t1)))
    assert t1 == t6


def test_message_chunk():
    pol = ua.SecurityPolicy()
    chunks = MessageChunk.message_to_chunks(pol, b'123', 65536)
    assert len(chunks) == 1
    seq = 0
    for chunk in chunks:
        seq += 1
        chunk.SequenceHeader.SequenceNumber = seq
    chunk2 = MessageChunk.from_binary(pol, ua.utils.Buffer(chunks[0].to_binary()))
    assert chunks[0].to_binary() == chunk2.to_binary()

    # for policy None, MessageChunk overhead is 12+4+8 = 24 bytes
    # Let's pack 11 bytes into 28-byte chunks. The message must be split as 4+4+3
    chunks = MessageChunk.message_to_chunks(pol, b'12345678901', 28)
    assert len(chunks) == 3
    assert chunks[0].Body == b'1234'
    assert chunks[1].Body == b'5678'
    assert chunks[2].Body == b'901'
    for chunk in chunks:
        seq += 1
        chunk.SequenceHeader.SequenceNumber = seq
        assert len(chunk.to_binary()) <= 28


def test_null():
    n = ua.NodeId()
    assert n.is_null()
    assert n.has_null_identifier()

    n = ua.NodeId(0, 0)
    assert n.is_null()
    assert n.has_null_identifier()

    n = ua.NodeId("", 0)
    assert n.is_null()
    assert n.has_null_identifier()

    n = ua.TwoByteNodeId(0)
    assert n.is_null()
    assert n.has_null_identifier()

    n = ua.NodeId(0, 3)
    assert n.is_null() is False
    assert n.has_null_identifier()


def test_where_clause():
    cf = ua.ContentFilter()
    el = ua.ContentFilterElement()
    op = ua.SimpleAttributeOperand()
    op.BrowsePath.append(ua.QualifiedName("property", 2))
    el.FilterOperands.append(op)
    for i in range(10):
        op = ua.LiteralOperand()
        op.Value = ua.Variant(i)
        el.FilterOperands.append(op)
    el.FilterOperator = ua.FilterOperator.InList
    cf.Elements.append(el)
    wce = WhereClauseEvaluator(logging.getLogger(__name__), None, cf)
    ev = BaseEvent()
    ev._freeze = False
    ev.property = 3
    assert wce.eval(ev)


class MyEnum(_MaskEnum):
    member1 = 0
    member2 = 1


def test_invalid_input():
    with pytest.raises(ValueError):
        MyEnum(12345)


def test_parsing():
    assert MyEnum.parse_bitfield(0b0) == set()
    assert MyEnum.parse_bitfield(0b1) == {MyEnum.member1}
    assert MyEnum.parse_bitfield(0b10) == {MyEnum.member2}
    assert MyEnum.parse_bitfield(0b11) == {MyEnum.member1, MyEnum.member2}


def test_identity():
    bitfields = [0b00, 0b01, 0b10, 0b11]

    for bitfield in bitfields:
        as_set = MyEnum.parse_bitfield(bitfield)
        back_to_bitfield = MyEnum.to_bitfield(as_set)
        assert back_to_bitfield == bitfield


def test_variant_intenum():
    ase = ua.AxisScaleEnumeration(ua.AxisScaleEnumeration.Linear)  # Just pick an existing IntEnum class
    vAse = ua.Variant(ase)
    assert vAse.VariantType == ua.VariantType.Int32


def test_bin_data_type_def():
    ad = ua.AddNodesItem()
    ad.ParentNodeId = ua.NodeId(22)
    dta = ua.DataTypeAttributes()
    dta.DisplayName = ua.LocalizedText("titi")
    ad.NodeAttributes = dta

    data = struct_to_binary(ad)
    ad2 = struct_from_binary(ua.AddNodesItem, ua.utils.Buffer(data))
    assert ad.ParentNodeId == ad2.ParentNodeId
    assert ad.NodeAttributes.DisplayName == ad2.NodeAttributes.DisplayName
