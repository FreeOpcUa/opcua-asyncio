from __future__ import annotations

import asyncio
import keyword
import logging
import re
import typing
from dataclasses import dataclass, field, make_dataclass
from enum import Enum, IntEnum, IntFlag
from typing import TYPE_CHECKING, Any, ClassVar

from asyncua import Node, ua
from asyncua.common.manage_nodes import create_data_type, create_encoding
from asyncua.ua.uaerrors import UaInvalidParameterError

if TYPE_CHECKING:
    from asyncua import Client, Server

_logger = logging.getLogger(__name__)


def new_struct_field(
    name: str,
    dtype: ua.NodeId | Node | ua.VariantType,
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
        field.ValueRank = ua.ValueRank.OneDimension
        field.ArrayDimensions = [1]  # type: ignore
    else:
        field.ValueRank = ua.ValueRank.Scalar
        field.ArrayDimensions = None
    return field


async def new_struct(
    server: Server | Client,
    idx: int | ua.NodeId,
    name: int | ua.QualifiedName,
    fields: list[ua.StructureField],
    is_union: bool = False,
) -> tuple[Node, list[Node]]:
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


def new_enum_field(
    name: str,
    description: str = "",
) -> ua.EnumField:
    """
    simple way to create an EnumField
    """
    field = ua.EnumField()
    field.DisplayName = ua.LocalizedText(Text=name)
    field.Name = name
    if description:
        field.Description = ua.LocalizedText(Text=description)
    else:
        field.Description = ua.LocalizedText(Text=name)
    return field


async def new_enum(
    server: Server | Client,
    idx: int | ua.NodeId,
    name: int | ua.QualifiedName,
    fields: list[str | ua.EnumField],
    option_set: bool = False,
) -> Node:
    edef = ua.EnumDefinition()
    counter = 0
    for item in fields:
        field = item if isinstance(item, ua.EnumField) else new_enum_field(item)
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
    but cannot be part of Python class names
    """
    if keyword.iskeyword(name):
        return name + "_"
    if name.isidentifier():
        return name
    newname = re.sub(r"\W+", "_", name)
    newname = re.sub(r"^[0-9]+", r"_\g<0>", newname)
    _logger.info("renamed %s to %s due to Python syntax", name, newname)
    return newname


def get_default_value(uatype, enums=None, hack=False, optional=False) -> str:
    if optional:
        return "None"

    if hasattr(ua, uatype):
        # That type is known, make sure this is not a subtype
        dtype = getattr(ua, uatype)
        uatype = dtype.__name__
    if enums is None:
        enums = {}
    if uatype == "String":
        return "ua.String()"
    if uatype == "Guid":
        return "uuid.uuid4()"
    if uatype in ("ByteString", "CharArray", "Char"):
        return "b''"
    if uatype == "Boolean":
        return "False"
    if uatype == "DateTime":
        return "datetime.now(timezone.utc)"
    if uatype in ("Int16", "Int32", "Int64", "UInt16", "UInt32", "UInt64", "Double", "Float", "Byte", "SByte"):
        return f"ua.{uatype}(0)"
    if uatype in enums:
        return f"ua.{uatype}({enums[uatype]})"
    if hasattr(ua, uatype) and issubclass(getattr(ua, uatype), Enum):
        # We have an enum, try to initialize it correctly
        val = list(getattr(ua, uatype).__members__)[0]
        return f"ua.{uatype}.{val}"
    if hack:
        # FIXME: This is horrible but necessary for old struc support
        return f"field(default_factory=lambda: ua.{uatype}())"
    return f"field(default_factory=ua.{uatype})"


def _make_union_property(name, idx):
    def getter(self):
        if getattr(self, "Encoding", 0) == idx:
            return getattr(self, "Value", None)
        return None

    def setter(self, value):
        self.Encoding = idx
        self.Value = value

    return property(getter, setter)


def make_structure(
    data_type: ua.NodeId, struct_name: str, sdef: ua.StructureDefinition, log_error: bool = True
) -> dict[str, type]:
    """
    given a StructureDefinition object, generate Python class
    """
    if sdef.StructureType not in (
        ua.StructureType.Structure,
        ua.StructureType.StructureWithOptionalFields,
        ua.StructureType.Union,
        ua.StructureType.StructureWithSubtypedValues,
    ):
        raise NotImplementedError(
            f"Only StructureType implemented, not {ua.StructureType(sdef.StructureType).name} for node {struct_name} with DataTypeDefinition {sdef}"
        )
    is_union = sdef.StructureType == ua.StructureType.Union
    bases = (ua.UaUnion,) if is_union else ()

    # Safe namespace for evaluating default values
    import uuid
    from datetime import datetime, timezone

    safe_eval_ns = {
        "ua": ua,
        "field": field,
        "uuid": uuid,
        "datetime": datetime,
        "timezone": timezone,
        "None": None,
    }

    fields = []
    union_field_names = []
    union_type_hints = []
    seen_names = set()
    if sdef.StructureType == ua.StructureType.StructureWithOptionalFields:
        fields.append(("Encoding", ua.UInt32, field(default=0, repr=False, init=True, compare=False)))
        seen_names.add("Encoding")

    for idx, sfield in enumerate(sdef.Fields, start=1):
        fname = clean_name(sfield.Name)
        seen_names.add(fname)
        if sfield.DataType.NamespaceIndex == 0 and sfield.DataType.Identifier in ua.ObjectIdNames:
            if sfield.DataType.Identifier == 24:
                uatype_name = "Variant"
            elif sfield.DataType.Identifier == 22:
                uatype_name = "ExtensionObject"
            else:
                uatype_name = ua.ObjectIdNames[sfield.DataType.Identifier]
        elif sfield.DataType in ua.extension_objects_by_datatype:
            uatype_name = ua.extension_objects_by_datatype[sfield.DataType].__name__
        elif sfield.DataType in ua.enums_by_datatype:
            uatype_name = ua.enums_by_datatype[sfield.DataType].__name__
        elif sfield.DataType in ua.basetype_by_datatype:
            uatype_name = ua.basetype_by_datatype[sfield.DataType]
        elif sfield.DataType == data_type:
            uatype_name = struct_name
        else:
            if log_error:
                _logger.error("Unknown datatype for field: %s in structure:%s, please report", sfield, struct_name)
            raise RuntimeError(f"Unknown datatype for field: {sfield} in structure:{struct_name}, please report")

        # Determine the actual type for the field as a string for type hinting
        if sfield.DataType == data_type:
            # handle recursive structure
            uatype = f"ua.{struct_name}"
        else:
            uatype = f"ua.{uatype_name}"

        if sfield.ValueRank >= 1 and uatype_name == "Char":
            uatype = "ua.String"

        if sfield.ValueRank >= 1 or sfield.ArrayDimensions:
            uatype = f"list[{uatype}]"

        prop_uatype = uatype
        if sfield.IsOptional or is_union:
            if sdef.StructureType is ua.StructureType.StructureWithSubtypedValues:
                prop_uatype = f"typing.Annotated[{uatype}, 'AllowSubtypes']"
            else:
                prop_uatype = f"typing.Optional[{uatype}]"

        # Determine default value as a string and eval it
        if is_union:
            # Union fields are handled by properties and Value field
            # We don't add them to 'fields' to avoid conflicts with properties in make_dataclass
            union_field_names.append((fname, idx, prop_uatype))
            union_type_hints.append(uatype)
            continue

        default_val_str = get_default_value(uatype_name, optional=sfield.IsOptional)
        if sfield.ValueRank >= 0 and not sfield.IsOptional:
            default_val = field(default_factory=list)
        else:
            try:
                # Update namespace with already registered classes in ua
                default_val = eval(default_val_str, safe_eval_ns)
            except Exception:
                # Fallback for complex defaults or if type not in namespace yet
                if "field" in default_val_str:
                    # It's already a field() call string, but we need the object
                    # This is rare here as we handle lists above
                    default_val = field(default_factory=list)
                else:
                    default_val = None

        fields.append((fname, uatype, default_val))

    namespace = {
        "ua": ua,
        "typing": typing,
        "field": field,
        "dataclass": dataclass,
    }

    if is_union:
        # For Union, we need Encoding and Value fields
        # 'Encoding' tracks which field is active, 'Value' holds the actual data
        fields.append(("Encoding", "ua.UInt32", field(default=0, init=True)))
        # Use a string representation for the Union type using typing.Union for max compatibility
        value_type = f"typing.Optional[typing.Union[{', '.join(union_type_hints)}]]"
        fields.append(("Value", value_type, field(default=None, init=True)))
        # Add properties for union fields
        for fname, idx, p_uatype in union_field_names:
            namespace[fname] = _make_union_property(fname, idx)

    # Use a namespace for make_dataclass to resolve ua, typing, etc.
    kwargs = {"bases": bases, "namespace": namespace}
    try:
        cls = make_dataclass(struct_name, fields, **kwargs)
    except Exception:
        _logger.warning(
            "Failed to create dataclass for struct %s with field %s and origin sdef: %s", struct_name, fields, sdef
        )
        return {}
        # breakpoint()
        # raise
    cls.__module__ = __name__
    cls.data_type = data_type  # type: ignore[attr-defined]
    cls.__doc__ = f"{struct_name} structure autogenerated from StructureDefinition object"

    # Register the class in the 'ua' module so forward references can be resolved by get_type_hints
    setattr(ua, struct_name, cls)

    if is_union:
        # Set _union_types for binary serialization/deserialization
        # We need actual type objects, not strings
        resolved_types = []
        for type_str in union_type_hints:
            try:
                if type_str.startswith("ua."):
                    resolved_types.append(getattr(ua, type_str[3:]))
                else:
                    resolved_types.append(eval(type_str, {"ua": ua, "typing": typing}))
            except Exception:
                _logger.warning("Failed to resolve union type hint: %s for %s", type_str, struct_name)
                resolved_types.append(type_str)
        cls._union_types = resolved_types  # type: ignore[attr-defined]

    return {struct_name: cls}


def _generate_object(
    name: str,
    sdef: ua.StructureDefinition,
    data_type: ua.NodeId | None = None,
    env: dict[str, Any] | None = None,
    enum: bool = False,
    option_set: bool = False,
    log_fail: bool = True,
) -> dict[str, Any]:
    """
    generate Python class
    return a dict of structures {name: class}
    """
    if env is None:
        env = {}
    if enum:
        env.update(make_enum(name, sdef, option_set))
    else:
        env.update(make_structure(data_type, name, sdef, log_error=log_fail))
    return env


class DataTypeSorter:
    dtype_index: ClassVar[dict[ua.NodeId, DataTypeSorter]] = {}
    referenced_dtypes: ClassVar[set[ua.NodeId]] = set()

    def __init__(self, data_type: ua.NodeId, name: str, desc: ua.ReferenceDescription, sdef: ua.StructureDefinition):
        self.data_type = data_type
        self.name = name
        self.desc = desc
        self.sdef = sdef
        self.encoding_id = self.sdef.DefaultEncodingId
        self.deps = [field.DataType for field in self.sdef.Fields]

        self.dtype_index[self.desc.NodeId] = self
        self.referenced_dtypes.update(self.deps)

    def depends_on(self, other: DataTypeSorter):
        if other.desc.NodeId in self.deps:
            return True
        for dep_nodeid in self.deps:
            if dep_nodeid not in self.dtype_index:
                continue
            dep = self.dtype_index[dep_nodeid]
            if dep != self and dep.depends_on(other):
                return True
        return False

    def __lt__(self, other: DataTypeSorter):
        return other.depends_on(self)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.desc.NodeId, self.deps, self.encoding_id})"

    def __str__(self):
        return f"<{self.__class__.__name__}: {self.name!r}>"


async def _recursive_parse(server, base_node, dtypes, parent_sdef=None, overwrite_existing=False):
    descs = await base_node.get_children_descriptions(refs=ua.ObjectIds.HasSubtype)
    nodes = []
    idxs = []
    for idx, desc in enumerate(descs):
        if desc.BrowseName.Name == "FilterOperand":
            continue
        if hasattr(ua, desc.BrowseName.Name) and not overwrite_existing:
            continue
        idxs.append(idx)
        nodes.append(server.get_node(desc.NodeId))

    if nodes:
        results = [dv.Value.Value for dv in await server.read_attributes(nodes, ua.AttributeIds.DataTypeDefinition)]
    else:
        results = []
    sdefs = [None for _ in descs]
    for i, sdef in zip(idxs, results):
        sdefs[i] = sdef

    requests = [
        __add_recursion(server, sdef, desc, parent_sdef, dtypes, overwrite_existing) for sdef, desc in zip(sdefs, descs)
    ]

    await asyncio.gather(*requests)


async def __add_recursion(server, sdef, desc, parent_sdef, dtypes, overwrite_existing) -> None:
    if isinstance(sdef, ua.StructureDefinition):
        name = clean_name(desc.BrowseName.Name)
        if parent_sdef:
            names = [f.Name for f in sdef.Fields]
            for sfield in reversed(parent_sdef.Fields):
                if sfield.Name not in names:
                    sdef.Fields.insert(0, sfield)
        dtypes.append(DataTypeSorter(desc.NodeId, name, desc, sdef))
        await _recursive_parse(
            server,
            server.get_node(desc.NodeId),
            dtypes,
            parent_sdef=sdef,
            overwrite_existing=overwrite_existing,
        )
    await _recursive_parse(
        server,
        server.get_node(desc.NodeId),
        dtypes,
        parent_sdef,
        overwrite_existing=overwrite_existing,
    )


async def _get_parent_types(node: Node) -> list[Node]:
    parents = []
    tmp_node = node
    for _ in range(10):
        refs = await tmp_node.get_references(refs=ua.ObjectIds.HasSubtype, direction=ua.BrowseDirection.Inverse)
        if not refs or (refs[0].NodeId.NamespaceIndex == 0 and refs[0].NodeId.Identifier == 22):
            return parents
        tmp_node = Node(tmp_node.session, refs[0].NodeId)
        parents.append(tmp_node)
    _logger.warning("Went 10 layers up while look of subtype of given node %s, something is wrong: %s", node, parents)
    return parents


async def load_custom_struct(node: Node) -> Any:
    sdef = await node.read_data_type_definition()
    if not isinstance(sdef, ua.StructureDefinition):
        raise UaInvalidParameterError(f"Expected StructureDefinition, got: {type(sdef)}")
    name = (await node.read_browse_name()).Name
    for parent in await _get_parent_types(node):
        parent_sdef = await parent.read_data_type_definition()
        if isinstance(parent_sdef, ua.StructureDefinition):
            names = [f.Name for f in sdef.Fields]
            for f in reversed(parent_sdef.Fields):
                if f.Name not in names:
                    sdef.Fields.insert(0, f)
    env = _generate_object(name, sdef, data_type=node.nodeid)
    struct = env[name]
    setattr(ua, name, struct)
    ua.register_extension_object(name, sdef.DefaultEncodingId, struct, node.nodeid)
    return struct


async def load_custom_struct_xml_import(node_id: ua.NodeId, attrs: ua.DataTypeAttributes) -> Any:
    """
    This function is used to load custom structs from xmlimporter
    """
    name = attrs.DisplayName.Text
    if hasattr(ua, name):
        return getattr(ua, name)
    # FIXME : mypy attribute not defined
    sdef = attrs.DataTypeDefinition  # type: ignore[attr-defined]
    env = _generate_object(name, sdef, data_type=node_id)
    struct = env[name]
    setattr(ua, name, struct)
    ua.register_extension_object(name, sdef.DefaultEncodingId, struct, node_id)
    return struct


async def _recursive_parse_basedatatypes(server, base_node, parent_datatype, new_alias) -> None:
    for desc in await base_node.get_children_descriptions(refs=ua.ObjectIds.HasSubtype):
        name = clean_name(desc.BrowseName.Name)
        if parent_datatype not in "Number":
            # Don't insert Number alias, they should be already insert because they have to be basetypes already
            if not hasattr(ua, name):
                env = make_basetype(name, parent_datatype)
                ua.register_basetype(name, desc.NodeId, env[name])
                new_alias[name] = env[name]
        await _recursive_parse_basedatatypes(server, server.get_node(desc.NodeId), name, new_alias)


async def load_basetype_alias_xml_import(server, name, nodeid, parent_datatype_nid) -> Any:
    """
    Insert alias for a datatype used for xml import
    """
    if hasattr(ua, name):
        return getattr(ua, name)
    parent = server.get_node(parent_datatype_nid)
    bname = await parent.read_browse_name()
    parent_datatype = clean_name(bname.Name)
    env = make_basetype(name, parent_datatype)
    ua.register_basetype(name, nodeid, env[name])
    return env[name]


def make_basetype(name: str, parent_datatype: str) -> dict[str, Any]:
    """
    alias basetypes
    """
    return {name: getattr(ua, parent_datatype)}


async def _load_base_datatypes(server: Server | Client) -> dict[str, Any]:
    new_alias = {}
    descriptions = await server.nodes.base_data_type.get_children_descriptions()
    for desc in descriptions:
        name = clean_name(desc.BrowseName.Name)
        if name not in ["Structure", "Enumeration"]:
            await _recursive_parse_basedatatypes(server, server.get_node(desc.NodeId), name, new_alias)
    return new_alias


async def load_data_type_definitions(server: Server | Client, base_node: Node = None, overwrite_existing=False) -> dict:
    """
    Read DataTypeDefinition attribute on all Structure and Enumeration defined
    on server and generate Python objects in ua namespace to be used to talk with server
    """
    new_objects = await _load_base_datatypes(server)  # we need to load all basedatatypes alias first
    new_objects.update(await load_enums(server))  # we need all enums to generate structure code
    new_objects.update(await load_enums(server, server.nodes.option_set_type, True))  # also load all optionsets
    if base_node is None:
        base_node = server.nodes.base_structure_type
    dtypes = []
    await _recursive_parse(server, base_node, dtypes, overwrite_existing=overwrite_existing)
    dtypes.sort()
    retries = 10
    for cnt in range(retries):
        # Retry to resolve datatypes
        failed_types = []
        log_ex = retries == cnt + 1
        for dts in dtypes:
            try:
                env = _generate_object(dts.name, dts.sdef, data_type=dts.data_type, log_fail=log_ex)
                cls = env[dts.name]
                cls.data_type = dts.data_type
                setattr(ua, dts.name, cls)
                ua.register_extension_object(dts.name, dts.encoding_id, cls, dts.data_type)
                new_objects[dts.name] = cls  # type: ignore
            except NotImplementedError:
                _logger.exception("Structure type %s not implemented", dts.sdef)
            except (AttributeError, RuntimeError):
                if log_ex:
                    _logger.exception("Failed to resolve datatype %s", dts.sdef)
                failed_types.append(dts)
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
    _logger.info("Registering data type %s %s", desc.NodeId, desc.BrowseName)
    node = server.get_node(desc.NodeId)
    try:
        sdef = await node.read_data_type_definition()
    except ua.uaerrors.BadAttributeIdInvalid:
        _logger.debug("%s has no DataTypeDefinition attribute", node)
        return None
    except Exception:
        _logger.exception("Error getting datatype for node %s", node)
        return None
    return sdef


def make_enum(name: str, edef: ua.EnumDefinition, option_set: bool) -> dict[str, type]:
    """
    if node has a DataTypeDefinition attribute, generate enum code
    """
    enum_type = IntEnum if not option_set else IntFlag
    members = {}
    if not edef or not hasattr(edef, "Fields") or not edef.Fields:
        # Some servers might have an empty definition or it's not an EnumDefinition
        _logger.error("Enum %s (NodeId: unknown): Failed to generate class from UA datatype", name)
        cls = typing.cast(Any, enum_type)(name, members)
        cls.__doc__ = f"{name} {'IntFlag' if option_set else 'IntEnum'} (empty) autogenerated"
        return {name: cls}
    for n, sfield in enumerate(edef.Fields):
        fieldname = clean_name(sfield.Name)
        if hasattr(sfield, "Value"):
            value = sfield.Value if not option_set else (1 << sfield.Value)
        else:
            # Some servers represent the datatype as StructureDefinition instead of EnumDefinition.
            # In this case the Value attribute is missing and we must guess.
            # XXX: Assuming that counting starts with 1 for enumerations, which is by no means guaranteed.
            value = n + 1 if not option_set else (1 << n)
            if n == 0:
                _logger.warning(
                    "%s type %s: guessing field values since the server does not provide them.",
                    "OptionSet" if option_set else "Enumeration",
                    name,
                )
        members[fieldname] = value
    cls = typing.cast(Any, enum_type)(name, members)
    cls.__doc__ = f"{name} {'IntFlag' if option_set else 'IntEnum'} autogenerated from EnumDefinition"
    return {name: cls}


async def load_enums(server: Server | Client, base_node: Node = None, option_set: bool = False) -> dict:
    typename = "OptionSet" if option_set else "Enum"
    if base_node is None:
        base_node = server.nodes.enum_data_type
    new_enums = {}
    for desc in await base_node.get_children_descriptions(refs=ua.ObjectIds.HasSubtype):
        name = clean_name(desc.BrowseName.Name)
        if hasattr(ua, name):
            continue
        _logger.info("Registering %s %s %s", typename, desc.NodeId, name)
        try:
            edef = await _read_data_type_definition(server, desc)
            if not edef:
                continue
            env = _generate_object(name, edef, enum=True, option_set=option_set, log_fail=False)
        except Exception:
            _logger.exception(
                "%s %s (NodeId: %s): Failed to generate class from UA datatype", typename, name, desc.NodeId
            )
            continue
        cls = env[name]
        setattr(ua, name, cls)
        ua.register_enum(name, desc.NodeId, cls)
        new_enums[name] = cls
    return new_enums


async def load_enum_xml_import(node_id: ua.NodeId, attrs: ua.DataTypeAttributes, option_set: bool):
    """
    This function is used to load enums from xmlimporter
    """
    name = attrs.DisplayName.Text
    if hasattr(ua, name):
        return getattr(ua, name)
    # FIXME: DateTypeDefinition is not a known attribute for mypy
    env = _generate_object(name, attrs.DataTypeDefinition, enum=True, option_set=option_set)  # type: ignore[attr-defined]
    cls = env[name]
    setattr(ua, name, cls)
    ua.register_enum(name, node_id, cls)
    return cls
