from enum import Enum
from enum import IntEnum, IntFlag
from datetime import datetime
import uuid
import logging
import re
import keyword
from typing import Union, List, TYPE_CHECKING, Tuple, Optional, Any, Dict, Set
from dataclasses import dataclass, field

from asyncua import ua
from asyncua import Node
from asyncua.common.manage_nodes import create_encoding, create_data_type
if TYPE_CHECKING:
    from asyncua import Client, Server

logger = logging.getLogger(__name__)


def new_struct_field(
    name: str,
    dtype: Union[ua.NodeId, Node, ua.VariantType],
    array: bool = False,
    optional: bool = False,
    description: str = "",
) -> ua.StructureField:
    """
    simple way to create a StructureField
    """
    field = ua.StructureField()
    field.Name = name
    field.IsOptional = optional
    if description:
        field.Description = ua.LocalizedText(Text=description)
    else:
        field.Description = ua.LocalizedText(Text=name)
    if isinstance(dtype, ua.VariantType):
        field.DataType = ua.NodeId(dtype.value, 0)
    elif isinstance(dtype, ua.NodeId):
        field.DataType = dtype
    elif isinstance(dtype, Node):
        field.DataType = dtype.nodeid
    else:
        raise ValueError(f"DataType of a field must be a NodeId, not {dtype} of type {type(dtype)}")
    if array:
        field.ValueRank = ua.ValueRank.OneOrMoreDimensions
        field.ArrayDimensions = [1]  # type: ignore
    else:
        field.ValueRank = ua.ValueRank.Scalar
        field.ArrayDimensions = None
    return field


async def new_struct(
    server: Union["Server", "Client"],
    idx: Union[int, ua.NodeId],
    name: Union[int, ua.QualifiedName],
    fields: List[ua.StructureField],
    is_union: bool = False
) -> Tuple[Node, List[Node]]:
    """
    simple way to create a new structure
    return the created data type node and the list of encoding nodes
    """

    type_name = server.nodes.base_structure_type
    if is_union:
        type_name = server.nodes.base_union_type

    dtype = await create_data_type(type_name, idx, name)

    if isinstance(idx, ua.NodeId):
        # user has provided a node id, we cannot reuse it
        idx = idx.NamespaceIndex
    enc = await create_encoding(dtype, ua.NodeId(0, idx), ua.QualifiedName("Default Binary", 0))
    # TODO: add other encoding the day we support them

    sdef = ua.StructureDefinition()
    if is_union:
        sdef.StructureType = ua.StructureType.Union
        sdef.BaseDataType = server.nodes.base_union_type.nodeid
    else:
        sdef.BaseDataType = server.nodes.base_structure_type.nodeid
        sdef.StructureType = ua.StructureType.Structure
        for sfield in fields:
            if sfield.IsOptional:
                sdef.StructureType = ua.StructureType.StructureWithOptionalFields
                break
    sdef.Fields = fields
    sdef.DefaultEncodingId = enc.nodeid

    await dtype.write_data_type_definition(sdef)
    return dtype, [enc]


async def new_enum(
    server: Union["Server", "Client"],
    idx: Union[int, ua.NodeId],
    name: Union[int, ua.QualifiedName],
    values: List[str],
    option_set: bool = False
) -> Node:
    edef = ua.EnumDefinition()
    counter = 0
    for val_name in values:
        field = ua.EnumField()
        field.DisplayName = ua.LocalizedText(Text=val_name)
        field.Name = val_name
        field.Value = counter
        counter += 1
        edef.Fields.append(field)
    if option_set:
        dtype = await server.nodes.option_set_type.add_data_type(idx, name)
    else:
        dtype = await server.nodes.enum_data_type.add_data_type(idx, name)
    await dtype.write_data_type_definition(edef)
    return dtype


def clean_name(name):
    """
    Remove characters that might be present in  OPC UA structures
    but cannot be part of of Python class names
    """
    if keyword.iskeyword(name):
        return name + "_"
    if name.isidentifier():
        return name
    newname = re.sub(r'\W+', '_', name)
    newname = re.sub(r'^[0-9]+', r'_\g<0>', newname)
    logger.warning("renamed %s to %s due to Python syntax", name, newname)
    return newname


