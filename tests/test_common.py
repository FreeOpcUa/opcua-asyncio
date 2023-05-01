# encoding: utf-8

"""
Tests that will be run twice. Once on server side and once on
client side since we have been carefull to have the exact
same api on server and client side
"""

import asyncio
import contextlib
import math
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from asyncua import Node, ua, uamethod
from asyncua.common import ua_utils
from asyncua.common.copy_node_util import copy_node
from asyncua.common.instantiate_util import instantiate
from asyncua.common.methods import call_method_full
from asyncua.common.sql_injection import SqlInjectionError, validate_table_name
from asyncua.common.structures104 import new_enum, new_struct, new_struct_field
from asyncua.ua.ua_binary import struct_from_binary, struct_to_binary

pytestmark = pytest.mark.asyncio


async def add_server_methods(srv):
    @uamethod
    def func(parent, value):
        return value * 2

    o = srv.nodes.objects
    await o.add_method(
        ua.NodeId("ServerMethod", 2), ua.QualifiedName('ServerMethod', 2),
        func, [ua.Int64], [ua.Int64]
    )

    @uamethod
    def func_no_arg(parent):
        return 13

    o = srv.nodes.objects
    await o.add_method(
        ua.NodeId("ServerMethodNoArg", 2), ua.QualifiedName('ServerMethodNoArg', 2),
        func_no_arg
    )

    @uamethod
    def func2(parent, methodname, value):
        if methodname == "panic":
            return ua.StatusCode(ua.StatusCodes.BadOutOfMemory)
        if methodname != "sin":
            res = ua.CallMethodResult()
            res.StatusCode = ua.StatusCode(ua.StatusCodes.BadInvalidArgument)
            res.InputArgumentResults = [ua.StatusCode(ua.StatusCodes.BadNotSupported), ua.StatusCode()]
            return res
        return math.sin(value)

    o = srv.nodes.objects
    await o.add_method(
        ua.NodeId("ServerMethodArray", 2), ua.QualifiedName('ServerMethodArray', 2), func2,
        [ua.VariantType.String, ua.VariantType.Int64], [ua.VariantType.Int64]
    )

    @uamethod
    def func3(parent, mylist):
        return [i * 2 for i in mylist]

    o = srv.nodes.objects
    await o.add_method(
        ua.NodeId("ServerMethodArray2", 2), ua.QualifiedName('ServerMethodArray2', 2), func3,
        [ua.VariantType.Int64], [ua.Int64]
    )

    @uamethod
    def func4(parent):
        return None

    base_otype = srv.get_node(ua.ObjectIds.BaseObjectType)
    custom_otype = await base_otype.add_object_type(2, 'ObjectWithMethodsType')
    await custom_otype.add_method(2, 'ServerMethodDefault', func4)
    await (await custom_otype.add_method(2, 'ServerMethodMandatory', func4)).set_modelling_rule(True)
    await (await custom_otype.add_method(2, 'ServerMethodOptional', func4)).set_modelling_rule(False)
    await (await custom_otype.add_method(2, 'ServerMethodNone', func4)).set_modelling_rule(None)
    await o.add_object(2, 'ObjectWithMethods', custom_otype)

    @uamethod
    def func5(parent):
        return 1, 2, 3

    o = srv.nodes.objects
    await o.add_method(
        ua.NodeId("ServerMethodTuple", 2), ua.QualifiedName('ServerMethodTuple', 2), func5, [],
        [ua.VariantType.Int64, ua.VariantType.Int64, ua.VariantType.Int64]
    )

    @uamethod
    async def func6(parent):
        await asyncio.sleep(0)

    o = srv.nodes.objects
    await o.add_method(
        ua.NodeId("ServerMethodAsync", 2), ua.QualifiedName('ServerMethodAsync', 2), func6, [], []
    )


async def test_find_servers(opc):
    await opc.opc.find_servers()
    # FIXME : finish


async def test_add_node_bad_args(opc):
    obj = opc.opc.nodes.objects

    with pytest.raises(TypeError):
        await obj.add_folder(1.2, "kk")

    with pytest.raises(TypeError):
        await obj.add_folder(ua.UaError, "khjh")

    with pytest.raises(ua.UaError):
        await obj.add_folder("kjk", 1.2)

    with pytest.raises(TypeError):
        await obj.add_folder("i=0;s='oooo'", 1.2)

    with pytest.raises(ua.UaError):
        await obj.add_folder("i=0;s='oooo'", "tt:oioi")


async def test_delete_nodes(opc):
    obj = opc.opc.nodes.objects
    fold = await obj.add_folder(2, "FolderToDelete")
    var = await fold.add_variable(2, "VarToDelete", 9.1)
    childs = await fold.get_children()
    assert var in childs
    await opc.opc.delete_nodes([var])
    with pytest.raises(ua.UaStatusCodeError):
        await var.write_value(7.8)
    with pytest.raises(ua.UaStatusCodeError):
        await obj.get_child(["2:FolderToDelete", "2:VarToDelete"])
    childs = await fold.get_children()
    assert var not in childs
    await opc.opc.delete_nodes([fold])


async def test_node_bytestring(opc):
    obj = opc.opc.nodes.objects
    var = await obj.add_variable(ua.ByteStringNodeId(b'VarByteString', 2), ua.QualifiedName("toto", 2), ua.UInt16(9))
    node = opc.opc.get_node("ns=2;b=VarByteString")
    assert node == var
    node = opc.opc.get_node(f"ns=2;b=0x{b'VarByteString'.hex()}")
    assert node == var


async def test_add_node_using_builtin(opc):
    obj = opc.opc.nodes.objects
    fold = await obj.add_folder(2, "FolderBuiltin")
    var = await fold.add_variable(2, "VarBuiltin", ua.UInt16(9))
    dv = await var.read_data_value()
    assert dv.Value.VariantType == ua.VariantType.UInt16
    data_type = await var.read_data_type()
    assert data_type.Identifier == ua.VariantType.UInt16.value == ua.ObjectIds.UInt16
    assert data_type.NamespaceIndex == 0
    await var.write_value(ua.UInt16(6))
    dv = await var.read_data_value()
    assert dv.Value.VariantType == ua.VariantType.UInt16
    assert dv.Value.Value == 6
    assert (await var.read_value()) == 6


async def test_delete_nodes_with_inverse_references(opc):
    obj = opc.opc.nodes.objects
    fold = await obj.add_folder(2, "FolderToDelete")
    var = await fold.add_variable(2, "VarToDelete", 9.1)
    var2 = await fold.add_variable(2, "VarWithReference", 9.2)
    childs = await fold.get_children()
    assert var in childs
    assert var2 in childs
    # add two references to var, this includes adding the inverse references to var2
    await var.add_reference(var2.nodeid, reftype=ua.ObjectIds.HasDescription, forward=True, bidirectional=True)
    await var.add_reference(var2.nodeid, reftype=ua.ObjectIds.HasEffect, forward=True, bidirectional=True)
    await opc.opc.delete_nodes([var])
    childs = await fold.get_children()
    assert var not in childs
    has_desc_refs = await var2.get_referenced_nodes(refs=ua.ObjectIds.HasDescription,
                                                    direction=ua.BrowseDirection.Inverse)
    assert len(has_desc_refs) == 0
    has_effect_refs = await var2.get_referenced_nodes(refs=ua.ObjectIds.HasEffect, direction=ua.BrowseDirection.Inverse)
    assert len(has_effect_refs) == 0
    await opc.opc.delete_nodes([fold])


async def test_delete_nodes_recursive(opc):
    obj = opc.opc.nodes.objects
    fold = await obj.add_folder(2, "FolderToDeleteR")
    var = await fold.add_variable(2, "VarToDeleteR", 9.1)
    await opc.opc.delete_nodes([fold, var])
    with pytest.raises(ua.UaStatusCodeError):
        await var.write_value(7.8)
    with pytest.raises(ua.UaStatusCodeError):
        await obj.get_child(["2:FolderToDelete", "2:VarToDelete"])


async def test_delete_nodes_recursive2(opc):
    obj = opc.opc.nodes.objects
    fold = await obj.add_folder(2, "FolderToDeleteRoot")
    mynodes = []
    for i in range(7):
        nfold = await fold.add_folder(2, f"FolderToDeleteRoot{i}")
        var = await nfold.add_variable(2, "VarToDeleteR", 9.1)
        var = await nfold.add_property(2, "ProToDeleteR", 9.1)
        prop = await nfold.add_property(2, "ProToDeleteR2", 9.1)
        o = await nfold.add_object(3, "ObjToDeleteR")
        mynodes.append(nfold)
        mynodes.append(var)
        mynodes.append(prop)
        mynodes.append(o)
    await opc.opc.delete_nodes([fold], recursive=True)
    for node in mynodes:
        with pytest.raises(ua.UaStatusCodeError):
            await node.read_browse_name()
    await opc.opc.delete_nodes([fold])


