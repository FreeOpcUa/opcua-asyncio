"""
implement ua datatypes
"""

import sys
from typing import Optional, Any, Union, Generic, List
import collections
import logging
from enum import Enum, IntEnum
import uuid
import re
import itertools
from datetime import datetime, timedelta, MAXYEAR, timezone
from dataclasses import dataclass, field

# hack to support python < 3.8
if sys.version_info.minor < 10:
    def get_origin(tp):
        if hasattr(tp, "__origin__"):
            return tp.__origin__
        if tp is Generic:
            return Generic
        return None

    def get_args(tp):
        if hasattr(tp, "__args__"):
            res = tp.__args__
            if get_origin(tp) is collections.abc.Callable and res[0] is not Ellipsis:
                res = (list(res[:-1]), res[-1])
            return res
        return ()
else:
    from typing import get_origin, get_args  # type: ignore


from asyncua.ua import status_codes
from .uaerrors import UaError, UaStatusCodeError, UaStringParsingError


_logger = logging.getLogger(__name__)

EPOCH_AS_FILETIME = 116444736000000000  # January 1, 1970 as MS file time
HUNDREDS_OF_NANOSECONDS = 10000000
FILETIME_EPOCH_AS_DATETIME = datetime(1601, 1, 1)
FILETIME_EPOCH_AS_UTC_DATETIME = FILETIME_EPOCH_AS_DATETIME.replace(tzinfo=timezone.utc)
MAX_FILETIME_EPOCH_DATETIME = datetime(9999, 12, 31, 23, 59, 59)
MAX_FILETIME_EPOCH_AS_UTC_DATETIME = MAX_FILETIME_EPOCH_DATETIME.replace(tzinfo=timezone.utc)
MAX_OPC_FILETIME = int((MAX_FILETIME_EPOCH_DATETIME - FILETIME_EPOCH_AS_DATETIME).total_seconds()) * HUNDREDS_OF_NANOSECONDS
MAX_INT64 = 2 ** 63 - 1


def type_is_union(uatype):
    return get_origin(uatype) == Union


def type_is_list(uatype):
    return get_origin(uatype) == list

def type_allow_subclass(uatype):
    return get_origin(uatype) not in [Union, list, None]


def types_or_list_from_union(uatype):
    # returns the type of a union or the list of type if a list is inside the union
    types = []
    for subtype in get_args(uatype):
        if hasattr(subtype, '_paramspec_tvars'):
            # @hack how to check if a parameter is a list:
            # check if have _paramspec_tvars works for type[X]
            return True, subtype
        elif hasattr(subtype, '_name'):
            # @hack how to check if parameter is union or list
            # if _name is not List, it is Union
            if subtype._name == 'List':
                return True, subtype
        elif not isinstance(None, subtype):
            types.append(subtype)
    if not types:
        raise ValueError(f"Union {uatype} does not seem to contain a valid type")
    return False, types[0]


def types_from_union(uatype, origin=None):
    if origin is None:
        origin = get_origin(uatype)
    if origin != Union:
        raise ValueError(f"{uatype} is not an Union")
    # need to find out what real type is
    types = list(filter(lambda subtype: not isinstance(None, subtype), get_args(uatype)))
    if not types:
        raise ValueError(f"Union {uatype} does not seem to contain a valid type")
    return types


def type_from_list(uatype):
    return get_args(uatype)[0]


def type_from_optional(uatype):
    return get_args(uatype)[0]


def type_from_allow_subtype(uatype):
    return get_args(uatype)[0]


def type_string_from_type(uatype):
    if type_is_union(uatype):
        uatype = types_from_union(uatype)[0]
    elif type_is_list(uatype):
        uatype = type_from_list(uatype)
    elif type_allow_subclass(uatype):
        uatype = type_from_allow_subtype(uatype)
    return uatype.__name__


@dataclass
class UaUnion:
    ''' class to identify unions '''
    pass


class SByte(int):
    pass


class Byte(int):
    pass


class Bytes(bytes):
    pass


class ByteString(bytes):  # what is the difference between Bytes and ByteString??
    pass


class Int16(int):
    pass


class Int32(int):
    pass


class Int64(int):
    pass


class UInt16(int):
    pass


class UInt32(int):
    pass


class UInt64(int):
    pass


class Boolean:  # Boolean(bool) is not supported in Python
    pass


class Double(float):
    pass


class Float(float):
    pass


class Null:  # Null(NoneType) is not supported in Python
    pass


class String(str):
    pass


class CharArray(str):
    pass


class DateTime(datetime):
    pass


class Guid(uuid.UUID):
    pass