def get_default_value(uatype, enums=None):
    if hasattr(ua, uatype):
        # That type is know, make sure this is not a subtype
        dtype = getattr(ua, uatype)
        uatype = dtype.__name__
    if enums is None:
        enums = {}
    if uatype == "String":
        return "None"
    if uatype == "Guid":
        return "uuid.uuid4()"
    if uatype in ("ByteString", "CharArray", "Char"):
        return b''
    if uatype == "Boolean":
        return "True"
    if uatype == "DateTime":
        return "datetime.utcnow()"
    if uatype in ("Int16", "Int32", "Int64", "UInt16", "UInt32", "UInt64", "Double", "Float", "Byte", "SByte"):
        return 0
    if uatype in enums:
        return f"ua.{uatype}({enums[uatype]})"
    if hasattr(ua, uatype) and issubclass(getattr(ua, uatype), Enum):
        # We have an enum, try to initilize it correctly
        val = list(getattr(ua, uatype).__members__)[0]
        return f"ua.{uatype}.{val}"
    return f"ua.{uatype}()"


def make_structure_code(data_type, struct_name, sdef, log_error=True):
    """
    given a StructureDefinition object, generate Python code
    """
    if sdef.StructureType not in (ua.StructureType.Structure, ua.StructureType.StructureWithOptionalFields, ua.StructureType.Union):
        raise NotImplementedError(f"Only StructureType implemented, not {ua.StructureType(sdef.StructureType).name} for node {struct_name} with DataTypdeDefinition {sdef}")
    is_union = sdef.StructureType == ua.StructureType.Union
    base_class = "" if not is_union else "(ua.UaUnion)"
    code = f"""

@dataclass
class {struct_name}{base_class}:

    '''
    {struct_name} structure autogenerated from StructureDefinition object
    '''

    data_type = ua.NodeId.from_string('''{data_type.to_string()}''')

"""

    if sdef.StructureType == ua.StructureType.StructureWithOptionalFields:
        code += "    Encoding: ua.UInt32 = field(default=0, repr=False, init=False, compare=False)\n"
    elif is_union:
        code += "    Encoding: ua.UInt32 = field(default=0, repr=False, init=False, compare=False)\n"
    fields = []
    for sfield in sdef.Fields:
        fname = clean_name(sfield.Name)
        if sfield.DataType.NamespaceIndex == 0 and sfield.DataType.Identifier in ua.ObjectIdNames:
            if sfield.DataType.Identifier == 24:
                uatype = "Variant"
            elif sfield.DataType.Identifier == 22:
                uatype = "ExtensionObject"
            else:
                uatype = ua.ObjectIdNames[sfield.DataType.Identifier]
        elif sfield.DataType in ua.extension_objects_by_datatype:
            uatype = ua.extension_objects_by_datatype[sfield.DataType].__name__
        elif sfield.DataType in ua.enums_by_datatype:
            uatype = ua.enums_by_datatype[sfield.DataType].__name__
        elif sfield.DataType in ua.basetype_by_datatype:
            uatype = ua.basetype_by_datatype[sfield.DataType]
        elif sfield.DataType == data_type:
            uatype = struct_name
        else:
            if log_error:
                logger.error(f"Unknown datatype for field: {sfield} in structure:{struct_name}, please report")
            raise RuntimeError(f"Unknown datatype for field: {sfield} in structure:{struct_name}, please report")

        if sfield.ValueRank >= 0:
            default_value = "field(default_factory=list)"
        else:
            default_value = get_default_value(uatype)

        if sfield.DataType != data_type:
            uatype = f"ua.{uatype}"
        else:
            # when field point to itself datatype use forward reference for typing
            uatype = f"'ua.{uatype}'"
        if sfield.ValueRank >= 1 and uatype == 'Char':
            uatype = 'String'
        elif sfield.ValueRank >= 1 or sfield.ArrayDimensions:
            uatype = f"List[{uatype}]"
        elif sfield.IsOptional:
            uatype = f"Optional[{uatype}]"
        fields.append((fname, uatype, default_value))
    if is_union:
        # Generate getter and setter to mimic opc ua union access
        names = [f[1] for f in fields]
        code += "    _union_types = [" + ','.join(names) + "]\n"
        code += "    Value: Union[None, " + ','.join(names) + "] = field(default=None, init=False)"
        for enc_idx, fd in enumerate(fields):
            name, uatype, _ = fd
            code += f'''

    @property
    def {name}(self) -> Optional[{uatype}]:
        if self.Encoding == {enc_idx + 1}:
            return self.Value
        return None

    @{name}.setter
    def {name}(self, value: {uatype}) -> None:
        self.Value = value
        self.Encoding = {enc_idx + 1}

            '''
    else:
        for fname, uatype, default_value in fields:
            code += f"    {fname}: {uatype} = {default_value}\n"

    return code