async def test_delete_references(opc):
    newtype = await opc.opc.get_node(ua.ObjectIds.HierarchicalReferences).add_reference_type(0,
                                                                                             "HasSuperSecretVariable")

    obj = opc.opc.nodes.objects
    fold = await obj.add_folder(2, "FolderToRef")
    var = await fold.add_variable(2, "VarToRef", 42)

    await fold.add_reference(var, newtype)

    assert [fold] == await var.get_referenced_nodes(newtype)
    assert [var] == await fold.get_referenced_nodes(newtype)

    await fold.delete_reference(var, newtype)

    assert [] == await var.get_referenced_nodes(newtype)
    assert [] == await fold.get_referenced_nodes(newtype)

    await fold.add_reference(var, newtype, bidirectional=False)

    assert [] == await var.get_referenced_nodes(newtype)
    assert [var] == await fold.get_referenced_nodes(newtype)

    await fold.delete_reference(var, newtype)

    assert [] == await var.get_referenced_nodes(newtype)
    assert [] == await fold.get_referenced_nodes(newtype)

    await var.add_reference(fold, newtype, forward=False, bidirectional=False)

    assert [fold] == await var.get_referenced_nodes(newtype)
    assert [] == await fold.get_referenced_nodes(newtype)

    with pytest.raises(ua.UaStatusCodeError):
        await fold.delete_reference(var, newtype)

    assert [fold] == await var.get_referenced_nodes(newtype)
    assert [] == await fold.get_referenced_nodes(newtype)

    with pytest.raises(ua.UaStatusCodeError):
        await var.delete_reference(fold, newtype)

    assert [fold] == await var.get_referenced_nodes(newtype)
    assert [] == await fold.get_referenced_nodes(newtype)

    await var.delete_reference(fold, newtype, forward=False)

    assert [] == await var.get_referenced_nodes(newtype)
    assert [] == await fold.get_referenced_nodes(newtype)

    # clean-up
    await opc.opc.delete_nodes([fold, newtype], recursive=True)


async def test_server_node(opc):
    node = opc.opc.nodes.server
    assert ua.QualifiedName('Server', 0) == await node.read_browse_name()


async def test_root(opc):
    root = opc.opc.nodes.root
    assert ua.QualifiedName('Root', 0) == await root.read_browse_name()
    assert ua.LocalizedText('Root') == await root.read_display_name()
    nid = ua.NodeId(84, 0)
    assert nid == root.nodeid


async def test_objects(opc):
    objects = opc.opc.nodes.objects
    assert ua.QualifiedName('Objects', 0) == await objects.read_browse_name()
    nid = ua.NodeId(85, 0)
    assert nid == objects.nodeid


async def test_browse(opc):
    objects = opc.opc.nodes.objects
    obj = await objects.add_object(4, "browsetest")
    folder = await obj.add_folder(4, "folder")
    prop = await obj.add_property(4, "property", 1)
    prop2 = await obj.add_property(4, "property2", 2)
    var = await obj.add_variable(4, "variable", 3)
    obj2 = await obj.add_object(4, "obj")
    alle = await obj.get_children()
    assert prop in alle
    assert prop2 in alle
    assert var in alle
    assert folder in alle
    assert obj not in alle
    props = await obj.get_children(refs=ua.ObjectIds.HasProperty)
    assert prop in props
    assert prop2 in props
    assert var not in props
    assert folder not in props
    assert obj2 not in props
    all_vars = await obj.get_children(nodeclassmask=ua.NodeClass.Variable)
    assert prop in all_vars
    assert var in all_vars
    assert folder not in props
    assert obj2 not in props
    all_objs = await obj.get_children(nodeclassmask=ua.NodeClass.Object)
    assert folder in all_objs
    assert obj2 in all_objs
    assert var not in all_objs
    await opc.opc.delete_nodes([folder, prop, prop2, var, obj2, obj])
    await opc.opc.delete_nodes(props)
    await opc.opc.delete_nodes(all_vars)
    await opc.opc.delete_nodes(all_objs)


async def test_browse_references(opc):
    objects = opc.opc.nodes.objects
    folder = await objects.add_folder(4, "folder")

    childs = await objects.get_referenced_nodes(
        refs=ua.ObjectIds.Organizes, direction=ua.BrowseDirection.Forward, includesubtypes=False
    )
    assert folder in childs

    childs = await objects.get_referenced_nodes(
        refs=ua.ObjectIds.Organizes, direction=ua.BrowseDirection.Both, includesubtypes=False
    )
    assert folder in childs

    childs = await objects.get_referenced_nodes(
        refs=ua.ObjectIds.Organizes, direction=ua.BrowseDirection.Inverse, includesubtypes=False
    )
    assert folder not in childs

    parents = await folder.get_referenced_nodes(
        refs=ua.ObjectIds.Organizes, direction=ua.BrowseDirection.Inverse, includesubtypes=False
    )
    assert objects in parents

    parents = await folder.get_referenced_nodes(
        refs=ua.ObjectIds.HierarchicalReferences, direction=ua.BrowseDirection.Inverse, includesubtypes=True
    )
    assert objects in parents

    parents = await folder.get_referenced_nodes(
        refs=ua.ObjectIds.HierarchicalReferences, direction=ua.BrowseDirection.Inverse, includesubtypes=False
    )
    assert objects not in parents

    assert await folder.get_parent() == objects


async def test_browsename_with_spaces(opc):
    o = opc.opc.nodes.objects
    v = await o.add_variable(3, 'BNVariable with spaces and %&+?/', 1.3)
    v2 = await o.get_child("3:BNVariable with spaces and %&+?/")
    assert v == v2
    await opc.opc.delete_nodes([v])


async def test_non_existing_path(opc):
    root = opc.opc.nodes.root
    with pytest.raises(ua.UaStatusCodeError):
        await root.get_child(['0:Objects', '0:Server', '0:nonexistingnode'])


async def test_bad_attribute(opc):
    root = opc.opc.nodes.root
    with pytest.raises(ua.UaStatusCodeError):
        await root.write_value(99)


async def test_get_node_by_nodeid(opc):
    root = opc.opc.nodes.root
    server_time_node = await root.get_child(['0:Objects', '0:Server', '0:ServerStatus', '0:CurrentTime'])
    correct = opc.opc.get_node(ua.NodeId(ua.ObjectIds.Server_ServerStatus_CurrentTime))
    assert server_time_node == correct


async def test_datetime_read_value(opc):
    time_node = opc.opc.get_node(ua.NodeId(ua.ObjectIds.Server_ServerStatus_CurrentTime))
    dt = await time_node.read_value()
    utcnow = datetime.utcnow()
    delta = utcnow - dt
    assert delta < timedelta(seconds=1)


async def test_datetime_write_value(opc):
    now = datetime.utcnow()
    objects = opc.opc.nodes.objects
    v1 = await objects.add_variable(4, "test_datetime", now)
    tid = await v1.read_value()
    assert now == tid
    await opc.opc.delete_nodes([v1])


async def test_variant_array_dim(opc):
    objects = opc.opc.nodes.objects
    arry = [[[1.0, 1.0, 1.0, 1.0], [2.0, 2.0, 2.0, 2.0], [3.0, 3.0, 3.0, 3.0]],
            [[5.0, 5.0, 5.0, 5.0], [7.0, 8.0, 9.0, 1.0], [1.0, 1.0, 1.0, 1.0]]]
    v = await objects.add_variable(3, 'variableWithDims', arry)

    await v.write_array_dimensions([0, 0, 0])
    dim = await v.read_array_dimensions()
    assert [0, 0, 0] == dim

    await v.write_value_rank(0)
    rank = await v.read_value_rank()
    assert 0 == rank

    v2 = await v.read_value()
    assert arry == v2
    dv = await v.read_data_value()
    assert [2, 3, 4] == dv.Value.Dimensions

    arry = [[[], [], []], [[], [], []]]
    variant = ua.Variant(arry, ua.VariantType.UInt32)
    v1 = await objects.add_variable(3, 'variableWithDimsEmpty', variant)
    v2 = await v1.read_value()
    assert arry == v2
    dv = await v1.read_data_value()
    assert [2, 3, 0] == dv.Value.Dimensions
    await opc.opc.delete_nodes([v, v1])


async def test_add_numeric_variable(opc):
    objects = opc.opc.nodes.objects
    v = await objects.add_variable('ns=3;i=888;', '3:numericnodefromstring', 99)
    nid = ua.NodeId(888, 3)
    qn = ua.QualifiedName('numericnodefromstring', 3)
    assert nid == v.nodeid
    assert qn == await v.read_browse_name()
    await opc.opc.delete_nodes([v])