_microsecond = timedelta(microseconds=1)


def datetime_to_win_epoch(dt: datetime):
    if dt.tzinfo is None:
        ref = FILETIME_EPOCH_AS_DATETIME
        max_ep = MAX_FILETIME_EPOCH_DATETIME
    else:
        ref = FILETIME_EPOCH_AS_UTC_DATETIME
        max_ep = MAX_FILETIME_EPOCH_AS_UTC_DATETIME
    # Python datetime starts from year 1, opc ua only support dates starting 1601-01-01 12:00AM UTC
    # So we need to trunc the value to zero
    if ref >= dt:
        return 0
    # A date/time is encoded as the maximum value for an Int64 if either
    # The value is equal to or greater than 9999-12-31 11:59:59PM UTC,
    if dt >= max_ep:
        return MAX_INT64
    return 10 * ((dt - ref) // _microsecond)


def get_win_epoch():
    return win_epoch_to_datetime(0)


def win_epoch_to_datetime(epch):
    if epch >= MAX_OPC_FILETIME:
        # FILETIMEs after 31 Dec 9999 are truncated to max value
        return MAX_FILETIME_EPOCH_DATETIME
    if epch < 0:
        return FILETIME_EPOCH_AS_DATETIME
    return FILETIME_EPOCH_AS_DATETIME + timedelta(microseconds=epch // 10)


FROZEN: bool = False


class ValueRank(IntEnum):
    """
    Defines dimensions of a variable.
    This enum does not support all cases since ValueRank support any n>0
    but since it is an IntEnum it can be replaced by a normal int
    """

    ScalarOrOneDimension = -3
    Any = -2
    Scalar = -1
    OneOrMoreDimensions = 0
    OneDimension = 1
    # the next names are not in spec but so common we express them here
    TwoDimensions = 2
    ThreeDimensions = 3
    FourDimensions = 4


class _MaskEnum(IntEnum):
    @classmethod
    def parse_bitfield(cls, the_int):
        """ Take an integer and interpret it as a set of enum values. """
        if not isinstance(the_int, int):
            raise ValueError(
                f"Argument should be an int, we received {the_int} fo type {type(the_int)}"
            )
        return {cls(b) for b in cls._bits(the_int)}

    @classmethod
    def to_bitfield(cls, collection):
        """ Takes some enum values and creates an integer from them. """
        # make sure all elements are of the correct type (use itertools.tee in case we get passed an
        # iterator)
        iter1, iter2 = itertools.tee(iter(collection))
        if not all(isinstance(x, cls) for x in iter1):
            raise TypeError(f"All elements have to be of type {cls}")
        return sum(x.mask for x in iter2)

    @property
    def mask(self):
        return 1 << self.value

    @staticmethod
    def _bits(n):
        """Iterate over the bits in n.

        e.g. bits(44) yields at 2, 3, 5
        """
        if not n >= 0:  # avoid infinite recursion
            raise ValueError()
        pos = 0
        while n:
            if n & 0x1:
                yield pos
            n //= 2
            pos += 1


class AccessLevel(_MaskEnum):
    """
    Bit index to indicate what the access level is.

    Spec Part 3, appears multiple times, e.g. paragraph 5.6.2 Variable NodeClass
    """

    CurrentRead = 0
    CurrentWrite = 1
    HistoryRead = 2
    HistoryWrite = 3
    SemanticChange = 4
    StatusWrite = 5
    TimestampWrite = 6


class WriteMask(_MaskEnum):
    """
    Bit index to indicate which attribute of a node is writable

    Spec Part 3, Paragraph 5.2.7 WriteMask
    """

    AccessLevel = 0
    ArrayDimensions = 1
    BrowseName = 2
    ContainsNoLoops = 3
    DataType = 4
    Description = 5
    DisplayName = 6
    EventNotifier = 7
    Executable = 8
    Historizing = 9
    InverseName = 10
    IsAbstract = 11
    MinimumSamplingInterval = 12
    NodeClass = 13
    NodeId = 14
    Symmetric = 15
    UserAccessLevel = 16
    UserExecutable = 17
    UserWriteMask = 18
    ValueRank = 19
    WriteMask = 20
    ValueForVariableType = 21


class EventNotifier(_MaskEnum):
    """
    Bit index to indicate how a node can be used for events.

    Spec Part 3, appears multiple times, e.g. Paragraph 5.4 View NodeClass
    """

    SubscribeToEvents = 0
    # Reserved        = 1
    HistoryRead = 2
    HistoryWrite = 3


@dataclass(frozen=True)
class StatusCode:
    """
    :ivar value:
    :vartype value: int
    :ivar name:
    :vartype name: string
    :ivar doc:
    :vartype doc: string
    """

    value: UInt32 = status_codes.StatusCodes.Good

    def __post_init__(self):
        if isinstance(self.value, str):
            object.__setattr__(self, "value", getattr(status_codes.StatusCodes, self.value))

    def check(self):
        """
        Raises an exception if the status code is anything else than 0 (good).
        """
        if not self.is_good():
            raise UaStatusCodeError(self.value)

    def is_good(self):
        """
        return True if status is Good (00).
        """
        mask = 3 << 30
        if mask & self.value == 0x00000000:
            return True
        return False

    def is_bad(self):
        """
        https://reference.opcfoundation.org/v104/Core/docs/Part4/7.34.1/
        11   Reserved for future use. All Clients should treat a StatusCode with this severity as “Bad”.

        return True if status is Bad (10) or (11).
        """
        mask = 3 << 30
        if mask & self.value in (0x80000000, 0xc0000000):
            return True
        return False

    def is_uncertain(self):
        """
        return True if status is Uncertain (01).
        """
        mask = 3 << 30
        if mask & self.value == 0x40000000:
            return True
        return False

    @property
    def name(self):
        name, _ = status_codes.get_name_and_doc(self.value)
        return name

    @property
    def doc(self):
        _, doc = status_codes.get_name_and_doc(self.value)
        return doc


class NodeIdType(IntEnum):
    TwoByte = 0
    FourByte = 1
    Numeric = 2
    String = 3
    Guid = 4
    ByteString = 5


_NodeIdType = NodeIdType  # ugly hack


@dataclass(frozen=True, eq=False, order=False)
class NodeId:
    """
    NodeId Object

    Args:
        identifier: The identifier might be an int, a string, bytes or a Guid
        namespaceidx(int): The index of the namespace
        nodeidtype(NodeIdType): The type of the nodeid if it cannot be guessed, or you want something
        special like twobyte nodeid or fourbytenodeid


    :ivar Identifier:
    :vartype Identifier: NodeId
    :ivar NamespaceIndex:
    :vartype NamespaceIndex: Int
    :ivar NamespaceUri:
    :vartype NamespaceUri: String
    :ivar ServerIndex:
    :vartype ServerIndex: Int
    """

    Identifier: Union[Int32, String, Guid, ByteString] = 0
    NamespaceIndex: Int16 = 0
    NodeIdType: _NodeIdType = None

    def __post_init__(self):
        if self.NodeIdType is None:
            if isinstance(self.Identifier, int):
                if self.Identifier < 255 and self.NamespaceIndex == 0:
                    object.__setattr__(self, "NodeIdType", NodeIdType.TwoByte)
                elif self.Identifier < 2 ** 16 and self.NamespaceIndex < 255:
                    object.__setattr__(self, "NodeIdType", NodeIdType.FourByte)
                else:
                    object.__setattr__(self, "NodeIdType", NodeIdType.Numeric)
            elif isinstance(self.Identifier, str):
                object.__setattr__(self, "NodeIdType", NodeIdType.String)
            elif isinstance(self.Identifier, bytes):
                object.__setattr__(self, "NodeIdType", NodeIdType.ByteString)
            elif isinstance(self.Identifier, uuid.UUID):
                object.__setattr__(self, "NodeIdType", NodeIdType.Guid)
            else:
                raise UaError("NodeId: Could not guess type of NodeId, set NodeIdType")
        else:
            self.check_identifier_type_compatibility()

    def check_identifier_type_compatibility(self):
        """
        Check whether the given identifier can be interpreted as the given node identifier type.
        """
        valid_type_combinations = [
            (int, [NodeIdType.Numeric, NodeIdType.TwoByte, NodeIdType.FourByte]),
            (str, [NodeIdType.String, NodeIdType.ByteString]),
            (bytes, [NodeIdType.ByteString, NodeIdType.TwoByte, NodeIdType.FourByte]),
            (uuid.UUID, [NodeIdType.Guid]),
        ]
        for identifier, valid_node_types in valid_type_combinations:
            if isinstance(self.Identifier, identifier) and self.NodeIdType in valid_node_types:
                return
        raise UaError(
            f"NodeId of type {self.NodeIdType.name} has an incompatible identifier {self.Identifier} of type {type(self.Identifier)}"
        )

    def __eq__(self, node):
        return isinstance(node, NodeId) and self.NamespaceIndex == node.NamespaceIndex and self.Identifier == node.Identifier

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.NamespaceIndex, self.Identifier))

    def __lt__(self, other):
        if not isinstance(other, NodeId):
            raise AttributeError("Can only compare to NodeId")
        return (self.NodeIdType, self.NamespaceIndex, self.Identifier) < (other.NodeIdType, other.NamespaceIndex, other.Identifier)

    def is_null(self):
        if self.NamespaceIndex != 0:
            return False
        return self.has_null_identifier()

    def has_null_identifier(self):
        if not self.Identifier:
            return True
        if self.NodeIdType is NodeIdType.Guid and self.Identifier.int == 0:
            return True
        return False

    @staticmethod
    def from_string(string):
        try:
            return NodeId._from_string(string)
        except ValueError as ex:
            raise UaStringParsingError(f"Error parsing string {string}", ex) from ex

    @staticmethod
    def _from_string(string):
        elements = string.split(";")
        identifier = None
        namespace = 0
        ntype = None
        srv = None
        nsu = None
        for el in elements:
            if not el:
                continue
            k, v = el.split("=", 1)
            k = k.strip()
            v = v.strip()
            if k == "ns":
                namespace = int(v)
            elif k == "i":
                ntype = NodeIdType.Numeric
                identifier = int(v)
            elif k == "s":
                ntype = NodeIdType.String
                identifier = v
            elif k == "g":
                ntype = NodeIdType.Guid
                identifier = uuid.UUID(f"urn:uuid:{v}")
            elif k == "b":
                ntype = NodeIdType.ByteString
                if v[0:2] == '0x':
                    identifier = bytes.fromhex(v[2:])
                else:
                    identifier = v.encode()
            elif k == "srv":
                srv = int(v)
            elif k == "nsu":
                nsu = v
        if identifier is None:
            raise UaStringParsingError(f"Could not find identifier in string: {string}")
        if nsu is not None or srv is not None:
            return ExpandedNodeId(identifier, namespace, ntype, NamespaceUri=nsu, ServerIndex=srv)
        return NodeId(identifier, namespace, ntype)

    def to_string(self):
        string = []
        if self.NamespaceIndex != 0:
            string.append(f"ns={self.NamespaceIndex}")
        identifier = self.Identifier
        ntype = None
        if self.NodeIdType == NodeIdType.Numeric:
            ntype = "i"
        elif self.NodeIdType == NodeIdType.String:
            ntype = "s"
        elif self.NodeIdType == NodeIdType.TwoByte:
            ntype = "i"
        elif self.NodeIdType == NodeIdType.FourByte:
            ntype = "i"
        elif self.NodeIdType == NodeIdType.Guid:
            ntype = "g"
        elif self.NodeIdType == NodeIdType.ByteString:
            ntype = "b"
            identifier = '0x' + identifier.hex()
        string.append(f"{ntype}={identifier}")
        return ";".join(string)

    def to_binary(self):
        import asyncua

        return asyncua.ua.ua_binary.nodeid_to_binary(self)


