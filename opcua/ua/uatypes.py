"""
implement ua datatypes
"""

import logging
from enum import Enum, IntEnum
from calendar import timegm
import os
import uuid
import re
import itertools
from datetime import datetime, timedelta, MAXYEAR, tzinfo

from opcua.ua import status_codes
from .uaerrors import UaError, UaStatusCodeError, UaStringParsingError

logger = logging.getLogger(__name__)


EPOCH_AS_FILETIME = 116444736000000000  # January 1, 1970 as MS file time
HUNDREDS_OF_NANOSECONDS = 10000000
FILETIME_EPOCH_AS_DATETIME = datetime(1601, 1, 1)


class UTC(tzinfo):
    """
    UTC
    """

    def utcoffset(self, dt):
        return timedelta(0)

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return timedelta(0)


def datetime_to_win_epoch(dt):
    """method copied from David Buxton <david@gasmark6.com> sample code"""
    if (dt.tzinfo is None) or (dt.tzinfo.utcoffset(dt) is None):
        dt = dt.replace(tzinfo=UTC())
    ft = EPOCH_AS_FILETIME + (timegm(dt.timetuple()) * HUNDREDS_OF_NANOSECONDS)
    return ft + (dt.microsecond * 10)


def get_win_epoch():
    return win_epoch_to_datetime(0)


