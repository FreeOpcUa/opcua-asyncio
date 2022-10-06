"""
parse xml file from asyncua-spec
"""
import re
import asyncio
import base64
import logging
from typing import List, Tuple
import xml.etree.ElementTree as ET

from pytz import utc
from asyncua import ua

from .ua_utils import string_to_val


def ua_type_to_python(val, uatype_as_str):
    """
    Converts a string value to a python value according to ua_utils.
    """
    if hasattr(ua.VariantType, uatype_as_str):
        return string_to_val(val, getattr(ua.VariantType, uatype_as_str))
    elif hasattr(ua, uatype_as_str):
        return string_to_val(val, getattr(ua, uatype_as_str))
    else:
        raise ValueError


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
        self.definitions = []
        self.struct_type = ""

    def __str__(self):
        return f"NodeData(nodeid:{self.nodeid})"

    __repr__ = __str__


class Field:
    def __init__(self, data):
        self.datatype = data.get("DataType", "i=24")  # Default is BaseDataType
        self.name = data.get("Name")
        self.dname = data.get("DisplayName", "")
        self.optional = bool(data.get("IsOptional", False))
        self.valuerank = int(data.get("ValueRank", -1))
        self.arraydim = data.get("ArrayDimensions", None)  # FIXME: check type
        self.value = int(data.get("Value", 0))
        self.desc = data.get("Description", "")
        self.max_str_len = int(data.get("MaxStringLength", 0))


class RefStruct:

    def __init__(self):
        self.reftype = None
        self.forward = True
        self.target = None

    def __str__(self):
        return f"RefStruct({self.reftype, self.forward, self.target})"

    __repr__ = __str__


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
            tree = await asyncio.get_running_loop().run_in_executor(None, ET.parse, xmlpath)
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
        self.logger.debug("Parsing node: %s %s", obj.nodeid, obj.browsename)
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
            obj.minsample = float(val)
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
            if el.attrib.get("IsUnion", False):
                obj.struct_type = "IsUnion"
            elif el.attrib.get("IsOptional", False):
                obj.struct_type = "IsOptional"
            for field in el:
                field = self._parse_field(field)
                obj.definitions.append(field)
        else:
            self.logger.info("Not implemented tag: %s", el)

    def _parse_field(self, field):
        return Field(field)

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
        elif ntag == "String" or ntag == "XmlElement":
            # String and XMLElement are identical only type is different
            mytext = val_el.text
            if mytext is None:
                # Support importing null strings.
                mytext = ""
            if ntag == "XmlElement":
                obj.value = ua.XmlElement(mytext)
            else:
                obj.value = mytext
        elif ntag == "Guid":
            self._parse_contained_value(val_el, obj)
            # Override parsed string type to guid.
            obj.valuetype = ntag
        elif ntag == "NodeId":
            id_el = val_el.find("uax:Identifier", self.ns)
            if id_el is not None:
                obj.value = id_el.text
        elif ntag == "ExpandedNodeId":
            id_el = val_el.find("uax:Identifier", self.ns)
            if id_el is not None:
                obj.value = ua.NodeId.from_string(id_el.text)
                if not isinstance(obj.value, ua.ExpandedNodeId):
                    obj.value = ua.ExpandedNodeId(obj.value.Identifier, obj.value.NamespaceIndex)
        elif ntag == "ExtensionObject":
            obj.value = self._parse_ext_obj(val_el)
        elif ntag == "LocalizedText":
            obj.value = self._parse_body(val_el)
        elif ntag == "ListOfLocalizedText":
            obj.value = self._parse_list_of_localized_text(val_el)
        elif ntag == "ListOfExtensionObject":
            obj.value = self._parse_list_of_extension_object(val_el)
        elif ntag == "StatusCode":
            code_el = val_el.find("uax:Code", self.ns)
            val = code_el.text if code_el is not None else "0"
            obj.value = ua.StatusCode(string_to_val(val, ua.VariantType.UInt32))
        elif ntag == "QualifiedName":
            obj.value = self._parse_qualifed_name(val_el)
        elif ntag.startswith("ListOf"):
            # Default case for "ListOf" types.
            # Should stay after particular cases (e.g.: "ListOfLocalizedText").
            obj.value = []
            for val_el in val_el:
                tmp = NodeData()
                self._parse_value(val_el, tmp)
                obj.value.append(tmp.value)
        else:
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

    def _parse_qualifed_name(self, el):
        name = None
        ns = 0
        nval = el.find("uax:Name", self.ns)
        if nval is not None:
            name = nval.text
        nsval = el.find("uax:NamespaceIndex", self.ns)
        if nsval is not None:
            ns = string_to_val(nsval.text, ua.VariantType.UInt16)
        v = ua.QualifiedName(name, ns)
        self.logger.warning("qn: %s", v)
        return v

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
        if not obj.parent:
            self.logger.info("Could not find parent for node '%s'", obj.nodeid)

    @staticmethod
    def list_required_models(xmlpath, xmlstring):
        """
        Try getting required XML Models, before parsing NodeSet
        """
        if xmlpath:
            tree = ET.parse(xmlpath)
        else:
            tree = ET.fromstring(xmlstring)
        required_models = []

        for child in tree.iter():
            if child.tag.endswith("RequiredModel"):
                # check if ModelUri X, in Version Y from time Z was already imported
                required_models.append(child.attrib)
        return required_models

    def get_nodeset_namespaces(self) -> List[Tuple[str, ua.String, ua.DateTime]]:
        """
        Get all namespaces that are registered with version and date_time
        """
        ns = []
        for model in self.root.findall('base:Models/base:Model', self.ns):
            uri = model.attrib.get('ModelUri')
            if uri is not None:
                version = model.attrib.get('Version', '')
                date_time = model.attrib.get('PublicationDate')
                if date_time is None:
                    date_time = ua.DateTime(1, 1, 1)
                else:
                    date_time = ua.DateTime.strptime(date_time, "%Y-%m-%dT%H:%M:%SZ")
                ns.append((uri, version, date_time))
        return ns