async def _generate_object(name, sdef, data_type=None, env=None, enum=False, option_set=False, log_fail=True):
    """
    generate Python code and execute in a new environment
    return a dict of structures {name: class}
    Rmw: Since the code is generated on the fly, in case of error the stack trace is
    not available and debugging is very hard...
    """
    if env is None:
        env = {}
    #  Add the required libraries to dict
    if "ua" not in env:
        env['ua'] = ua
    if "datetime" not in env:
        env['datetime'] = datetime
    if "uuid" not in env:
        env['uuid'] = uuid
    if "enum" not in env:
        env['IntEnum'] = IntEnum
        env['IntFlag'] = IntFlag
    if "dataclass" not in env:
        env['dataclass'] = dataclass
    if "Optional" not in env:
        env['Optional'] = Optional
    if "List" not in env:
        env['List'] = List
    if "field" not in env:
        env['field'] = field
    if "Union" not in env:
        env['Union'] = Union
    # generate classe add it to env dict
    if enum:
        code = make_enum_code(name, sdef, option_set)
    else:
        code = make_structure_code(data_type, name, sdef, log_error=log_fail)
    logger.debug("Executing code: %s", code)
    try:
        exec(code, env)
    except Exception:
        if log_fail:
            logger.exception("Failed to execute auto-generated code from UA datatype: %s", code)
        raise
    return env


class DataTypeSorter:
    dtype_index: Dict[ua.NodeId, 'DataTypeSorter'] = {}
    referenced_dtypes: Set[ua.NodeId] = set()

    def __init__(self, data_type: ua.NodeId, name: str,
                 desc: ua.ReferenceDescription, sdef: ua.StructureDefinition):
        self.data_type = data_type
        self.name = name
        self.desc = desc
        self.sdef = sdef
        self.encoding_id = self.sdef.DefaultEncodingId
        self.deps = [field.DataType for field in self.sdef.Fields]

        self.dtype_index[self.desc.NodeId] = self
        self.referenced_dtypes.update(self.deps)

    def depends_on(self, other: 'DataTypeSorter'):
        if other.desc.NodeId in self.deps:
            return True
        for dep_nodeid in self.deps:
            if dep_nodeid not in self.dtype_index:
                continue
            dep = self.dtype_index[dep_nodeid]
            if dep != self and dep.depends_on(other):
                return True
        return False

    def __lt__(self, other: 'DataTypeSorter'):
        return other.depends_on(self)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.desc.NodeId, self.deps, self.encoding_id})"

    def __str__(self):
        return f"<{self.__class__.__name__}: {self.name!r}>"


async def _recursive_parse(server, base_node, dtypes, parent_sdef=None, add_existing=False):
    ch = await base_node.get_children_descriptions(refs=ua.ObjectIds.HasSubtype)
    for desc in ch:
        sdef = await _read_data_type_definition(server, desc, read_existing=add_existing)
        if sdef:
            name = clean_name(desc.BrowseName.Name)
            if parent_sdef:
                for sfield in reversed(parent_sdef.Fields):
                    sdef.Fields.insert(0, sfield)
            dtypes.append(DataTypeSorter(desc.NodeId, name, desc, sdef))
            await _recursive_parse(server, server.get_node(desc.NodeId), dtypes, parent_sdef=sdef, add_existing=add_existing)
        else:
            await _recursive_parse(server, server.get_node(desc.NodeId), dtypes, parent_sdef, add_existing=add_existing)


async def _get_parent_types(node: Node):
    parents = []
    tmp_node = node
    for _ in range(10):
        refs = await tmp_node.get_references(refs=ua.ObjectIds.HasSubtype, direction=ua.BrowseDirection.Inverse)
        if not refs or refs[0].NodeId.NamespaceIndex == 0 and refs[0].NodeId.Identifier == 22:
            return parents
        tmp_node = Node(tmp_node.server, refs[0])
        parents.append(tmp_node)
    logger.warning("Went 10 layers up while look of subtype of given node %s, something is wrong: %s", node, parents)


async def load_custom_struct(node: Node) -> Any:
    sdef = await node.read_data_type_definition()
    name = (await node.read_browse_name()).Name
    for parent in await _get_parent_types(node):
        parent_sdef = await parent.read_data_type_definition()
        for f in reversed(parent_sdef.fields):
            sdef.Fields.insert(0, f)
    env = await _generate_object(name, sdef, data_type=node.nodeid)
    struct = env[name]
    ua.register_extension_object(name, sdef.DefaultEncodingId, struct, node.nodeid)
    return env[name]


async def _recursive_parse_basedatatypes(server, base_node, parent_datatype, new_alias) -> Any:

    for desc in await base_node.get_children_descriptions(refs=ua.ObjectIds.HasSubtype):
        name = clean_name(desc.BrowseName.Name)
        if parent_datatype not in 'Number':
            # Don't insert Number alias, they should be allready insert because they have to be basetypes allready
            if not hasattr(ua, name):
                env = make_basetype_code(name, parent_datatype)
                ua.register_basetype(name, desc.NodeId, env[name])
                new_alias[name] = env[name]
        await _recursive_parse_basedatatypes(server, server.get_node(desc.NodeId), name, new_alias)


