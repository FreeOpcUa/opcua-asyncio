from __future__ import annotations

import asyncio
import keyword
import logging
import re
import typing
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field, make_dataclass
from datetime import datetime, timezone
from enum import Enum, IntEnum, IntFlag
from typing import TYPE_CHECKING, Any

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
    name: str | ua.QualifiedName,
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


def clean_name(name: str) -> str:
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


def get_default_value(
    uatype: str, enums: dict[str, Any] | None = None, hack: bool = False, optional: bool = False
) -> str:
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


def _make_union_property(name: str, idx: int) -> property:
    def getter(self: Any) -> Any:
        if getattr(self, "Encoding", 0) == idx:
            return getattr(self, "Value", None)
        return None

    def setter(self: Any, value: Any) -> None:
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
    safe_eval_ns = _SAFE_EVAL_NS

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
    cls = make_dataclass(struct_name, fields, slots=True, **kwargs)
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
    sdef: ua.StructureDefinition | ua.EnumDefinition,
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


# Module-level safe eval namespace, built once to avoid repeated imports and dict construction
_SAFE_EVAL_NS: dict[str, Any] = {
    "ua": ua,
    "field": field,
    "uuid": uuid,
    "datetime": datetime,
    "timezone": timezone,
    "None": None,
}


@dataclass
class DataTypeInfo:
    """Holds parsed metadata for a single structure DataType node."""

    data_type: ua.NodeId
    name: str
    desc: ua.ReferenceDescription
    sdef: ua.StructureDefinition
    encoding_id: ua.NodeId = field(init=False)
    deps: list[ua.NodeId] = field(init=False)

    def __post_init__(self) -> None:
        self.encoding_id = self.sdef.DefaultEncodingId
        self.deps = [f.DataType for f in self.sdef.Fields]


def _topological_sort_dtypes(dtypes: list[DataTypeInfo]) -> list[DataTypeInfo]:
    """Sort data types using Kahn's algorithm so dependencies come before dependents."""
    node_map: dict[ua.NodeId, DataTypeInfo] = {dt.desc.NodeId: dt for dt in dtypes}
    known_ids = node_map.keys()

    # Build adjacency list and in-degree counts (only for edges within our set)
    in_degree: dict[ua.NodeId, int] = {nid: 0 for nid in known_ids}
    dependents: dict[ua.NodeId, list[ua.NodeId]] = defaultdict(list)

    for dt in dtypes:
        for dep_nid in dt.deps:
            if dep_nid in known_ids and dep_nid != dt.desc.NodeId:
                in_degree[dt.desc.NodeId] += 1
                dependents[dep_nid].append(dt.desc.NodeId)

    queue = deque(nid for nid, deg in in_degree.items() if deg == 0)
    result: list[DataTypeInfo] = []

    while queue:
        nid = queue.popleft()
        result.append(node_map[nid])
        for dependent_nid in dependents[nid]:
            in_degree[dependent_nid] -= 1
            if in_degree[dependent_nid] == 0:
                queue.append(dependent_nid)

    # Anything remaining has circular dependencies - append at the end
    if len(result) < len(dtypes):
        seen = {dt.desc.NodeId for dt in result}
        for dt in dtypes:
            if dt.desc.NodeId not in seen:
                result.append(dt)
    return result


async def get_children_descriptions_type_definitions(
    server: Server | Client, base_node: Node, overwrite_existing: bool = False
) -> tuple[list[ua.ReferenceDescription], list[Any]]:
    descs = await base_node.get_children_descriptions(refs=ua.ObjectIds.HasSubtype)
    nodes = []
    idxs = []
    for idx, desc in enumerate(descs):
        if hasattr(ua, desc.BrowseName.Name) and not overwrite_existing:
            existing = getattr(ua, desc.BrowseName.Name)
            existing_dtype = getattr(existing, "data_type", None)
            # Skip only if the existing class is already bound to this exact
            # DataType node. Name-only checks can collide across companion specs.
            if isinstance(existing_dtype, ua.NodeId) and existing_dtype == desc.NodeId:
                continue
        idxs.append(idx)
        nodes.append(server.get_node(desc.NodeId))

    if nodes:
        results = [
            dv.Value.Value if dv.Value is not None else None
            for dv in await server.read_attributes(nodes, ua.AttributeIds.DataTypeDefinition)
        ]
    else:
        results = []
    sdefs = [None for _ in descs]
    for i, sdef in zip(idxs, results):
        sdefs[i] = sdef
    return descs, sdefs


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