@dataclass(frozen=True, eq=False, order=False)
class TwoByteNodeId(NodeId):
    def __post_init__(self):
        object.__setattr__(self, "NodeIdType", NodeIdType.TwoByte)
        if not isinstance(self.Identifier, int):
            raise ValueError(f"{self.__class__.__name__} Identifier must be int")
        if self.Identifier > 255:
            raise ValueError(f"{self.__class__.__name__} cannot have identifier > 255")
        if self.NamespaceIndex != 0:
            raise ValueError(f"{self.__class__.__name__}  cannot have NamespaceIndex != 0")


@dataclass(frozen=True, eq=False, order=False)
class FourByteNodeId(NodeId):
    def __post_init__(self):
        object.__setattr__(self, "NodeIdType", NodeIdType.FourByte)
        if not isinstance(self.Identifier, int):
            raise ValueError(f"{self.__class__.__name__} Identifier must be int")
        if self.Identifier > 65535:
            raise ValueError(f"{self.__class__.__name__} cannot have identifier > 65535")
        if self.NamespaceIndex > 255:
            raise ValueError(f"{self.__class__.__name__} cannot have NamespaceIndex != 0")


@dataclass(frozen=True, eq=False, order=False)
class NumericNodeId(NodeId):
    def __post_init__(self):
        object.__setattr__(self, "NodeIdType", NodeIdType.Numeric)
        if not isinstance(self.Identifier, int):
            raise ValueError(f"{self.__class__.__name__} Identifier must be int")


