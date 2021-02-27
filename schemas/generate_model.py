"""
Generate address space code from xml file specification
"""
from copy import copy
from xml.etree import ElementTree
from logging import getLogger

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

# structs that end with Request or Response but are not
NotRequest = ["MonitoredItemCreateRequest", "MonitoredItemModifyRequest", "CallMethodRequest"]
OverrideTypes = {}


class Bit(object):
    def __init__(self, name=None, idx=None, container=None, length=1):
        self.name = name
        self.idx = idx
        self.container = container
        self.length = length

    def __str__(self):
        return f'(Bit: {self.name}, container:{self.container}, idx:{self.idx})'

    __repr__ = __str__


class Struct(object):
    def __init__(self):
        self.name = None
        self.basetype = None
        self.doc = ""
        self.fields = []
        self.bits = {}
        self.needconstructor = None
        self.needoverride = False
        self.children = []
        self.parents = []
        self.extensionobject = False  # used for struct which are not pure extension objects

    def get_field(self, name):
        for f in self.fields:
            if f.name == name:
                return f
        raise Exception(f'field not found: {name}')

    def __str__(self):
        return f'Struct {self.name}:{self.basetype}'

    __repr__ = __str__


class Field(object):
    def __init__(self, name=None, uatype=None, length=None, sourcetype=None,
                 switchfield=None, switchvalue=None, bitlength=1):
        self.name = name
        self.uatype = uatype
        self.length = length
        self.sourcetype = sourcetype
        self.switchfield = switchfield
        self.switchvalue = switchvalue
        self.bitlength = bitlength

    def __str__(self):
        return f'Field {self.name}({self.uatype})'

    __repr__ = __str__

    def is_native_type(self):
        if self.uatype in (
                'Char', 'SByte', 'Int16', 'Int32', 'Int64', 'UInt16', 'UInt32', 'UInt64', 'Boolean', 'Double',
                'Float', 'Byte', 'String', 'CharArray', 'ByteString', 'DateTime'):
            return True
        return False


class Enum(object):
    def __init__(self):
        self.name = None
        self.uatype = None
        self.values = []
        self.doc = ""

    def get_ctype(self):
        return f'uint{self.uatype}_t'


class EnumValue(object):
    def __init__(self):
        self.name = None
        self.value = None


class Model(object):
    def __init__(self):
        self.structs = []
        self.enums = []
        self.struct_list = []
        self.enum_list = []

    def get_struct(self, name):
        for struct in self.structs:
            if name == struct.name:
                return struct
        raise Exception("No struct named: " + str(name))

    def get_enum(self, name):
        for s in self.enums:
            if name == s.name:
                return s
        raise Exception("No enum named: " + str(name))


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
    types = IgnoredStructs + IgnoredEnums + [
        'Bit', 'Char', 'CharArray', 'Guid', 'SByte', 'Int16', 'Int32', 'Int64', 'UInt16', 'UInt32', 'UInt64',
        'DateTime', 'Boolean', 'Double', 'Float', 'ByteString', 'Byte', 'StatusCode', 'DiagnosticInfo', 'String',
        'AttributeID', "NodeId", "Variant"
    ] + [enum.name for enum in model.enums] + ['VariableAccessLevel']
    waiting_structs = {}
    newstructs = []
    for s in model.structs:
        s.waitingfor = []
        ok = True
        for f in s.fields:
            if f.uatype not in types:
                if f.uatype in waiting_structs:
                    waiting_structs[f.uatype].append(s)
                else:
                    waiting_structs[f.uatype] = [s]
                s.waitingfor.append(f.uatype)
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
            _logger.warning(f'{s} is waiting_structs for: {s.waitingfor}')
    #from IPython import embed
    #embed()
    model.structs = newstructs


def override_types(model):
    for struct in model.structs:
        for field in struct.fields:
            if field.name in OverrideTypes.keys():
                field.uatype = OverrideTypes[field.name]


def remove_duplicates(model):
    for struct in model.structs:
        fields = []
        names = []
        for field in struct.fields:
            if field.name not in names:
                names.append(field.name)
                fields.append(field)
        struct.fields = fields


def add_encoding_field(model):
    for struct in model.structs:
        newfields = []
        container = None
        idx = 0
        for field in struct.fields:
            if field.uatype in ('UInt6', 'NodeIdType'):
                container = field.name
                b = Bit(field.name, 0, container, 6)
                idx = b.length
                struct.bits[b.name] = b

            if field.uatype == 'Bit':
                if not container or idx > 7:
                    container = 'Encoding'
                    idx = 0
                    f = Field('Encoding', 'Byte', sourcetype=field.sourcetype)
                    newfields.append(f)

                b = Bit(field.name, idx, container, field.bitlength)
                idx += field.bitlength
                struct.bits[b.name] = b
            else:
                newfields.append(field)
        struct.fields = newfields


def remove_vector_length(model):
    for struct in model.structs:
        new = []
        for field in struct.fields:
            if not field.name.startswith('NoOf') and field.name != 'Length':
                new.append(field)
        struct.fields = new


