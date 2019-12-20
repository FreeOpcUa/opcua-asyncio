"""
from a list of nodes in the address space, build an XML file
format is the one from opc-ua specification
"""
import logging
import functools
from collections import OrderedDict
import xml.etree.ElementTree as Et
from copy import copy
import base64

from asyncua import ua
from ..ua import object_ids as o_ids
from .ua_utils import get_base_data_type
from asyncua.ua.uaerrors import UaError


class XmlExporter:
    """
    If it is required that for _extobj_to_etree members to the value should be written in a certain
    order it can be added to the dictionary below.
    """
    extobj_ordered_elements = {
        ua.NodeId(ua.ObjectIds.Argument): [
            'Name',
            'DataType',
            'ValueRank',
            'ArrayDimensions',
            'Description'
        ]
    }

    def __init__(self, server):
        self.logger = logging.getLogger(__name__)
        self.server = server
        self.aliases = {}
        self._addr_idx_to_xml_idx = {}

        node_set_attributes = OrderedDict()
        node_set_attributes['xmlns:xsi'] = 'http://www.w3.org/2001/XMLSchema-instance'
        node_set_attributes['xmlns:uax'] = 'http://opcfoundation.org/UA/2008/02/Types.xsd'
        node_set_attributes['xmlns:xsd'] = 'http://www.w3.org/2001/XMLSchema'
        node_set_attributes['xmlns'] = 'http://opcfoundation.org/UA/2011/03/UANodeSet.xsd'

        self.etree = Et.ElementTree(Et.Element('UANodeSet', node_set_attributes))

    async def build_etree(self, node_list, uris=None):
        """
        Create an XML etree object from a list of nodes; custom namespace uris are optional
        Namespaces used by nodes are always exported for consistency.
        Args:
            node_list: list of Node objects for export
            uris: list of namespace uri strings

        Returns:
        """
        self.logger.info('Building XML etree')
        await self._add_namespaces(node_list, uris)
        # add all nodes in the list to the XML etree
        for node in node_list:
            await self.node_to_etree(node)
        # add aliases to the XML etree
        self._add_alias_els()

    async def _add_namespaces(self, nodes, uris):
        idxs = await self._get_ns_idxs_of_nodes(nodes)
        ns_array = await self.server.get_namespace_array()
        # now add index of provided uris if necessary
        if uris:
            self._add_idxs_from_uris(idxs, uris, ns_array)
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
                node_idxs.append((await node.get_browse_name()).NamespaceIndex)
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

        Returns:
        """
        # try to write the XML etree to a file
        self.logger.info('Exporting XML file to %s', xmlpath)
        if pretty:
            indent(self.etree.getroot())
        func = functools.partial(self.etree.write, xmlpath, encoding='utf-8', xml_declaration=True)
        await self.server.loop.run_in_executor(None, func)

    def dump_etree(self):
        """
        Dump etree to console for debugging
        Returns:
        """
        self.logger.info('Dumping XML etree to console')
        Et.dump(self.etree)

    async def node_to_etree(self, node):
        """
        Add the necessary XML sub elements to the etree for exporting the node
        Args:
            node: Node object which will be added to XML etree

        Returns:
        """
        node_class = await node.get_node_class()

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
            nodeid = copy(nodeid)
            nodeid.NamespaceIndex = self._addr_idx_to_xml_idx[nodeid.NamespaceIndex]
        return nodeid.to_string()

    def _bname_to_string(self, bname):
        if bname.NamespaceIndex in self._addr_idx_to_xml_idx:
            bname = copy(bname)
            bname.NamespaceIndex = self._addr_idx_to_xml_idx[bname.NamespaceIndex]
        return bname.to_string()

    async def _add_node_common(self, nodetype, node):
        browsename = await node.get_browse_name()
        nodeid = node.nodeid
        parent = await node.get_parent()
        displayname = (await node.get_display_name()).Text
        desc = await node.get_description()
        if desc:
            desc = desc.Text
        node_el = Et.SubElement(self.etree.getroot(), nodetype)
        node_el.attrib["NodeId"] = self._node_to_string(nodeid)
        node_el.attrib["BrowseName"] = self._bname_to_string(browsename)
        if parent is not None:
            node_class = await node.get_node_class()
            if node_class in (ua.NodeClass.Object, ua.NodeClass.Variable, ua.NodeClass.Method):
                node_el.attrib["ParentNodeId"] = self._node_to_string(parent)
        self._add_sub_el(node_el, 'DisplayName', displayname)
        if desc not in (None, ""):
            self._add_sub_el(node_el, 'Description', desc)
        # FIXME: add WriteMask and UserWriteMask
        return node_el

    async def add_etree_object(self, node):
        """
        Add a UA object element to the XML etree
        """
        obj_el = await self._add_node_common("UAObject", node)
        var = await node.get_attribute(ua.AttributeIds.EventNotifier)
        if var.Value.Value != 0:
            obj_el.attrib["EventNotifier"] = str(var.Value.Value)
        await self._add_ref_els(obj_el, node)

    async def add_etree_object_type(self, node):
        """
        Add a UA object type element to the XML etree
        """
        obj_el = await self._add_node_common("UAObjectType", node)
        abstract = (await node.get_attribute(ua.AttributeIds.IsAbstract)).Value.Value
        if abstract:
            obj_el.attrib["IsAbstract"] = 'true'
        await self._add_ref_els(obj_el, node)

    async def add_variable_common(self, node, el):
        dtype = await node.get_data_type()
        if dtype.NamespaceIndex == 0 and dtype.Identifier in o_ids.ObjectIdNames:
            dtype_name = o_ids.ObjectIdNames[dtype.Identifier]
            self.aliases[dtype] = dtype_name
        else:
            dtype_name = dtype.to_string()
        rank = await node.read_rank()
        if rank != -1:
            el.attrib["ValueRank"] = str(int(rank))
        dim = await node.get_attribute(ua.AttributeIds.ArrayDimensions)
        if dim.Value.Value:
            el.attrib["ArrayDimensions"] = ",".join([str(i) for i in dim.Value.Value])
        el.attrib["DataType"] = dtype_name
        await self.value_to_etree(el, dtype_name, dtype, node)

    async def add_etree_variable(self, node):
        """
        Add a UA variable element to the XML etree
        """
        var_el = await self._add_node_common("UAVariable", node)
        await self._add_ref_els(var_el, node)
        await self.add_variable_common(node, var_el)

        accesslevel = (await node.get_attribute(ua.AttributeIds.AccessLevel)).Value.Value
        useraccesslevel = (await node.get_attribute(ua.AttributeIds.UserAccessLevel)).Value.Value

        # We only write these values if they are different from defaults
        # Not sure where default is defined....
        if accesslevel not in (0, ua.AccessLevel.CurrentRead.mask):
            var_el.attrib["AccessLevel"] = str(accesslevel)
        if useraccesslevel not in (0, ua.AccessLevel.CurrentRead.mask):
            var_el.attrib["UserAccessLevel"] = str(useraccesslevel)

        var = await node.get_attribute(ua.AttributeIds.MinimumSamplingInterval)
        if var.Value.Value:
            var_el.attrib["MinimumSamplingInterval"] = str(var.Value.Value)
        var = await node.get_attribute(ua.AttributeIds.Historizing)
        if var.Value.Value:
            var_el.attrib["Historizing"] = 'true'

    async def add_etree_variable_type(self, node):
        """
        Add a UA variable type element to the XML etree
        """
        var_el = await self._add_node_common("UAVariableType", node)
        await self.add_variable_common(node, var_el)
        abstract = await node.get_attribute(ua.AttributeIds.IsAbstract)
        if abstract.Value.Value:
            var_el.attrib["IsAbstract"] = "true"
        await self._add_ref_els(var_el, node)

    async def add_etree_method(self, node):
        obj_el = await self._add_node_common("UAMethod", node)
        var = await node.get_attribute(ua.AttributeIds.Executable)
        if var.Value.Value is False:
            obj_el.attrib["Executable"] = "false"
        var = await node.get_attribute(ua.AttributeIds.UserExecutable)
        if var.Value.Value is False:
            obj_el.attrib["UserExecutable"] = "false"
            await self._add_ref_els(obj_el, node)

    async def add_etree_reference_type(self, obj):
        obj_el = await self._add_node_common("UAReferenceType", obj)
        await self._add_ref_els(obj_el, obj)
        var = await obj.get_attribute(ua.AttributeIds.InverseName)
        if var is not None and var.Value.Value is not None and var.Value.Value.Text is not None:
            self._add_sub_el(obj_el, 'InverseName', var.Value.Value.Text)

    async def add_etree_datatype(self, obj):
        """
        Add a UA data type element to the XML etree
        """
        obj_el = await self._add_node_common("UADataType", obj)
        await self._add_ref_els(obj_el, obj)

    def _add_namespace_uri_els(self, uris):
        nuris_el = Et.Element('NamespaceUris')
        for uri in uris:
            self._add_sub_el(nuris_el, 'Uri', uri)
        self.etree.getroot().insert(0, nuris_el)

    def _add_alias_els(self):
        aliases_el = Et.Element('Aliases')
        ordered_keys = list(self.aliases.keys())
        ordered_keys.sort()
        for nodeid in ordered_keys:
            name = self.aliases[nodeid]
            ref_el = Et.SubElement(aliases_el, 'Alias', Alias=name)
            ref_el.text = nodeid.to_string()
        # insert behind the namespace element
        self.etree.getroot().insert(1, aliases_el)

    async def _add_ref_els(self, parent_el, obj):
        refs = await obj.get_references()
        refs_el = Et.SubElement(parent_el, 'References')
        for ref in refs:
            if ref.ReferenceTypeId.Identifier in o_ids.ObjectIdNames:
                ref_name = o_ids.ObjectIdNames[ref.ReferenceTypeId.Identifier]
            else:
                ref_name = ref.ReferenceTypeId.to_string()
            ref_el = Et.SubElement(refs_el, 'Reference')
            ref_el.attrib['ReferenceType'] = ref_name
            if not ref.IsForward:
                ref_el.attrib['IsForward'] = 'false'
            ref_el.text = self._node_to_string(ref.NodeId)

            self.aliases[ref.ReferenceTypeId] = ref_name

    async def member_to_etree(self, el, name, dtype, val):
        member_el = Et.SubElement(el, "uax:" + name)
        if isinstance(val, (list, tuple)):
            for v in val:
                await self._value_to_etree(member_el, ua.ObjectIdNames[dtype.Identifier], dtype, v)
        else:
            await self._val_to_etree(member_el, dtype, val)

    async def _val_to_etree(self, el, dtype, val):
        if dtype == ua.NodeId(ua.ObjectIds.NodeId):
            id_el = Et.SubElement(el, "uax:Identifier")
            id_el.text = val.to_string()
        elif dtype == ua.NodeId(ua.ObjectIds.Guid):
            id_el = Et.SubElement(el, "uax:String")
            id_el.text = str(val)
        elif dtype == ua.NodeId(ua.ObjectIds.Boolean):
            el.text = 'true' if val else 'false'
        elif dtype == ua.NodeId(ua.ObjectIds.ByteString):
            if val is None:
                val = b""
            data = base64.b64encode(val)
            el.text = data.decode("utf-8")
        elif not hasattr(val, "ua_types"):
            if isinstance(val, bytes):
                # FIXME: should we also encode this (localized text I guess) using base64??
                el.text = val.decode("utf-8")
            else:
                if val is not None:
                    el.text = str(val)
        else:
            for name, vtype in val.ua_types:
                await self.member_to_etree(el, name, ua.NodeId(getattr(ua.ObjectIds, vtype)), getattr(val, name))

    async def value_to_etree(self, el, dtype_name, dtype, node):
        var = (await node.get_data_value()).Value
        if var.Value is not None:
            val_el = Et.SubElement(el, 'Value')
            await self._value_to_etree(val_el, dtype_name, dtype, var.Value)

    async def _value_to_etree(self, el, type_name, dtype, val):
        if val is None:
            return

        if isinstance(val, (list, tuple)):
            if dtype.NamespaceIndex == 0 and dtype.Identifier <= 21:
                elname = "uax:ListOf" + type_name
            else:  # this is an extentionObject:
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

    async def _extobj_to_etree(self, val_el, name, dtype, val):
        obj_el = Et.SubElement(val_el, "uax:ExtensionObject")
        type_el = Et.SubElement(obj_el, "uax:TypeId")
        id_el = Et.SubElement(type_el, "uax:Identifier")
        id_el.text = dtype.to_string()
        body_el = Et.SubElement(obj_el, "uax:Body")
        struct_el = Et.SubElement(body_el, "uax:" + name)
        for name, vtype in val.ua_types:
            # FIXME; what happend if we have a custom type which is not part of ObjectIds???
            if vtype.startswith("ListOf"):
                vtype = vtype[6:]
            await self.member_to_etree(struct_el, name, ua.NodeId(getattr(ua.ObjectIds, vtype)), getattr(val, name))
            # self.member_to_etree(struct_el, name, extension_object_ids[vtype], getattr(val, name))
        # for name in self._get_member_order(dtype, val):
        # self.member_to_etree(struct_el, name, ua.NodeId(getattr(ua.ObjectIds, val.ua_types[name])), getattr(val, name))

    def _get_member_order(self, dtype, val):
        """
        If an dtype has an entry in XmlExporter.extobj_ordered_elements return the export order of the elements
        else return the unordered members.
        """
        if dtype not in XmlExporter.extobj_ordered_elements.keys():
            return val.ua_types.keys()
        else:
            member_keys = [name for name in XmlExporter.extobj_ordered_elements[dtype] if
                name in val.ua_types.keys() and getattr(val, name) is not None]

        return member_keys

def indent(elem, level=0):
    """
    copy and paste from http://effbot.org/zone/element-lib.htm#prettyprint
    it basically walks your tree and adds spaces and newlines so the tree is
    printed in a nice way
    """
    i = "\n" + level * "  "
    if len(elem):
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