@dataclass(frozen=True, eq=False, order=False)
class ByteStringNodeId(NodeId):
    def __post_init__(self):
        object.__setattr__(self, "NodeIdType", NodeIdType.ByteString)
        if not isinstance(self.Identifier, bytes):
            raise ValueError(f"{self.__class__.__name__} Identifier must be bytes")


@dataclass(frozen=True, eq=False, order=False)
class GuidNodeId(NodeId):
    def __post_init__(self):
        object.__setattr__(self, "NodeIdType", NodeIdType.Guid)
        if not isinstance(self.Identifier, uuid.UUID):
            raise ValueError(f"{self.__class__.__name__} Identifier must be uuid")


@dataclass(frozen=True, eq=False, order=False)
class StringNodeId(NodeId):
    def __post_init__(self):
        object.__setattr__(self, "NodeIdType", NodeIdType.String)
        if not isinstance(self.Identifier, str):
            raise ValueError(f"{self.__class__.__name__} Identifier must be string")


@dataclass(frozen=True, eq=False, order=False)
class ExpandedNodeId(NodeId):
    NamespaceUri: Optional[String] = field(default=None, compare=True)
    ServerIndex: Int32 = field(default=0, compare=True)

    def to_string(self):
        string = NodeId.to_string(self)
        string = [string]
        if self.ServerIndex:
            string.append(f"srv={self.ServerIndex}")
        if self.NamespaceUri:
            string.append(f"nsu={self.NamespaceUri}")
        return ";".join(string)


