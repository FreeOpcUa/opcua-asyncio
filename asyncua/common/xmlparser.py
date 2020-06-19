"""
parse xml file from asyncua-spec
"""
import re
import asyncio
import base64
import logging
from pytz import utc


import xml.etree.ElementTree as ET

from .ua_utils import string_to_val
from asyncua import ua


def ua_type_to_python(val, uatype_as_str):
    """
    Converts a string value to a python value according to ua_utils.
    """
    return string_to_val(val, getattr(ua.VariantType, uatype_as_str))


def _to_bool(val):
    """
    Easy access to boolean conversion.
    """
    return ua_type_to_python(val, "Boolean")


class NodeData:

    def __init__(self):
        self.nodetype = None
        self.nodeid = None
        self.browsename = None
        self.displayname = None
        self.symname = None  # FIXME: this param is never used, why?
        self.parent = None
        self.parentlink = None
        self.desc = ""
        self.typedef = None
        self.refs = []
        self.nodeclass = None
        self.eventnotifier = 0

        # variable
        self.datatype = None
        self.rank = -1  # check default value
        self.value = None
        self.valuetype = None
        self.dimensions = None
        self.accesslevel = None
        self.useraccesslevel = None
        self.minsample = None

        # referencetype
        self.inversename = ""
        self.abstract = False
        self.symmetric = False

        # datatype
        self.definition = []

    def __str__(self):
        return f"NodeData(nodeid:{self.nodeid})"

    __repr__ = __str__


class RefStruct:

    def __init__(self):
        self.reftype = None
        self.forward = True
        self.target = None


class ExtObj:

    def __init__(self):
        self.typeid = None
        self.objname = None
        self.bodytype = None
        self.body = {}

    def __str__(self):
        return f"ExtObj({self.objname}, {self.body})"

    __repr__ = __str__


