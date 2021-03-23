"""
Generate address space code from xml file specification
"""
from copy import copy
from xml.etree import ElementTree
from logging import getLogger
from dataclasses import dataclass, field
from typing import Any, List
import re
from pathlib import Path

from IPython import embed

_logger = getLogger(__name__)

IgnoredEnums = []
IgnoredStructs = []

# by default we split requests and respons in header and parameters, but some are so simple we do not split them
NoSplitStruct = ["GetEndpointsResponse", "CloseSessionRequest", "AddNodesResponse", "DeleteNodesResponse",
                 "BrowseResponse", "HistoryReadResponse", "HistoryUpdateResponse", "RegisterServerResponse",
                 "CloseSecureChannelRequest", "CloseSecureChannelResponse", "CloseSessionRequest",
                 "CloseSessionResponse", "UnregisterNodesResponse", "MonitoredItemModifyRequest",
                 "MonitoredItemsCreateRequest", "ReadResponse", "WriteResponse",
                 "TranslateBrowsePathsToNodeIdsResponse", "DeleteSubscriptionsResponse", "DeleteMonitoredItemsResponse",
                 "CreateMonitoredItemsResponse", "ServiceFault", "AddReferencesResponse",
                 "ModifyMonitoredItemsResponse", "RepublishResponse", "CallResponse", "FindServersResponse",
                 "RegisterServerRequest", "RegisterServer2Response"]

buildin_types = [
                'Char', 'SByte', 'Int16', 'Int32', 'Int64', 'UInt16', 'UInt32', 'UInt64', 'Boolean', 'Double',
                'Float', 'Byte', 'String', 'CharArray', 'ByteString', 'DateTime', "Guid"]

# structs that end with Request or Response but are not
NotRequest = ["MonitoredItemCreateRequest", "MonitoredItemModifyRequest", "CallMethodRequest"]
OverrideTypes = {}


@dataclass
class EnumField:
    name: str = None
    value: int = None


@dataclass
class Field:
    name: str = None
    data_type: str = "i=24"  #i=24 means anything
    value_rank: int = -1
    array_dimensions: List[int] = None
    max_string_length: int = None
    value: Any = None
    is_optional: bool = False
    allow_subtypes: bool = False
    is_nullable: bool = False

    def is_native_type(self):
        if self.uatype in buildin_types:
            return True
        return False

    def is_array(self):
        return self.value_rank != -1 or self.array_dimensions


@dataclass
class Struct:
    name: str = None
    basetype: str = None
    node_id: str = None
    doc: str = ""
    fields: List[Field] = field(default_factory=list)
    has_optional: bool = False
    needoverride = False
    children: List[Any] = field(default_factory=list)
    parents: List[Any] = field(default_factory=list)
    do_not_register: bool = False  # we splt some structs, they must not be registered as extension objects

    def __hash__(self):
        return hash(self.name)

    def get_field(self, name):
        for f in self.fields:
            if f.name == name:
                return f
        raise Exception(f'field not found: {name}')


@dataclass
class Enum:
    name: str = None
    data_type: str = None
    fields: List[Field] = field(default_factory=list)
    doc: str = ""


@dataclass
class Alias:
    name: str
    data_type: str
    real_type: str


class Model:
    def __init__(self):
        self.structs = []
        self.enums = []
        self.struct_list = []
        self.enum_list = []
        self.known_structs = []
        self.aliases = {}

    def get_struct(self, name):
        for struct in self.structs:
            if name == struct.name:
                return struct
        raise Exception("No struct named: " + name)

    def get_struct_by_nodeid(self, nodeid):
        for struct in self.structs:
            if nodeid == struct.node_id:
                return struct
        raise Exception("No struct with node id: " + nodeid)

    def get_enum(self, name):
        for s in self.enums:
            if name == s.name:
                return s
        raise Exception("No enum named: " + str(name))

    def get_alias(self, name):
        for alias in self.aliases.values():
            if alias.name == name:
                return alias
        return None


def _add_struct(struct, newstructs, waiting_structs, known_structs):
    newstructs.append(struct)
    known_structs.append(struct.name)
    # now seeing if some struct where waiting for this one
    waitings = waiting_structs.pop(struct.name, None)
    if waitings:
        for s in waitings:
            s.waitingfor.remove(struct.name)
            if not s.waitingfor:
                _add_struct(s, newstructs, waiting_structs, known_structs)