@dataclass(frozen=True, init=False, order=True)
class QualifiedName:
    """
    A string qualified with a namespace index.
    """

    NamespaceIndex: UInt16 = 0
    Name: String = ""

    def __init__(self, Name=None, NamespaceIndex=0):
        object.__setattr__(self, "Name", Name)
        object.__setattr__(self, "NamespaceIndex", NamespaceIndex)
        if isinstance(self.NamespaceIndex, str) and isinstance(self.Name, int):
            # originally the order or argument was inversed, try to support it
            _logger.warning("QualifiedName are str, int, while int, str is expected, switching")

        if not isinstance(self.NamespaceIndex, int) or not isinstance(self.Name, (str, type(None))):
            raise ValueError(f"QualifiedName constructor args have wrong types, {self}")

    def to_string(self):
        return f"{self.NamespaceIndex}:{self.Name}"

    @staticmethod
    def from_string(string):
        if ":" in string:
            try:
                idx, name = string.split(":", 1)
                idx = int(idx)
            except (TypeError, ValueError) as ex:
                raise UaStringParsingError(f"Error parsing string {string}", ex) from ex
        else:
            idx = 0
            name = string
        return QualifiedName(Name=name, NamespaceIndex=idx)


@dataclass(frozen=True, init=False)
class LocalizedText:
    """
    A string qualified with a namespace index.
    """

    Encoding: Byte = field(default=0, repr=False, init=False, compare=False)
    Locale: Optional[String] = None
    Text: Optional[String] = None

    def __init__(self, Text=None, Locale=None):
        # need to write init method since args ar inverted in original implementation
        object.__setattr__(self, "Text", Text)
        object.__setattr__(self, "Locale", Locale)

        if self.Text is not None:
            if not isinstance(self.Text, str):
                raise ValueError(
                    f'A LocalizedText object takes a string as argument "text"'
                    f"not a {type(self.Text)}, {self.Text}"
                )

        if self.Locale is not None:
            if not isinstance(self.Locale, str):
                raise ValueError(
                    f'A LocalizedText object takes a string as argument "locale",'
                    f" not a {type(self.Locale)}, {self.Locale}"
                )

    def to_string(self):
        return self.__str__()

    @staticmethod
    def from_string(string):
        m = re.match(r"^LocalizedText\(Locale='(.*)', Text='(.*)'\)$", string)
        if m:
            text = m.group(2) if m.group(2) != str(None) else None
            locale = m.group(1) if m.group(1) != str(None) else None
            return LocalizedText(Text=text, Locale=locale)
        return LocalizedText(string)


@dataclass(frozen=True)
class ExtensionObject:
    """
    Any UA object packed as an ExtensionObject

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar Body:
    :vartype Body: bytes
    """

    TypeId: NodeId = NodeId()
    Encoding: Byte = field(default=0, repr=False, init=False, compare=False)
    Body: Optional[ByteString] = None

    def __bool__(self):
        return self.Body is not None