async def test_add_string_variable(opc):
    objects = opc.opc.nodes.objects
    v = await objects.add_variable('ns=3;s=stringid;', '3:stringnodefromstring', [68])
    nid = ua.NodeId('stringid', 3)
    qn = ua.QualifiedName('stringnodefromstring', 3)
    assert nid == v.nodeid
    assert qn == await v.read_browse_name()
    await opc.opc.delete_nodes([v])


async def test_utf8(opc):
    objects = opc.opc.nodes.objects
    utf_string = "æøå@%&"
    bn = ua.QualifiedName(utf_string, 3)
    nid = ua.NodeId("æølå", 3)
    val = "æøå"
    v = await objects.add_variable(nid, bn, val)
    assert nid == v.nodeid
    val2 = await v.read_value()
    assert val == val2
    bn2 = await v.read_browse_name()
    assert bn == bn2
    await opc.opc.delete_nodes([v])


async def test_null_variable(opc):
    objects = opc.opc.nodes.objects
    var = await objects.add_variable(3, 'nullstring', "a string")
    await var.write_value(ua.Variant(None, ua.VariantType.String))
    val = await var.read_value()
    assert val is None
    await var.write_value("")
    val = await var.read_value()
    assert val is not None
    assert "" == val
    await opc.opc.delete_nodes([var])


async def test_variable_data_type(opc):
    objects = opc.opc.nodes.objects
    var = await objects.add_variable(3, 'stringfordatatype', "a string")
    val = await var.read_data_type_as_variant_type()
    assert ua.VariantType.String == val
    await opc.opc.delete_nodes([var])
    var = await objects.add_variable(3, 'stringarrayfordatatype', ["a", "b"])
    val = await var.read_data_type_as_variant_type()
    assert ua.VariantType.String == val
    await opc.opc.delete_nodes([var])


async def test_add_string_array_variable(opc):
    objects = opc.opc.nodes.objects
    v = await objects.add_variable('ns=3;s=stringarrayid;', '9:stringarray', ['l', 'b'])
    nid = ua.NodeId('stringarrayid', 3)
    qn = ua.QualifiedName('stringarray', 9)
    assert nid == v.nodeid
    assert qn == await v.read_browse_name()
    val = await v.read_value()
    assert ['l', 'b'] == val
    await opc.opc.delete_nodes([v])


async def test_add_numeric_node(opc):
    objects = opc.opc.nodes.objects
    nid = ua.NodeId(9999, 3)
    qn = ua.QualifiedName('AddNodeVar1', 3)
    v1 = await objects.add_variable(nid, qn, 0)
    assert nid == v1.nodeid
    assert qn == await v1.read_browse_name()
    await opc.opc.delete_nodes([v1])


async def test_add_string_node(opc):
    objects = opc.opc.nodes.objects
    qn = ua.QualifiedName('AddNodeVar2', 3)
    nid = ua.NodeId('AddNodeVar2Id', 3)
    v2 = await objects.add_variable(nid, qn, 0)
    assert nid == v2.nodeid
    assert qn == await v2.read_browse_name()
    await opc.opc.delete_nodes([v2])


async def test_add_find_node_(opc):
    objects = opc.opc.nodes.objects
    o = await objects.add_object('ns=2;i=101;', '2:AddFindObject')
    o2 = await objects.get_child('2:AddFindObject')
    assert o == o2
    await opc.opc.delete_nodes([o, o2])


async def test_same_browse_name(opc):
    objects = opc.opc.nodes.objects
    f = await objects.add_folder('ns=2;i=201;', '2:MyBNameFolder')
    o = await f.add_object('ns=2;i=202;', '2:MyBName')
    v = await o.add_variable('ns=2;i=203;', '2:MyBNameTarget', 2.0)
    o2 = await f.add_object('ns=2;i=204;', '2:MyBName')
    v2 = await o2.add_variable('ns=2;i=205;', '2:MyBNameTarget', 2.0)
    nodes = await objects.get_child(['2:MyBNameFolder', '2:MyBName', '2:MyBNameTarget'], return_all=True)
    assert len(nodes) == 2
    assert nodes[0] == v
    assert nodes[1] == v2
    await opc.opc.delete_nodes([f, o, o2, v, v2])


async def test_node_path(opc):
    objects = opc.opc.nodes.objects
    o = await objects.add_object('ns=2;i=105;', '2:NodePathObject')
    root = opc.opc.nodes.root
    o2 = await root.get_child(['0:Objects', '2:NodePathObject'])
    assert o == o2
    await opc.opc.delete_nodes([o, o2])


async def test_add_read_node(opc):
    objects = opc.opc.nodes.objects
    o = await objects.add_object('ns=2;i=102;', '2:AddReadObject')
    nid = ua.NodeId(102, 2)
    assert nid == o.nodeid
    qn = ua.QualifiedName('AddReadObject', 2)
    assert qn == await o.read_browse_name()
    await opc.opc.delete_nodes([o])


async def test_simple_value(opc):
    o = opc.opc.nodes.objects
    v = await o.add_variable(3, 'VariableTestValue', 4.32)
    val = await v.read_value()
    assert 4.32 == val
    await opc.opc.delete_nodes([v])


async def test_add_exception(opc):
    objects = opc.opc.nodes.objects
    v = await objects.add_object('ns=2;i=103;', '2:AddReadObject')
    with pytest.raises(ua.UaStatusCodeError):
        await objects.add_object('ns=2;i=103;', '2:AddReadObject')
    await opc.opc.delete_nodes([v])


async def test_negative_value(opc):
    o = opc.opc.nodes.objects
    v = await o.add_variable(3, 'VariableNegativeValue', 4.0)
    await v.write_value(-4.54)
    assert -4.54 == await v.read_value()
    await opc.opc.delete_nodes([v])


async def test_read_server_state(opc):
    statenode = opc.opc.get_node(ua.NodeId(ua.ObjectIds.Server_ServerStatus_State))
    assert 0 == await statenode.read_value()


async def test_bad_node(opc):
    bad = opc.opc.get_node(ua.NodeId(999, 999))
    with pytest.raises(ua.UaStatusCodeError):
        await bad.read_browse_name()
    with pytest.raises(ua.UaStatusCodeError):
        await bad.write_value(89)
    with pytest.raises(ua.UaStatusCodeError):
        await bad.add_object(0, "0:myobj")
    with pytest.raises(ua.UaStatusCodeError):
        await bad.get_child("0:myobj")
    await opc.opc.delete_nodes([bad])


async def test_value(opc):
    o = opc.opc.nodes.objects
    var = ua.Variant(ua.Double(1.98))
    v = await o.add_variable(3, 'VariableValue', var)
    assert 1.98 == await v.read_value()
    dvar = ua.DataValue(var)
    dv = await v.read_data_value()
    assert ua.DataValue == type(dv)
    assert dvar.Value == dv.Value
    assert dvar.Value == var
    await opc.opc.delete_nodes([v])


async def test_write_value(opc):
    o = opc.opc.nodes.objects
    var = ua.Variant(1.98, ua.VariantType.Double)
    dvar = ua.DataValue(var)
    v = await o.add_variable(3, 'VariableValue', var)
    await v.write_value(var.Value)
    v1 = await v.read_value()
    assert v1 == var.Value
    await v.write_value(var)
    v2 = await v.read_value()
    assert v2 == var.Value
    await v.write_value(dvar)
    v3 = await v.read_data_value()
    assert v3.Value == dvar.Value
    await opc.opc.delete_nodes([v])


async def test_write_value_statuscode_bad(opc):
    o = opc.opc.nodes.objects
    var = ua.Variant('Some value that should not be set!')
    dvar = ua.DataValue(None, StatusCode_=ua.StatusCode(ua.StatusCodes.BadDeviceFailure))
    v = await o.add_variable(3, 'VariableValueBad', var)
    await v.write_value(dvar)
    with pytest.raises(ua.UaStatusCodeError) as error_read:
        await v.read_data_value()
    assert error_read.type.code == dvar.StatusCode.value
    await opc.opc.delete_nodes([v])


async def test_array_value(opc):
    o = opc.opc.nodes.objects
    v = await o.add_variable(3, 'VariableArrayValue', [1, 2, 3])
    assert [1, 2, 3] == await v.read_value()
    await opc.opc.delete_nodes([v])


async def test_bool_variable(opc):
    o = opc.opc.nodes.objects
    v = await o.add_variable(3, 'BoolVariable', True)
    dt = await v.read_data_type_as_variant_type()
    assert ua.VariantType.Boolean == dt
    val = await v.read_value()
    assert val is True
    await v.write_value(False)
    val = await v.read_value()
    assert val is False
    await opc.opc.delete_nodes([v])