def reorder_structs(model):
    types = IgnoredStructs + IgnoredEnums + buildin_types + [
        'StatusCode', 'DiagnosticInfo', "ExtensionObject", "QualifiedName", "ResponseHeader", "RequestHeader",
        'AttributeID', "ExpandedNodeId", "NodeId", "Variant", "DataValue", "LocalizedText",
    ] + [enum.name for enum in model.enums] + ['VariableAccessLevel'] + [alias.name for alias in model.aliases.values()]
    waiting_structs = {}
    newstructs = []
    for s in model.structs:
        s.waitingfor = []
        ok = True
        for f in s.fields:
            if f.data_type not in types:
                if f.data_type in waiting_structs:
                    waiting_structs[f.data_type].append(s)
                else:
                    waiting_structs[f.data_type] = [s]
                s.waitingfor.append(f.data_type)
                ok = False
        if ok:
            _add_struct(s, newstructs, waiting_structs, types)
    if len(model.structs) != len(newstructs):
        _logger.warning(f'Error while reordering structs, some structs could not be reinserted,'
                        f' had {len(model.structs)} structs, we now have {len(newstructs)} structs')
        s1 = set(model.structs)
        s2 = set(newstructs)
        _logger.debug('Variant' in types)
        for s in s1 - s2:
            _logger.warning(f'{s.name} is waiting_structs for: {s.waitingfor}')
    model.structs = newstructs


def nodeid_to_names(model):
    ids = {}
    with open(Path.cwd() / "UA-Nodeset-master" / "Schema" / "NodeIds.csv") as f:
        for line in f:
            name, nb, datatype = line.split(",")
            ids[nb] = name
    ids["24"] = "Variant"
    ids["22"] = "ExtensionObject"

    for struct in model.structs:
        for sfield in struct.fields:
            if sfield.data_type.startswith("i="):
                sfield.data_type = ids[sfield.data_type[2:]]
    for alias in model.aliases.values():
        alias.data_type = ids[alias.data_type[2:]]
        alias.real_type = ids[alias.real_type[2:]]


def override_types(model):
    for struct in model.structs:
        for sfield in struct.fields:
            if sfield.name in OverrideTypes.keys():
                sfield.uatype = OverrideTypes[sfield.name]


def remove_duplicates(model):
    for struct in model.structs:
        fields = []
        names = []
        for sfield in struct.fields:
            if sfield.name not in names:
                names.append(sfield.name)
                fields.append(sfield)
        struct.fields = fields


def remove_duplicate_types(model):
    for struct in model.structs:
        for sfield in struct.fields:
            if sfield.uatype == 'CharArray':
                sfield.uatype = 'String'


# def remove_extensionobject_fields(model):
# for obj in model.structs:
# if obj.name.endswith("Request") or obj.name.endswith("Response"):
# obj.fields = [el for el in obj.fields if el.name not in ("TypeId", "Body", "Encoding")]

def split_requests(model):
    structs = []
    for struct in model.structs:
        structtype = None
        if struct.name.endswith('Request') and struct.name not in NotRequest:
            structtype = 'Request'
        elif struct.name.endswith('Response') or struct.name == 'ServiceFault':
            structtype = 'Response'
        if structtype:
            struct.needconstructor = True
            field = Field(name="TypeId", data_type="NodeId")
            struct.fields.insert(0, field)

        if structtype and struct.name not in NoSplitStruct:
            paramstruct = Struct(do_not_register=True)
            if structtype == 'Request':
                basename = struct.name.replace('Request', '') + 'Parameters'
                paramstruct.name = basename
            else:
                basename = struct.name.replace('Response', '') + 'Result'
                paramstruct.name = basename
            paramstruct.fields = struct.fields[2:]

            struct.fields = struct.fields[:2]
            structs.append(paramstruct)

            typeid = Field(name="Parameters", data_type=paramstruct.name)
            struct.fields.append(typeid)
        structs.append(struct)
    model.structs = structs