class VariantType(Enum):
    """
    The possible types of a variant.

    :ivar Null:
    :ivar Boolean:
    :ivar SByte:
    :ivar Byte:
    :ivar Int16:
    :ivar UInt16:
    :ivar Int32:
    :ivar UInt32:
    :ivar Int64:
    :ivar UInt64:
    :ivar Float:
    :ivar Double:
    :ivar String:
    :ivar DateTime:
    :ivar Guid:
    :ivar ByteString:
    :ivar XmlElement:
    :ivar NodeId:
    :ivar ExpandedNodeId:
    :ivar StatusCode:
    :ivar QualifiedName:
    :ivar LocalizedText:
    :ivar ExtensionObject:
    :ivar DataValue:
    :ivar Variant:
    :ivar DiagnosticInfo:
    """

    Null = 0
    Boolean = 1
    SByte = 2
    Byte = 3
    Int16 = 4
    UInt16 = 5
    Int32 = 6
    UInt32 = 7
    Int64 = 8
    UInt64 = 9
    Float = 10
    Double = 11
    String = 12
    DateTime = 13
    Guid = 14
    ByteString = 15
    XmlElement = 16
    NodeId = 17
    ExpandedNodeId = 18
    StatusCode = 19
    QualifiedName = 20
    LocalizedText = 21
    ExtensionObject = 22
    DataValue = 23
    Variant = 24
    DiagnosticInfo = 25


class VariantTypeCustom:
    """
    Looks like sometime we get variant with other values than those
    defined in VariantType.
    FIXME: We should not need this class, as far as I understand the spec
    variants can only be of VariantType
    """

    def __init__(self, val):
        self.name = "Custom"
        self.value = val
        if self.value > 0b00111111:
            raise UaError(
                f"Cannot create VariantType. VariantType must be {0b111111} > x > {25}, received {val}"
            )

    def __str__(self):
        return f"VariantType.Custom:{self.value}"

    __repr__ = __str__

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.value == other.value

    def __hash__(self) -> int:
        return self.value.__hash__()


@dataclass(frozen=True)
class Variant:
    """
    Create an OPC-UA Variant object.
    if no argument a Null Variant is created.
    if not variant type is given, attempts to guess type from python type
    if a variant is given as value, the new objects becomes a copy of the argument

    :ivar Value:
    :vartype Value: Any supported type
    :ivar VariantType:
    :vartype VariantType: VariantType
    :ivar Dimension:
    :vartype Dimensions: The length of each dimension. Make the variant a Matrix
    :ivar is_array:
    :vartype is_array: If the variant is an array. Always True if Dimension is specified
    """

    # FIXME: typing is wrong here
    Value: Any = None
    VariantType: VariantType = None
    Dimensions: Optional[List[Int32]] = None
    is_array: Optional[bool] = None

    def __post_init__(self):

        if self.is_array is None:
            if isinstance(self.Value, (list, tuple)) or self.Dimensions :
                object.__setattr__(self, "is_array", True)
            else:
                object.__setattr__(self, "is_array", False)

        if isinstance(self.Value, Variant):
            object.__setattr__(self, "VariantType", self.Value.VariantType)
            object.__setattr__(self, "Value", self.Value.Value)

        if not isinstance(self.VariantType, (VariantType, VariantTypeCustom)):
            if self.VariantType is None:
                object.__setattr__(self, "VariantType", self._guess_type(self.Value))
            else:
                if hasattr(VariantType, self.VariantType.__name__):
                    object.__setattr__(self, "VariantType", VariantType[self.VariantType.__name__])
                else:
                    raise ValueError("VariantType argument must be an instance of VariantType")

        if self.Value is None and not self.is_array:
            # only some types of Variants can be NULL when not in an array
            if self.VariantType == VariantType.NodeId:
                # why do we rewrite this case and not the others?
                object.__setattr__(self, "Value", NodeId(0, 0))
            elif self.VariantType not in (
                    VariantType.Null,
                    VariantType.String,
                    VariantType.DateTime,
                    VariantType.ExtensionObject,
            ):
                raise UaError(
                    f"Non array Variant of type {self.VariantType} cannot have value None"
                )

        if self.Dimensions is None and isinstance(self.Value, (list, tuple)):
            dims = get_shape(self.Value)
            if len(dims) > 1:
                object.__setattr__(self, "Dimensions", dims)

    def __eq__(self, other):
        if (
            isinstance(other, Variant)
            and self.VariantType == other.VariantType
            and self.Value == other.Value
        ):
            return True
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def _guess_type(self, val):
        error_val = None
        if isinstance(val, (list, tuple)):
            error_val = val
        while isinstance(val, (list, tuple)):
            if len(val) == 0:
                raise UaError(f"could not guess UA type of variable {error_val}")
            val = val[0]
        # now check if this is one our buildin types
        type_name = type(val).__name__
        if hasattr(VariantType, type_name):
            return VariantType[type_name]
        # nope so guess the type
        if val is None:
            return VariantType.Null
        if isinstance(val, bool):
            return VariantType.Boolean
        if isinstance(val, float):
            return VariantType.Double
        if isinstance(val, IntEnum):
            return VariantType.Int32
        if isinstance(val, int):
            return VariantType.Int64
        if isinstance(val, str):
            return VariantType.String
        if isinstance(val, bytes):
            return VariantType.ByteString
        if isinstance(val, datetime):
            return VariantType.DateTime
        if isinstance(val, uuid.UUID):
            return VariantType.Guid
        if isinstance(val, object):
            try:
                return getattr(VariantType, val.__class__.__name__)
            except AttributeError:
                return VariantType.ExtensionObject
        raise UaError(
            f"Could not guess UA type of {val} with type {type(val)}, specify UA type"
        )