async def test_array_size_one_value(opc):
    o = opc.opc.nodes.objects
    v = await o.add_variable(3, 'VariableArrayValue2', [1, 2, 3])
    await v.write_value([1])
    assert [1] == await v.read_value()
    await opc.opc.delete_nodes([v])


async def test_use_namespace(opc):
    idx = await opc.opc.get_namespace_index("urn:freeopcua:python:server")
    assert 1 == idx
    root = opc.opc.nodes.root
    myvar = await root.add_variable(idx, 'var_in_custom_namespace', [5])
    myid = myvar.nodeid
    assert idx == myid.NamespaceIndex
    await opc.opc.delete_nodes([myvar])


async def test_method(opc):
    o = opc.opc.nodes.objects
    await o.get_child("2:ServerMethod")
    result = await o.call_method("2:ServerMethod", 2.1)
    assert 4.2 == result
    with pytest.raises(ua.UaStatusCodeError):
        # FIXME: we should raise a more precise exception
        await o.call_method("2:ServerMethod", 2.1, 89, 9)
    with pytest.raises(ua.UaStatusCodeError):
        await o.call_method(ua.NodeId(999), 2.1)  # non existing method


async def test_method_no_arg(opc):
    o = opc.opc.nodes.objects
    await o.get_child("2:ServerMethodNoArg")
    result = await o.call_method("2:ServerMethodNoArg")
    assert 13 == result
    with pytest.raises(ua.UaStatusCodeError):
        # FIXME: we should raise a more precise exception
        await o.call_method("2:ServerMethodNoArg", 2.1, 89, 9)


async def test_method_array(opc):
    o = opc.opc.nodes.objects
    m = await o.get_child("2:ServerMethodArray")
    result = await o.call_method(m, "sin", ua.Variant(math.pi))
    assert result < 0.01
    with pytest.raises(ua.UaStatusCodeError) as exc_info:
        await o.call_method(m, "cos", ua.Variant(math.pi))
    assert ua.StatusCodes.BadInvalidArgument == exc_info.type.code
    with pytest.raises(ua.UaStatusCodeError) as exc_info:
        await o.call_method(m, "panic", ua.Variant(math.pi))
    assert ua.StatusCodes.BadOutOfMemory == exc_info.type.code


async def test_method_array2(opc):
    o = opc.opc.nodes.objects
    m = await o.get_child("2:ServerMethodArray2")
    result = await o.call_method(m, [1.1, 3.4, 9])
    assert [2.2, 6.8, 18] == result
    result = await call_method_full(o, m, [1.1, 3.4, 9])
    assert [[2.2, 6.8, 18]] == result.OutputArguments


async def test_method_tuple(opc):
    o = opc.opc.nodes.objects
    m = await o.get_child("2:ServerMethodTuple")
    result = await o.call_method(m)
    assert [1, 2, 3] == result
    result = await call_method_full(o, m)
    assert [1, 2, 3] == result.OutputArguments


async def test_method_none(opc):
    # this test calls the function linked to the type's method..
    o = await opc.opc.get_node(ua.ObjectIds.BaseObjectType).get_child("2:ObjectWithMethodsType")
    m = await o.get_child("2:ServerMethodDefault")
    result = await o.call_method(m)
    assert result is None
    result = await call_method_full(o, m)
    assert [] == result.OutputArguments


async def test_method_async(opc):
    o = opc.opc.nodes.objects
    m = await o.get_child("2:ServerMethodAsync")
    await o.call_method(m)
    await call_method_full(o, m)


async def test_add_nodes(opc):
    objects = opc.opc.nodes.objects
    f = await objects.add_folder(3, 'MyFolder')
    child = await objects.get_child("3:MyFolder")
    assert child == f
    o = await f.add_object(3, 'MyObject')
    child = await f.get_child("3:MyObject")
    assert child == o
    v = await f.add_variable(3, 'MyVariable', 6)
    child = await f.get_child("3:MyVariable")
    assert child == v
    p = await f.add_property(3, 'MyProperty', 10)
    child = await f.get_child("3:MyProperty")
    assert child == p
    childs = await f.get_children()
    assert o in childs
    assert v in childs
    assert p in childs
    await opc.opc.delete_nodes([f, o, v, p, child])


async def test_modelling_rules(opc):
    obj = await opc.opc.nodes.base_object_type.add_object_type(2, 'MyFooObjectType')
    v = await obj.add_variable(2, "myvar", 1.1)
    await v.set_modelling_rule(True)
    p = await obj.add_property(2, "myvar2", 1.1)
    await p.set_modelling_rule(False)

    refs = await obj.get_referenced_nodes(refs=ua.ObjectIds.HasModellingRule)
    assert 0 == len(refs)

    refs = await v.get_referenced_nodes(refs=ua.ObjectIds.HasModellingRule)
    assert opc.opc.get_node(ua.ObjectIds.ModellingRule_Mandatory) == refs[0]

    refs = await p.get_referenced_nodes(refs=ua.ObjectIds.HasModellingRule)
    assert opc.opc.get_node(ua.ObjectIds.ModellingRule_Optional) == refs[0]

    await p.set_modelling_rule(None)
    refs = await p.get_referenced_nodes(refs=ua.ObjectIds.HasModellingRule)
    assert 0 == len(refs)
    await opc.opc.delete_nodes([v, p])


async def test_incl_subtypes(opc):
    base_type = await opc.opc.nodes.root.get_child(["0:Types", "0:ObjectTypes", "0:BaseObjectType"])
    descs = await base_type.get_children_descriptions(includesubtypes=True)
    assert len(descs) > 10
    descs = await base_type.get_children_descriptions(includesubtypes=False)
    assert 0 == len(descs)


async def test_add_node_with_type(opc):
    objects = opc.opc.nodes.objects
    f = await objects.add_folder(3, 'MyFolder_TypeTest')

    o = await f.add_object(3, 'MyObject1', ua.ObjectIds.BaseObjectType)
    assert ua.NodeId(ua.ObjectIds.BaseObjectType) == await o.read_type_definition()

    o = await f.add_object(3, 'MyObject2', ua.NodeId(ua.ObjectIds.BaseObjectType, 0))
    assert ua.NodeId(ua.ObjectIds.BaseObjectType) == await o.read_type_definition()

    base_otype = opc.opc.get_node(ua.ObjectIds.BaseObjectType)
    custom_otype = await base_otype.add_object_type(2, 'MyFooObjectType2')

    o = await f.add_object(3, 'MyObject3', custom_otype.nodeid)
    assert custom_otype.nodeid == await o.read_type_definition()

    references = await o.get_references(refs=ua.ObjectIds.HasTypeDefinition, direction=ua.BrowseDirection.Forward)
    assert 1 == len(references)
    assert custom_otype.nodeid == references[0].NodeId
    await opc.opc.delete_nodes([f, o])


async def test_references_for_added_nodes(opc):
    objects = opc.opc.nodes.objects
    o = await objects.add_object(3, 'MyObject4')
    nodes = await objects.get_referenced_nodes(
        refs=ua.ObjectIds.Organizes, direction=ua.BrowseDirection.Forward, includesubtypes=False
    )
    assert o in nodes
    nodes = await o.get_referenced_nodes(
        refs=ua.ObjectIds.Organizes, direction=ua.BrowseDirection.Inverse, includesubtypes=False
    )
    assert objects in nodes
    assert objects == await o.get_parent()
    assert ua.NodeId(ua.ObjectIds.BaseObjectType) == await o.read_type_definition()
    assert [] == await o.get_references(ua.ObjectIds.HasModellingRule)

    o2 = await o.add_object(3, 'MySecondObject')
    nodes = await o.get_referenced_nodes(
        refs=ua.ObjectIds.HasComponent, direction=ua.BrowseDirection.Forward, includesubtypes=False
    )
    assert o2 in nodes
    nodes = await o2.get_referenced_nodes(
        refs=ua.ObjectIds.HasComponent, direction=ua.BrowseDirection.Inverse, includesubtypes=False
    )
    assert o in nodes
    assert o == await o2.get_parent()
    assert ua.NodeId(ua.ObjectIds.BaseObjectType) == await o2.read_type_definition()
    assert [] == await o2.get_references(ua.ObjectIds.HasModellingRule)

    v = await o.add_variable(3, 'MyVariable', 6)
    nodes = await o.get_referenced_nodes(
        refs=ua.ObjectIds.HasComponent, direction=ua.BrowseDirection.Forward, includesubtypes=False
    )
    assert v in nodes
    nodes = await v.get_referenced_nodes(
        refs=ua.ObjectIds.HasComponent, direction=ua.BrowseDirection.Inverse, includesubtypes=False
    )
    assert o in nodes
    assert o == await v.get_parent()
    assert ua.NodeId(ua.ObjectIds.BaseDataVariableType) == await v.read_type_definition()
    assert [] == await v.get_references(ua.ObjectIds.HasModellingRule)

    p = await o.add_property(3, 'MyProperty', 2)
    nodes = await o.get_referenced_nodes(
        refs=ua.ObjectIds.HasProperty, direction=ua.BrowseDirection.Forward, includesubtypes=False
    )
    assert p in nodes
    nodes = await p.get_referenced_nodes(
        refs=ua.ObjectIds.HasProperty, direction=ua.BrowseDirection.Inverse, includesubtypes=False
    )
    assert o in nodes
    assert o == await p.get_parent()
    assert ua.NodeId(ua.ObjectIds.PropertyType) == await p.read_type_definition()
    assert [] == await p.get_references(ua.ObjectIds.HasModellingRule)

    m = await objects.get_child("2:ServerMethod")
    assert [] == await m.get_references(ua.ObjectIds.HasModellingRule)


