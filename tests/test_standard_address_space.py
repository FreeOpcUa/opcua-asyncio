import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from asyncua import ua
from asyncua.server.address_space import AddressSpace, NodeManagementService
from asyncua.server.standard_address_space import standard_address_space


def find_elem(parent, name, ns=None):
    if ns is None:
        try:
            return parent.find(parent.tag[0 : parent.tag.index("}") + 1] + name)
        except ValueError:
            return parent.find(name)
    return parent.find(ns + name)


def remove_elem(parent, name):
    e = find_elem(parent, name)
    if e is not None:
        parent.remove(e)


def try_apply(item, aliases):
    attrib = item.attrib
    for name in ("ReferenceType", "DataType"):
        try:
            value = attrib[name]
            attrib[name] = aliases[value]
        except KeyError:
            pass


def read_nodes(path):
    tree = ET.parse(path)
    root = tree.getroot()
    aliases_elem = find_elem(root, "Aliases")
    aliases = dict((a.attrib["Alias"], a.text) for a in aliases_elem)
    any(try_apply(i, aliases) for i in root.iter())
    root.remove(aliases_elem)
    remove_elem(root, "Models")
    remove_elem(root, "NamespaceUris")
    return dict((e.attrib["NodeId"], e) for e in root)


def get_refs(e):
    return set(
        (r.attrib["ReferenceType"], r.text, r.attrib.get("IsForward", "true") == "true")
        for r in find_elem(e, "References")
    )


@pytest.mark.skip("Donot understand that code and I am not sure we should test the xml file. it is not ours")
def test_std_address_space_references():
    aspace = AddressSpace()
    node_mgt_service = NodeManagementService(aspace)
    standard_address_space.fill_address_space(node_mgt_service)
    std_nodes = read_nodes(Path(__file__).parent.parent.absolute() / "schemas" / "Opc.Ua.NodeSet2.xml")
    for k in aspace.keys():
        refs = set((r.ReferenceTypeId.to_string(), r.NodeId.to_string(), r.IsForward) for r in aspace[k].references)
        xml_refs = set(
            (r.attrib["ReferenceType"], r.text, r.attrib.get("IsForward", "true") == "true")
            for r in find_elem(std_nodes[k.to_string()], "References")
        )
        assert 0 == len(xml_refs - refs)


def test_add_node_stores_write_masks_as_uint32() -> None:
    aspace = AddressSpace()
    node_mgt_service = NodeManagementService(aspace)
    attrs = ua.ObjectAttributes()
    attrs.WriteMask = 0x1234
    attrs.UserWriteMask = 0x5678
    attrs.SpecifiedAttributes = ua.NodeAttributesMask.WriteMask | ua.NodeAttributesMask.UserWriteMask
    item = ua.AddNodesItem()
    item.RequestedNewNodeId = ua.NodeId(1, 1)
    item.BrowseName = ua.QualifiedName("Obj", 1)
    item.NodeClass = ua.NodeClass.Object
    item.NodeAttributes = attrs
    assert list(node_mgt_service.try_add_nodes([item], check=False)) == []
    attributes = aspace[ua.NodeId(1, 1)].attributes
    for attr_id, expected in ((ua.AttributeIds.WriteMask, 0x1234), (ua.AttributeIds.UserWriteMask, 0x5678)):
        data_value = attributes[attr_id].value
        assert data_value is not None
        variant = data_value.Value
        assert variant is not None
        assert variant.VariantType == ua.VariantType.UInt32
        assert variant.Value == expected