def flatten_and_get_shape(mylist):
    dims = [len(mylist)]
    while isinstance(mylist[0], (list, tuple)):
        dims.append(len(mylist[0]))
        mylist = [item for sublist in mylist for item in sublist]
        if len(mylist) == 0:
            break
    return mylist, dims


def flatten(mylist):
    if mylist is None:
        return None
    if len(mylist) == 0:
        return mylist
    while isinstance(mylist[0], (list, tuple)):
        mylist = [item for sublist in mylist for item in sublist]
        if len(mylist) == 0:
            break
    return mylist


def get_shape(mylist):
    dims = []
    while isinstance(mylist, (list, tuple)):
        dims.append(len(mylist))
        if len(mylist) == 0:
            break
        mylist = mylist[0]
    return dims


# For completeness, these datatypes are abstract!
# If they are used in structs, abstract types are either Variant or ExtensionObjects.
# If they only contain basic types (int16, float, double..) they are Variants
UInteger = Variant
Integer = Variant


@dataclass(frozen=True)
class DataValue:
    """
    A value with an associated timestamp, and quality.
    Automatically generated from xml , copied and modified here to fix errors in xml spec

    :ivar Value:
    :vartype Value: Variant
    :ivar StatusCode:
    :vartype StatusCode: StatusCode
    :ivar SourceTimestamp:
    :vartype SourceTimestamp: datetime
    :ivar SourcePicoSeconds:
    :vartype SourcePicoSeconds: int
    :ivar ServerTimestamp:
    :vartype ServerTimestamp: datetime
    :ivar ServerPicoseconds:
    :vartype ServerPicoseconds: int
    """

    data_type = NodeId(25)

    Encoding: Byte = field(default=0, repr=False, init=False, compare=False)
    Value: Optional[Variant] = None
    StatusCode_: Optional[StatusCode] = field(default_factory=StatusCode)
    SourceTimestamp: Optional[DateTime] = None # FIXME type DateType raises type hinting errors because datetime is assigned
    ServerTimestamp: Optional[DateTime] = None
    SourcePicoseconds: Optional[UInt16] = None
    ServerPicoseconds: Optional[UInt16] = None

    def __post_init__(
        self,
    ):
        if not isinstance(self.Value, Variant):
            object.__setattr__(self, "Value", Variant(self.Value))

    @property
    def StatusCode(self):
        return self.StatusCode_


@dataclass(frozen=True)
class DiagnosticInfo:
    """
    A recursive structure containing diagnostic information associated with a status code.

    :ivar Encoding:
    :vartype Encoding: Byte
    :ivar SymbolicId:
    :vartype SymbolicId: Int32
    :ivar NamespaceURI:
    :vartype NamespaceURI: Int32
    :ivar Locale:
    :vartype Locale: Int32
    :ivar LocalizedText:
    :vartype LocalizedText: Int32
    :vartype LocalizedText: Int32
    :ivar AdditionalInfo:
    :vartype AdditionalInfo: String
    :ivar InnerStatusCode:
    :vartype InnerStatusCode: StatusCode
    :ivar InnerDiagnosticInfo:
    :vartype InnerDiagnosticInfo: DiagnosticInfo
    """

    data_type = NodeId(25)

    Encoding: Byte = field(default=0, repr=False, init=False, compare=False)
    SymbolicId: Optional[Int32] = None
    NamespaceURI: Optional[Int32] = None
    Locale: Optional[Int32] = None
    LocalizedText: Optional[Int32] = None
    AdditionalInfo: Optional[String] = None
    InnerStatusCode: Optional[StatusCode] = None
    InnerDiagnosticInfo: Optional[ExtensionObject] = None


def datatype_to_varianttype(int_type):
    """
    Takes a NodeId or int and return a VariantType
    This is only supported if int_type < 63 due to VariantType encoding
    At low level we do not have access to address space thus decoding is limited
    a better version of this method can be find in ua_utils.py
    """
    if isinstance(int_type, NodeId):
        int_type = int_type.Identifier

    if int_type <= 25:
        return VariantType(int_type)
    return VariantTypeCustom(int_type)


