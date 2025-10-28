from enum import IntEnum
import re


from asyncua.ua.uatypes import NodeId, NodeIdType, RelativePath, RelativePathElement, QualifiedName
from asyncua.ua.uaerrors import UaInvalidParameterError
from asyncua.ua.object_ids import ObjectIds, ObjectIdNames


_NS_IDX_PATTERN = re.compile(r"([0-9]*):")
_REFERENCE_TYPE_PREFIX_CHARS = "/.<"
_REFERENCE_TYPE_SUFFIX_CHAR = ">"
_RESERVED_CHARS = "/.<>:#!&"


class RelativePathElementType(IntEnum):
    AnyHierarchical = 0
    AnyComponent = 1
    ForwardReference = 2
    InverseReference = 3


class RelativePathElementFormatter:
    _element_type: RelativePathElementType = RelativePathElementType.AnyHierarchical
    _include_subtypes: bool = True
    _target_name: QualifiedName | None = None
    _reference_type_name: QualifiedName | None = None

    def __init__(self, element: RelativePathElement | None = None):
        if element is not None:
            self._include_subtypes = element.IncludeSubtypes
            self._target_name = element.TargetName

            if not element.IsInverse and element.IncludeSubtypes:
                if element.ReferenceTypeId.Identifier == ObjectIds.HierarchicalReferences:
                    self._element_type = RelativePathElementType.AnyHierarchical
                elif element.ReferenceTypeId.Identifier == ObjectIds.Aggregates:
                    self._element_type = RelativePathElementType.AnyComponent
                else:
                    self._element_type = RelativePathElementType.ForwardReference
                    self._reference_type_name = _find_reference_type_name(element.ReferenceTypeId)
            else:
                if not element.IsInverse:
                    self._element_type = RelativePathElementType.ForwardReference
                else:
                    self._element_type = RelativePathElementType.InverseReference
                self._reference_type_name = _find_reference_type_name(element.ReferenceTypeId)

            if self._element_type is None:
                raise UaInvalidParameterError("RelativePathElementType is not specified.")

    @staticmethod
    def parse(string: str) -> tuple["RelativePathElementFormatter", str]:
        el = RelativePathElementFormatter()

        rest = string
        head = _peek(rest)
        if head == "/":
            el._element_type = RelativePathElementType.AnyHierarchical
            rest = rest[1:]
        elif head == ".":
            el._element_type = RelativePathElementType.AnyComponent
            rest = rest[1:]
        elif head == "<":
            el._element_type = RelativePathElementType.ForwardReference
            rest = rest[1:]
            if _peek(rest) == "#":
                el._include_subtypes = False
                rest = rest[1:]
            if _peek(rest) == "!":
                el._element_type = RelativePathElementType.InverseReference
                rest = rest[1:]
            el._reference_type_name, rest = RelativePathElementFormatter._parse_name(rest, True)
        else:
            el._element_type = RelativePathElementType.AnyHierarchical

        el._target_name, rest = RelativePathElementFormatter._parse_name(rest, False)

        return el, rest

    @staticmethod
    def _parse_name(string: str, is_reference: bool) -> tuple[QualifiedName | None, str]:
        rest = string

        # Extract namespace index if present.
        idx = 0
        m = _NS_IDX_PATTERN.match(rest)
        if m:
            idx_str = m.group(1)
            if idx_str:
                idx = int(idx_str)
            rest = rest[m.end() :]

        # Extract rest of name.
        name = []
        head: str = ""
        while len(rest) > 0:
            head = rest[0]

            if is_reference:
                if head == _REFERENCE_TYPE_SUFFIX_CHAR:
                    rest = rest[1:]
                    break
            elif head in _REFERENCE_TYPE_PREFIX_CHARS:
                break

            if head == "&":
                rest = rest[1:]
                if len(rest) > 0:
                    head = rest[0]
                    if head in _RESERVED_CHARS:
                        name.append(head)
                        rest = rest[1:]
                        continue
                    raise ValueError(f"Invalid escape sequence '&{head}' in browse path.")
                raise ValueError("Unexpected end after escape character '&'.")
            name.append(head)
            rest = rest[1:]

        if is_reference and head != ">":
            raise ValueError("Missing closing '>' for reference type name in browse path.")

        if len(name) == 0:
            if is_reference:
                raise ValueError("Reference type name is null in browse path.")
            if idx == 0:
                return None, rest

        return QualifiedName("".join(name), idx), rest

    def build(self) -> RelativePathElement:
        reference_type_id: NodeId | None = None
        is_inverse = False
        include_subtypes = self._include_subtypes
        target_name = self._target_name

        if self._element_type == RelativePathElementType.AnyHierarchical:
            reference_type_id = NodeId(ObjectIds.HierarchicalReferences)
        elif self._element_type == RelativePathElementType.AnyComponent:
            reference_type_id = NodeId(ObjectIds.Aggregates)
        elif self._element_type == RelativePathElementType.ForwardReference:
            reference_type_id = _find_reference_type(self._reference_type_name)
        elif self._element_type == RelativePathElementType.InverseReference:
            reference_type_id = _find_reference_type(self._reference_type_name)
            is_inverse = True

        if reference_type_id is None:
            raise ValueError(f"Could not convert BrowseName to a ReferenceTypeId: {self._reference_type_name}")

        return RelativePathElement(
            ReferenceTypeId=reference_type_id,
            IsInverse=is_inverse,
            IncludeSubtypes=include_subtypes,
            TargetName=target_name,
        )

    def to_string(self) -> str:
        path = []

        # Append the reference type component.
        if self._element_type == RelativePathElementType.AnyHierarchical:
            path.append("/")
        elif self._element_type == RelativePathElementType.AnyComponent:
            path.append(".")
        elif (
            self._element_type == RelativePathElementType.ForwardReference
            or self._element_type == RelativePathElementType.InverseReference
        ):
            if self._reference_type_name and self._reference_type_name.Name:
                path.append("<")
                if not self._include_subtypes:
                    path.append("#")
                if self._element_type == RelativePathElementType.InverseReference:
                    path.append("!")
                if self._reference_type_name.NamespaceIndex != 0:
                    path.append(f"{self._reference_type_name.NamespaceIndex}:")
                path.append(_encode_name(self._reference_type_name.Name))
                path.append(">")

        # Append the target browse name component.
        if self._target_name and self._target_name.Name:
            if self._target_name.NamespaceIndex != 0:
                path.append(f"{self._target_name.NamespaceIndex}:")
            path.append(_encode_name(self._target_name.Name))

        return "".join(path)


