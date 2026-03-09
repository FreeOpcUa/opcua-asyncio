import struct
from dataclasses import dataclass, field

from asyncua.common import utils
from asyncua.ua import uaprotocol_auto as auto
from asyncua.ua import uatypes

OPC_TCP_SCHEME = "opc.tcp"


@dataclass(slots=True)
class Hello:
    ProtocolVersion: uatypes.UInt32 = 0
    # the following values could be set to 0 (meaning no limits)
    # unfortunately many servers do not support it
    # even newer version of prosys is broken,
    # so we set then to a high value known to work most places
    ReceiveBufferSize: uatypes.UInt32 = 2**31 - 1
    SendBufferSize: uatypes.UInt32 = 2**31 - 1
    MaxMessageSize: uatypes.UInt32 = 2**31 - 1
    MaxChunkCount: uatypes.UInt32 = 2**31 - 1
    EndpointUrl: uatypes.String = ""


@dataclass(slots=True)
class ReverseHello:
    """
    OPC UA ReverseHello message (Part 6 §7.1.3).
    Sent by the server immediately after establishing a reverse TCP connection to a client.
    The client uses ServerUri / EndpointUrl to decide whether to accept and open a Secure Channel.
    """

    ServerUri: uatypes.String = ""
    EndpointUrl: uatypes.String = ""


class MessageType:
    Invalid: bytes = b"INV"  # FIXME: check value
    Hello: bytes = b"HEL"
    Acknowledge: bytes = b"ACK"
    Error: bytes = b"ERR"
    ReverseHello: bytes = b"RHE"
    SecureOpen: bytes = b"OPN"
    SecureClose: bytes = b"CLO"
    SecureMessage: bytes = b"MSG"


class ChunkType:
    Invalid: bytes = b"0"  # FIXME check
    Single: bytes = b"F"
    Intermediate: bytes = b"C"
    Abort: bytes = b"A"  # when an error occurred and the Message is aborted (body is ErrorMessage)


@dataclass(slots=False)
class Header:
    MessageType: MessageType = None
    ChunkType: ChunkType = None
    ChannelId: int = 0
    body_size = 0
    packet_size = 0
    header_size = 8

    def add_size(self, size):
        self.body_size += size

    @staticmethod
    def max_size():
        return struct.calcsize("<3scII")


@dataclass(slots=True)
class ErrorMessage:
    Error: uatypes.StatusCode = field(default_factory=lambda: uatypes.StatusCode())
    Reason: uatypes.String = field(default_factory=lambda: uatypes.String())


@dataclass(slots=True)
class Acknowledge:
    ProtocolVersion: uatypes.UInt32 = 0
    ReceiveBufferSize: uatypes.UInt32 = 65536
    SendBufferSize: uatypes.UInt32 = 65536
    MaxMessageSize: uatypes.UInt32 = 0  # No limits
    MaxChunkCount: uatypes.UInt32 = 0  # No limits


@dataclass(slots=True)
class AsymmetricAlgorithmHeader:
    SecurityPolicyURI: uatypes.String = "http://opcfoundation.org/UA/SecurityPolicy#None"
    SenderCertificate: uatypes.ByteString = None
    ReceiverCertificateThumbPrint: uatypes.ByteString = None

    def __str__(self):
        len(self.SenderCertificate) if self.SenderCertificate is not None else None
        size2 = len(self.ReceiverCertificateThumbPrint) if self.ReceiverCertificateThumbPrint is not None else None
        return (
            f"{self.__class__.__name__}(SecurityPolicy:{self.SecurityPolicyURI},"
            f" certificatesize:{size2}, receiverCertificatesize:{size2} )"
        )

    __repr__ = __str__


@dataclass(slots=True)
class SymmetricAlgorithmHeader:
    TokenId: uatypes.UInt32 = 0

    @staticmethod
    def max_size():
        return struct.calcsize("<I")


@dataclass(slots=True)
class SequenceHeader:
    SequenceNumber: uatypes.UInt32 = None
    RequestId: uatypes.UInt32 = None

    @staticmethod
    def max_size():
        return struct.calcsize("<II")


class Message:
    def __init__(self, chunks):
        self._chunks = chunks

    def request_id(self):
        return self._chunks[0].SequenceHeader.RequestId

    def SequenceHeader(self):
        return self._chunks[0].SequenceHeader

    def SecurityHeader(self):
        return self._chunks[0].SecurityHeader

    def body(self):
        body = b"".join([c.Body for c in self._chunks])
        return utils.Buffer(body)


# FIXES for missing switchfield in NodeAttributes classes
ana = auto.NodeAttributesMask