async def test_path_string(opc):
    o = await (await opc.opc.nodes.objects.add_folder(1, "titif")).add_object(3, "opath")
    path = await o.get_path(as_string=True)
    assert ["0:Root", "0:Objects", "1:titif", "3:opath"] == path
    path = await o.get_path(2, as_string=True)
    assert ["1:titif", "3:opath"] == path


async def test_path(opc):
    of = await opc.opc.nodes.objects.add_folder(1, "titif")
    op = await of.add_object(3, "opath")
    path = await op.get_path()
    assert [opc.opc.nodes.root, opc.opc.nodes.objects, of, op] == path
    path = await op.get_path(2)
    assert [of, op] == path
    target = opc.opc.get_node("i=13387")
    path = await target.get_path()
    assert [
        opc.opc.nodes.root, opc.opc.nodes.types, opc.opc.nodes.object_types, opc.opc.nodes.base_object_type,
        opc.opc.nodes.folder_type, opc.opc.get_node(ua.ObjectIds.FileDirectoryType), target
    ] == path


async def test_get_endpoints(opc):
    endpoints = await opc.opc.get_endpoints()
    assert len(endpoints) > 0
    assert endpoints[0].EndpointUrl.startswith("opc.tcp://")


async def test_copy_node(opc):
    dev_t = await opc.opc.nodes.base_structure_type.add_object_type(0, "MyDevice")
    _ = await dev_t.add_variable(0, "sensor", 1.0)
    _ = await dev_t.add_property(0, "sensor_id", "0340")
    ctrl_t = await dev_t.add_object(0, "controller")
    prop_t = await ctrl_t.add_property(0, "state", "Running")
    # Create device sutype
    devd_t = await dev_t.add_object_type(0, "MyDeviceDerived")
    _ = await devd_t.add_variable(0, "childparam", 1.0)
    _ = await devd_t.add_property(0, "sensorx_id", "0340")
    nodes = await copy_node(opc.opc.nodes.objects, dev_t)
    mydevice = nodes[0]
    assert ua.NodeClass.ObjectType == await mydevice.read_node_class()
    assert 4 == len(await mydevice.get_children())
    _ = await mydevice.get_child(["0:controller"])
    prop = await mydevice.get_child(["0:controller", "0:state"])
    assert ua.NodeId(ua.ObjectIds.PropertyType) == await prop.read_type_definition()
    assert "Running" == await prop.read_value()
    assert prop.nodeid != prop_t.nodeid


async def test_instantiate_1(opc):
    # Create device type
    dev_t = await opc.opc.nodes.base_object_type.add_object_type(0, "MyDevice")
    v_t = await dev_t.add_variable(0, "sensor", 1.0)
    await v_t.set_modelling_rule(True)
    p_t = await dev_t.add_property(0, "sensor_id", "0340")
    await p_t.set_modelling_rule(True)
    ctrl_t = await dev_t.add_object(0, "controller")
    await ctrl_t.set_modelling_rule(True)
    v_opt_t = await dev_t.add_variable(0, "vendor", 1.0)
    await v_opt_t.set_modelling_rule(False)
    v_none_t = await dev_t.add_variable(0, "model", 1.0)
    await v_none_t.set_modelling_rule(None)
    prop_t = await ctrl_t.add_property(0, "state", "Running")
    await prop_t.set_modelling_rule(True)

    # Create device sutype
    devd_t = await dev_t.add_object_type(0, "MyDeviceDerived")
    v_t = await devd_t.add_variable(0, "childparam", 1.0)
    await v_t.set_modelling_rule(True)
    p_t = await devd_t.add_property(0, "sensorx_id", "0340")
    await p_t.set_modelling_rule(True)

    # instanciate device
    nodes = await instantiate(opc.opc.nodes.objects, dev_t, bname="2:Device0001")
    mydevice = nodes[0]

    assert ua.NodeClass.Object == await mydevice.read_node_class()
    assert dev_t.nodeid == await mydevice.read_type_definition()
    _ = await mydevice.get_child(["0:controller"])
    prop = await mydevice.get_child(["0:controller", "0:state"])
    _ = await mydevice.get_child(["0:vendor"])
    with pytest.raises(ua.uaerrors.BadNoMatch):
        await mydevice.get_child(["0:model"])
    with pytest.raises(ua.uaerrors.BadNoMatch):
        await mydevice.get_child(["0:MyDeviceDerived"])

    assert ua.NodeId(ua.ObjectIds.PropertyType) == await prop.read_type_definition()
    assert "Running" == await prop.read_value()
    assert prop.nodeid != prop_t.nodeid

    # instanciate device subtype
    nodes = await instantiate(opc.opc.nodes.objects, devd_t, bname="2:Device0002")
    mydevicederived = nodes[0]
    _ = await mydevicederived.get_child(["0:sensorx_id"])
    _ = await mydevicederived.get_child(["0:childparam"])
    _ = await mydevicederived.get_child(["0:sensor"])
    _ = await mydevicederived.get_child(["0:sensor_id"])
    await opc.opc.delete_nodes([devd_t, dev_t])


async def test_instantiate_string_nodeid(opc):
    # Create device type
    dev_t = await opc.opc.nodes.base_object_type.add_object_type(0, "MyDevice2")
    v_t = await dev_t.add_variable(0, "sensor", 1.0)
    await v_t.set_modelling_rule(True)
    p_t = await dev_t.add_property(0, "sensor_id", "0340")
    await p_t.set_modelling_rule(True)
    ctrl_t = await dev_t.add_object(0, "controller")
    await ctrl_t.set_modelling_rule(True)
    prop_t = await ctrl_t.add_property(0, "state", "Running")
    await prop_t.set_modelling_rule(True)

    # instanciate device
    nodes = await instantiate(opc.opc.nodes.objects, dev_t, nodeid=ua.NodeId("InstDevice", 2, ua.NodeIdType.String),
                              bname="2:InstDevice")
    mydevice = nodes[0]

    assert ua.NodeClass.Object == await mydevice.read_node_class()
    assert dev_t.nodeid == await mydevice.read_type_definition()
    obj = await mydevice.get_child(["0:controller"])
    obj_nodeid_ident = obj.nodeid.Identifier
    prop = await mydevice.get_child(["0:controller", "0:state"])
    assert "InstDevice.controller" == obj_nodeid_ident
    assert ua.NodeId(ua.ObjectIds.PropertyType) == await prop.read_type_definition()
    assert "Running" == await prop.read_value()
    assert prop.nodeid != prop_t.nodeid
    await opc.opc.delete_nodes([dev_t])


async def test_instantiate_abstract(opc):
    finit_statemachine_type = opc.opc.get_node("ns=0;i=2771")  # IsAbstract=True
    with pytest.raises(ua.UaError):
        _ = await instantiate(opc.opc.nodes.objects, finit_statemachine_type, bname="2:TestFiniteStateMachine")


async def test_variable_with_datatype(opc):
    v1 = await opc.opc.nodes.objects.add_variable(
        3, 'VariableEnumType1', ua.ApplicationType.ClientAndServer, datatype=ua.NodeId(ua.ObjectIds.ApplicationType)
    )
    tp1 = await v1.read_data_type()
    assert tp1 == ua.NodeId(ua.ObjectIds.ApplicationType)

    v2 = await opc.opc.nodes.objects.add_variable(
        3, 'VariableEnumType2', ua.ApplicationType.ClientAndServer, datatype=ua.NodeId(ua.ObjectIds.ApplicationType)
    )
    tp2 = await v2.read_data_type()
    assert tp2 == ua.NodeId(ua.ObjectIds.ApplicationType)
    await opc.opc.delete_nodes([v1, v2])