class RelativePathFormatter:
    """
    Implementation of OPC-UA Specification Part 4: Services - A.2 BNF of RelativePath.

    https://reference.opcfoundation.org/Core/Part4/v105/docs/A.2
    """

    _elements: list[RelativePathElementFormatter]

    def __init__(self, relative_path: RelativePath | None = None):
        self._elements = []
        if relative_path:
            self._elements = [RelativePathElementFormatter(el) for el in relative_path.Elements]

    @staticmethod
    def parse(string: str):
        formatter = RelativePathFormatter()

        if string:
            rest = string
            try:
                while len(rest) > 0:
                    el, rest = RelativePathElementFormatter.parse(rest)
                    formatter._elements.append(el)
            except Exception as e:
                raise ValueError(f"Cannot parse relative path: {string}") from e

        return formatter

    def build(self) -> RelativePath:
        return RelativePath(Elements=[el.build() for el in self._elements])

    def to_string(self) -> str:
        return "".join([el.to_string() for el in self._elements])


def _peek(string: str) -> str | None:
    return string[0] if len(string) > 0 else None


def _encode_name(name: str) -> str:
    return "".join([ch if ch not in _RESERVED_CHARS else f"&{ch}" for ch in name])


def _find_reference_type(reference_type_name: QualifiedName) -> NodeId:
    type_id = getattr(ObjectIds, reference_type_name.Name, None)
    if type_id is not None:
        return NodeId(Identifier=type_id, NamespaceIndex=0)
    raise ValueError("Non-standard ReferenceTypes are not supported.")


def _find_reference_type_name(reference_type_id: NodeId) -> QualifiedName:
    if reference_type_id.Identifier in ObjectIdNames.keys():
        id_type = reference_type_id.NodeIdType
        if id_type == NodeIdType.TwoByte or id_type == NodeIdType.FourByte or id_type == NodeIdType.Numeric:
            type_id: int = reference_type_id.Identifier
            return QualifiedName.from_string(ObjectIdNames[type_id])
        raise ValueError("Non-integer NodeIds are not supported.")
    raise ValueError("Non-standard ReferenceTypes are not supported.")