class XMLParser:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._retag = re.compile(r"(\{.*\})(.*)")
        self.root = None
        # FIXME: hard to get these xml namespaces with ElementTree, we may have to shift to lxml
        self.ns = {
            'base': "http://opcfoundation.org/UA/2011/03/UANodeSet.xsd",
            'uax': "http://opcfoundation.org/UA/2008/02/Types.xsd",
            'xsd': "http://www.w3.org/2001/XMLSchema",
            'xsi': "http://www.w3.org/2001/XMLSchema-instance"
        }

    async def parse(self, xmlpath=None, xmlstring=None):
        if xmlstring:
            self.root = ET.fromstring(xmlstring)
        else:
            tree = await asyncio.get_event_loop().run_in_executor(None, ET.parse, xmlpath)
            self.root = tree.getroot()

    def parse_sync(self, xmlpath=None, xmlstring=None):
        if xmlstring:
            self.root = ET.fromstring(xmlstring)
        else:
            tree = ET.parse(xmlpath)
            self.root = tree.getroot()

    def get_used_namespaces(self):
        """
        Return the used namespace uris in this import file
        """
        namespaces_uris = []
        for child in self.root:
            tag = self._retag.match(child.tag).groups()[1]
            if tag == 'NamespaceUris':
                namespaces_uris = [ns_element.text for ns_element in child]
                break
        return namespaces_uris

    def get_aliases(self) -> dict:
        """
        Return the used node aliases in this import file
        """
        aliases = {}
        for child in self.root:
            tag = self._retag.match(child.tag).groups()[1]
            if tag == 'Aliases':
                for el in child:
                    aliases[el.attrib["Alias"]] = el.text
                break
        return aliases

    def get_node_datas(self):
        nodes = []
        for child in self.root:
            tag = self._retag.match(child.tag).groups()[1]
            if tag not in ["Aliases", "NamespaceUris", "Extensions", "Models"]:  # these XML tags don't contain nodes
                node = self._parse_node(tag, child)
                nodes.append(node)
        return nodes

    def _parse_node(self, nodetype, child):
        """
        Parse a XML node and create a NodeData object.
        """
        obj = NodeData()
        obj.nodetype = nodetype
        for key, val in child.attrib.items():
            self._set_attr(key, val, obj)
        self.logger.info("Parsing node: %s %s", obj.nodeid, obj.browsename)
        obj.displayname = obj.browsename  # give a default value to display name
        for el in child:
            self._parse_attr(el, obj)
        return obj

    def _set_attr(self, key, val, obj):
        if key == "NodeId":
            obj.nodeid = val
        elif key == "BrowseName":
            obj.browsename = val
        elif key == "SymbolicName":
            obj.symname = val
        elif key == "ParentNodeId":
            obj.parent = val
        elif key == "DataType":
            obj.datatype = val
        elif key == "IsAbstract":
            obj.abstract = _to_bool(val)
        elif key == "Executable":
            obj.executable = _to_bool(val)
        elif key == "EventNotifier":
            obj.eventnotifier = int(val)
        elif key == "ValueRank":
            obj.rank = int(val)
        elif key == "ArrayDimensions":
            obj.dimensions = [int(i) for i in val.split(",")]
        elif key == "MinimumSamplingInterval":
            obj.minsample = int(val)
        elif key == "AccessLevel":
            obj.accesslevel = int(val)
        elif key == "UserAccessLevel":
            obj.useraccesslevel = int(val)
        elif key == "Symmetric":
            obj.symmetric = _to_bool(val)
        else:
            self.logger.info("Attribute not implemented: %s:%s", key, val)

    def _parse_attr(self, el, obj):
        tag = self._retag.match(el.tag).groups()[1]

        if tag == "DisplayName":
            obj.displayname = el.text
        elif tag == "Description":
            obj.desc = el.text
        elif tag == "References":
            self._parse_refs(el, obj)
        elif tag == "Value":
            self._parse_contained_value(el, obj)
        elif tag == "InverseName":
            obj.inversename = el.text
        elif tag == "Definition":
            for field in el:
                obj.definition.append(field)
        else:
            self.logger.info("Not implemented tag: %s", el)

    def _parse_contained_value(self, el, obj):
        """
        Parse the child of el as a constant.
        """
        val_el = el.find(".//")  # should be only one child
        self._parse_value(val_el, obj)

    def _parse_value(self, val_el, obj):
        """
        Parse the node val_el as a constant.
        """
        if val_el is not None and val_el.text is not None:
            ntag = self._retag.match(val_el.tag).groups()[1]
        else:
            ntag = "Null"

        obj.valuetype = ntag
        if ntag == "Null":
            obj.value = None
        elif hasattr(ua.ua_binary.Primitives1, ntag):
            # Elementary types have their parsing directly relying on ua_type_to_python.
            obj.value = ua_type_to_python(val_el.text, ntag)
        elif ntag == "DateTime":
            obj.value = ua_type_to_python(val_el.text, ntag)
            # According to specs, DateTime should be either UTC or with a timezone.
            if obj.value.tzinfo is None or obj.value.tzinfo.utcoffset(obj.value) is None:
                utc.localize(obj.value)  # FIXME Forcing to UTC if unaware, maybe should raise?
        elif ntag == "ByteString":
            if val_el.text is None:
                mytext = b""
            else:
                mytext = val_el.text.encode()
                mytext = base64.b64decode(mytext)
            obj.value = mytext
        elif ntag == "String":
            mytext = val_el.text
            if mytext is None:
                # Support importing null strings.
                mytext = ""
            # mytext = mytext.replace('\n', '').replace('\r', '')
            obj.value = mytext
        elif ntag == "Guid":
            self._parse_contained_value(val_el, obj)
            # Override parsed string type to guid.
            obj.valuetype = ntag
        elif ntag == "NodeId":
            id_el = val_el.find("uax:Identifier", self.ns)
            if id_el is not None:
                obj.value = id_el.text
        elif ntag == "ExtensionObject":
            obj.value = self._parse_ext_obj(val_el)
        elif ntag == "LocalizedText":
            obj.value = self._parse_body(val_el)
        elif ntag == "ListOfLocalizedText":
            obj.value = self._parse_list_of_localized_text(val_el)
        elif ntag == "ListOfExtensionObject":
            obj.value = self._parse_list_of_extension_object(val_el)
        elif ntag.startswith("ListOf"):
            # Default case for "ListOf" types.
            # Should stay after particular cases (e.g.: "ListOfLocalizedText").
            obj.value = []
            for val_el in val_el:
                tmp = NodeData()
                self._parse_value(val_el, tmp)
                obj.value.append(tmp.value)
        else:
            # Missing according to string_to_val: XmlElement, ExpandedNodeId,
            # QualifiedName, StatusCode.
            # Missing according to ua.VariantType (also missing in string_to_val):
            # DataValue, Variant, DiagnosticInfo.
            self.logger.warning("Parsing value of type '%s' not implemented", ntag)

    def _get_text(self, el):
        txtlist = [txt.strip() for txt in el.itertext()]
        return "".join(txtlist)

    def _parse_list_of_localized_text(self, el):
        value = []
        for localized_text in el:
            mylist = self._parse_body(localized_text)
            # each localized text is in a dictionary with "Locale" and "Text" keys
            item = {"Text": None, "Locale": None}
            for name, val in mylist:
                item.update({str(name): val})
            # value is an array of dictionaries with localized texts
            value.append(item) 
        return value

    def _parse_list_of_extension_object(self, el):
        """
        Parse a uax:ListOfExtensionObject Value
        Return an list of ExtObj
        """
        value = []
        for extension_object in el:
            ext_obj = self._parse_ext_obj(extension_object)
            value.append(ext_obj)
        return value

    def _parse_ext_obj(self, el):
        ext = ExtObj()
        for extension_object_part in el:
            ntag = self._retag.match(extension_object_part.tag).groups()[1]
            if ntag == 'TypeId':
                ntag = self._retag.match(extension_object_part.find('*').tag).groups()[1]
                ext.typeid = self._get_text(extension_object_part)
            elif ntag == 'Body':
                ext.objname = self._retag.match(extension_object_part.find('*').tag).groups()[1]
                ext.body = self._parse_body(extension_object_part)
            else:
                self.logger.warning("Unknown ntag", ntag)
        return ext

    def _parse_body(self, el):
        body = []
        for body_item in el:
            otag = self._retag.match(body_item.tag).groups()[1]
            childs = [i for i in body_item]
            if not childs:
                val = self._get_text(body_item)
            else:
                val = self._parse_body(body_item)
            if val:
                body.append((otag, val))
        return body

    def _parse_refs(self, el, obj):
        parent, parentlink = obj.parent, None

        for ref in el:
            struct = RefStruct()
            struct.forward = "IsForward" not in ref.attrib or ref.attrib["IsForward"] not in ("false", "False")
            struct.target = ref.text
            struct.reftype = ref.attrib["ReferenceType"]
            obj.refs.append(struct)

            if ref.attrib["ReferenceType"] == "HasTypeDefinition":
                obj.typedef = ref.text
            elif not struct.forward:
                parent, parentlink = struct.target, struct.reftype
                if obj.parent == parent or obj.parent != parent and not obj.parentlink:
                    obj.parentlink = parentlink

        if obj.parent and not obj.parentlink:
            # the case of asimple parent attribute without any reverse link
            obj.parentlink = "HasComponent"
        if not obj.parent:
            obj.parent, obj.parentlink = parent, parentlink
            self.logger.info("Could not find parent for node '%s'", obj.nodeid)