async def test_enum(opc):
    # create enum type
    enums = await opc.opc.nodes.root.get_child(["0:Types", "0:DataTypes", "0:BaseDataType", "0:Enumeration"])
    myenum_type = await enums.add_data_type(0, "MyEnum")
    es = await myenum_type.add_variable(
        0, "EnumStrings", [ua.LocalizedText("String0"), ua.LocalizedText("String1"), ua.LocalizedText("String2")],
        ua.VariantType.LocalizedText
    )
    # es.write_value_rank(1)
    # instantiate
    o = opc.opc.nodes.objects
    myvar = await o.add_variable(2, "MyEnumVar", ua.LocalizedText("String1"), datatype=myenum_type.nodeid)
    # myvar.set_writable(True)
    # tests
    assert myenum_type.nodeid == await myvar.read_data_type()
    await myvar.write_value(ua.LocalizedText("String2"))
    await opc.opc.delete_nodes([es, myvar])
    await opc.opc.delete_nodes([myenum_type])


async def test_supertypes(opc):
    nint32 = opc.opc.get_node(ua.ObjectIds.Int32)
    node = await ua_utils.get_node_supertype(nint32)
    assert opc.opc.get_node(ua.ObjectIds.Integer) == node

    nodes = await ua_utils.get_node_supertypes(nint32)
    assert opc.opc.get_node(ua.ObjectIds.Number) == nodes[1]
    assert opc.opc.get_node(ua.ObjectIds.Integer) == nodes[0]

    # test custom
    dtype = await nint32.add_data_type(0, "MyCustomDataType")
    node = await ua_utils.get_node_supertype(dtype)
    assert nint32 == node

    dtype2 = await dtype.add_data_type(0, "MyCustomDataType2")
    node = await ua_utils.get_node_supertype(dtype2)
    assert dtype == node
    await opc.opc.delete_nodes([dtype, dtype2])


async def test_base_data_type(opc):
    nint32 = opc.opc.get_node(ua.ObjectIds.Int32)
    dtype = await nint32.add_data_type(0, "MyCustomDataType")
    dtype2 = await dtype.add_data_type(0, "MyCustomDataType2")
    assert nint32 == await ua_utils.get_base_data_type(dtype)
    assert nint32 == await ua_utils.get_base_data_type(dtype2)

    ext = await opc.opc.nodes.objects.add_variable(0, "MyExtensionObject", ua.Argument())
    d = await ext.read_data_type()
    d = opc.opc.get_node(d)
    assert opc.opc.get_node(ua.ObjectIds.Structure) == await ua_utils.get_base_data_type(d)
    assert ua.VariantType.ExtensionObject == await ua_utils.data_type_to_variant_type(d)
    await opc.opc.delete_nodes([ext])


async def test_data_type_to_variant_type(opc):
    test_data = {
        ua.ObjectIds.Boolean: ua.VariantType.Boolean,
        ua.ObjectIds.Byte: ua.VariantType.Byte,
        ua.ObjectIds.String: ua.VariantType.String,
        ua.ObjectIds.Int32: ua.VariantType.Int32,
        ua.ObjectIds.UInt32: ua.VariantType.UInt32,
        ua.ObjectIds.NodeId: ua.VariantType.NodeId,
        ua.ObjectIds.LocalizedText: ua.VariantType.LocalizedText,
        ua.ObjectIds.Structure: ua.VariantType.ExtensionObject,
        ua.ObjectIds.EnumValueType: ua.VariantType.ExtensionObject,
        ua.ObjectIds.Enumeration: ua.VariantType.Int32,  # enumeration
        ua.ObjectIds.AttributeWriteMask: ua.VariantType.UInt32,
        ua.ObjectIds.AxisScaleEnumeration: ua.VariantType.Int32  # enumeration
    }
    for dt, vdt in test_data.items():
        k = await ua_utils.data_type_to_variant_type(opc.opc.get_node(ua.NodeId(dt)))
        assert vdt == k


async def test_guid_node_id():
    """
    Test that a Node can be instantiated with a GUID string and that the NodeId ca be converted to binary.
    """
    node = Node(None, "ns=4;g=35d5f86f-2777-4550-9d48-b098f5ee285c")
    binary_node_id = ua.ua_binary.nodeid_to_binary(node.nodeid)
    assert type(binary_node_id) is bytes


async def test_import_xml_data_type_definition(opc):
    nodes = await opc.opc.import_xml("tests/substructs.xml")
    await opc.opc.load_data_type_definitions()
    assert hasattr(ua, "MySubstruct")
    assert hasattr(ua, "MyStruct")

    datatype = opc.opc.get_node(ua.MySubstruct.data_type)
    sdef = await datatype.read_data_type_definition()
    assert isinstance(sdef, ua.StructureDefinition)
    s = ua.MyStruct()

    s.toto = 0.1
    ss = ua.MySubstruct()
    assert ss.titi is None
    assert ss.opt_array is None
    assert isinstance(ss.structs, list)
    ss.titi = 1.0
    ss.structs.append(s)
    ss.structs.append(s)

    var = await opc.opc.nodes.objects.add_variable(2, "MySubStructVar", ss, datatype=ua.MySubstruct.data_type)

    s2 = await var.read_value()
    assert s2.structs[1].toto == ss.structs[1].toto == 0.1
    assert s2.opt_array is None
    s2.opt_array = [1]
    await var.write_value(s2)
    s2 = await var.read_value()
    assert s2.opt_array == [1]
    await opc.opc.delete_nodes([datatype, var])
    n = []
    [n.append(opc.opc.get_node(node)) for node in nodes]
    await opc.opc.delete_nodes(n)


async def test_struct_data_type(opc):
    assert isinstance(ua.AddNodesItem.data_type, ua.NodeId)
    node = opc.opc.get_node(ua.AddNodesItem.data_type)
    path = await node.get_path()
    assert opc.opc.nodes.base_structure_type in path
    await opc.opc.delete_nodes([node])


async def test_import_xml_enum_data_type_definition(opc):
    nodes = await opc.opc.import_xml("tests/testenum104.xml")
    await opc.opc.load_data_type_definitions()
    assert hasattr(ua, "MyEnum")
    e = ua.MyEnum.val2
    var = await opc.opc.nodes.objects.add_variable(2, "MyEnumVar", e, datatype=ua.enums_datatypes[ua.MyEnum])
    e2 = await var.read_value()
    assert e2 == ua.MyEnum.val2
    await opc.opc.delete_nodes([var])
    n = []
    [n.append(opc.opc.get_node(node)) for node in nodes]
    await opc.opc.delete_nodes(n)


async def test_duplicated_browsenames_same_ns_protperties(opc):
    parentfolder = await opc.opc.nodes.objects.add_folder(2, "parent_folder")
    _ = await parentfolder.add_property(2, "Myproperty", 123)
    try:
        _ = await parentfolder.add_property(2, "Myproperty", 456)
        await opc.opc.delete_nodes([parentfolder])
        pytest.fail("childproperty2 should never be created!")
    except Exception:
        await opc.opc.delete_nodes([parentfolder])
        return


async def test_custom_enum_x(opc):
    idx = 4
    await new_enum(opc.opc, idx, "MyCustEnum", [
        "titi",
        "toto",
        "None",
    ])

    await opc.opc.load_data_type_definitions()

    var = await opc.opc.nodes.objects.add_variable(idx, "my_enum", ua.MyCustEnum.toto)
    val = await var.read_value()
    assert val == 1


async def test_custom_option_set(opc):
    idx = 4
    await new_enum(opc.opc, idx, "MyOptionSet", ["tata", "titi", "toto", "None"], True)
    await opc.opc.load_data_type_definitions()
    assert ua.MyOptionSet.toto | ua.MyOptionSet.titi == ua.MyOptionSet((1 << 2) | (1 << 1))
    var = await opc.opc.nodes.objects.add_variable(idx, "my_option", ua.MyOptionSet.toto | ua.MyOptionSet.titi)
    val = await var.read_value()
    assert val == (1 << 2) | (1 << 1)


async def test_custom_struct_(opc):
    idx = 4

    await new_struct(opc.opc, idx, "MyMyStruct", [
        new_struct_field("MyBool", ua.VariantType.Boolean),
        new_struct_field("MyUInt32", ua.VariantType.UInt32, array=True),
    ])

    await opc.opc.load_data_type_definitions()
    mystruct = ua.MyMyStruct()
    mystruct.MyUInt32 = [78, 79]
    var = await opc.opc.nodes.objects.add_variable(idx, "my_struct", ua.Variant(mystruct, ua.VariantType.ExtensionObject))
    val = await var.read_value()
    assert val.MyUInt32 == [78, 79]