def get_default_value(vtype):
    """
    Given a variant type return default value for this type
    """
    if vtype == VariantType.Null:
        return None
    if vtype == VariantType.Boolean:
        return False
    if vtype in (VariantType.SByte, VariantType.Byte):
        return 0
    if vtype == VariantType.ByteString:
        return b""
    if 4 <= vtype.value <= 9:
        return 0
    if vtype in (VariantType.Float, VariantType.Double):
        return 0.0
    if vtype == VariantType.String:
        return None  # a string can be null
    if vtype == VariantType.DateTime:
        return datetime.utcnow()
    if vtype == VariantType.Guid:
        return uuid.uuid4()
    if vtype == VariantType.XmlElement:
        return None  # Not sure if this is correct
    if vtype == VariantType.NodeId:
        return NodeId()
    if vtype == VariantType.ExpandedNodeId:
        return ExpandedNodeId()
    if vtype == VariantType.StatusCode:
        return StatusCode()
    if vtype == VariantType.QualifiedName:
        return QualifiedName()
    if vtype == VariantType.LocalizedText:
        return LocalizedText()
    if vtype == VariantType.ExtensionObject:
        return ExtensionObject()
    if vtype == VariantType.DataValue:
        return DataValue()
    if vtype == VariantType.Variant:
        return Variant()
    raise RuntimeError(f"function take a uatype as argument, got: {vtype}")


basetype_by_datatype = {}
basetype_datatypes = {}


# register of alias of basetypes
def register_basetype(name, nodeid, class_type):
    """
    Register a new alias of basetypes for automatic decoding and make them available in ua module
    """
    _logger.info("registering new basetype alias: %s %s %s", name, nodeid, class_type)
    basetype_by_datatype[nodeid] = name
    basetype_datatypes[class_type] = nodeid
    import asyncua.ua

    setattr(asyncua.ua, name, class_type)


# register of custom enums (Those loaded with load_enums())
enums_by_datatype = {}
enums_datatypes = {}


def register_enum(name, nodeid, class_type):
    """
    Register a new enum for automatic decoding and make them available in ua module
    """
    _logger.info("registering new enum: %s %s %s", name, nodeid, class_type)
    enums_by_datatype[nodeid] = class_type
    enums_datatypes[class_type] = nodeid
    import asyncua.ua

    setattr(asyncua.ua, name, class_type)


# These dictionaries are used to register extensions classes for automatic
# decoding and encoding
extension_objects_by_datatype = {}  # Dict[Datatype, type]
extension_objects_by_typeid = {}  # Dict[EncodingId, type]
extension_object_typeids = {}
datatype_by_extension_object = {}


def register_extension_object(name, encoding_nodeid, class_type, datatype_nodeid=None):
    """
    Register a new extension object for automatic decoding and make them available in ua module
    """
    _logger.info(
        "registering new extension object: %s %s %s %s",
        name,
        encoding_nodeid,
        class_type,
        datatype_nodeid,
    )
    if datatype_nodeid:
        extension_objects_by_datatype[datatype_nodeid] = class_type
        datatype_by_extension_object[class_type] = datatype_nodeid
    extension_objects_by_typeid[encoding_nodeid] = class_type
    extension_object_typeids[name] = encoding_nodeid
    # FIXME: Next line is not exactly a Python best practices, so feel free to propose something else
    # add new extensions objects to ua modules to automate decoding
    import asyncua.ua

    setattr(asyncua.ua, name, class_type)


def get_extensionobject_class_type(typeid):
    """
    Returns the registered class type for typid of an extension object
    """
    if typeid in extension_objects_by_typeid:
        return extension_objects_by_typeid[typeid]
    return None


class SecurityPolicyType(Enum):
    """
    The supported types of SecurityPolicy.

    "None"
    "Basic128Rsa15_Sign"
    "Basic128Rsa15_SignAndEncrypt"
    "Basic256_Sign"
    "Basic256_SignAndEncrypt"
    "Basic256Sha256_Sign"
    "Basic256Sha256_SignAndEncrypt"

    """

    NoSecurity = 0
    Basic128Rsa15_Sign = 1
    Basic128Rsa15_SignAndEncrypt = 2
    Basic256_Sign = 3
    Basic256_SignAndEncrypt = 4
    Basic256Sha256_Sign = 5
    Basic256Sha256_SignAndEncrypt = 6
    Aes128Sha256RsaOaep_Sign = 7
    Aes128Sha256RsaOaep_SignAndEncrypt = 8