class Parser(object):
    def __init__(self, path):
        self.path = path
        self.model = None
        self._tag_re = re.compile(r"\{.*\}(.*)")

    def parse(self):
        _logger.debug("Parsing: ", self.path)
        self.model = Model()
        tree = ElementTree.parse(self.path)
        root = tree.getroot()
        for child in root.findall("{*}UADataType"):
            self._add_data_type(child)

        return self.model

    def _add_data_type(self, el):
        name = el.get("BrowseName")

        for ref in el.findall("./{*}References/{*}Reference"):
            if ref.get("ReferenceType") == "HasSubtype" and ref.get("IsForward", "true") == "false":
                if ref.text == "i=29":
                    enum = self.parse_enum(name, el)
                    self.model.enums.append(enum)
                    self.model.enum_list.append(enum.name)
                    return
                elif ref.text in ("i=7", "i=3", "i=5", "i=9"):
                    #looks like some enums are defined there too
                    enum = self.parse_enum(name, el)
                    if not enum.fields:
                        alias = Alias(name, el.get("NodeId"), ref.text)
                        self.model.aliases[alias.data_type] = alias
                        return
                    self.model.enums.append(enum)
                    self.model.enum_list.append(enum.name)
                    return

                elif ref.text == "i=22" or ref.text in self.model.known_structs:
                    struct = self.parse_struct(name, el)
                    if ref.text in self.model.known_structs:
                        parent = self.model.get_struct_by_nodeid(ref.text)
                        for sfield in reversed(parent.fields):
                            struct.fields.insert(0, sfield)
                    self.model.structs.append(struct)
                    self.model.known_structs.append(struct.node_id)
                    self.model.struct_list.append(struct.name)
                    return
                elif 0 < int(ref.text[2:]) < 21:
                    alias = Alias(name, el.get("NodeId"), ref.text)
                    self.model.aliases[alias.data_type] = alias
                    return
                elif ref.text in self.model.aliases:
                    alias = Alias(name, el.get("NodeId"), self.model.aliases[ref.text].real_type)
                    self.model.aliases[alias.data_type] = alias
                    return
                elif ref.text in ("i=24"):
                    return
                print(name, "is of unknown type", ref.text)
                if name == "Boolean":
                    embed()

    def parse_struct(self, name, el):
        doc_el = el.find("{*}Documentation")
        if doc_el is not None:
            doc = doc_el.text
        else:
            doc = ""
        struct = Struct(
                name=name,
                doc=doc,
                node_id=el.get("NodeId"),
                )
        for sfield in el.findall("./{*}Definition/{*}Field"):
            opt = sfield.get("IsOptional", "false"),
            is_optional = True if opt == "true" else False
            f = Field(
                    name=sfield.get("Name"),
                    data_type=sfield.get("DataType", "i=24"),
                    value_rank=sfield.get("ValueRank", -1),
                    array_dimensions=sfield.get("ArayDimensions"),
                    value=sfield.get("Value"),
                    is_optional=is_optional,
                    )
            if is_optional:
                struct.has_optional = True
            struct.fields.append(f)
        return struct

    def _add_fields(self, struct, parent):
        for el in parent:
            tag = self._tag_re.match(el.tag).groups()[0]
            if tag == 'element':
                field = Field()
                for key, val in el.attrib.items():
                    if key == 'name':
                        field.name = val
                    elif key == 'type':
                        if val.startswith("ListOf"):
                            field.uatype = val.split(':')[1][6:]
                            field.length = "This is a length"
                        else:
                            field.uatype = val.split(':')[1]
                    elif key == 'SourceType':
                        field.sourcetype = val
                    elif key == 'SwitchField':
                        field.switchfield = val
                    elif key == 'SwitchValue':
                        field.switchvalue = val
                    elif key == 'Length':
                        field.bitlength = int(val)
                    else:
                        _logger.warning(f'Unknown field item: {struct.name} {key}')

                struct.fields.append(field)

    @staticmethod
    def parse_enum(name, el):
        doc_el = el.find("{*}Documentation")
        if doc_el is not None:
            doc = doc_el.text
        else:
            doc = ""
        enum = Enum(name=name,
                data_type = el.get("NodeId"),
                doc = doc,
                )
        for field in el.findall("./{*}Definition/{*}Field"):
            efield = EnumField(name=field.get("Name"), value=int(field.get("Value")))
            enum.fields.append(efield)
        return enum


def fix_names(model):
    for s in model.enums:
        for f in s.fields:
            if f.name == 'None':
                f.name = 'None_'
    for s in model.structs:
        if s.name[0] == "3":
            s.name = "Three" + s.name[1:]
            for f in s.fields:
                if f.data_type[0] == "3":
                    f.data_type = "Three" + s.name[1:]
        # Next code mght be better but the only case is the "3" above and
        # at many places the structs are call Three instead of 3 so the
        # code over ie better for now

        #if s.name[0].isdigit():
            #s.name = "_" + s.name
            #for f in s.fields:
                #if f.data_type[0].isdigit():
                    #f.data_type = "_" + s.name


if __name__ == "__main__":
    BASE_DIR = Path.cwd()
    xml_path = BASE_DIR / 'UA-Nodeset-master' / 'Schema' / 'Opc.Ua.NodeSet2.Services.xml'
    p = Parser(xml_path)
    model = p.parse()
    nodeid_to_names(model)
    split_requests(model)
    fix_names(model)
    reorder_structs(model)
    model.structs[0]
    embed()