async def _recursive_parse_basedatatypes(
    server: Server | Client, base_node: Node, parent_datatype: str, new_alias: dict[str, Any]
) -> None:
    descs = await base_node.get_children_descriptions(refs=ua.ObjectIds.HasSubtype)
    # Register all children at this level first (parent must exist before child)
    for desc in descs:
        name = clean_name(desc.BrowseName.Name)
        if parent_datatype not in "Number":
            # Don't insert Number alias, they should be already insert because they have to be basetypes already
            if not hasattr(ua, name):
                env = make_basetype(name, parent_datatype)
                ua.register_basetype(name, desc.NodeId, env[name])
                new_alias[name] = env[name]
    # Recurse into siblings in parallel (all parents already registered above)
    if descs:
        await asyncio.gather(
            *[
                _recursive_parse_basedatatypes(
                    server, server.get_node(desc.NodeId), clean_name(desc.BrowseName.Name), new_alias
                )
                for desc in descs
            ]
        )


async def load_basetype_alias_xml_import(
    server: Server | Client, name: str, nodeid: ua.NodeId, parent_datatype_nid: ua.NodeId
) -> Any:
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


class RecursiveParser:
    def __init__(self, server: Server | Client) -> None:
        self.server = server
        self._visited: set[ua.NodeId] = set()
        self._dtypes: list[DataTypeInfo] = []

    async def parse(self, base_node: Node, overwrite_existing: bool = False) -> list[DataTypeInfo]:
        await self._parse_node(
            node=base_node,
            parent_sdef=None,
            overwrite_existing=overwrite_existing,
        )
        return self._dtypes

    async def _parse_node(
        self, node: Node, parent_sdef: ua.StructureDefinition | None, overwrite_existing: bool
    ) -> None:
        if node.nodeid in self._visited:
            return

        self._visited.add(node.nodeid)

        descs, sdefs = await get_children_descriptions_type_definitions(
            self.server,
            node,
            overwrite_existing,
        )

        if len(descs) != len(sdefs):
            _logger.warning("Descriptions and type definitions length mismatch, some data type nodes will be ignored")

        await asyncio.gather(
            *[self._process_child(desc, sdef, parent_sdef, overwrite_existing) for desc, sdef in zip(descs, sdefs)]
        )

    async def _process_child(
        self,
        desc: ua.ReferenceDescription,
        sdef: ua.StructureDefinition | None,
        parent_sdef: ua.StructureDefinition | None,
        overwrite_existing: bool,
    ) -> None:
        next_parent = parent_sdef

        if isinstance(sdef, ua.StructureDefinition):
            name = clean_name(desc.BrowseName.Name)

            if parent_sdef:
                existing = {f.Name for f in sdef.Fields}
                inherited = [f for f in parent_sdef.Fields if f.Name not in existing]
                if inherited:
                    sdef.Fields = inherited + list(sdef.Fields)

            self._dtypes.append(DataTypeInfo(desc.NodeId, name, desc, sdef))
            next_parent = sdef

        child_node = self.server.get_node(desc.NodeId)

        await self._parse_node(
            node=child_node,
            parent_sdef=next_parent,
            overwrite_existing=overwrite_existing,
        )


async def load_data_type_definitions(
    server: Server | Client, base_node: Node | None = None, overwrite_existing: bool = False
) -> dict[str, type]:
    """
    Read DataTypeDefinition attribute on all Structure and Enumeration defined
    on server and generate Python objects in ua namespace to be used to talk with server
    """
    new_objects = await _load_base_datatypes(server)  # we need to load all basedatatypes alias first

    # Load enums and option sets in parallel - they are independent of each other
    enum_results, optionset_results = await asyncio.gather(
        load_enums(server),
        load_enums(server, server.nodes.option_set_type, True),
    )
    new_objects.update(enum_results)
    new_objects.update(optionset_results)

    if base_node is None:
        base_node = server.nodes.base_structure_type

    parser = RecursiveParser(server)
    dtypes = await parser.parse(base_node)

    # Topological sort: O(n+e) instead of comparison-based O(n^2 log n)
    dtypes = _topological_sort_dtypes(dtypes)

    retries = 3
    for cnt in range(retries):
        # Retry to resolve datatypes (only needed for circular deps / edge cases)
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


async def load_enums(
    server: Server | Client, base_node: Node | None = None, option_set: bool = False, overwrite_existing: bool = False
) -> dict[str, type]:
    typename = "OptionSet" if option_set else "Enum"
    if base_node is None:
        base_node = server.nodes.enum_data_type
    descs, sdefs = await get_children_descriptions_type_definitions(server, base_node, overwrite_existing)
    new_enums = {}
    for idx, desc in enumerate(descs):
        name = clean_name(desc.BrowseName.Name)
        if hasattr(ua, name):
            continue
        _logger.info("Registering %s %s %s", typename, desc.NodeId, name)
        edef = sdefs[idx]
        if not edef:
            continue
        try:
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


async def load_enum_xml_import(node_id: ua.NodeId, attrs: ua.DataTypeAttributes, option_set: bool) -> Any:
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