async def test_custom_struct_with_optional_fields(opc):
    idx = 4

    await new_struct(opc.opc, idx, "MyOptionalStruct", [
        new_struct_field("MyBool", ua.VariantType.Boolean),
        new_struct_field("MyUInt32", ua.VariantType.UInt32),
        new_struct_field("MyString", ua.VariantType.String, optional=True),
        new_struct_field("MyInt64", ua.VariantType.Int64, optional=True)
    ])

    await opc.opc.load_data_type_definitions()

    my_struct_optional = ua.MyOptionalStruct()
    assert my_struct_optional.MyBool is not None
    assert my_struct_optional.MyUInt32 is not None
    assert my_struct_optional.MyString is None
    assert my_struct_optional.MyInt64 is None

    my_struct_optional.MyUInt32 = 45
    my_struct_optional.MyInt64 = -67
    var = await opc.opc.nodes.objects.add_variable(idx, "my_struct_optional", ua.Variant(my_struct_optional, ua.VariantType.ExtensionObject))

    val = await var.read_value()
    assert val.MyUInt32 == 45
    assert val.MyInt64 == -67
    assert val.MyString is None

    my_struct_optional = ua.MyOptionalStruct()
    my_struct_optional.MyUInt32 = 45
    my_struct_optional.MyInt64 = -67
    my_struct_optional.MyString = 'abc'
    await var.write_value(my_struct_optional)
    val = await var.read_value()
    assert val.MyUInt32 == 45
    assert val.MyInt64 == -67
    assert val.MyString == 'abc'


async def test_custom_struct_union(opc):
    idx = 4
    await new_struct(opc.opc, idx, "MyUnionStruct", [
        new_struct_field("MyString", ua.VariantType.String),
        new_struct_field("MyInt64", ua.VariantType.Int64),
    ], is_union=True)
    await opc.opc.load_data_type_definitions()
    my_union = ua.MyUnionStruct()
    my_union.MyInt64 = 555
    var = await opc.opc.nodes.objects.add_variable(idx, "my_union_struct", ua.Variant(my_union, ua.VariantType.ExtensionObject))
    val = await var.read_value()
    assert val.MyInt64 == 555
    assert val.MyString is None
    my_union.MyString = '1234'
    await var.write_value(my_union)
    val = await var.read_value()
    assert val.MyInt64 is None
    assert val.MyString == '1234'

    # test for union with the same type and multiple fields
    await new_struct(opc.opc, idx, "MyDuplicateTypeUnionStruct", [
        new_struct_field("MyString", ua.VariantType.String),
        new_struct_field("MyInt64", ua.VariantType.Int64),
        new_struct_field("MySecondString", ua.VariantType.String)
    ], is_union=True)
    await opc.opc.load_data_type_definitions()
    my_union = ua.MyDuplicateTypeUnionStruct()
    my_union.MyInt64 = 555
    var = await opc.opc.nodes.objects.add_variable(idx, "my_duplicate_union_struct", ua.Variant(my_union, ua.VariantType.ExtensionObject))
    val = await var.read_value()
    assert val.MyInt64 == 555
    assert val.MyString is None
    assert val.MySecondString is None
    my_union.MyString = '1234'
    await var.write_value(my_union)
    val = await var.read_value()
    assert val.MyInt64 is None
    assert val.MyString == '1234'
    assert val.MySecondString is None
    my_union.MySecondString = 'ABC'
    await var.write_value(my_union)
    val = await var.read_value()
    assert val.MyInt64 is None
    assert val.MyString is None
    assert val.MySecondString == 'ABC'


async def test_custom_struct_of_struct(opc):
    idx = 4

    dtype, encs = await new_struct(opc.opc, idx, "MySubStruct2", [
        new_struct_field("MyBool", ua.VariantType.Boolean),
        new_struct_field("MyUInt32", ua.VariantType.UInt32),
    ])

    await new_struct(opc.opc, idx, "MyMotherStruct2", [
        new_struct_field("MyBool", ua.VariantType.Boolean),
        new_struct_field("MySubStruct", dtype),
    ])

    await opc.opc.load_data_type_definitions()

    mystruct = ua.MyMotherStruct2()
    mystruct.MySubStruct = ua.MySubStruct2()
    mystruct.MySubStruct.MyUInt32 = 78
    var = await opc.opc.nodes.objects.add_variable(idx, "my_mother_struct", mystruct)
    val = await var.read_value()
    assert val.MySubStruct.MyUInt32 == 78


async def test_custom_list_of_struct(opc):
    idx = 4

    dtype, encs = await new_struct(opc.opc, idx, "MySubStruct3", [
        new_struct_field("MyBool", ua.VariantType.Boolean),
        new_struct_field("MyUInt32", ua.VariantType.UInt32),
    ])

    await new_struct(opc.opc, idx, "MyMotherStruct3", [
        new_struct_field("MyBool", ua.VariantType.Boolean),
        new_struct_field("MySubStruct", dtype, array=True),
    ])

    await opc.opc.load_data_type_definitions()

    mystruct = ua.MyMotherStruct3()
    mystruct.MySubStruct = [ua.MySubStruct3()]
    mystruct.MySubStruct[0].MyUInt32 = 78
    var = await opc.opc.nodes.objects.add_variable(idx, "my_mother_struct3", ua.Variant(mystruct, ua.VariantType.ExtensionObject))
    val = await var.read_value()
    assert val.MySubStruct[0].MyUInt32 == 78


async def test_custom_struct_with_enum(opc):
    idx = 4

    dtype = await new_enum(opc.opc, idx, "MyCustEnum2", [
        "titi",
        "toto",
        "tutu",
    ])

    await new_struct(opc.opc, idx, "MyStructEnum", [
        new_struct_field("MyBool", ua.VariantType.Boolean),
        new_struct_field("MyEnum", dtype),
    ])

    await opc.opc.load_data_type_definitions()

    mystruct = ua.MyStructEnum()
    mystruct.MyEnum = ua.MyCustEnum2.tutu
    var = await opc.opc.nodes.objects.add_variable(idx, "my_struct2", ua.Variant(mystruct, ua.VariantType.ExtensionObject))
    val = await var.read_value()
    assert val.MyEnum == ua.MyCustEnum2.tutu
    assert isinstance(val.MyEnum, ua.MyCustEnum2)


async def test_nested_struct_arrays(opc):
    idx = 4

    snode1, _ = await new_struct(opc.opc, idx, "MyStruct4", [
        new_struct_field("MyBool", ua.VariantType.Boolean),
        new_struct_field("MyUInt32List", ua.VariantType.UInt32, array=True),
    ])

    snode2, _ = await new_struct(opc.opc, idx, "MyNestedStruct", [
        new_struct_field("MyStructArray", snode1, array=True),
    ])

    await opc.opc.load_data_type_definitions()

    mystruct = ua.MyNestedStruct()
    mystruct.MyStructArray = [ua.MyStruct4(), ua.MyStruct4()]
    var = await opc.opc.nodes.objects.add_variable(idx, "nested", ua.Variant(mystruct, ua.VariantType.ExtensionObject))
    val = await var.read_value()
    assert len(val.MyStructArray) == 2
    assert mystruct.MyStructArray == val.MyStructArray


@contextlib.contextmanager
def expect_file_creation(filename: str):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / filename
        yield path
        assert Path.is_file(path), f"File {path} should have been created"


async def test_custom_struct_export(opc):
    idx = 4

    dtype, encs = await new_struct(opc.opc, idx, "MyMyStructExport", [
        new_struct_field("MyBool", ua.VariantType.Boolean),
        new_struct_field("MyUInt32", ua.VariantType.UInt32, array=True),
    ])
    with expect_file_creation("custom_struct_export.xml") as path:
        await opc.opc.export_xml([dtype, *encs], path)


async def test_custom_enum_export(opc):
    idx = 4

    dtype = await new_enum(opc.opc, idx, "MyCustEnumExport", [
        "titi",
        "toto",
        "tutu",
    ])
    with expect_file_creation("custom_enum_export.xml") as path:
        await opc.opc.export_xml([dtype], path)


async def test_custom_enum_import(opc):
    nodes = await opc.opc.import_xml("tests/custom_enum.xml")
    nodes = [opc.opc.get_node(node) for node in nodes]  # FIXME why does it return nodeids and not nodes?
    node = nodes[0]
    sdef = await node.read_data_type_definition()
    assert sdef.Fields[0].Name == "titi"
    with expect_file_creation("custom_enum_v2.xml") as path:
        await opc.opc.export_xml(nodes, path)