def make_basetype_code(name, parent_datatype):
    """
    alias basetypes
    """
    code = f"""
{name} = ua.{parent_datatype}
"""
    env = {}
    env['ua'] = ua
    logger.debug("Executing code: %s", code)
    print(code)
    try:
        exec(code, env)
    except Exception:
        logger.exception("Failed to execute auto-generated code from UA datatype: %s", code)
        raise
    return env


async def _load_base_datatypes(server: Union["Server", "Client"]) -> Any:
    new_alias = {}
    descriptions = await server.nodes.base_data_type.get_children_descriptions()
    for desc in descriptions:
        name = clean_name(desc.BrowseName.Name)
        if name not in ['Structure', 'Enumeration']:
            await _recursive_parse_basedatatypes(server, server.get_node(desc.NodeId), name, new_alias)
    return new_alias


async def load_data_type_definitions(server: Union["Server", "Client"], base_node: Node = None, overwrite_existing=False) -> Dict:
    """
    Read DataTypeDefition attribute on all Structure  and Enumeration  defined
    on server and generate Python objects in ua namespace to be used to talk with server
    """
    new_objects = await _load_base_datatypes(server)  # we need to load all basedatatypes alias first
    new_objects.update(await load_enums(server))  # we need all enums to generate structure code
    new_objects.update(await load_enums(server, server.nodes.option_set_type, True))  # also load all optionsets
    if base_node is None:
        base_node = server.nodes.base_structure_type
    dtypes = []
    await _recursive_parse(server, base_node, dtypes, add_existing=overwrite_existing)
    dtypes.sort()
    retries = 10
    for cnt in range(retries):
        # Retry to resolve datatypes
        failed_types = []
        log_ex = retries == cnt + 1
        for dts in dtypes:
            try:
                env = await _generate_object(dts.name, dts.sdef, data_type=dts.data_type, log_fail=log_ex)
                ua.register_extension_object(dts.name, dts.encoding_id, env[dts.name], dts.data_type)
                new_objects[dts.name] = env[dts.name]  # type: ignore
            except NotImplementedError:
                logger.exception("Structure type %s not implemented", dts.sdef)
            except AttributeError:
                # Failed to resolve datatypes
                failed_types.append(dts)
                if log_ex:
                    raise
            except RuntimeError:
                # Failed to resolve datatypes
                failed_types.append(dts)
                if log_ex:
                    raise
        if not failed_types:
            break
        dtypes = failed_types
    return new_objects


async def _read_data_type_definition(server, desc: ua.ReferenceDescription, read_existing: bool = False):
    if desc.BrowseName.Name == "FilterOperand":
        # FIXME: find out why that one is not in ua namespace...
        return None
    # FIXME: this is fishy, we may have same name in different Namespaces
    if not read_existing and hasattr(ua, desc.BrowseName.Name):
        return None
    logger.info("Registering data type %s %s", desc.NodeId, desc.BrowseName)
    node = server.get_node(desc.NodeId)
    try:
        sdef = await node.read_data_type_definition()
    except ua.uaerrors.BadAttributeIdInvalid:
        logger.debug("%s has no DataTypeDefinition attribute", node)
        return None
    except Exception:
        logger.exception("Error getting datatype for node %s", node)
        return None
    return sdef


def make_enum_code(name, edef, option_set):
    """
    if node has a DataTypeDefinition attribute, generate enum code
    """
    enum_type = "IntEnum" if not option_set else "IntFlag"
    code = f"""

class {name}({enum_type}):

    '''
    {name} EnumInt autogenerated from EnumDefinition
    '''

"""

    for sfield in edef.Fields:
        name = clean_name(sfield.Name)
        value = sfield.Value if not option_set else (1 << sfield.Value)
        code += f"    {name} = {value}\n"
    logger.error(f"{name} - {sfield} {option_set} {code}")
    return code


async def load_enums(server: Union["Server", "Client"], base_node: Node = None, option_set: bool = False) -> Dict:
    if base_node is None:
        base_node = server.nodes.enum_data_type
    new_enums = {}
    for desc in await base_node.get_children_descriptions(refs=ua.ObjectIds.HasSubtype):
        name = clean_name(desc.BrowseName.Name)
        if hasattr(ua, name):
            continue
        logger.info("Registring Enum %s %s OptionSet=%s", desc.NodeId, name, option_set)
        edef = await _read_data_type_definition(server, desc)
        if not edef:
            continue
        env = await _generate_object(name, edef, enum=True, option_set=option_set)
        ua.register_enum(name, desc.NodeId, env[name])
        new_enums[name] = env[name]
    return new_enums