def remove_body_length(model):
    for struct in model.structs:
        new = []
        for field in struct.fields:
            if not field.name == 'BodyLength':
                new.append(field)
        struct.fields = new


def remove_duplicate_types(model):
    for struct in model.structs:
        for field in struct.fields:
            if field.uatype == 'CharArray':
                field.uatype = 'String'


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
            field = Field()
            field.name = 'TypeId'
            field.uatype = 'NodeId'
            struct.fields.insert(0, field)

        if structtype and struct.name not in NoSplitStruct:
            paramstruct = Struct()
            if structtype == 'Request':
                basename = struct.name.replace('Request', '') + 'Parameters'
                paramstruct.name = basename
            else:
                basename = struct.name.replace('Response', '') + 'Result'
                paramstruct.name = basename
            paramstruct.fields = struct.fields[2:]
            paramstruct.bits = struct.bits

            struct.fields = struct.fields[:2]
            structs.append(paramstruct)

            typeid = Field()
            typeid.name = "Parameters"
            typeid.uatype = paramstruct.name
            struct.fields.append(typeid)
        structs.append(struct)
    model.structs = structs


class Parser(object):
    def __init__(self, path):
        self.path = path
        self.model = None

    def parse(self):
        _logger.debug("Parsing: ", self.path)
        self.model = Model()
        tree = ElementTree.parse(self.path)
        root = tree.getroot()
        self.add_extension_object()
        self.add_data_type_definition()
        for child in root:
            tag = child.tag[40:]
            if tag == 'StructuredType':
                struct = self.parse_struct(child)
                if struct.name != 'ExtensionObject':
                    self.model.structs.append(struct)
                    self.model.struct_list.append(struct.name)
            elif tag == 'EnumeratedType':
                enum = self.parse_enum(child)
                self.model.enums.append(enum)
                self.model.enum_list.append(enum.name)
            else:
                _logger.debug("Not implemented node type: " + tag + "\n")
        return self.model

    def add_extension_object(self):
        obj = Struct()
        obj.name = "ExtensionObject"
        obj.fields.extend([Field('TypeId', 'NodeId'),
                           Field('BinaryBody', 'Bit'),
                           Field('XmlBody', 'Bit'),
                           Field('Body', 'ByteString', switchfield='BinaryBody')])
        self.model.struct_list.append(obj.name)
        self.model.structs.append(obj)

    def add_data_type_definition(self):
        obj = Struct()
        obj.name = "DataTypeDefinition"
        self.model.struct_list.append(obj.name)
        self.model.structs.append(obj)

    def parse_struct(self, child):
        struct = Struct()
        for key, val in child.attrib.items():
            if key == 'Name':
                struct.name = val
            elif key == 'BaseType':
                if ':' in val:
                    prefix, val = val.split(':')
                struct.basetype = val
                tmp = struct
                while tmp.basetype:
                    struct.parents.append(tmp.basetype)
                    tmp = self.model.get_struct(tmp.basetype)
            else:
                _logger.warning(f'Error unknown key: {key}')
        for el in child:
            tag = el.tag[40:]
            if tag == 'Field':
                field = Field()
                for key, val in el.attrib.items():
                    if key == 'Name':
                        field.name = val
                    elif key == 'TypeName':
                        field.uatype = val.split(':')[1]
                    elif key == 'LengthField':
                        field.length = val
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
            elif tag == 'Documentation':
                struct.doc = el.text
            else:
                _logger.warning(f'Unknown tag: {tag}')

        return struct

    @staticmethod
    def parse_enum(child):
        enum = Enum()
        for k, v in child.items():
            if k == 'Name':
                enum.name = v
            elif k == 'LengthInBits':
                enum.uatype = f'UIntv{v}'
            else:
                _logger.warning(f'Unknown attr for enum: {k}')
        for el in child:
            tag = el.tag[40:]
            if tag == 'EnumeratedValue':
                ev = EnumValue()
                for k, v in el.attrib.items():
                    if k == 'Name':
                        ev.name = v
                    elif k == 'Value':
                        ev.value = v
                    else:
                        _logger.warning(f'Unknown field attrib: {k}')
                enum.values.append(ev)
            elif tag == 'Documentation':
                enum.doc = el.text
            else:
                _logger.warning(f'Unknown enum tag: {tag}')
        return enum


def add_basetype_members(model):
    for struct in model.structs:
        if not struct.basetype:
            continue
        emptystruct = False
        if len(struct.fields) == 0:
            emptystruct = True
        if struct.basetype in ('ExtensionObject',):
            struct.basetype = None
            continue
        base = model.get_struct(struct.basetype)
        for name, bit in base.bits.items():
            struct.bits[name] = bit
        for idx, field in enumerate(base.fields):
            field = copy(field)
            if field.name == 'Body' and not emptystruct:
                struct.extensionobject = True
                field.name = 'BodyLength'
                field.uatype = 'Int32'
                field.length = None
                field.switchfield = None
            if not field.sourcetype:
                field.sourcetype = base.name
            struct.fields.insert(idx, field)


def fix_names(model):
    for s in model.enums:
        for f in s.values:
            if f.name == 'None':
                f.name = 'None_'
