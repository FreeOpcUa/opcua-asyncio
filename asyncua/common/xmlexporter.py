"""
from a list of nodes in the address space, build an XML file
format is the one from opc-ua specification
"""

from __future__ import annotations

import logging
import asyncio
import functools
from collections import OrderedDict
from typing import Any, Union
import xml.etree.ElementTree as Et
import base64
from dataclasses import is_dataclass
from enum import Enum

import asyncua
from asyncua import ua
from asyncua.ua.uatypes import type_string_from_type
from asyncua.ua.uaerrors import UaError, UaInvalidParameterError
from .. import Node
from ..ua import object_ids as o_ids
from .ua_utils import get_base_data_type
from .utils import fields_with_resolved_types


class XmlExporter:
    """
    If it is required that for _extobj_to_etree members to the value should be written in a certain
    order it can be added to the dictionary below.
    """

    extobj_ordered_elements = {
        ua.NodeId(ua.ObjectIds.Argument): ["Name", "DataType", "ValueRank", "ArrayDimensions", "Description"]
    }

    def __init__(self, server: Union[asyncua.Server, asyncua.Client], export_values: bool = False):
        """
        param: export_values: exports values from variants (CustomDataTypes are not support!)
        """
        self.logger = logging.getLogger(__name__)
        self.server = server
        self.aliases = {}
        self._addr_idx_to_xml_idx = {}

        node_write_attributes = OrderedDict()
        node_write_attributes["xmlns:xsi"] = "http://www.w3.org/2001/XMLSchema-instance"
        node_write_attributes["xmlns:uax"] = "http://opcfoundation.org/UA/2008/02/Types.xsd"
        node_write_attributes["xmlns:xsd"] = "http://www.w3.org/2001/XMLSchema"
        node_write_attributes["xmlns"] = "http://opcfoundation.org/UA/2011/03/UANodeSet.xsd"

        self.etree = Et.ElementTree(Et.Element("UANodeSet", node_write_attributes))
        self._export_values = export_values
        if self._export_values:
            self.logger.warning("Exporting values of variables is limited and can result in invalid xmls.")

    async def build_etree(self, node_list, add_all_namespaces = False):
        """
        Create an XML etree object from a list of nodes;
        Namespaces used by nodes are always exported for consistency.
        Args:
            node_list: list of Node objects for export
            add_all_namespaces: if true export all server namespaces no matter which are used.
        Returns:
        """
        self.logger.info("Building XML etree")

        await self._add_namespaces(node_list, add_all_namespaces)
        # add all nodes in the list to the XML etree
        for node in node_list:
            await self.node_to_etree(node)
        # add aliases to the XML etree
        self._add_alias_els()

    def _chunked_iterable(self, iterable, chunk_size):
        """Yield successive chunk_size chunks from iterable."""
        for i in range(0, len(iterable), chunk_size):
            yield iterable[i:i + chunk_size]

    async def build_etree_chunked(self, node_list, add_all_namespaces = False, chunk_size=500):

        """
        Create an XML etree object from a list of nodes in chunks to prevent a server-overload because of the mass requests;
        Namespaces used by nodes are always exported for consistency.
        Args:
            node_list: list of Node objects for export
            add_all_namespaces: if true export all server namespaces no matter which are used.
        Returns:
        """
        self.logger.info("Building XML etree chunked")

        await self._add_namespaces(node_list, add_all_namespaces)
        # add all nodes in the list to the XML etree
        for i, chunk in enumerate(self._chunked_iterable(list, chunk_size)):
            await self.server.disconnect()
            await self.server.connect()
            # add all nodes in the list to the XML etree
            for node in chunk:
                await self.node_to_etree(node)

        # add aliases to the XML etree
        self._add_alias_els()

    async def _add_namespaces(self, nodes, add_all_namespaces = False):

        if add_all_namespaces:
            # add all namespaces
            ns_array = await self.server.get_namespace_array()
            self._addr_idx_to_xml_idx = {count: count for count in range(len(ns_array))}
            # write namespaces to xml
            self._add_namespace_uri_els(ns_array)
        else:
            ns_array = await self.server.get_namespace_array()
            idxs = await self._get_ns_idxs_of_nodes(nodes)

            # now create a dict of idx_in_address_space to idx_in_exported_file
            self._addr_idx_to_xml_idx = self._make_idx_dict(idxs, ns_array)
            ns_to_export = [ns_array[i] for i in sorted(list(self._addr_idx_to_xml_idx.keys())) if i != 0]
            # write namespaces to xml
            self._add_namespace_uri_els(ns_to_export)

    def _make_idx_dict(self, idxs, ns_array):
        idxs.sort()
        addr_idx_to_xml_idx = {0: 0}
        for xml_idx, addr_idx in enumerate(idxs):
            if addr_idx >= len(ns_array):
                break
            addr_idx_to_xml_idx[addr_idx] = xml_idx + 1
        return addr_idx_to_xml_idx

    async def _get_ns_idxs_of_nodes(self, nodes):
        """
        get a list of all indexes used or references by nodes
        """
        idxs = []
        for node in nodes:
            node_idxs = [node.nodeid.NamespaceIndex]
            try:
                node_idxs.append((await node.read_browse_name()).NamespaceIndex)
            except UaError:
                self.logger.exception("Error retrieving browse name of node %s", node)
                raise

            node_idxs.extend(ref.NodeId.NamespaceIndex for ref in await node.get_references())
            node_idxs = list(set(node_idxs))  # remove duplicates
            for i in node_idxs:
                if i != 0 and i not in idxs:
                    idxs.append(i)
        return idxs

    def _add_idxs_from_uris(self, idxs, uris, ns_array):
        for uri in uris:
            if uri in ns_array:
                i = ns_array.index(uri)
                if i not in idxs:
                    idxs.append(i)

    async def write_xml(self, xmlpath, pretty=True):
        """
        Write the XML etree in the exporter object to a file
        Args:
            xmlpath: string representing the path/file name
            pretty: add spaces and newlines, to be more readable
        Returns:
        """
        # try to write the XML etree to a file
        self.logger.info("Exporting XML file to %s", xmlpath)
        if pretty:
            indent(self.etree.getroot())
        func = functools.partial(self.etree.write, xmlpath, encoding="utf-8", xml_declaration=True)
        await asyncio.get_running_loop().run_in_executor(None, func)

    def dump_etree(self):
        """
        Dump etree to console for debugging
        Returns:
        """
        self.logger.info("Dumping XML etree to console")
        Et.dump(self.etree)

    async def node_to_etree(self, node):
        """
        Add the necessary XML sub elements to the etree for exporting the node
        Args:
            node: Node object which will be added to XML etree

        Returns:
        """
        node_class = await node.read_node_class()

        if node_class is ua.NodeClass.Object:
            await self.add_etree_object(node)
        elif node_class is ua.NodeClass.ObjectType:
            await self.add_etree_object_type(node)
        elif node_class is ua.NodeClass.Variable:
            await self.add_etree_variable(node)
        elif node_class is ua.NodeClass.VariableType:
            await self.add_etree_variable_type(node)
        elif node_class is ua.NodeClass.ReferenceType:
            await self.add_etree_reference_type(node)
        elif node_class is ua.NodeClass.DataType:
            await self.add_etree_datatype(node)
        elif node_class is ua.NodeClass.Method:
            await self.add_etree_method(node)
        else:
            self.logger.info("Exporting node class not implemented: %s ", node_class)

    def _add_sub_el(self, el, name, text):
        child_el = Et.SubElement(el, name)
        child_el.text = text
        return child_el

    def _node_to_string(self, nodeid):
        if not isinstance(nodeid, ua.NodeId):
            nodeid = nodeid.nodeid

        if nodeid.NamespaceIndex in self._addr_idx_to_xml_idx:
            nodeid = ua.NodeId(nodeid.Identifier, NamespaceIndex=self._addr_idx_to_xml_idx[nodeid.NamespaceIndex])
        return nodeid.to_string()

    def _bname_to_string(self, bname):
        if bname.NamespaceIndex in self._addr_idx_to_xml_idx:
            bname = ua.QualifiedName(Name=bname.Name, NamespaceIndex=self._addr_idx_to_xml_idx[bname.NamespaceIndex])
        return bname.to_string()

    async def _add_node_common(self, nodetype, node):
        browsename = await node.read_browse_name()
        nodeid = node.nodeid
        parent = await node.get_parent()
        displayname = (await node.read_display_name()).Text
        try:
            desc = await node.read_description()
            if desc:
                desc = desc.Text
        except ua.uaerrors.BadAttributeIdInvalid:
            desc = None
        node_el = Et.SubElement(self.etree.getroot(), nodetype)
        node_el.attrib["NodeId"] = self._node_to_string(nodeid)
        node_el.attrib["BrowseName"] = self._bname_to_string(browsename)
        if parent is not None:
            node_class = await node.read_node_class()
            if node_class in (ua.NodeClass.Object, ua.NodeClass.Variable, ua.NodeClass.Method):
                node_el.attrib["ParentNodeId"] = self._node_to_string(parent)
        self._add_sub_el(node_el, "DisplayName", displayname)
        if desc not in (None, ""):
            self._add_sub_el(node_el, "Description", desc)
        # FIXME: add WriteMask and UserWriteMask
        await self._add_ref_els(node_el, node)
        return node_el

    async def add_etree_object(self, node):
        """
        Add a UA object element to the XML etree
        """
        obj_el = await self._add_node_common("UAObject", node)
        var = await node.read_attribute(ua.AttributeIds.EventNotifier)
        if var.Value.Value != 0:
            obj_el.attrib["EventNotifier"] = str(var.Value.Value)

    async def add_etree_object_type(self, node):
        """
        Add a UA object type element to the XML etree
        """
        obj_el = await self._add_node_common("UAObjectType", node)
        abstract = (await node.read_attribute(ua.AttributeIds.IsAbstract)).Value.Value
        if abstract:
            obj_el.attrib["IsAbstract"] = "true"

    async def add_variable_common(self, node, el, export_value: bool):
        dtype = await node.read_data_type()
        if dtype.NamespaceIndex == 0 and dtype.Identifier in o_ids.ObjectIdNames:
            dtype_name = o_ids.ObjectIdNames[dtype.Identifier]
            self.aliases[dtype] = dtype_name
        else:
            dtype_name = self._node_to_string(dtype)
        try:
            rank = await node.read_value_rank()
            if rank != -1:
                el.attrib["ValueRank"] = str(int(rank))
        except ua.uaerrors.BadAttributeIdInvalid:
            pass

        dim = await node.read_attribute(ua.AttributeIds.ArrayDimensions, raise_on_bad_status=False)
        if dim is not None and dim.Value.Value:
            el.attrib["ArrayDimensions"] = ",".join([str(i) for i in dim.Value.Value])
        el.attrib["DataType"] = dtype_name
        if export_value:
            await self.value_to_etree(el, dtype_name, dtype, node)

    async def add_etree_variable(self, node):
        """
        Add a UA variable element to the XML etree
        """
        var_el = await self._add_node_common("UAVariable", node)
        await self.add_variable_common(node, var_el, self._export_values)

        accesslevel = (await node.read_attribute(ua.AttributeIds.AccessLevel)).Value.Value
        useraccesslevel = (await node.read_attribute(ua.AttributeIds.UserAccessLevel)).Value.Value

        # We only write these values if they are different from defaults
        # Not sure where default is defined....
        if accesslevel not in (0, ua.AccessLevel.CurrentRead.mask):
            var_el.attrib["AccessLevel"] = str(accesslevel)
        if useraccesslevel not in (0, ua.AccessLevel.CurrentRead.mask):
            var_el.attrib["UserAccessLevel"] = str(useraccesslevel)

        var = await node.read_attribute(ua.AttributeIds.MinimumSamplingInterval, raise_on_bad_status=False)
        if var.Value.Value:
            var_el.attrib["MinimumSamplingInterval"] = str(var.Value.Value)
        var = await node.read_attribute(ua.AttributeIds.Historizing)
        if var.Value.Value:
            var_el.attrib["Historizing"] = "true"

    async def add_etree_variable_type(self, node):
        """
        Add a UA variable type element to the XML etree
        """
        var_el = await self._add_node_common("UAVariableType", node)
        await self.add_variable_common(node, var_el, True)
        abstract = await node.read_attribute(ua.AttributeIds.IsAbstract)
        if abstract.Value.Value:
            var_el.attrib["IsAbstract"] = "true"

    async def add_etree_method(self, node):
        obj_el = await self._add_node_common("UAMethod", node)
        var = await node.read_attribute(ua.AttributeIds.Executable)
        if var.Value.Value is False:
            obj_el.attrib["Executable"] = "false"
        var = await node.read_attribute(ua.AttributeIds.UserExecutable)
        if var.Value.Value is False:
            obj_el.attrib["UserExecutable"] = "false"

    async def add_etree_reference_type(self, obj):
        obj_el = await self._add_node_common("UAReferenceType", obj)
        var = await obj.read_attribute(ua.AttributeIds.InverseName, raise_on_bad_status=False)
        if var is not None and var.Value.Value is not None and var.Value.Value.Text is not None:
            self._add_sub_el(obj_el, "InverseName", var.Value.Value.Text)

    async def add_etree_datatype(self, obj):
        """
        Add a UA data type element to the XML etree
        """
        obj_el = await self._add_node_common("UADataType", obj)
        dv = await obj.read_attribute(ua.AttributeIds.DataTypeDefinition, raise_on_bad_status=False)
        if dv is not None and dv.Value.Value:
            sdef = dv.Value.Value
            # FIXME: can probably get that name somewhere else
            bname = await obj.read_attribute(ua.AttributeIds.BrowseName)
            bname = bname.Value.Value
            sdef_el = Et.SubElement(obj_el, "Definition")
            sdef_el.attrib["Name"] = bname.Name
            if isinstance(sdef, ua.StructureDefinition):
                if sdef.StructureType == ua.StructureType.Union:
                    sdef_el.attrib["IsUnion"] = "true"
                elif sdef.StructureType == ua.StructureType.StructureWithOptionalFields:
                    sdef_el.attrib["IsOptional"] = "true"
                self._structure_fields_to_etree(sdef_el, sdef)
            elif isinstance(sdef, ua.EnumDefinition):
                self._enum_fields_to_etree(sdef_el, sdef)
            else:
                self.logger.warning("Unknown DataTypeSpecification element: %s", sdef)

    def _structure_fields_to_etree(self, sdef_el, sdef):
        for field in sdef.Fields:
            field_el = Et.SubElement(sdef_el, "Field")
            field_el.attrib["Name"] = field.Name
            field_el.attrib["DataType"] = self._node_to_string(field.DataType)
            if field.ValueRank != -1:
                field_el.attrib["ValueRank"] = str(int(field.ValueRank))
            if field.ArrayDimensions:
                field_el.attrib["ArrayDimensions"] = ", ".join([str(i) for i in field.ArrayDimensions])
            if field.IsOptional:
                field_el.attrib["IsOptional"] = "true"

    def _enum_fields_to_etree(self, sdef_el, sdef):
        for field in sdef.Fields:
            field_el = Et.SubElement(sdef_el, "Field")
            field_el.attrib["Name"] = field.Name
            field_el.attrib["Value"] = str(field.Value)

    def _add_namespace_uri_els(self, uris):
        nuris_el = Et.Element("NamespaceUris")
        for uri in uris:
            self._add_sub_el(nuris_el, "Uri", uri)
        self.etree.getroot().insert(0, nuris_el)

    def _add_alias_els(self):
        aliases_el = Et.Element("Aliases")
        ordered_keys = list(self.aliases.keys())
        ordered_keys.sort()
        for nodeid in ordered_keys:
            name = self.aliases[nodeid]
            ref_el = Et.SubElement(aliases_el, "Alias", Alias=name)
            ref_el.text = self._node_to_string(nodeid)
        # insert behind the namespace element
        self.etree.getroot().insert(1, aliases_el)

    async def _add_ref_els(self, parent_el, obj):
        refs = await obj.get_references()
        refs_el = Et.SubElement(parent_el, "References")
        for ref in refs:
            if ref.ReferenceTypeId.NamespaceIndex == 0 and ref.ReferenceTypeId.Identifier in o_ids.ObjectIdNames:
                ref_name = o_ids.ObjectIdNames[ref.ReferenceTypeId.Identifier]
            else:
                ref_name = self._node_to_string(ref.ReferenceTypeId)
            ref_el = Et.SubElement(refs_el, "Reference")
            ref_el.attrib["ReferenceType"] = ref_name
            if not ref.IsForward:
                ref_el.attrib["IsForward"] = "false"
            ref_el.text = self._node_to_string(ref.NodeId)

            self.aliases[ref.ReferenceTypeId] = ref_name

    async def member_to_etree(self, el, name, dtype, val):
        member_el = Et.SubElement(el, "uax:" + name)
        if isinstance(val, (list, tuple)):
            for v in val:
                try:
                    type_name = ua.ObjectIdNames[dtype.Identifier]
                except KeyError:
                    dtype_node = self.server.get_node(dtype)
                    enc_node = (
                        await dtype_node.get_referenced_nodes(ua.ObjectIds.HasEncoding, ua.BrowseDirection.Forward)
                    )[0]
                    type_name = ua.extension_objects_by_typeid[enc_node.nodeid].__name__

                await self._value_to_etree(member_el, type_name, dtype, v)
        else:
            await self._val_to_etree(member_el, dtype, val)

    async def _val_to_etree(self, el, dtype, val):
        if dtype == ua.NodeId(ua.ObjectIds.NodeId) or dtype == ua.NodeId(ua.ObjectIds.ExpandedNodeId):
            id_el = Et.SubElement(el, "uax:Identifier")
            if val.NamespaceIndex in self._addr_idx_to_xml_idx:
                val = ua.NodeId(val.Identifier, NamespaceIndex=self._addr_idx_to_xml_idx[val.NamespaceIndex])
            id_el.text = val.to_string()
        elif dtype == ua.NodeId(ua.ObjectIds.Guid):
            id_el = Et.SubElement(el, "uax:String")
            id_el.text = str(val)
        elif dtype == ua.NodeId(ua.ObjectIds.Boolean):
            el.text = "true" if val else "false"
        elif dtype == ua.NodeId(ua.ObjectIds.XmlElement):
            if val.Value is None:
                val = ""
            el.text = val.Value
        elif dtype == ua.NodeId(ua.ObjectIds.ByteString):
            if val is None:
                val = b""
            data = base64.b64encode(val)
            el.text = data.decode("utf-8")
        elif dtype == ua.NodeId(ua.ObjectIds.QualifiedName):
            if val.Name is not None:
                name_el = Et.SubElement(el, "uax:Name")
                name_el.text = val.Name
            if val.NamespaceIndex != 0:
                ns = Et.SubElement(el, "uax:NamespaceIndex")
                ns.text = str(val.NamespaceIndex)
        elif dtype == ua.NodeId(ua.ObjectIds.StatusCode):
            code_el = Et.SubElement(el, "uax:Code")
            code_el.text = str(val.value)
        elif not is_dataclass(val):
            if isinstance(val, bytes):
                # FIXME: should we also encode this (localized text I guess) using base64??
                el.text = val.decode("utf-8")
            elif isinstance(val, Enum):
                el.text = str(val.value)
            else:
                if val is not None:
                    el.text = str(val)
        else:
            await self._all_fields_to_etree(el, val)

    async def value_to_etree(self, el, dtype_name, dtype, node):
        var = await node.read_data_value(raise_on_bad_status=False)
        if var.Value.Value is not None:
            val_el = Et.SubElement(el, "Value")
            await self._value_to_etree(val_el, dtype_name, dtype, var.Value.Value)

    async def _value_to_etree(self, el: Et.Element, type_name: str, dtype: ua.NodeId, val: Any) -> None:
        if val is None:
            return

        if isinstance(val, (list, tuple)):
            if not isinstance(dtype.Identifier, int):
                raise UaInvalidParameterError(f"Expected int, got {type(dtype.Identifier)}")
            if dtype.NamespaceIndex == 0 and dtype.Identifier <= 21:
                elname = "uax:ListOf" + type_name
            else:  # this is an extensionObject:
                elname = "uax:ListOfExtensionObject"

            list_el = Et.SubElement(el, elname)
            for nval in val:
                await self._value_to_etree(list_el, type_name, dtype, nval)
        else:
            dtype_base = await get_base_data_type(self.server.get_node(dtype))
            dtype_base = dtype_base.nodeid

            if dtype_base == ua.NodeId(ua.ObjectIds.Enumeration):
                dtype_base = ua.NodeId(ua.ObjectIds.Int32)
                type_name = ua.ObjectIdNames[dtype_base.Identifier]

            if dtype_base.NamespaceIndex == 0 and dtype_base.Identifier <= 21:
                type_name = ua.ObjectIdNames[dtype_base.Identifier]
                val_el = Et.SubElement(el, "uax:" + type_name)
                await self._val_to_etree(val_el, dtype_base, val)
            else:
                await self._extobj_to_etree(el, type_name, dtype, val)

    async def _extobj_to_etree(self, val_el: Et.Element, name: str, dtype: ua.NodeId, val: Any) -> None:
        if "=" in name:
            try:
                name = ua.extension_objects_by_datatype[dtype].__name__
            except KeyError:
                try:
                    name = ua.enums_by_datatype[dtype].__name__
                except KeyError:
                    node: Node = self.server.get_node(dtype)
                    browse_name = await node.read_browse_name()
                    name = browse_name.Name
        obj_el = Et.SubElement(val_el, "uax:ExtensionObject")
        type_el = Et.SubElement(obj_el, "uax:TypeId")
        id_el = Et.SubElement(type_el, "uax:Identifier")
        id_el.text = self._node_to_string(dtype)
        body_el = Et.SubElement(obj_el, "uax:Body")
        struct_el = Et.SubElement(body_el, "uax:" + name)
        await self._all_fields_to_etree(struct_el, val)

    async def _all_fields_to_etree(self, struct_el: Et.Element, val: Any) -> None:
        # TODO: adding the 'ua' module to the globals to resolve the type hints might not be enough.
        #       it is possible that the type annotations also refere to classes defined in other modules.
        for field in fields_with_resolved_types(val, globalns={"ua": ua}):
            # FIXME; what happened if we have a custom type which is not part of ObjectIds???
            if field.name == "Encoding":
                continue
            type_name = type_string_from_type(field.type)
            try:
                dtype = ua.NodeId(getattr(ua.ObjectIds, type_name))
            except AttributeError:
                try:
                    enc_node: Node = self.server.get_node(ua.extension_object_typeids[type_name])
                    dtype_node = (
                        await enc_node.get_referenced_nodes(ua.ObjectIds.HasEncoding, ua.BrowseDirection.Inverse)
                    )[0]
                    dtype = dtype_node.nodeid
                except KeyError:
                    for cls in ua.enums_datatypes:
                        if cls.__class__ == field.type.__class__:
                            dtype = ua.enums_datatypes[cls]
                            break
                    self.logger.debug("could not find field type %s in registered types", field.type)
                    return
            await self.member_to_etree(struct_el, field.name, dtype, getattr(val, field.name))


def indent(elem, level=0):
    """
    copy and paste from http://effbot.org/zone/element-lib.htm#prettyprint
    it basically walks your tree and adds spaces and newlines so the tree is
    printed in a nice way
    """
    i = "\n" + level * "  "
    if elem:
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