def win_epoch_to_datetime(epch):
    try:
        return FILETIME_EPOCH_AS_DATETIME + timedelta(microseconds=epch // 10)
    except OverflowError:
        # FILETIMEs after 31 Dec 9999 can't be converted to datetime
        logger.warning('datetime overflow: %s', epch)
        return datetime(MAXYEAR, 12, 31, 23, 59, 59, 999999)


class _FrozenClass(object):
    """
    Make it impossible to add members to a class.
    Not pythonic at all but we found out it prevents many many
    bugs in use of protocol structures
    """
    _freeze = False

    def __setattr__(self, key, value):
        if self._freeze and not hasattr(self, key):
            raise TypeError(f"Error adding member '{key}' to class '{self.__class__.__name__}', class is frozen, members are {self.__dict__.keys()}")
        object.__setattr__(self, key, value)


if "PYOPCUA_TYPO_CHECK" in os.environ:
    # typo check is cpu consuming, but it will make debug easy.
    # set PYOPCUA_TYPO_CHECK will make all uatype classes inherit from _FrozenClass
    logger.warning('uaypes typo checking is active')
    FrozenClass = _FrozenClass
else:
    FrozenClass = object


class ValueRank(IntEnum):
    """
    Defines dimensions of a variable.
    This enum does not support all cases since ValueRank support any n>0
    but since it is an IntEnum it can be replace by a normal int
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
            raise ValueError(f"Argument should be an int, we received {the_int} fo type {type(the_int)}")
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
        """ Iterate over the bits in n.

            e.g. bits(44) yields at 2, 3, 5
        """
        if not n >= 0:  # avoid infinite recursion
            raise ValueError()
        pos = 0
        while n:
            if n & 0x1:
                yield pos
            n = n // 2
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


class StatusCode(FrozenClass):
    """
    :ivar value:
    :vartype value: int
    :ivar name:
    :vartype name: string
    :ivar doc:
    :vartype doc: string
    """

    ua_types = [("value", "UInt32")]

    def __init__(self, value=0):
        if isinstance(value, str):
            self.name = value
            self.value = getattr(status_codes.StatusCodes, value)
        else:
            self.value = value
            self.name, self.doc = status_codes.get_name_and_doc(value)
        self._freeze = True

    def check(self):
        """
        Raises an exception if the status code is anything else than 0 (good).

        Use the is_good() method if you do not want an exception.
        """
        if not self.is_good():
            raise UaStatusCodeError(self.value)

    def is_good(self):
        """
        return True if status is Good.
        """
        mask = 3 << 30
        if mask & self.value:
            return False
        else:
            return True

    def __str__(self):
        return f'StatusCode({self.name})'

    __repr__ = __str__

    def __eq__(self, other):
        return self.value == other.value

    def __ne__(self, other):
        return not self.__eq__(other)


class NodeIdType(IntEnum):
    TwoByte = 0
    FourByte = 1
    Numeric = 2
    String = 3
    Guid = 4
    ByteString = 5


class NodeId(object):
    """
    NodeId Object

    Args:
        identifier: The identifier might be an int, a string, bytes or a Guid
        namespaceidx(int): The index of the namespace
        nodeidtype(NodeIdType): The type of the nodeid if it cannor be guess or you want something special like twobyte nodeid or fourbytenodeid


    :ivar Identifier:
    :vartype Identifier: NodeId
    :ivar NamespaceIndex:
    :vartype NamespaceIndex: Int
    :ivar NamespaceUri:
    :vartype NamespaceUri: String
    :ivar ServerIndex:
    :vartype ServerIndex: Int
    """

    def __init__(self, identifier=None, namespaceidx=0, nodeidtype=None):

        self.Identifier = identifier
        self.NamespaceIndex = namespaceidx
        self.NodeIdType = nodeidtype
        self.NamespaceUri = ""
        self.ServerIndex = 0
        self._freeze = True
        if self.Identifier is None:
            self.Identifier = 0
            self.NodeIdType = NodeIdType.TwoByte
            return
        if self.NodeIdType is None:
            if isinstance(self.Identifier, int):
                self.NodeIdType = NodeIdType.Numeric
            elif isinstance(self.Identifier, str):
                self.NodeIdType = NodeIdType.String
            elif isinstance(self.Identifier, bytes):
                self.NodeIdType = NodeIdType.ByteString
            elif isinstance(self.Identifier, uuid.UUID):
                self.NodeIdType = NodeIdType.Guid
            else:
                raise UaError("NodeId: Could not guess type of NodeId, set NodeIdType")

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
        if self.NodeIdType == NodeIdType.Guid and re.match(b'0.', self.Identifier):
            return True
        return False

    @staticmethod
    def from_string(string):
        try:
            return NodeId._from_string(string)
        except ValueError as ex:
            raise UaStringParsingError(f"Error parsing string {string}", ex)

    @staticmethod
    def _from_string(string):
        l = string.split(";")
        identifier = None
        namespace = 0
        ntype = None
        srv = None
        nsu = None
        for el in l:
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
                identifier = v
            elif k == "b":
                ntype = NodeIdType.ByteString
                identifier = v
            elif k == "srv":
                srv = v
            elif k == "nsu":
                nsu = v
        if identifier is None:
            raise UaStringParsingError(f"Could not find identifier in string: {string}")
        nodeid = NodeId(identifier, namespace, ntype)
        nodeid.NamespaceUri = nsu
        nodeid.ServerIndex = srv
        return nodeid

    def to_string(self):
        string = []
        if self.NamespaceIndex != 0:
            string.append("ns={0}".format(self.NamespaceIndex))
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
        string.append("{0}={1}".format(ntype, self.Identifier))
        if self.ServerIndex:
            string.append("srv={}".format(self.ServerIndex))
        if self.NamespaceUri:
            string.append("nsu={0}".format(self.NamespaceUri))
        return ";".join(string)

    def __str__(self):
        return f"{self.NodeIdType.name}NodeId({self.to_string()})"

    __repr__ = __str__

    def to_binary(self):
        import opcua
        return opcua.ua.ua_binary.nodeid_to_binary(self)


class TwoByteNodeId(NodeId):
    def __init__(self, identifier):
        NodeId.__init__(self, identifier, 0, NodeIdType.TwoByte)


class FourByteNodeId(NodeId):
    def __init__(self, identifier, namespace=0):
        NodeId.__init__(self, identifier, namespace, NodeIdType.FourByte)


class NumericNodeId(NodeId):
    def __init__(self, identifier, namespace=0):
        NodeId.__init__(self, identifier, namespace, NodeIdType.Numeric)


class ByteStringNodeId(NodeId):
    def __init__(self, identifier, namespace=0):
        NodeId.__init__(self, identifier, namespace, NodeIdType.ByteString)


class GuidNodeId(NodeId):
    def __init__(self, identifier, namespace=0):
        NodeId.__init__(self, identifier, namespace, NodeIdType.Guid)


class StringNodeId(NodeId):
    def __init__(self, identifier, namespace=0):
        NodeId.__init__(self, identifier, namespace, NodeIdType.String)


ExpandedNodeId = NodeId


class QualifiedName(FrozenClass):
    """
    A string qualified with a namespace index.
    """

    ua_types = [
        ('NamespaceIndex', 'UInt16'),
        ('Name', 'String'),
    ]

    def __init__(self, name=None, namespaceidx=0):
        if not isinstance(namespaceidx, int):
            raise UaError(f"namespaceidx must be an int not {namespaceidx} of type {type(namespaceidx)}")
        self.NamespaceIndex = namespaceidx
        self.Name = name
        self._freeze = True

    def to_string(self):
        return "{0}:{1}".format(self.NamespaceIndex, self.Name)

    @staticmethod
    def from_string(string):
        if ":" in string:
            try:
                idx, name = string.split(":", 1)
                idx = int(idx)
            except (TypeError, ValueError) as ex:
                raise UaStringParsingError(f"Error parsing string {string}", ex)
        else:
            idx = 0
            name = string
        return QualifiedName(name, idx)

    def __eq__(self, bname):
        return isinstance(bname,
                          QualifiedName) and self.Name == bname.Name and self.NamespaceIndex == bname.NamespaceIndex

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if not isinstance(other, QualifiedName):
            raise TypeError(f"Cannot compare QualifiedName and {other}")
        if self.NamespaceIndex == other.NamespaceIndex:
            return self.Name < other.Name
        else:
            return self.NamespaceIndex < other.NamespaceIndex

    def __str__(self):
        return f'QualifiedName({self.NamespaceIndex}:{self.Name})'

    __repr__ = __str__


class LocalizedText(FrozenClass):
    """
    A string qualified with a namespace index.
    """

    ua_switches = {
        'Locale': ('Encoding', 0),
        'Text': ('Encoding', 1),
    }

    ua_types = (
            ('Encoding', 'Byte'), 
            ('Locale', 'String'), 
            ('Text', 'String'), )

    def __init__(self, text=None):
        self.Encoding = 0
        if text is not None and not isinstance(text, str):
            raise ValueError(f"A LocalizedText object takes a string as argument, not a {text}, {type(text)}")
        self.Text = text
        if self.Text:
            self.Encoding |= (1 << 1)
        self.Locale = None
        self._freeze = True

    def to_string(self):
        # FIXME: use local
        if self.Text is None:
            return ""
        return self.Text

    def __str__(self):
        return f'LocalizedText(Encoding:{self.Encoding}, Locale:{self.Locale}, Text:{self.Text})'

    __repr__ = __str__

    def __eq__(self, other):
        if isinstance(other, LocalizedText) and self.Locale == other.Locale and self.Text == other.Text:
            return True
        return False

    def __ne__(self, other):
        return not self.__eq__(other)


class ExtensionObject(FrozenClass):
    """
    Any UA object packed as an ExtensionObject

    :ivar TypeId:
    :vartype TypeId: NodeId
    :ivar Body:
    :vartype Body: bytes
    """
    ua_switches = {
        'Body': ('Encoding', 0),
    }

    ua_types = (
            ("TypeId", "NodeId"), 
            ("Encoding", "Byte"), 
            ("Body", "ByteString"), 
            )

    def __init__(self):
        self.TypeId = NodeId()
        self.Encoding = 0
        self.Body = None
        self._freeze = True

    def __bool__(self):
        return self.Body is not None
    __nonzero__ = __bool__  # Python2 compatibilty

    def __str__(self):
        size = len(self.Body) if self.Body is not None else None
        return f'ExtensionObject(TypeId:{self.TypeId}, Encoding:{self.Encoding}, {size} bytes)'

    __repr__ = __str__


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


class VariantTypeCustom(object):
    """
    Looks like sometime we get variant with other values than those
    defined in VariantType.
    FIXME: We should not need this class, as far as I iunderstand the spec
    variants can only be of VariantType
    """

    def __init__(self, val):
        self.name = "Custom"
        self.value = val
        if self.value > 0b00111111:
            raise UaError(f"Cannot create VariantType. VariantType must be {0b111111} > x > {25}, received {val}")

    def __str__(self):
        return f"VariantType.Custom:{self.value}"

    __repr__ = __str__

    def __eq__(self, other):
        return self.value == other.value


class Variant(FrozenClass):
    """
    Create an OPC-UA Variant object.
    if no argument a Null Variant is created.
    if not variant type is given, attemps to guess type from python type
    if a variant is given as value, the new objects becomes a copy of the argument

    :ivar Value:
    :vartype Value: Any supported type
    :ivar VariantType:
    :vartype VariantType: VariantType
    :ivar Dimension:
    :vartype Dimensions: The length of each dimensions. Usually guessed from value.
    :ivar is_array:
    :vartype is_array: If the variant is an array. Usually guessed from value.
    """

    def __init__(self, value=None, varianttype=None, dimensions=None, is_array=None):
        self.Value = value
        self.VariantType = varianttype
        self.Dimensions = dimensions
        self.is_array = is_array
        if self.is_array is None:
            if isinstance(value, (list, tuple)):
                self.is_array = True
            else:
                self.is_array = False
        self._freeze = True
        if isinstance(value, Variant):
            self.Value = value.Value
            self.VariantType = value.VariantType
        if self.VariantType is None:
            self.VariantType = self._guess_type(self.Value)
        if self.Value is None and not self.is_array and self.VariantType not in (VariantType.Null, VariantType.String,
                                                                                 VariantType.DateTime):
            raise UaError(f"Non array Variant of type {self.VariantType} cannot have value None")
        if self.Dimensions is None and isinstance(self.Value, (list, tuple)):
            dims = get_shape(self.Value)
            if len(dims) > 1:
                self.Dimensions = dims

    def __eq__(self, other):
        if isinstance(other, Variant) and self.VariantType == other.VariantType and self.Value == other.Value:
            return True
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def _guess_type(self, val):
        if isinstance(val, (list, tuple)):
            error_val = val
        while isinstance(val, (list, tuple)):
            if len(val) == 0:
                raise UaError(f"could not guess UA type of variable {error_val}")
            val = val[0]
        if val is None:
            return VariantType.Null
        elif isinstance(val, bool):
            return VariantType.Boolean
        elif isinstance(val, float):
            return VariantType.Double
        elif isinstance(val, IntEnum):
            return VariantType.Int32
        elif isinstance(val, int):
            return VariantType.Int64
        elif isinstance(val, str):
            return VariantType.String
        elif isinstance(val, bytes):
            return VariantType.ByteString
        elif isinstance(val, datetime):
            return VariantType.DateTime
        elif isinstance(val, uuid.UUID):
            return VariantType.Guid
        else:
            if isinstance(val, object):
                try:
                    return getattr(VariantType, val.__class__.__name__)
                except AttributeError:
                    return VariantType.ExtensionObject
            else:
                raise UaError(f"Could not guess UA type of {val} with type {type(val)}, specify UA type")

    def __str__(self):
        return f"Variant(val:{self.Value!s},type:{self.VariantType})"

    __repr__ = __str__

    def to_binary(self):
        from .ua_binary import variant_to_binary
        return variant_to_binary(self)


def _split_list(l, n):
    n = max(1, n)
    return [l[i:i + n] for i in range(0, len(l), n)]


def flatten_and_get_shape(mylist):
    dims = []
    dims.append(len(mylist))
    while isinstance(mylist[0], (list, tuple)):
        dims.append(len(mylist[0]))
        mylist = [item for sublist in mylist for item in sublist]
        if len(mylist) == 0:
            break
    return mylist, dims


def flatten(mylist):
    if mylist is None:
        return None
    elif len(mylist) == 0:
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


class DataValue(FrozenClass):
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

    ua_switches = {
        'Value': ('Encoding', 0),
        'StatusCode': ('Encoding', 1),
        'SourceTimestamp': ('Encoding', 2),
        'ServerTimestamp': ('Encoding', 3),
        'SourcePicoseconds': ('Encoding', 4),
        'ServerPicoseconds': ('Encoding', 5),
    }

    ua_types = (
            ('Encoding', 'Byte'), 
            ('Value', 'Variant'), 
            ('StatusCode', 'StatusCode'), 
            ('SourceTimestamp', 'DateTime'),
            ('SourcePicoseconds', 'UInt16'), 
            ('ServerTimestamp', 'DateTime'), 
            ('ServerPicoseconds', 'UInt16'), 
            )

    def __init__(self, variant=None, status=None):
        self.Encoding = 0
        if not isinstance(variant, Variant):
            variant = Variant(variant)
        self.Value = variant
        if status is None:
            self.StatusCode = StatusCode()
        else:
            self.StatusCode = status
        self.SourceTimestamp = None  # DateTime()
        self.SourcePicoseconds = None
        self.ServerTimestamp = None  # DateTime()
        self.ServerPicoseconds = None
        self._freeze = True

    def __str__(self):
        s = []
        if self.StatusCode is not None:
            s.append(f', StatusCode:{self.StatusCode}')
        if self.SourceTimestamp is not None:
            s.append(f', SourceTimestamp:{self.SourceTimestamp}')
        if self.ServerTimestamp is not None:
            s.append(f', ServerTimestamp:{self.ServerTimestamp}')
        if self.SourcePicoseconds is not None:
            s.append(f', SourcePicoseconds:{self.SourcePicoseconds}')
        if self.ServerPicoseconds is not None:
            s.append(f', ServerPicoseconds:{self.ServerPicoseconds}')
        return f'DataValue(Value:{self.Value}{"".join(s)})'

    __repr__ = __str__


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
    else:
        return VariantTypeCustom(int_type)


def get_default_value(vtype):
    """
    Given a variant type return default value for this type
    """
    if vtype == VariantType.Null:
        return None
    elif vtype == VariantType.Boolean:
        return False
    elif vtype in (VariantType.SByte, VariantType.Byte):
        return 0
    elif vtype == VariantType.ByteString:
        return b""
    elif 4 <= vtype.value <= 9:
        return 0
    elif vtype in (VariantType.Float, VariantType.Double):
        return 0.0
    elif vtype == VariantType.String:
        return None  # a string can be null
    elif vtype == VariantType.DateTime:
        return datetime.utcnow()
    elif vtype == VariantType.Guid:
        return uuid.uuid4()
    elif vtype == VariantType.XmlElement:
        return None  #Not sure this is correct
    elif vtype == VariantType.NodeId:
        return NodeId()
    elif vtype == VariantType.ExpandedNodeId:
        return NodeId()
    elif vtype == VariantType.StatusCode:
        return StatusCode()
    elif vtype == VariantType.QualifiedName:
        return QualifiedName()
    elif vtype == VariantType.LocalizedText:
        return LocalizedText()
    elif vtype == VariantType.ExtensionObject:
        return ExtensionObject()
    elif vtype == VariantType.DataValue:
        return DataValue()
    elif vtype == VariantType.Variant:
        return Variant()
    else:
        raise RuntimeError(f"function take a uatype as argument, got: {vtype}")


# These dictionnaries are used to register extensions classes for automatic
# decoding and encoding
extension_object_classes = {}
extension_object_ids = {}


def register_extension_object(name, nodeid, class_type):
    """
    Register a new extension object for automatic decoding and make them available in ua module
    """
    logger.info("registring new extension object: %s %s %s", name, nodeid, class_type)
    extension_object_classes[nodeid] = class_type
    extension_object_ids[name] = nodeid
    # FIXME: Next line is not exactly a Python best practices, so feel free to propose something else
    # add new extensions objects to ua modules to automate decoding
    import opcua.ua
    setattr(opcua.ua, name, class_type)


def get_extensionobject_class_type(typeid):
    """
    Returns the registered class type for typid of an extension object
    """
    if typeid in extension_object_classes:
        return extension_object_classes[typeid]
    else:
        return None


class SecurityPolicyType(Enum):
    """
    The supported types of SecurityPolicy.
    
    "None"
    "Basic128Rsa15_Sign"
    "Basic128Rsa15_SignAndEncrypt"
    "Basic256_Sign"
    "Basic256_SignAndEncrypt"

    """

    NoSecurity = 0
    Basic128Rsa15_Sign = 1
    Basic128Rsa15_SignAndEncrypt = 2
    Basic256_Sign = 3
    Basic256_SignAndEncrypt = 4