async def test_custom_struct_import(opc):
    nodes = await opc.opc.import_xml("tests/custom_struct.xml")
    nodes = [opc.opc.get_node(node) for node in nodes]  # FIXME why does it return nodeids and not nodes?
    node = nodes[0]  # FIXME: make that more robust
    sdef = await node.read_data_type_definition()
    assert sdef.StructureType == ua.StructureType.Structure
    assert sdef.Fields[0].Name == "MyBool"
    with expect_file_creation("custom_enum_v2.xml") as path:
        await opc.opc.export_xml(nodes, path)


async def test_custom_struct_recursive(opc):
    nodes = await opc.opc.import_xml("tests/custom_struct_recursive.xml")
    await opc.opc.load_data_type_definitions()

    nodes = [opc.opc.get_node(node) for node in nodes]  # FIXME why does it return nodeids and not nodes?
    node = nodes[0]  # FIXME: make that more robust
    sdef = await node.read_data_type_definition()
    assert sdef.StructureType == ua.StructureType.Structure
    assert sdef.Fields[0].Name == "Subparameters"

    # Check encoding / decoding
    param = ua.MyParameterType(Value=2)
    param.Subparameters.append(ua.MyParameterType(Value=1))
    bin = struct_to_binary(param)
    res = struct_from_binary(ua.MyParameterType, ua.utils.Buffer(bin))
    assert param == res

    with expect_file_creation("custom_struct_recursive_export.xml") as path:
        await opc.opc.export_xml(nodes, path)


async def test_enum_string_identifier_and_spaces(opc):
    idx = 4
    nodeid = ua.NodeId("My Identifier", idx)
    qname = ua.QualifiedName("My Enum", idx)
    await new_enum(opc.opc, nodeid, qname, [
        "my name with hole",
        "toto",
        "tutu",
    ])

    await opc.opc.load_data_type_definitions()

    var = await opc.opc.nodes.objects.add_variable(idx, "my enum", ua.My_Enum.my_name_with_hole)
    val = await var.read_value()
    assert val == 0


async def test_custom_struct_of_struct_with_spaces(opc):
    idx = 6

    nodeid = ua.NodeId("toto.My Identifier", idx)
    qname = ua.QualifiedName("My Sub Struct 1", idx)
    dtype, encs = await new_struct(opc.opc, nodeid, qname, [
        new_struct_field("My Bool", ua.VariantType.Boolean),
        new_struct_field("My UInt32", ua.VariantType.UInt32),
    ])

    await new_struct(opc.opc, idx, "My Mother Struct", [
        new_struct_field("My Bool", ua.VariantType.Boolean),
        new_struct_field("My Sub Struct", dtype),
    ])

    await opc.opc.load_data_type_definitions()

    mystruct = ua.My_Mother_Struct()
    mystruct.My_Sub_Struct = ua.My_Sub_Struct_1()
    mystruct.My_Sub_Struct.My_UInt32 = 78
    var = await opc.opc.nodes.objects.add_variable(idx, "my mother struct", mystruct)
    val = await var.read_value()
    assert val.My_Sub_Struct.My_UInt32 == 78


async def test_custom_method_with_struct(opc):
    idx = 4

    data_type, nodes = await new_struct(opc.opc, idx, "MyStructArg", [
        new_struct_field("MyBool", ua.VariantType.Boolean),
        new_struct_field("MyUInt32", ua.VariantType.UInt32, array=True),
    ])

    await opc.opc.load_data_type_definitions()

    @uamethod
    def func(parent, mystruct):
        mystruct.MyUInt32.append(100)
        return mystruct

    methodid = await opc.server.nodes.objects.add_method(
        ua.NodeId("ServerMethodWithStruct", 10),
        ua.QualifiedName('ServerMethodWithStruct', 10),
        func, [ua.MyStructArg], [ua.MyStructArg]
    )

    mystruct = ua.MyStructArg()
    mystruct.MyUInt32 = [78, 79]

    assert data_type.nodeid == mystruct.data_type

    result = await opc.opc.nodes.objects.call_method(methodid, mystruct)

    assert result.MyUInt32 == [78, 79, 100]


async def test_custom_method_with_enum(opc):
    idx = 4
    enum_node = await new_enum(opc.opc, idx, "MyCustEnumForMethod", [
        "titi",
        "toto",
    ])

    await opc.opc.load_data_type_definitions()

    @uamethod
    def func(parent, myenum1, myenum2, myenum3):
        assert myenum1 == ua.MyCustEnumForMethod.titi
        return ua.MyCustEnumForMethod.toto

    methodid = await opc.server.nodes.objects.add_method(
        ua.NodeId("servermethodwithenum", 10),
        ua.QualifiedName('servermethodwithenum', 10),
        func, [ua.MyCustEnumForMethod, enum_node, enum_node.nodeid], [ua.MyCustEnumForMethod]
    )

    result = await opc.opc.nodes.objects.call_method(methodid, ua.MyCustEnumForMethod.titi, ua.MyCustEnumForMethod.titi, ua.MyCustEnumForMethod.titi)

    assert result == ua.MyCustEnumForMethod.toto


async def test_sub_class(opc):
    idx = 4
    struct_with_sub = ua.PublishedDataSetDataType('Test', [''], ua.DataSetMetaDataType(), [], ua.PublishedEventsDataType(ua.NodeId(NamespaceIndex=1), [], ua.ContentFilter([])))
    var = await opc.opc.nodes.objects.add_variable(idx, "struct with sub", struct_with_sub, datatype=struct_with_sub.data_type)
    await var.write_value(struct_with_sub)
    val = await var.read_value()
    assert val == struct_with_sub
    assert val.DataSetSource == struct_with_sub.DataSetSource


async def test_object_meth_args(opc):
    # Test if InputArguments and OutputArguments are create in an instantiated object
    base_otype = opc.opc.get_node(ua.ObjectIds.BaseObjectType)
    custom_otype = await base_otype.add_object_type(2, 'ObjectWithMethodTestArgs')

    @uamethod
    def func(_parent, value):
        return value * 2
    meth = await custom_otype.add_method(ua.NodeId('ObjectWithMethodTestArgsTest', 2), ua.QualifiedName('ObjectWithMethodTestArgsTest', 2), func, [ua.VariantType.Int64], [ua.VariantType.Int64])
    await meth.set_modelling_rule(True)
    obj = await opc.opc.nodes.objects.add_object(2, 'ObjectWithMethodsArgs', custom_otype)
    await obj.get_child(['2:ObjectWithMethodTestArgsTest', 'InputArguments'])
    await obj.get_child(['2:ObjectWithMethodTestArgsTest', 'OutputArguments'])


async def test_alias(opc):
    '''
    Testing renaming buildin datatypes like UInt32, str and test it in a struct
    '''
    idx = 4
    parent = opc.opc.get_node(ua.ObjectIds.String)
    dt_str = await parent.add_data_type(ua.NodeId(NamespaceIndex=idx), "MyString")

    data_type, _ = await new_struct(opc.opc, idx, "MyAliasStruct", [
        new_struct_field("MyStringType", dt_str),
    ])
    await opc.opc.load_data_type_definitions()
    assert type(ua.MyString()) == ua.String
    var = await opc.opc.nodes.objects.add_variable(idx, "AliasedString", '1234', datatype=dt_str.nodeid)
    val = await var.read_value()
    assert val == '1234'

    v = ua.MyAliasStruct()
    var = await opc.opc.nodes.objects.add_variable(idx, "AliasedStruct", v, datatype=data_type.nodeid)
    val = await var.read_value()
    assert val == v
    v.MyStringType = '1234'
    await var.write_value(v)
    val = await var.read_value()


async def test_custom_struct_with_strange_chars(opc):
    idx = 4

    await new_struct(opc.opc, ua.StringNodeId('Toto"æ', 99), ua.QualifiedName("Siemens", 99), [
        new_struct_field('My"Bool', ua.VariantType.Boolean),
        new_struct_field("My'UInt32", ua.VariantType.UInt32, array=True),
    ])

    await opc.opc.load_data_type_definitions()
    mystruct = ua.Siemens()
    mystruct.My_UInt32 = [78, 79]
    mystruct.My_Bool = False
    var = await opc.opc.nodes.objects.add_variable(idx, "my_siemens_struct", ua.Variant(mystruct, ua.VariantType.ExtensionObject))
    val = await var.read_value()
    assert val.My_UInt32 == [78, 79]

async def test_sql_injection():
    table = 'myTable'
    validate_table_name(table)
    table = 'my table'
    with pytest.raises(SqlInjectionError) as _:
        validate_table_name(table)
    table = 'user;SELECT true'
    with pytest.raises(SqlInjectionError) as _:
        validate_table_name(table)
    table = 'user"'
    with pytest.raises(SqlInjectionError) as _:
        validate_table_name(table)
    table = "user'"
    with pytest.raises(SqlInjectionError) as _:
        validate_table_name(table)