@dataclass(slots=True)
class ObjectAttributes(auto.ObjectAttributes):
    def __post_init__(self):
        object.__setattr__(
            self,
            "SpecifiedAttributes",
            ana.DisplayName | ana.Description | ana.WriteMask | ana.UserWriteMask | ana.EventNotifier,
        )


@dataclass(slots=True)
class ObjectTypeAttributes(auto.ObjectTypeAttributes):
    def __post_init__(self):
        object.__setattr__(
            self,
            "SpecifiedAttributes",
            ana.DisplayName | ana.Description | ana.WriteMask | ana.UserWriteMask | ana.IsAbstract,
        )


@dataclass(slots=True)
class VariableAttributes(auto.VariableAttributes):
    ArrayDimensions: list[uatypes.UInt32] = None
    Historizing: uatypes.Boolean = False
    AccessLevel: uatypes.Byte = auto.AccessLevel.CurrentRead.mask
    UserAccessLevel: uatypes.Byte = auto.AccessLevel.CurrentRead.mask
    SpecifiedAttributes: uatypes.UInt32 = (
        ana.DisplayName
        | ana.Description
        | ana.WriteMask
        | ana.UserWriteMask
        | ana.Value
        | ana.DataType
        | ana.ValueRank
        | ana.ArrayDimensions
        | ana.AccessLevel
        | ana.UserAccessLevel
        | ana.MinimumSamplingInterval
        | ana.Historizing
    )


@dataclass(slots=True)
class VariableTypeAttributes(auto.VariableTypeAttributes):
    def __post_init__(self):
        object.__setattr__(
            self,
            "SpecifiedAttributes",
            (
                ana.DisplayName
                | ana.Description
                | ana.WriteMask
                | ana.UserWriteMask
                | ana.Value
                | ana.DataType
                | ana.ValueRank
                | ana.ArrayDimensions
                | ana.IsAbstract
            ),
        )


@dataclass(slots=True)
class MethodAttributes(auto.MethodAttributes):
    def __post_init__(self):
        object.__setattr__(
            self,
            "SpecifiedAttributes",
            ana.DisplayName | ana.Description | ana.WriteMask | ana.UserWriteMask | ana.Executable | ana.UserExecutable,
        )


@dataclass(slots=True)
class ReferenceTypeAttributes(auto.ReferenceTypeAttributes):
    def __post_init__(self):
        object.__setattr__(
            self,
            "SpecifiedAttributes",
            (
                ana.DisplayName
                | ana.Description
                | ana.WriteMask
                | ana.UserWriteMask
                | ana.IsAbstract
                | ana.Symmetric
                | ana.InverseName
            ),
        )


# FIXME: changes in that class donnot seem to be part of spec as of 1.04
# not sure what the spec expect, maybe DataTypeDefinition must be set using an extra call...
# maybe it will be part of spec in 1.05??? no ideas
@dataclass(slots=True)
class DataTypeAttributes(auto.DataTypeAttributes):
    DataTypeDefinition: uatypes.ExtensionObject = field(default_factory=auto.ExtensionObject)

    def __post_init__(self):
        object.__setattr__(
            self,
            "SpecifiedAttributes",
            (
                ana.DisplayName
                | ana.Description
                | ana.WriteMask
                | ana.UserWriteMask
                | ana.IsAbstract
                | ana.DataTypeDefinition
            ),
        )


# we now need to register DataTypeAttributes since we added a new attribute
nid = uatypes.FourByteNodeId(auto.ObjectIds.DataTypeAttributes_Encoding_DefaultBinary)
uatypes.extension_objects_by_typeid[nid] = DataTypeAttributes
uatypes.extension_object_typeids["DataTypeAttributes"] = nid


@dataclass(slots=True)
class ViewAttributes(auto.ViewAttributes):
    def __post_init__(self):
        object.__setattr__(
            self,
            "SpecifiedAttributes",
            (
                ana.DisplayName
                | ana.Description
                | ana.WriteMask
                | ana.UserWriteMask
                | ana.ContainsNoLoops
                | ana.EventNotifier
            ),
        )


@dataclass(slots=True)
class Argument(auto.Argument):
    ValueRank: auto.Int32 = -1


@dataclass(slots=True)
class XmlElement:
    """
    An XML element encoded as a UTF-8 string.
    :ivar Value:
    :vartype Value: String
    """

    Value: uatypes.String = ""


# Default is StatusValue -> https://reference.opcfoundation.org/Core/Part4/v105/docs/7.10#Table134
@dataclass(slots=True)
class DataChangeFilter(auto.DataChangeFilter):
    Trigger = auto.DataChangeTrigger.StatusValue
